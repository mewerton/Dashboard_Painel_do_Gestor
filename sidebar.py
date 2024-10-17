import streamlit as st
import pandas as pd

def load_sidebar(df, dashboard_name):

    # ========= FILTROS DOS SERVIDORES =========

    if dashboard_name == 'Servidores':
        # Carregar o CSV contendo UG, descrição, sigla e Unidade
        df_ug_info = pd.read_csv("./database/UGS-COD-NOME-SIGLA.csv")

        # Mapeamento UG -> Descrição, SIGLA e Unidade
        ugs_interesse = df_ug_info['UG'].tolist()
        siglas_ugs_interesse = df_ug_info['SIGLA_UG'].tolist()
        unidades_ugs_interesse = df_ug_info['Unidade'].tolist()  # Alterado para 'Unidade'

        # Combinar as opções de UG e SIGLA para exibição clara
        options_combined_servidores = [
            f"{ug} - {sigla}" for ug, sigla in zip(ugs_interesse, siglas_ugs_interesse)
        ]

        # Filtro para seleção de UG ou Sigla
        selected_ug_sigla_servidores = st.sidebar.text_input(
            'Digite a UG ou a SIGLA de interesse:'
        )

        # Verificar se a UG ou SIGLA existe no dataset
        if selected_ug_sigla_servidores:
            try:
                # Tentar encontrar a UG digitada
                if selected_ug_sigla_servidores.isdigit():
                    selected_ug = int(selected_ug_sigla_servidores)
                    unidade_filtrada = df_ug_info.loc[df_ug_info['UG'] == selected_ug, 'Unidade'].values[0]
                else:
                    # Caso tenha sido digitada uma SIGLA
                    selected_sigla = selected_ug_sigla_servidores.upper()
                    unidade_filtrada = df_ug_info.loc[df_ug_info['SIGLA_UG'] == selected_sigla, 'Unidade'].values[0]

                # Filtrar todas as UGs que pertencem à mesma Unidade
                ugs_mesma_unidade = df_ug_info[df_ug_info['Unidade'] == unidade_filtrada]
                st.sidebar.write(f"Unidade {unidade_filtrada} selecionada: {len(ugs_mesma_unidade)} UGs encontradas.")

                return ugs_mesma_unidade['UG'].tolist()

            except IndexError:
                st.sidebar.error("UG ou SIGLA não encontrada. Tente novamente.")
                return []
        else:
            st.sidebar.warning("Digite uma UG ou SIGLA para filtrar.")
            return []

    # ========= FILTROS DE CONTRATOS =========
    elif dashboard_name == 'Contratos':
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
    
    # ========= FILTROS DE DESPESAS E DIÁRIAS =========
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
        ('Despesas Detalhado', 'Diárias', 'Contratos', 'Servidores', 'Adiantamentos', 'Combustível', 'Orçamento')
    )
    return page
