import json
import xml.etree.ElementTree as ET
import pandas as pd

class BradescoAuditor:
    def __init__(self, caminho_schema: str):
        with open(caminho_schema, 'r', encoding='utf-8') as f:
            self.dados = json.load(f)
        
        self.pacotes = pd.DataFrame(self.dados.get("pacotes_padronizados", []))
        self.materiais = pd.DataFrame(self.dados.get("tabela_materiais_gig", []))

    def ler_xml_tiss(self, arquivo_xml):
        """Lê o ficheiro XML TISS de forma flexível e extrai os procedimentos e materiais."""
        try:
            xml_bytes = arquivo_xml.getvalue()
            root = ET.fromstring(xml_bytes)
        except Exception as e:
            return None, f"Erro ao processar o XML: {e}"

        # Remove namespaces para facilitar a pesquisa das tags TISS
        for elem in root.iter():
            if '}' in elem.tag:
                elem.tag = elem.tag.split('}', 1)[1]

        procedimentos_encontrados = []
        materiais_encontrados = []

        # Variações comuns de tags de procedimentos no padrão TISS
        tags_proc = ['procedimentoExecutado', 'procedimentoRealizado', 'procedimento', 'procedimentoADT']
        for tag in tags_proc:
            for proc in root.iter(tag):
                codigo = proc.findtext('codigoProcedimento') or proc.findtext('codigoTUSS') or proc.findtext('codigo')
                descricao = proc.findtext('descricaoProcedimento') or proc.findtext('descricao')
                valor = proc.findtext('valorExecutado') or proc.findtext('valor') or proc.findtext('valorTotal')
                if codigo and not any(p['codigo'] == codigo for p in procedimentos_encontrados):
                    procedimentos_encontrados.append({
                        "codigo": codigo,
                        "descricao": descricao or "Procedimento TUSS",
                        "valor": float(valor) if valor and valor.replace('.', '', 1).isdigit() else 0.0
                    })

        # Variações comuns de tags de materiais e despesas no padrão TISS
        tags_mat = ['materialConsumido', 'outrasDespesas', 'despesa', 'itemServico', 'materialMedicamento']
        for tag in tags_mat:
            for mat in root.iter(tag):
                codigo_mat = mat.findtext('codigoItem') or mat.findtext('codigoMaterial') or mat.findtext('codigo')
                desc_mat = mat.findtext('descricaoItem') or mat.findtext('descricao')
                qtd = mat.findtext('quantidadeExecutada') or mat.findtext('quantidade')
                valor_unit = mat.findtext('valorUnitario') or mat.findtext('valor')
                if codigo_mat and not any(m['codigo'] == codigo_mat for m in materiais_encontrados):
                    materiais_encontrados.append({
                        "codigo": codigo_mat,
                        "descricao": desc_mat or "Material/Insumo",
                        "quantidade": float(qtd) if qtd and qtd.replace('.', '', 1).isdigit() else 1.0,
                        "valor_unitario": float(valor_unit) if valor_unit and valor_unit.replace('.', '', 1).isdigit() else 0.0
                    })

        return {
            "procedimentos": procedimentos_encontrados,
            "materiais": materiais_encontrados
        }, None

    def auditar_conta(self, dados_tiss):
        """Cruza os dados do TISS com as regras de pacotes e tabela GIG."""
        codigos_tuss = [p['codigo'] for p in dados_tiss['procedimentos']]
        
        # 1. Verifica se se enquadra em algum Pacote Padronizado
        pacotes_aplicaveis = []
        for _, pacote in self.pacotes.iterrows():
            inclusos = set(pacote['tuss_inclusos'])
            if inclusos.issubset(set(codigos_tuss)):
                pacotes_aplicaveis.append(pacote['nome_pacote'])

        # 2. Audita materiais contra a Tabela GIG
        alertas_materiais = []
        for mat in dados_tiss['materiais']:
            item_gig = self.materiais[self.materiais['id_orizon'] == mat['codigo']]
            if not item_gig.empty:
                teto = item_gig.iloc[0]['preco_unitario']
                if mat['valor_unitario'] > teto:
                    alertas_materiais.append({
                        "item": mat['codigo'],
                        "descricao": mat['descricao'],
                        "cobrado": mat['valor_unitario'],
                        "teto_permitido": teto,
                        "alerta": "Divergência de Preço (Acima do Teto GIG)"
                    })
            else:
                if len(pacotes_aplicaveis) > 0:
                    alertas_materiais.append({
                        "item": mat['codigo'],
                        "descricao": mat['descricao'],
                        "cobrado": mat['valor_unitario'],
                        "teto_permitido": 0.0,
                        "alerta": "Possível Glosa: Material já incluso no Pacote Padronizado"
                    })

        return {
            "pacotes_encontrados": pacotes_aplicaveis,
            "alertas_materiais": alertas_materiais,
            "total_procedimentos": len(codigos_tuss),
            "total_materiais": len(dados_tiss['materiais'])
        }
