import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import streamlit as st
import hashlib
import time
import despesas_ug
import diarias
import contratos
import servidores  # Novo dashboard de Servidores
import adiantamentos  # Novo dashboard de Servidores
import combustivel  # Novo dashboard de Servidores
import orcamento  # Novo dashboard de Servidores
from sidebar import load_sidebar, navigate_pages
from data_loader import load_data  # Importar o módulo de carregamento de dados

# Configuração da página
st.set_page_config(layout="wide")

# Criar um contêiner fixo no topo da página
header = st.container()

# Adicionar a imagem e o título dentro do contêiner
with header:
    col1, col2 = st.columns([5, 1])
    with col1:
        st.markdown('<style>h1 { margin-left: 0px; font-size: 30px; }</style>', unsafe_allow_html=True)
        st.title('Painel do Gestor')
    with col2:
        st.image('./src/assets/logo.png', width=150)
        st.text("")

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    return make_hashes(password) == hashed_text

users = {
    "admin": make_hashes("1122"),
    "user2": make_hashes("password2"),
}

def login():
    st.markdown("<h1 style='text-align: center;'>Login</h1>", unsafe_allow_html=True)
    
    # Criar colunas para centralizar o formulário de login
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col2:
        # Inputs de login e senha
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type='password')
    
        # Botão de login
        if st.button("Login", on_click=login_action, args=(username, password)):
            pass  # Ação de login é tratada pela função `login_action`

def login_action(username, password):
    if username in users and check_hashes(password, users[username]):
        st.session_state['authenticated'] = True
        placeholder = st.empty()  # Placeholder para a mensagem de sucesso
        placeholder.success("Login bem-sucedido!")
        time.sleep(5)  # Espera por 3 segundos
        placeholder.empty()  # Limpa a mensagem de sucesso
    else:
        st.error("Usuário ou senha incorretos.")

# Verifica se o usuário já está autenticado
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    login()
else:
    st.button("Logout", on_click=lambda: st.session_state.update(authenticated=False, data=None))
    selected_page = navigate_pages()
    if selected_page == 'Despesas Detalhado':
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
