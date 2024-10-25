import streamlit as st
import pandas as pd
import pyarrow.parquet as pq
from google.oauth2 import service_account
from googleapiclient.discovery import build
from io import BytesIO
import os
from dotenv import load_dotenv
import json

# Carregar as variáveis do arquivo .env
load_dotenv()

# Caminho para o arquivo de credenciais da conta de serviço
#CREDENTIALS_FILE = json.loads(os.getenv('CREDENTIALS_FILE'))

# Construir o JSON de credenciais
credentials_info = {
    "type": os.getenv("CREDENTIALS_FILE_TYPE"),
    "project_id": os.getenv("PROJECT_ID"),
    "private_key_id": os.getenv("PRIVATE_KEY_ID"),
    "private_key": os.getenv("PRIVATE_KEY").replace("\\n", "\n"),  # Corrigir o formato da chave
    "client_email": os.getenv("CLIENT_EMAIL"),
    "client_id": os.getenv("CLIENT_ID"),
    "auth_uri": os.getenv("AUTH_URI"),
    "token_uri": os.getenv("TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("AUTH_PROVIDER_CERT_URL"),
    "client_x509_cert_url": os.getenv("CLIENT_CERT_URL"),
}

# ID da pasta do Google Drive onde estão os dados "dataset_despesas_detalhado"
FOLDER_ID = os.getenv('FOLDER_ID')

# ID da pasta do Google Drive onde estão os dados "contratos"
CONTRATOS_FOLDER_ID = os.getenv('CONTRATOS_FOLDER_ID')

# Função para autenticar e construir o serviço Google Drive API
# def get_drive_service():
#     # Carregar o JSON como um dicionário do .env
#     credentials_info = json.loads(os.getenv('CREDENTIALS_FILE'))
    
#     # Usar from_service_account_info para passar o dicionário em vez de um arquivo
#     credentials = service_account.Credentials.from_service_account_info(
#         credentials_info,
#         scopes=['https://www.googleapis.com/auth/drive']
#     )
    
#     return build('drive', 'v3', credentials=credentials)

# Função para autenticar e construir o serviço Google Drive API
def get_drive_service():
    credentials = service_account.Credentials.from_service_account_info(
        credentials_info,
        scopes=['https://www.googleapis.com/auth/drive']
    )
    return build('drive', 'v3', credentials=credentials)

# ========== Login CSV Data Loader ==========

# Função para listar arquivos .csv na pasta de login no Google Drive
def list_login_files(service):
    LOGIN_FOLDER_ID = os.getenv('LOGIN_FOLDER_ID')  # Adicionar o ID da pasta de login no .env

    login_files = service.files().list(
        q=f"'{LOGIN_FOLDER_ID}' in parents and name contains '.csv'",
        fields="files(id, name)",
        orderBy='createdTime desc'
    ).execute().get('files', [])

    if not login_files:
        st.error('Nenhum arquivo de login encontrado na pasta do Google Drive.')
        return None

    return login_files[0]  # Pegar o arquivo mais recente

# Função para carregar o CSV de login do Google Drive (sem cache)
def load_login_data():
    service = get_drive_service()
    
    login_file = list_login_files(service)
    if not login_file:
        return pd.DataFrame()

    # Baixar o arquivo CSV de login
    login_content = download_file_from_drive(service, login_file['id'])
    
    # Carregar o CSV como DataFrame
    df_login = pd.read_csv(login_content)
    
    return df_login

# ========== Fim do Login CSV Data Loader ==========


# Função para listar arquivos .parquet na pasta de despesas e diárias no Google Drive
def list_parquet_files(service):
    results = service.files().list(
        q=f"'{FOLDER_ID}' in parents and mimeType='application/vnd.google-apps.folder'",
        fields="files(id, name)"
    ).execute()
    folders = results.get('files', [])

    parquet_files = []
    for folder in folders:
        folder_id = folder['id']
        # Listar os arquivos dentro de cada pasta de ano
        year_files = service.files().list(
            q=f"'{folder_id}' in parents and mimeType='application/octet-stream'",
            fields="files(id, name)"
        ).execute()
        for file in year_files.get('files', []):
            if file['name'].endswith('.parquet'):
                parquet_files.append(file)

    return parquet_files

# Função para listar arquivos .parquet na pasta de contratos
def list_contracts_files(service):
    # Listar os arquivos na pasta "contratos" usando o ID fornecido
    contract_files = service.files().list(
        q=f"'{CONTRATOS_FOLDER_ID}' in parents and mimeType='application/octet-stream'",
        fields="files(id, name)"
    ).execute().get('files', [])

    if not contract_files:
        st.error('Nenhum arquivo de contratos encontrado na pasta "contratos" do Google Drive.')
        return []

    return contract_files

# Função para baixar arquivos do Google Drive
def download_file_from_drive(service, file_id):
    request = service.files().get_media(fileId=file_id)
    response = request.execute()
    return BytesIO(response)

# Função para carregar arquivos de despesas e diárias, com cache
@st.cache_resource
def load_parquet_data_from_drive():
    service = get_drive_service()
    parquet_files = list_parquet_files(service)

    if not parquet_files:
        st.error('Nenhum arquivo .parquet encontrado no Google Drive.')
        return pd.DataFrame()

    # Carregar todos os arquivos .parquet e concatenar
    data_frames = []
    total_files = len(parquet_files)
    
    # Inicializar a barra de progresso
    progress_bar = st.progress(0)
    for idx, file in enumerate(parquet_files):
        file_content = download_file_from_drive(service, file['id'])
        data_frames.append(pq.read_table(file_content).to_pandas())
        
        # Atualizar a barra de progresso
        progress_percentage = (idx + 1) / total_files
        progress_bar.progress(progress_percentage)

    return pd.concat(data_frames, ignore_index=True)

# Função para carregar arquivos de contratos (sem alterações)
@st.cache_resource
def load_contracts_data():
    service = get_drive_service()
    contract_files = list_contracts_files(service)

    if not contract_files:
        st.error('Nenhum arquivo de contratos encontrado no Google Drive.')
        return pd.DataFrame(), pd.DataFrame()

    # Procurar os arquivos específicos de aditivos e lista de contratos
    aditivos_file = next((file for file in contract_files if file['name'] == 'aditivos_reajustes.parquet'), None)
    contratos_file = next((file for file in contract_files if file['name'] == 'lista_contratos_siafe.parquet'), None)

    if not aditivos_file or not contratos_file:
        st.error('Arquivos "aditivos_reajustes.parquet" ou "lista_contratos_siafe.parquet" não encontrados.')
        return pd.DataFrame(), pd.DataFrame()

    # Baixar os arquivos e carregar como DataFrames
    aditivos_content = download_file_from_drive(service, aditivos_file['id'])
    contratos_content = download_file_from_drive(service, contratos_file['id'])

    df_aditivos = pq.read_table(aditivos_content).to_pandas()
    df_contratos = pq.read_table(contratos_content).to_pandas()

    return df_aditivos, df_contratos

# Função para carregar o arquivo de servidores (folha de pagamento) do Google Drive
@st.cache_resource
def load_servidores_data():
    service = get_drive_service()
    
    # Carregar o ID da pasta do arquivo de folha a partir do .env
    FOLHA_FOLDER_ID = os.getenv('FOLHA_FOLDER_ID')

    if not FOLHA_FOLDER_ID:
        st.error('ID da pasta da folha de pagamento não encontrado. Verifique o arquivo .env.')
        return pd.DataFrame()

    # pylint: disable=no-member
    # Listar os arquivos na pasta "folha de pagamento"
    folha_files = service.files().list(
        q=f"'{FOLHA_FOLDER_ID}' in parents",
        fields="files(id, name)",
        orderBy='createdTime desc'
    ).execute().get('files', [])

    if not folha_files:
        st.error('Nenhum arquivo de folha de pagamento encontrado na pasta "folha_1_mes" do Google Drive.')
        return pd.DataFrame()

    # Pegar o primeiro arquivo Parquet encontrado
    folha_file = next((file for file in folha_files if file['name'].endswith('.parquet')), None)

    if not folha_file:
        st.error('Nenhum arquivo .parquet encontrado na pasta "folha de pagamento".')
        return pd.DataFrame()

    # Baixar o arquivo e carregar como DataFrame
    folha_content = download_file_from_drive(service, folha_file['id'])
    df_servidores = pq.read_table(folha_content).to_pandas()

    return df_servidores

# Função principal para carregar os dados de despesas e diárias
def load_data():
    # Apenas uma mensagem de carregamento para a primeira chamada
    loading_message = st.empty()
    loading_message.info("Carregando os dados... Isso pode demorar um pouco.")

    # Chamar a função com cache
    data = load_parquet_data_from_drive()

    # Remover a mensagem de carregamento após os dados serem carregados
    loading_message.empty()

    return data
