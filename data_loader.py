import streamlit as st
import pandas as pd
import pyarrow.parquet as pq
from google.oauth2 import service_account
from googleapiclient.discovery import build
from io import BytesIO
import json
import toml

# Carregar configurações do arquivo TOML
#config = toml.load('config.toml')
config = st.secrets

# Caminho para o arquivo de credenciais da conta de serviço
CREDENTIALS_FILE = json.loads(config['CREDENTIALS_FILE'])

# ID da pasta do Google Drive onde estão os dados "dataset_despesas_detalhado"
FOLDER_ID = config['FOLDER_ID']

# ID da pasta do Google Drive onde estão os dados "contratos"
CONTRATOS_FOLDER_ID = config['CONTRATOS_FOLDER_ID']

# Função para autenticar e construir o serviço Google Drive API
def get_drive_service():
    # Carregar o JSON como um dicionário do .env
    credentials_info = json.loads(config['CREDENTIALS_FILE'])

    # Usar from_service_account_info para passar o dicionário em vez de um arquivo
    credentials = service_account.Credentials.from_service_account_info(
        credentials_info,
        scopes=['https://www.googleapis.com/auth/drive']
    )

    return build('drive', 'v3', credentials=credentials)

# ========== Login CSV Data Loader ==========
# Função para listar arquivos .csv na pasta de login no Google Drive
def list_login_files(service):
    LOGIN_FOLDER_ID = config['LOGIN_FOLDER_ID']  # Adicionar o ID da pasta de login no .env
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
    
    # Inicializar a barra de progresso
    progress_bar = st.progress(0)
    total_files = 2  # Apenas dois arquivos, aditivos e contratos

    # Baixar os arquivos e carregar como DataFrames
    aditivos_content = download_file_from_drive(service, aditivos_file['id'])
    contratos_content = download_file_from_drive(service, contratos_file['id'])

    df_aditivos = pq.read_table(aditivos_content).to_pandas()
    progress_bar.progress(1 / total_files)
    df_contratos = pq.read_table(contratos_content).to_pandas()
    progress_bar.progress(2 / total_files)

    return df_aditivos, df_contratos

# Função para carregar o arquivo de servidores (folha de pagamento) do Google Drive
@st.cache_resource
def load_servidores_data():
    service = get_drive_service()

    # Carregar o ID da pasta do arquivo de folha a partir do .env
    FOLHA_FOLDER_ID = config['FOLHA_FOLDER_ID']

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
    
    # Inicializar a barra de progresso
    progress_bar = st.progress(0)

    # Baixar o arquivo e carregar como DataFrame
    folha_content = download_file_from_drive(service, folha_file['id'])
    df_servidores = pq.read_table(folha_content).to_pandas()

    # Atualizar a barra de progresso para 100% após o carregamento do arquivo
    progress_bar.progress(1.0)

    return df_servidores

# Função para listar arquivos .parquet na pasta de dotação no Google Drive
def list_dotacao_files(service):
    DOTACAO_FOLDER_ID = config['DOTACAO_FOLDER_ID']
    
    results = service.files().list(
        q=f"'{DOTACAO_FOLDER_ID}' in parents and mimeType='application/vnd.google-apps.folder'",
        fields="files(id, name)"
    ).execute()
    folders = results.get('files', [])
    
    dotacao_files = []
    for folder in folders:
        folder_id = folder['id']
        # Listar os arquivos dentro de cada pasta de ano
        year_files = service.files().list(
            q=f"'{folder_id}' in parents and mimeType='application/octet-stream'",
            fields="files(id, name)"
        ).execute()
        for file in year_files.get('files', []):
            if file['name'].endswith('.parquet'):
                dotacao_files.append(file)
    
    return dotacao_files

# Função para carregar arquivos de dotação do Google Drive
@st.cache_resource
def load_dotacao_data():
    service = get_drive_service()
    dotacao_files = list_dotacao_files(service)
    
    if not dotacao_files:
        st.error('Nenhum arquivo .parquet encontrado na pasta de dotação do Google Drive.')
        return pd.DataFrame()
    
    # Carregar todos os arquivos .parquet e concatenar
    data_frames = []
    #total_files = len(dotacao_files)
    
    # Inicializar a barra de progresso
    #progress_bar = st.progress(0)
    #for idx, file in enumerate(dotacao_files):
    for file in dotacao_files:
        file_content = download_file_from_drive(service, file['id'])
        data_frames.append(pq.read_table(file_content).to_pandas())

        # Atualizar a barra de progresso
        #progress_percentage = (idx + 1) / total_files
        #progress_bar.progress(progress_percentage)
    
    return pd.concat(data_frames, ignore_index=True)

# Função para listar arquivos .parquet na pasta de restos a pagar no Google Drive
def list_restos_files(service):
    RESTOS_FOLDER_ID = config['RESTOS_FOLDER_ID']
    
    results = service.files().list(
        q=f"'{RESTOS_FOLDER_ID}' in parents and mimeType='application/vnd.google-apps.folder'",
        fields="files(id, name)"
    ).execute()
    folders = results.get('files', [])
    
    restos_files = []
    for folder in folders:
        folder_id = folder['id']
        # Listar os arquivos dentro de cada pasta de ano
        year_files = service.files().list(
            q=f"'{folder_id}' in parents and mimeType='application/octet-stream'",
            fields="files(id, name)"
        ).execute()
        for file in year_files.get('files', []):
            if file['name'].endswith('.parquet'):
                restos_files.append(file)
    
    return restos_files

# Função para carregar arquivos de restos a pagar do Google Drive
@st.cache_resource
def load_restos_data():
    service = get_drive_service()
    restos_files = list_restos_files(service)
    
    if not restos_files:
        st.error('Nenhum arquivo .parquet encontrado na pasta de restos a pagar do Google Drive.')
        return pd.DataFrame()
    
    # Carregar todos os arquivos .parquet e concatenar
    data_frames = []
    
    for file in restos_files:
        file_content = download_file_from_drive(service, file['id'])
        data_frames.append(pq.read_table(file_content).to_pandas())

    return pd.concat(data_frames, ignore_index=True)

# Função para listar arquivos .parquet na pasta de adiantamentos no Google Drive
def list_adiantamentos_files(service):
    ADIANTAMENTOS_FOLDER_ID = config['ADIANTAMENTOS_FOLDER_ID']
    
    results = service.files().list(
        q=f"'{ADIANTAMENTOS_FOLDER_ID}' in parents and mimeType='application/vnd.google-apps.folder'",
        fields="files(id, name)"
    ).execute()
    folders = results.get('files', [])

    adiantamentos_files = []

    for folder in folders:
        folder_id = folder['id']
        # Listar os arquivos dentro de cada pasta de ano
        year_files = service.files().list(
            q=f"'{folder_id}' in parents and mimeType='application/octet-stream'",
            fields="files(id, name)"
        ).execute()
        for file in year_files.get('files', []):
            if file['name'].endswith('.parquet'):
                adiantamentos_files.append(file)

    return adiantamentos_files

# Função para carregar arquivos de adiantamentos do Google Drive
@st.cache_resource
def load_adiantamentos_data():
    service = get_drive_service()
    adiantamentos_files = list_adiantamentos_files(service)

    if not adiantamentos_files:
        st.error('Nenhum arquivo .parquet encontrado na pasta de adiantamentos do Google Drive.')
        return pd.DataFrame()

    # Carregar todos os arquivos .parquet e concatenar
    data_frames = []
    total_files = len(adiantamentos_files) 

    # Inicializar a barra de progresso
    progress_bar = st.progress(0)  

    for idx, file in enumerate(adiantamentos_files):
        file_content = download_file_from_drive(service, file['id'])
        data_frames.append(pq.read_table(file_content).to_pandas())

        # Atualizar a barra de progresso
        progress_percentage = (idx + 1) / total_files  
        progress_bar.progress(progress_percentage)  

    return pd.concat(data_frames, ignore_index=True)


# # Função para listar arquivos .parquet na pasta de adiantamentos no Google Drive
# def list_adiantamentos_files(service):
#     ADIANTAMENTOS_FOLDER_ID = config['ADIANTAMENTOS_FOLDER_ID']
    
#     # Buscar diretamente os arquivos .parquet na pasta de adiantamentos
#     results = service.files().list(
#         q=f"'{ADIANTAMENTOS_FOLDER_ID}' in parents and name contains '.parquet'",
#         fields="files(id, name)"
#     ).execute()
    
#     return results.get('files', [])

# # Função para carregar arquivos de adiantamentos do Google Drive
# @st.cache_resource
# def load_adiantamentos_data():
#     service = get_drive_service()
#     adiantamentos_files = list_adiantamentos_files(service)
    
#     if not adiantamentos_files:
#         st.error('Nenhum arquivo .parquet encontrado na pasta de adiantamentos do Google Drive.')
#         return pd.DataFrame()
    
#     # Carregar todos os arquivos .parquet e concatenar
#     data_frames = []
    
#     for file in adiantamentos_files:
#         file_content = download_file_from_drive(service, file['id'])
#         data_frames.append(pq.read_table(file_content).to_pandas())

#     return pd.concat(data_frames, ignore_index=True)