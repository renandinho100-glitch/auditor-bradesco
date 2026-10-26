import streamlit as st
import pandas as pd
from bradesco_auditor import BradescoAuditor

st.set_page_config(
    page_title="Auditor de Contas - Bradesco Saúde",
    page_icon="🏥",
    layout="wide"
)

st.title("🏥 Painel de Auditoria e Prevenção de Glosas (XML TISS)")
st.markdown("Faça o upload do arquivo XML de faturamento para cruzar com as regras e pacotes do Bradesco Saúde.")

# Inicializar o auditor
@st.cache_resource
def carregar_auditor():
    return BradescoAuditor("schema_bradesco_gig.json")

try:
    auditor = carregar_auditor()
    st.sidebar.success("Base de regras GIG carregada com sucesso!")
except Exception as e:
    st.sidebar.error(f"Erro ao carregar regras: {e}")

# Sidebar para upload de XML TISS
st.sidebar.header("📁 Importação de Lote")
uploaded_file = st.sidebar.file_uploader("Envie o arquivo XML TISS", type=["xml"])

if uploaded_file is not None:
    try:
        # Processa o XML utilizando a classe auditora
        dados_tiss, erro = auditor.ler_xml_tiss(uploaded_file)
        
        if erro:
            st.error(f"Erro na leitura do XML: {erro}")
        else:
            st.success("Arquivo XML TISS lido com sucesso!")
            
            # Executa a auditoria
            resultado = auditor.auditar_conta(dados_tiss)
            
            # Exibição de Métricas
            col1, col2, col3 = st.columns(3)
            col1.metric("Procedimentos TUSS Lidos", resultado["total_procedimentos"])
            col2.metric("Materiais / Insumos Lidos", resultado["total_materiais"])
            col3.metric("Pacotes Padronizados Detectados", len(resultado["pacotes_encontrados"]))
            
            # Detalhes dos Pacotes
            if resultado["pacotes_encontrados"]:
                st.info(f"💡 **Pacotes Aplicáveis Identificados:** {', '.join(resultado['pacotes_encontrados'])}")
            
            # Alertas de Materiais / Glosas
            st.subheader("⚠️ Relatório de Alertas e Divergências")
            if resultado["alertas_materiais"]:
                df_alertas = pd.DataFrame(resultado["alertas_materiais"])
                st.dataframe(df_alertas, use_container_width=True)
            else:
                st.success("Nenhuma divergência ou risco de glosa encontrado nos materiais deste arquivo!")
                
            # Exibir listagem pura dos procedimentos extraídos
            with st.expander("Ver Procedimentos Extraídos do XML"):
                st.dataframe(pd.DataFrame(dados_tiss["procedimentos"]), use_container_width=True)
                
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado ao processar o arquivo: {e}")
else:
    st.info("👈 Envie um arquivo XML TISS na barra lateral para iniciar a auditoria automatizada.")
