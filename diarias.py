import streamlit as st
import pandas as pd
import plotly.express as px
import locale
from sidebar import load_sidebar

# Configurar o locale para português do Brasil
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

def run_dashboard():
    @st.cache_data
    def load_data(file_paths):
        dfs = []
        total_files = len(file_paths)
        with st.empty():
            progress_bar = st.progress(0)
            for i, file_path in enumerate(file_paths):
                try:
                    df = pd.read_excel(file_path, sheet_name=0)
                    dfs.append(df)
                except FileNotFoundError:
                    st.error(f"O arquivo {file_path} não foi encontrado.")
                except Exception as e:
                    st.error(f"Ocorreu um erro ao carregar o arquivo {file_path}: {e}")
            
                progress = (i + 1) / total_files
                progress_bar.progress(progress)
    
        if len(dfs) == 0:
            return None
        else:
            return pd.concat(dfs, ignore_index=True)

    file_paths = [
        "./database/despesa_empenhado_liquidado_pago_detalhado_2018.xlsx",
        "./database/despesa_empenhado_liquidado_pago_detalhado_2019.xlsx",
        "./database/despesa_empenhado_liquidado_pago_detalhado_2020.xlsx",
        "./database/despesa_empenhado_liquidado_pago_detalhado_2021.xlsx",
        "./database/despesa_empenhado_liquidado_pago_detalhado_2022.xlsx",
        "./database/despesa_empenhado_liquidado_pago_detalhado_2023.xlsx",
        "./database/despesa_empenhado_liquidado_pago_detalhado_2024.xlsx"
    ]
    df = load_data(file_paths)

    if df is None:
        st.error("Nenhum dado foi carregado. Por favor, verifique os arquivos de entrada.")
        return

    # Carregar o sidebar
    selected_ugs_despesas, selected_ano, selected_mes = load_sidebar(df)

    if df is not None:
        # Filtrar dados apenas para o Poder Executivo
        df = df[df['PODER'] == 'EXE']

    # Aplicar filtros ao dataframe
    df_filtered = df[df['UG'].isin(selected_ugs_despesas)]
    df_filtered = df_filtered[(df_filtered['ANO'] >= selected_ano[0]) & (df_filtered['ANO'] <= selected_ano[1])]
    df_filtered = df_filtered[(df_filtered['MES'] >= selected_mes[0]) & (df_filtered['MES'] <= selected_mes[1])]

    # Filtrar dados de diárias
    df_diarias = df_filtered[df_filtered['DESCRICAO_NATUREZA6'].isin(['DIARIAS - CIVIL', 'DIARIAS - MILITAR'])]

    # Calcular as métricas
    quantidade_despesas = df_diarias[df_diarias['VALOR_PAGO'] > 0].shape[0]
    valor_total_diarias = df_diarias['VALOR_PAGO'].sum()
    valor_total_formatado = locale.currency(valor_total_diarias, grouping=True)

    # Exibir as métricas
    st.subheader('Métricas de diárias')
    col3, col4 = st.columns(2)
    col3.metric("Quantidade total de diárias", quantidade_despesas)
    col4.metric("Valor total de diárias", valor_total_formatado)

    col3, col4 = st.columns(2)

    with col3:
        df_mensal = df_diarias.groupby('MES')[['VALOR_EMPENHADO', 'VALOR_PAGO']].sum().reset_index()
        fig_mensal = px.line(df_mensal, x='MES', y=['VALOR_EMPENHADO', 'VALOR_PAGO'], title='Evolução Mensal das Despesas')
        st.plotly_chart(fig_mensal)

    with col4:
        df_categoria = df_diarias.groupby('DESCRICAO_NATUREZA')[['VALOR_EMPENHADO', 'VALOR_PAGO']].sum().reset_index()
        fig_pizza = px.pie(df_categoria, values='VALOR_PAGO', names='DESCRICAO_NATUREZA', title='Proporção das Despesas com Diárias')
        st.plotly_chart(fig_pizza)

    col7, col8 = st.columns(2)

    with col7:
        st.subheader('Resumo Mensal de Despesas com Diárias')
        df_mensal['VALOR_EMPENHADO'] = df_mensal['VALOR_EMPENHADO'].apply(lambda x: locale.currency(x, grouping=True))
        df_mensal['VALOR_PAGO'] = df_mensal['VALOR_PAGO'].apply(lambda x: locale.currency(x, grouping=True))
        st.dataframe(df_mensal)

    with col8:
        st.subheader('Resumo Detalhado por Categoria de Diária')
        df_categoria['VALOR_EMPENHADO'] = df_categoria['VALOR_EMPENHADO'].apply(lambda x: locale.currency(x, grouping=True))
        df_categoria['VALOR_PAGO'] = df_categoria['VALOR_PAGO'].apply(lambda x: locale.currency(x, grouping=True))
        st.dataframe(df_categoria)

    st.subheader('Favorecidos das Diárias')
    df_diarias = df_diarias[df_diarias['VALOR_PAGO'] > 0]
    df_favorecidos = df_diarias.groupby(['NOME_FAVORECIDO', 'DESCRICAO_NATUREZA', 'COD_PROCESSO', 'NOTA_EMPENHO', 'OBSERVACAO_NE']).agg({'VALOR_PAGO': 'sum', 'MES': 'count'}).reset_index()
    df_favorecidos['VALOR_PAGO'] = df_favorecidos['VALOR_PAGO'].apply(lambda x: locale.currency(x, grouping=True))
    df_favorecidos.rename(columns={'MES': 'QUANTIDADE'}, inplace=True)
    st.dataframe(df_favorecidos[['NOME_FAVORECIDO', 'DESCRICAO_NATUREZA', 'COD_PROCESSO', 'QUANTIDADE', 'VALOR_PAGO', 'NOTA_EMPENHO', 'OBSERVACAO_NE']])

if __name__ == "__main__":
    run_dashboard()
