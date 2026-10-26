import streamlit as st
import pandas as pd
from bradesco_auditor import BradescoAuditor

st.set_page_config(
    page_title="Auditor de Contas - Bradesco Saúde",
    page_icon="🏥",
    layout="wide"
)

st.title("🏥 Painel de Auditoria e Prevenção de Glosas")
st.markdown("Ferramenta para cruzamento de contas médicas com base nos Aditivos e Tabelas GIG do Bradesco Saúde.")

# Inicializar o auditor
@st.cache_resource
def carregar_auditor():
    return BradescoAuditor("schema_bradesco_gig.json")

auditor = carregar_auditor()

# Sidebar para upload de arquivos
st.sidebar.header("📁 Importação de Dados")
uploaded_file = st.sidebar.file_uploader("Envie o arquivo de lançamentos (CSV ou XML)", type=["csv", "xml"])

if uploaded_file is not None:
    st.success("Arquivo carregado com sucesso!")
    # Aqui você colocaria a lógica para ler o arquivo com pandas e rodar o auditor.
    # Exemplo visual:
    st.subheader("📊 Resumo da Auditoria")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Itens Analisados", "142")
    col2.metric("Potenciais Glosas Evitadas", "R$ 1.250,00", delta="-12%")
    col3.metric("Pacotes Identificados", "18")
else:
    st.info("👈 Por favor, faça o upload de um arquivo na barra lateral para iniciar a auditoria.")