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

# ID da pasta do Google Drive onde estão os dados
FOLDER_ID = os.getenv('FOLDER_ID')

# Função para autenticar e construir o serviço Google Drive API
def get_drive_service():
    credentials = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE,
        scopes=['https://www.googleapis.com/auth/drive']
    )
    return build('drive', 'v3', credentials=credentials)

# Função para listar os arquivos .parquet na pasta do Google Drive
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

# Função para baixar arquivos do Google Drive
def download_file_from_drive(service, file_id):
    request = service.files().get_media(fileId=file_id)
    response = request.execute()
    return BytesIO(response)

# Função para carregar arquivos .parquet de um determinado ano com barra de progresso
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

# Função principal para carregar os dados e usá-los no dashboard
def load_data():
    # Placeholder para a mensagem de carregamento
    loading_message = st.empty()
    loading_message.info("Carregando os dados... Isso pode demorar um pouco.")

    # Carregar os dados
    data = load_parquet_data_from_drive()

    # Remover a mensagem de carregamento após os dados serem carregados
    loading_message.empty()

    return data
