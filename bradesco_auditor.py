import json
import pandas as pd

class BradescoAuditor:
    def __init__(self, caminho_schema: str):
        with open(caminho_schema, 'r', encoding='utf-8') as f:
            self.dados = json.load(f)
        
        self.pacotes = pd.DataFrame(self.dados.get("pacotes_padronizados", []))
        self.materiais = pd.DataFrame(self.dados.get("tabela_materiais_gig", []))

    def validar_pacote_procedimento(self, lista_tuss_executados: list):
        """Identifica se os códigos TUSS executados correspondem a algum pacote padronizado."""
        encontrados = []
        for _, pacote in self.pacotes.iterrows():
            inclusos = set(pacote['tuss_inclusos'])
            if inclusos.issubset(set(lista_tuss_executados)):
                encontrados.append({
                    "codigo_pacote": pacote['codigo_pacote'],
                    "nome_pacote": pacote['nome_pacote'],
                    "valor_limite": pacote['valor_limite']
                })
        return encontrados

    def auditar_item_material(self, id_orizon: str, valor_cobrado: float):
        """Verifica se o material está na tabela GIG e se o preço está dentro do teto."""
        material = self.materiais[self.materiais['id_orizon'] == id_orizon]
        if material.empty:
            return {"status": "GLOSA", "motivo": "Material não encontrado na Tabela GIG"}
        
        preco_tabela = material.iloc[0]['preco_unitario']
        if valor_cobrado > preco_tabela:
        
            return {"status": "DIVERGÊNCIA DE PREÇO", "teto": preco_tabela, "cobrado": valor_cobrado}
        
        return {"status": "APROVADO"}
