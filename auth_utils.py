import hashlib
import pandas as pd
import streamlit as st
import time
from data_loader import load_login_data

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    return password == hashed_text  # Comparar diretamente se as senhas são em texto puro

def load_users():
    df = load_login_data()   
    return df

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

# Função de autenticação usando CSV
def login_action(username, password):
    users_df = load_users()

    # Converter o 'username' para string e garantir que não tenha espaços em branco
    users_df['username'] = users_df['username'].astype(str).str.strip()

    # Garantir que a entrada do usuário também seja tratada como string e sem espaços
    username = username.strip()

    try:
        # Converter a senha digitada pelo usuário para inteiro
        password = int(password)

        # Verificar se o usuário existe e se a senha está correta
        user_row = users_df[users_df['username'] == username]

        # Comparar a senha digitada (int) com a senha armazenada no CSV
        if not user_row.empty and password == user_row.iloc[0]['password']:
            st.session_state['authenticated'] = True
            placeholder = st.empty()  # Placeholder para a mensagem de sucesso
            placeholder.success("Login bem-sucedido!")
            time.sleep(3)  # Espera por 3 segundos
            placeholder.empty()  # Limpa a mensagem de sucesso
        else:
            st.error("Usuário ou senha incorretos.")
    except ValueError:
        st.error("A senha deve ser um número inteiro.")
