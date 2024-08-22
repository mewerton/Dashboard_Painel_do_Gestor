import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import streamlit as st
import hashlib
import despesas_ug
import diarias
import contratos
from sidebar import load_sidebar, navigate_pages

# Configuração da página
st.set_page_config(layout="wide")

# Criar um contêiner fixo no topo da página
header = st.container()

# Adicionar a imagem e o título dentro do contêiner
with header:
    # Layout em duas colunas
    col1, col2 = st.columns([5, 1])

    # Coluna do título
    with col1:
        st.markdown('<style>h1 { margin-left: 0px; font-size: 30px; }</style>', unsafe_allow_html=True)
        st.title('Painel do Gestor')

    # Coluna da imagem
    with col2:
        st.image('./src/assets/logo.png', width=150)
        st.text("")  # Espaço em branco para alinhar horizontalmente

# Função para criar hash da senha
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# Função para verificar hash
def check_hashes(password, hashed_text):
    return make_hashes(password) == hashed_text

# Banco de dados de usuários e senhas
users = {
    "admin": make_hashes("1122"),
    "user2": make_hashes("password2"),
    # Adicione mais usuários e senhas aqui
}

# Função de login com tela centralizada
def login():
    st.markdown("<h1 style='text-align: center;'>Login</h1>", unsafe_allow_html=True)

    # Crie uma coluna centralizada para o formulário
    col1, col2, col3 = st.columns([2, 2, 2])  # Ajuste a largura das colunas conforme desejado

    with col2:  # Use a coluna central para o formulário
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type='password')

        # Botão de login
        if st.button("Login"):
            if username in users and check_hashes(password, users[username]):
                st.session_state['authenticated'] = True
                st.success("Login bem-sucedido!")
            else:
                st.error("Usuário ou senha incorretos.")

# Verifica se o usuário está autenticado
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    login()
else:
    st.button("Logout", on_click=lambda: st.session_state.update(authenticated=False))
    selected_page = navigate_pages()  # Navegação de páginas
    if selected_page == 'Despesas UG':
        despesas_ug.run_dashboard()
    elif selected_page == 'Diárias':
        diarias.run_dashboard()
    elif selected_page == 'Contratos':
        contratos.run_dashboard()
