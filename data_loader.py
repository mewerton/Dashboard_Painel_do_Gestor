import pandas as pd
import streamlit as st

@st.cache_resource
def load_data():
    file_paths = [
        "./database/despesa_empenhado_liquidado_pago_detalhado_2018.csv",
        "./database/despesa_empenhado_liquidado_pago_detalhado_2019.csv",
        "./database/despesa_empenhado_liquidado_pago_detalhado_2020.csv",
        "./database/despesa_empenhado_liquidado_pago_detalhado_2021.csv",
        "./database/despesa_empenhado_liquidado_pago_detalhado_2022.csv",
        "./database/despesa_empenhado_liquidado_pago_detalhado_2023.csv"
        #"./database/amostra_de_despesas_de_2024.csv"
    ]
    
    dfs = []
    total_files = len(file_paths)

    # Criando Barra de Progresso
    texto = st.empty()
    bar = st.progress(0)

    for i, file_path in enumerate(file_paths):
        try:
            # Ler o arquivo CSV com delimitador "|"
            df = pd.read_csv(file_path, delimiter='|')
            dfs.append(df)
        except FileNotFoundError:
            st.error(f"O arquivo {file_path} não foi encontrado.")
        except Exception as e:
            st.error(f"Ocorreu um erro ao carregar o arquivo {file_path}: {e}")
        
        # Atualizar a barra de progresso
        progress = int((i + 1) / total_files * 100)
        bar.progress(progress)
        texto.text(f"Carregando...{progress}%")

    # Limpar o texto após o carregamento
    texto.empty()

    if len(dfs) == 0:
        return None
    else:
        return pd.concat(dfs, ignore_index=True)
