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

try:
    auditor = carregar_auditor()
    st.sidebar.success("Base de regras carregada com sucesso!")
except Exception as e:
    st.sidebar.error(f"Erro ao carregar regras: {e}")

# Sidebar para upload de arquivos
st.sidebar.header("📁 Importação de Dados")
uploaded_file = st.sidebar.file_uploader("Envie o arquivo de lançamentos (CSV)", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.success("Arquivo carregado com sucesso!")
    st.subheader("📊 Prévia dos Dados")
    st.dataframe(df.head())
else:
    st.info("👈 Por favor, faça o upload de um arquivo CSV na barra lateral para iniciar a auditoria.")
