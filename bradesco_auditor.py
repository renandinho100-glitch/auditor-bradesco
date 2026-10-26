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
        """Lê o arquivo XML TISS e extrai os procedimentos e materiais cobrados."""
        try:
            tree = ET.parse(arquivo_xml)
            root = tree.getroot()
        except Exception as e:
            return None, f"Erro ao ler o XML: {e}"

        # Remove namespaces para facilitar a busca das tags TISS independentemente da versão
        for elem in root.iter():
            if '}' in elem.tag:
                elem.tag = elem.tag.split('}', 1)[1]

        procedimentos_encontrados = []
        materiais_encontrados = []

        # Varre procedimentos executados (ex: em guias de consulta, SADT ou internação)
        for proc in root.iter('procedimentoExecutado'):
            codigo = proc.findtext('codigoProcedimento')
            descricao = proc.findtext('descricaoProcedimento')
            valor = proc.findtext('valorExecutado')
            if codigo:
                procedimentos_encontrados.append({
                    "codigo": codigo,
                    "descricao": descricao or "Procedimento TUSS",
                    "valor": float(valor) if valor else 0.0
                })

        # Varre materiais / taxas / insumos cobrados
        for mat in root.iter('materialConsumido'): # ou tags equivalentes de insumos do lote
            codigo_mat = mat.findtext('codigoItem') or mat.findtext('codigoMaterial')
            desc_mat = mat.findtext('descricaoItem')
            qtd = mat.findtext('quantidadeExecutada')
            valor_unit = mat.findtext('valorUnitario')
            if codigo_mat:
                materiais_encontrados.append({
                    "codigo": codigo_mat,
                    "descricao": desc_mat or "Material/Insumo",
                    "quantidade": float(qtd) if qtd else 1.0,
                    "valor_unitario": float(valor_unit) if valor_unit else 0.0
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
