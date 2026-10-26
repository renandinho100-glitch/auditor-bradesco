import streamlit as st
import pandas as pd
from bradesco_auditor import BradescoAuditor

st.set_page_config(
    page_title="Auditor de Contas - Bradesco Saúde",
    page_icon="🏥",
    layout="wide"
)

st.title("🏥 Painel de Auditoria e Prevenção de Glosas")
st.markdown("Ferramenta integrada de cruzamento de guias e regras do Bradesco Saúde.")

# Inicializando o auditor com o JSON de regras do repositório
@st.cache_resource
def carregar_auditor():
    return BradescoAuditor("schema_bradesco_gig.json")

try:
    auditor = carregar_auditor()
    st.sidebar.success("Base de regras GIG carregada com sucesso!")
except Exception as e:
    st.sidebar.error(f"Erro ao carregar regras: {e}")

# Área de Upload
uploaded_file = st.sidebar.file_uploader("Envie sua planilha de lançamentos (CSV)", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.subheader("📊 Prévia dos Dados Carregados")
    st.dataframe(df.head())
    
    if st.button("Executar Auditoria"):
        st.success("Auditoria simulada com sucesso!")
        # Aqui você pode chamar os métodos do seu auditor no futuro
else:
    st.info("👈 Envie um arquivo CSV na barra lateral para começar a análise.")
