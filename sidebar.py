import streamlit as st
import pandas as pd

def load_sidebar(df, dashboard_name):
    if dashboard_name == 'Contratos':
        # Carregar o CSV contendo UG, descrição e sigla
        df_ug_info = pd.read_csv("./database/UGS-COD-NOME-SIGLA.csv")

        # Mapeamento UG -> Descrição e Sigla
        ugs_interesse_contratos = df_ug_info['UG'].tolist()
        siglas_ugs_interesse = df_ug_info['SIGLA_UG'].tolist()

        # Combinar as opções de UG e SIGLA para exibição clara
        options_combined_contratos = [
            f"{ug} - {sigla}" for ug, sigla in zip(ugs_interesse_contratos, siglas_ugs_interesse)
        ]

        # Definir uma UG padrão
        ugs_default_contratos = [410512]

        # Filtro para seleção de UG ou Sigla
        selected_ug_sigla_contratos = st.sidebar.multiselect(
            'Selecione a UG ou a SIGLA de interesse:',
            options=options_combined_contratos,
            default=[f"{ug} - {siglas_ugs_interesse[ugs_interesse_contratos.index(ug)]}" for ug in ugs_default_contratos]
        )

        # Separar as UGs selecionadas
        selected_ugs_contratos = [int(option.split(" - ")[0]) for option in selected_ug_sigla_contratos]

        # Conversão de timestamps para datetime
        df['DATA_INICIO_VIGENCIA'] = pd.to_datetime(df['DATA_INICIO_VIGENCIA'], unit='ms')
        df['DATA_FIM_VIGENCIA'] = pd.to_datetime(df['DATA_FIM_VIGENCIA'], unit='ms')

        min_data_inicio = df['DATA_INICIO_VIGENCIA'].min().date()
        max_data_inicio = df['DATA_INICIO_VIGENCIA'].max().date()
        selected_data_inicio = st.sidebar.slider(
            'Selecione o período de início da vigência:',
            min_value=min_data_inicio,
            max_value=max_data_inicio,
            value=(min_data_inicio, max_data_inicio)
        )

        min_data_fim = df['DATA_FIM_VIGENCIA'].min().date()
        max_data_fim = df['DATA_FIM_VIGENCIA'].max().date()
        selected_data_fim = st.sidebar.slider(
            'Selecione o período de fim da vigência:',
            min_value=min_data_fim,
            max_value=max_data_fim,
            value=(min_data_fim, max_data_fim)
        )

        return selected_ugs_contratos, selected_data_inicio, selected_data_fim

    else:
        # Filtros padrões para o dashboard de despesas e diárias
        df_ug_info = pd.read_csv("./database/UGS-COD-NOME-SIGLA.csv")

        # Mapeamento UG -> Descrição e Sigla
        ugs_interesse_despesas = df_ug_info['UG'].tolist()
        siglas_ugs_interesse = df_ug_info['SIGLA_UG'].tolist()

        # Combinar as opções de UG e SIGLA para exibição clara
        options_combined = [
            f"{ug} - {sigla}" for ug, sigla in zip(ugs_interesse_despesas, siglas_ugs_interesse)
        ]

        # Definir uma UG padrão
        ugs_default_despesas = [410512]

        # Filtro para seleção de UG ou Sigla
        selected_ug_sigla = st.sidebar.multiselect(
            'Selecione a UG ou a SIGLA de interesse:',
            options=options_combined,
            default=[f"{ug} - {siglas_ugs_interesse[ugs_interesse_despesas.index(ug)]}" for ug in ugs_default_despesas]
        )

        # Separar as UGs selecionadas
        selected_ugs = [int(option.split(" - ")[0]) for option in selected_ug_sigla]

        # Filtrar pelo ano e mês
        min_ano = int(df['ANO'].min())
        max_ano = int(df['ANO'].max())

        if min_ano == max_ano:
            min_ano = max_ano - 1  # Ajustar para evitar erro no slider

        selected_ano = st.sidebar.slider(
            'Selecione o Ano:',
            min_value=min_ano,
            max_value=max_ano,
            value=(min_ano, max_ano)
        )

        min_mes = 1
        max_mes = 12
        selected_mes = st.sidebar.slider(
            'Selecione o Mês:',
            min_value=min_mes,
            max_value=max_mes,
            value=(min_mes, max_mes)
        )

        return selected_ugs, selected_ano, selected_mes


def navigate_pages():
    page = st.sidebar.radio(
        'Navegação',
        ('Despesas Detalhado', 'Diárias', 'Contratos')
    )
    return page
