import pandas as pd
import streamlit as st

@st.cache_resource
def load_data():
    file_paths = [
        "./database/despesa_empenhado_liquidado_pago_detalhado_2018.xlsx",
        "./database/despesa_empenhado_liquidado_pago_detalhado_2019.xlsx",
        "./database/despesa_empenhado_liquidado_pago_detalhado_2020.xlsx",
        "./database/despesa_empenhado_liquidado_pago_detalhado_2021.xlsx",
        "./database/despesa_empenhado_liquidado_pago_detalhado_2022.xlsx",
        "./database/despesa_empenhado_liquidado_pago_detalhado_2023.xlsx",
        "./database/despesa_empenhado_liquidado_pago_detalhado_2024.xlsx"
    ]
    
    dfs = []
    total_files = len(file_paths)

    # Criando Barra de Progresso
    texto = st.empty()
    bar = st.progress(0)

    for i, file_path in enumerate(file_paths):
        try:
            df = pd.read_excel(file_path, sheet_name=0)
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

