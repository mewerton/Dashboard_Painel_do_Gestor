import streamlit as st
import pandas as pd
import pyarrow.parquet as pq
from google.oauth2 import service_account
from googleapiclient.discovery import build
from io import BytesIO
import os
from dotenv import load_dotenv

# Carregar as variáveis do arquivo .env
load_dotenv()

# Caminho para o arquivo de credenciais da conta de serviço
CREDENTIALS_FILE = './connection/painelgestor-1f0078538d0c.json'

# ID da pasta do Google Drive onde estão os dados "dataset_despesas_detalhado"
FOLDER_ID = os.getenv('FOLDER_ID')

# ID da pasta do Google Drive onde estão os dados "contratos"
CONTRATOS_FOLDER_ID = os.getenv('CONTRATOS_FOLDER_ID')

# Função para autenticar e construir o serviço Google Drive API
def get_drive_service():
    credentials = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE,
        scopes=['https://www.googleapis.com/auth/drive']
    )
    return build('drive', 'v3', credentials=credentials)

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

# Função para carregar o arquivo de servidores (folha de pagamento)
@st.cache_resource
def load_servidores_data():
    file_path = './database/dados_folha_09_2024.parquet'
    
    if not os.path.exists(file_path):
        st.error(f'Arquivo {file_path} não encontrado.')
        return pd.DataFrame()
    
    # Carregar o arquivo .parquet como DataFrame
    df_servidores = pd.read_parquet(file_path)
    
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
