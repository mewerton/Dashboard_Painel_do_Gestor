import streamlit as st
import time
import base64
import despesas_ug
import diarias
import contratos
import servidores  # Novo dashboard de Servidores
import adiantamentos  # Novo dashboard de Servidores
import combustivel  # Novo dashboard de Servidores
import orcamento  # Novo dashboard de Servidores
import home  # Novo dashboard de Servidores
from sidebar import load_sidebar, navigate_pages
import auth_utils  # Importar o módulo de autenticação

# Configuração da página
st.set_page_config(layout="wide",
                    page_title="Painel do Gestor",  
                    page_icon="./src/assets/logo-ogp-favicon.png"  
)

# Criar um contêiner fixo no topo da página
header = st.container()

def get_image_as_base64(file_path):
    with open(file_path, "rb") as file:
        return base64.b64encode(file.read()).decode("utf-8")

logo_path = "./src/assets/logo2.png"
logo_base64 = get_image_as_base64(logo_path)

with st.container():
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown('<style>h1 { margin-left: 0px; font-size: 30px; }</style>', unsafe_allow_html=True)
        st.title('Painel do Gestor')
    
    with col2:
        st.markdown(
            f"""
            <div style="text-align: right; margin-right: 10px;">
                <img src="data:image/png;base64,{logo_base64}" width="350">
            </div>
            """,
            unsafe_allow_html=True
        )

# Verifica se o usuário já está autenticado
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    auth_utils.login()
else:
    selected_page = navigate_pages()
    if selected_page == 'Início':
        home.run_dashboard()
    elif selected_page == 'Despesas Detalhado':
        despesas_ug.run_dashboard()
    elif selected_page == 'Diárias':
        diarias.run_dashboard()
    elif selected_page == 'Contratos':
        contratos.run_dashboard()
    elif selected_page == 'Servidores': 
        servidores.run_dashboard()
    elif selected_page == 'Adiantamentos': 
        adiantamentos.run_dashboard()
    elif selected_page == 'Combustível': 
        combustivel.run_dashboard()
    elif selected_page == 'Orçamento': 
        orcamento.run_dashboard()
