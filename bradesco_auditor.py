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
        """Lê o ficheiro XML TISS extraindo procedimentos e itens de outrasDespesas."""
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

        # 1. Extração de Procedimentos Executados
        for proc in root.iter('procedimentoExecutado'):
            codigo = proc.findtext('codigoProcedimento')
            descricao = proc.findtext('descricaoProcedimento')
            valor = proc.findtext('valorUnitario') or proc.findtext('valorTotal')
            
            if codigo:
                procedimentos_encontrados.append({
                    "codigo": codigo,
                    "descricao": descricao or "Procedimento TUSS",
                    "valor": float(valor.replace(',', '.')) if valor and valor.replace('.', '', 1).isdigit() else 0.0
                })

        # 2. Extração de Materiais / Medicamentos / Taxas a partir de outrasDespesas -> servicosExecutados
        for serv in root.iter('servicosExecutados'):
            codigo = serv.findtext('codigoProcedimento') or serv.findtext('codigoItem') or serv.findtext('codigoMaterial')
            descricao = serv.findtext('descricaoProcedimento') or serv.findtext('descricaoItem')
            qtd = serv.findtext('quantidadeExecutada')
            valor_unit = serv.findtext('valorUnitario')
            
            if codigo:
                materiais_encontrados.append({
                    "codigo": codigo,
                    "descricao": descricao or "Material / Taxa / Insumo",
                    "quantidade": float(qtd.replace(',', '.')) if qtd and qtd.replace('.', '', 1).isdigit() else 1.0,
                    "valor_unitario": float(valor_unit.replace(',', '.')) if valor_unit and valor_unit.replace('.', '', 1).isdigit() else 0.0
                })

        return {
            "procedimentos": procedimentos_encontrados,
            "materiais": materiais_encontrados
        }, None

    def auditar_conta(self, dados_tiss):
        """Cruza os dados extraídos do XML com as regras da Tabela GIG."""
        codigos_tuss = [p['codigo'] for p in dados_tiss['procedimentos']]
        
        # 1. Identificação de Pacotes
        pacotes_aplicaveis = []
        for _, pacote in self.pacotes.iterrows():
            inclusos = set(pacote['tuss_inclusos'])
            if inclusos.issubset(set(codigos_tuss)):
                pacotes_aplicaveis.append(pacote['nome_pacote'])

        if not pacotes_aplicaveis and any(c in codigos_tuss for c in ['31309054', '31309038']):
            pacotes_aplicaveis.append("Pacote Cirúrgico Obstétrico (Cesariana)")

        # 2. Auditoria de Materiais e Insumos contra a Tabela GIG
        alertas_materiais = []
        for mat in dados_tiss['materiais']:
            item_gig = self.materiais[self.materiais['id_orizon'] == mat['codigo']]
            if not item_gig.empty:
                teto = float(item_gig.iloc[0]['preco_unitario'])
                if mat['valor_unitario'] > teto:
                    alertas_materiais.append({
                        "item": mat['codigo'],
                        "descricao": mat['descricao'],
                        "cobrado": mat['valor_unitario'],
                        "teto_permitido": teto,
                        "alerta": "Divergência de Preço (Acima do Teto GIG)"
                    })
            else:
                # Se não está na GIG e há pacotes aplicáveis, gera alerta de possível inclusão no pacote
                if len(pacotes_aplicaveis) > 0 and mat['valor_unitario'] > 0:
                    alertas_materiais.append({
                        "item": mat['codigo'],
                        "descricao": mat['descricao'],
                        "cobrado": mat['valor_unitario'],
                        "teto_permitido": 0.0,
                        "alerta": "Possível Glosa: Item cobrado em separado num procedimento em pacote"
                    })

        return {
            "pacotes_encontrados": pacotes_aplicaveis,
            "alertas_materiais": alertas_materiais,
            "total_procedimentos": len(codigos_tuss),
            "total_materiais": len(dados_tiss['materiais'])
        }
