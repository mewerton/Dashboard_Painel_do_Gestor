import streamlit as st
import pandas as pd
from chatbot import render_chatbot
from datetime import datetime, timedelta
#from streamlit_option_menu import option_menu

def render_logout_button():
    if st.sidebar.button("Sair"):
        st.session_state.update(authenticated=False, data=None)

def load_sidebar(df, dashboard_name):
    # Exibe o botão de logout no sidebar
    render_logout_button()

    # ========= FILTROS DO DASHBOARD DE ADIANTAMENTOS =========
    if dashboard_name == "Adiantamentos":
        # Normalizar os nomes das colunas para evitar problemas de case sensitivity
        df.columns = df.columns.str.strip().str.upper()

        required_columns = {"ANO", "UG", "DESCRICAO_UG", "NUM_MES"}

        # Verifica se todas as colunas necessárias existem no dataset
        if not required_columns.issubset(set(df.columns)):
            st.error("Erro: O dataset não contém as colunas necessárias para filtros de Adiantamentos.")
            return None

        # Carregar o CSV contendo UG, descrição e sigla (se necessário)
        df_ug_info = pd.read_csv("./database/UGS-COD-NOME-SIGLA.csv")

        # Mapeamento UG -> Descrição
        ugs_interesse = df_ug_info["UG"].tolist()
        descricao_ugs_interesse = df_ug_info["SIGLA_UG"].tolist()

        # Combinar as opções de UG e SIGLA para exibição clara
        options_combined = [
            f"{ug} - {sigla}" for ug, sigla in zip(ugs_interesse, descricao_ugs_interesse)
        ]

        # Definir uma UG padrão como nos outros dashboards
        ug_padrao = [410512]

        # ==========================
        # MULTISELECT PARA UG (SEGUINDO A MESMA LÓGICA)
        # ==========================
        selected_ug_sigla = st.sidebar.multiselect(
            "Selecione a UG ou a SIGLA de interesse:",
            options=options_combined,
            default=[f"{ug} - {descricao_ugs_interesse[ugs_interesse.index(ug)]}" for ug in ug_padrao]
        )

        # Separar as UGs selecionadas
        selected_ugs = [int(option.split(" - ")[0]) for option in selected_ug_sigla]

        # ==========================
        # SLIDER PARA ANO (SEGUINDO A MESMA LÓGICA)
        # ==========================
        min_ano = int(df["ANO"].min())
        max_ano = int(df["ANO"].max())

        selected_ano = st.sidebar.slider(
            "Selecione o Ano:",
            min_value=min_ano,
            max_value=max_ano,
            value=(min_ano, max_ano)
        )

        # ==========================
        # SLIDER PARA MÊS (CONVERTENDO 'NUM_MES' PARA INTEIRO)
        # ==========================
        df["NUM_MES"] = df["NUM_MES"].astype(int)

        min_mes = 1
        max_mes = 12

        selected_mes = st.sidebar.slider(
            "Selecione o Mês:",
            min_value=min_mes,
            max_value=max_mes,
            value=(min_mes, max_mes)
        )

        return selected_ugs, selected_ano, selected_mes



    # ========= FILTROS DO DASHBOARD DE ORÇAMENTO =========
    if dashboard_name == "Orçamento":
        # Normalizar os nomes das colunas para evitar problemas de case sensitivity
        df.columns = df.columns.str.strip().str.upper()

        required_columns = {"ANO", "UG", "DESCRICAO_UG", "MES"}

        # Verifica se todas as colunas necessárias existem no dataset
        if not required_columns.issubset(set(df.columns)):
            st.error("Erro: O dataset não contém as colunas necessárias para filtros de Orçamento.")
            return None

        # Carregar o CSV contendo UG, descrição e sigla (se necessário)
        df_ug_info = pd.read_csv("./database/UGS-COD-NOME-SIGLA.csv")

        # Mapeamento UG -> Descrição
        ugs_interesse = df_ug_info["UG"].tolist()
        descricao_ugs_interesse = df_ug_info["SIGLA_UG"].tolist()

        # Combinar as opções de UG e SIGLA para exibição clara
        options_combined = [
            f"{ug} - {sigla}" for ug, sigla in zip(ugs_interesse, descricao_ugs_interesse)
        ]

        # Definir uma UG padrão como nos outros dashboards
        ug_padrao = [410512]

        # ==========================
        # MULTISELECT PARA UG (SEGUINDO A MESMA LÓGICA)
        # ==========================
        selected_ug_sigla = st.sidebar.multiselect(
            "Selecione a UG ou a SIGLA de interesse:",
            options=options_combined,
            default=[f"{ug} - {descricao_ugs_interesse[ugs_interesse.index(ug)]}" for ug in ug_padrao]
        )

        # Separar as UGs selecionadas
        selected_ugs = [int(option.split(" - ")[0]) for option in selected_ug_sigla]

        # ==========================
        # SLIDER PARA ANO (SEGUINDO A MESMA LÓGICA)
        # ==========================
        min_ano = int(df["ANO"].min())
        max_ano = int(df["ANO"].max())

        selected_ano = st.sidebar.slider(
            "Selecione o Ano:",
            min_value=min_ano,
            max_value=max_ano,
            value=(min_ano, max_ano)
        )

        # ==========================
        # SLIDER PARA MÊS (SEGUINDO A MESMA LÓGICA)
        # ==========================
        min_mes = 1
        max_mes = 12

        selected_mes = st.sidebar.slider(
            "Selecione o Mês:",
            min_value=min_mes,
            max_value=max_mes,
            value=(min_mes, max_mes)
        )

        return selected_ugs, selected_ano, selected_mes

     # ========= FILTROS DOS SERVIDORES =========

    if dashboard_name == 'Servidores':
        # Carregar o CSV contendo UG, descrição, sigla e Unidade
        df_ug_info = pd.read_csv("./database/UGS-COD-NOME-SIGLA.csv")

        # Mapeamento UG -> Descrição e Sigla
        ugs_interesse_servidores = df_ug_info['UG'].tolist()
        siglas_ugs_interesse_servidores = df_ug_info['SIGLA_UG'].tolist()

        # Combinar as opções de UG e SIGLA para exibição clara
        options_combined_servidores = [
            f"{ug} - {sigla}" for ug, sigla in zip(ugs_interesse_servidores, siglas_ugs_interesse_servidores)
        ]

        # Definir uma UG padrão
        ugs_default_servidores = [410512]

        # Filtro para seleção de UG ou Sigla
        selected_ug_sigla_servidores = st.sidebar.multiselect(
            'Selecione a UG ou a SIGLA de interesse:',
            options=options_combined_servidores,
            default=[f"{ug} - {siglas_ugs_interesse_servidores[ugs_interesse_servidores.index(ug)]}" for ug in ugs_default_servidores]
        )

        # Separar as UGs selecionadas
        selected_ugs_servidores = [int(option.split(" - ")[0]) for option in selected_ug_sigla_servidores]

        # Verificar se algo foi selecionado
        if selected_ug_sigla_servidores:
            try:
                # Obter a unidade associada à primeira UG selecionada
                unidade_filtrada = df_ug_info.loc[df_ug_info['UG'] == selected_ugs_servidores[0], 'Unidade'].values[0]

                # Exibir a unidade selecionada no sidebar
                st.sidebar.write(f"Unidade Selecionada: {unidade_filtrada}")

                # Retornar a unidade filtrada
                return unidade_filtrada

            except IndexError:
                st.sidebar.error("UG ou SIGLA não encontrada. Tente novamente.")
                return None
        else:
            st.sidebar.warning("Selecione uma UG ou SIGLA para filtrar.")
            return None

    # ========= FILTROS DA PÁGINA INICIAL =========
    
    elif dashboard_name == 'Início':
        # Carregar o CSV contendo UG, descrição e sigla
        df_ug_info = pd.read_csv("./database/UGS-COD-NOME-SIGLA.csv")

        # Mapeamento UG -> Descrição e Sigla
        ugs_interesse = df_ug_info['UG'].tolist()
        siglas_ugs_interesse = df_ug_info['SIGLA_UG'].tolist()

        # Combinar as opções de UG e SIGLA para exibição clara
        options_combined_inicio = [
            f"{ug} - {sigla}" for ug, sigla in zip(ugs_interesse, siglas_ugs_interesse)
        ]

        # Definir uma UG padrão
        ugs_default_inicio = [410512]

        # Filtro para seleção de UG ou Sigla
        selected_ug_sigla_inicio = st.sidebar.multiselect(
            'Selecione a UG ou a SIGLA de interesse:',
            options=options_combined_inicio,
            default=[f"{ug} - {siglas_ugs_interesse[ugs_interesse.index(ug)]}" for ug in ugs_default_inicio]
        )

        # Separar as UGs selecionadas
        selected_ugs_inicio = [int(option.split(" - ")[0]) for option in selected_ug_sigla_inicio]

        # Retornar as UGs selecionadas para a página inicial
        return selected_ugs_inicio
    
    # # ========= FILTROS DE CONTRATOS =========
    # elif dashboard_name == 'Contratos':
    #     # Carregar o CSV contendo UG, descrição e sigla
    #     df_ug_info = pd.read_csv("./database/UGS-COD-NOME-SIGLA.csv")

    #     # Mapeamento UG -> Descrição e Sigla
    #     ugs_interesse_contratos = df_ug_info['UG'].tolist()
    #     siglas_ugs_interesse = df_ug_info['SIGLA_UG'].tolist()

    #     # Combinar as opções de UG e SIGLA para exibição clara
    #     options_combined_contratos = [
    #         f"{ug} - {sigla}" for ug, sigla in zip(ugs_interesse_contratos, siglas_ugs_interesse)
    #     ]

    #     # Definir uma UG padrão
    #     ugs_default_contratos = [410512]

    #     # Filtro para seleção de UG ou Sigla
    #     selected_ug_sigla_contratos = st.sidebar.multiselect(
    #         'Selecione a UG ou a SIGLA de interesse:',
    #         options=options_combined_contratos,
    #         default=[f"{ug} - {siglas_ugs_interesse[ugs_interesse_contratos.index(ug)]}" for ug in ugs_default_contratos]
    #     )

    #     # Separar as UGs selecionadas
    #     selected_ugs_contratos = [int(option.split(" - ")[0]) for option in selected_ug_sigla_contratos]

    #     # Conversão de timestamps para datetime
    #     df['DATA_INICIO_VIGENCIA'] = pd.to_datetime(df['DATA_INICIO_VIGENCIA'], unit='ms')
    #     df['DATA_FIM_VIGENCIA'] = pd.to_datetime(df['DATA_FIM_VIGENCIA'], unit='ms')

    #     min_data_inicio = df['DATA_INICIO_VIGENCIA'].min().date()
    #     max_data_inicio = df['DATA_INICIO_VIGENCIA'].max().date()
    #     selected_data_inicio = st.sidebar.slider(
    #         'Selecione o período de início da vigência:',
    #         min_value=min_data_inicio,
    #         max_value=max_data_inicio,
    #         value=(min_data_inicio, max_data_inicio)
    #     )

    #     min_data_fim = df['DATA_FIM_VIGENCIA'].min().date()
    #     max_data_fim = df['DATA_FIM_VIGENCIA'].max().date()
    #     selected_data_fim = st.sidebar.slider(
    #         'Selecione o período de fim da vigência:',
    #         min_value=min_data_fim,
    #         max_value=max_data_fim,
    #         value=(min_data_fim, max_data_fim)
    #     )

    #     return selected_ugs_contratos, selected_data_inicio, selected_data_fim

    #     # ========= FILTROS DE CONTRATOS =========
    # elif dashboard_name == 'Contratos':
    #     # Carregar o CSV contendo UG, descrição e sigla
    #     df_ug_info = pd.read_csv("./database/UGS-COD-NOME-SIGLA.csv")

    #     # Mapeamento UG -> Descrição e Sigla
    #     ugs_interesse_contratos = df_ug_info['UG'].tolist()
    #     siglas_ugs_interesse = df_ug_info['SIGLA_UG'].tolist()

    #     # Adicionando a opção "TODAS" na lista de seleção
    #     options_combined_contratos = ["TODAS"] + [
    #         f"{ug} - {sigla}" for ug, sigla in zip(ugs_interesse_contratos, siglas_ugs_interesse)
    #     ]

    #     # Definir uma UG padrão
    #     ugs_default_contratos = [410512]

    #     # Filtro para seleção de UG ou Sigla
    #     selected_ug_sigla_contratos = st.sidebar.multiselect(
    #         'Selecione a UG ou a SIGLA de interesse:',
    #         options=options_combined_contratos,
    #         default=[f"{ug} - {siglas_ugs_interesse[ugs_interesse_contratos.index(ug)]}" for ug in ugs_default_contratos]
    #     )

    #     # Verificar se "TODAS" foi selecionado
    #     if "TODAS" in selected_ug_sigla_contratos:
    #         selected_ugs_contratos = ugs_interesse_contratos  # Seleciona todas as UGs
    #     else:
    #         # Separar as UGs selecionadas (caso não tenha selecionado "TODAS")
    #         selected_ugs_contratos = [
    #             int(option.split(" - ")[0]) for option in selected_ug_sigla_contratos
    #         ]

    #     # Conversão de timestamps para datetime
    #     df['DATA_INICIO_VIGENCIA'] = pd.to_datetime(df['DATA_INICIO_VIGENCIA'], unit='ms')
    #     df['DATA_FIM_VIGENCIA'] = pd.to_datetime(df['DATA_FIM_VIGENCIA'], unit='ms')

    #     min_data_inicio = df['DATA_INICIO_VIGENCIA'].min().date()
    #     max_data_inicio = df['DATA_INICIO_VIGENCIA'].max().date()
    #     selected_data_inicio = st.sidebar.slider(
    #         'Selecione o período de início da vigência:',
    #         min_value=min_data_inicio,
    #         max_value=max_data_inicio,
    #         value=(min_data_inicio, max_data_inicio)
    #     )

    #     min_data_fim = df['DATA_FIM_VIGENCIA'].min().date()
    #     max_data_fim = df['DATA_FIM_VIGENCIA'].max().date()
    #     selected_data_fim = st.sidebar.slider(
    #         'Selecione o período de fim da vigência:',
    #         min_value=min_data_fim,
    #         max_value=max_data_fim,
    #         value=(min_data_fim, max_data_fim)
    #     )

    #     return selected_ugs_contratos, selected_data_inicio, selected_data_fim

    # # ========= FILTROS DE CONTRATOS =========
    # elif dashboard_name == 'Contratos':
    #     # Carregar o CSV contendo UG, descrição e sigla
    #     df_ug_info = pd.read_csv("./database/UGS-COD-NOME-SIGLA.csv")

    #     # Mapeamento UG -> Descrição e Sigla
    #     ugs_interesse_contratos = df_ug_info['UG'].tolist()
    #     siglas_ugs_interesse = df_ug_info['SIGLA_UG'].tolist()

    #     # Adicionando a opção "TODAS" na lista de seleção
    #     options_combined_contratos = ["TODAS"] + [
    #         f"{ug} - {sigla}" for ug, sigla in zip(ugs_interesse_contratos, siglas_ugs_interesse)
    #     ]

    #     # Definir uma UG padrão
    #     ugs_default_contratos = [410512]

    #     # Filtro para seleção de UG ou Sigla
    #     selected_ug_sigla_contratos = st.sidebar.multiselect(
    #         'Selecione a UG ou a SIGLA de interesse:',
    #         options=options_combined_contratos,
    #         default=[f"{ug} - {siglas_ugs_interesse[ugs_interesse_contratos.index(ug)]}" for ug in ugs_default_contratos]
    #     )

    #     # Verificar se "TODAS" foi selecionado
    #     if "TODAS" in selected_ug_sigla_contratos:
    #         selected_ugs_contratos = ugs_interesse_contratos  # Seleciona todas as UGs
    #     else:
    #         # Separar as UGs selecionadas (caso não tenha selecionado "TODAS")
    #         selected_ugs_contratos = [
    #             int(option.split(" - ")[0]) for option in selected_ug_sigla_contratos
    #         ]

    #     # Conversão de timestamps para datetime
    #     df['DATA_INICIO_VIGENCIA'] = pd.to_datetime(df['DATA_INICIO_VIGENCIA'], unit='ms')
    #     df['DATA_FIM_VIGENCIA'] = pd.to_datetime(df['DATA_FIM_VIGENCIA'], unit='ms')

    #     min_data_inicio = df['DATA_INICIO_VIGENCIA'].min().date()
    #     max_data_inicio = df['DATA_INICIO_VIGENCIA'].max().date()
    #     selected_data_inicio = st.sidebar.slider(
    #         'Selecione o período de início da vigência:',
    #         min_value=min_data_inicio,
    #         max_value=max_data_inicio,
    #         value=(min_data_inicio, max_data_inicio)
    #     )

    #     min_data_fim = df['DATA_FIM_VIGENCIA'].min().date()
    #     max_data_fim = df['DATA_FIM_VIGENCIA'].max().date()
    #     selected_data_fim = st.sidebar.slider(
    #         'Selecione o período de fim da vigência:',
    #         min_value=min_data_fim,
    #         max_value=max_data_fim,
    #         value=(min_data_fim, max_data_fim)
    #     )

    #     # Novo filtro para a Situação do Contrato (DSC_SITUACAO)
    #     situacoes_disponiveis = df['DSC_SITUACAO'].dropna().unique().tolist()
    #     situacoes_disponiveis.sort()
    #       # Adicionando opção "TODAS"
        
    #     selected_situacao = st.sidebar.multiselect(
    #         'Selecione a Situação do Contrato:',
    #         options=situacoes_disponiveis,
    #         default=situacoes_disponiveis
    #     )

    #     # Verificar se "TODAS" foi selecionado
    #     if "TODAS" in selected_situacao:
    #         selected_situacoes = situacoes_disponiveis[1:]  # Seleciona todas as situações
    #     else:
    #         selected_situacoes = selected_situacao  # Apenas as selecionadas

    #     return selected_ugs_contratos, selected_ug_sigla_contratos, selected_data_inicio, selected_data_fim, selected_situacoes


    # # ========= FILTROS DE CONTRATOS =========
    # if dashboard_name == 'Contratos':
    #     # Carregar o CSV contendo UG, descrição e sigla
    #     df_ug_info = pd.read_csv("./database/UGS-COD-NOME-SIGLA.csv")

    #     # Mapeamento UG -> Descrição e Sigla
    #     ugs_interesse_contratos = df_ug_info['UG'].tolist()
    #     siglas_ugs_interesse = df_ug_info['SIGLA_UG'].tolist()

    #     # Adicionando a opção "TODAS" na lista de seleção
    #     options_combined_contratos = ["TODAS"] + [
    #         f"{ug} - {sigla}" for ug, sigla in zip(ugs_interesse_contratos, siglas_ugs_interesse)
    #     ]

    #     # Definir uma UG padrão
    #     ugs_default_contratos = [410512]

    #     # Filtro para seleção de UG ou Sigla
    #     selected_ug_sigla_contratos = st.sidebar.multiselect(
    #         'Selecione a UG ou a SIGLA de interesse:',
    #         options=options_combined_contratos,
    #         default=[f"{ug} - {siglas_ugs_interesse[ugs_interesse_contratos.index(ug)]}" for ug in ugs_default_contratos]
    #     )

    #     # Verificar se "TODAS" foi selecionado
    #     if "TODAS" in selected_ug_sigla_contratos:
    #         selected_ugs_contratos = ugs_interesse_contratos  # Seleciona todas as UGs
    #     else:
    #         # Separar as UGs selecionadas (caso não tenha selecionado "TODAS")
    #         selected_ugs_contratos = [
    #             int(option.split(" - ")[0]) for option in selected_ug_sigla_contratos
    #         ]

    #     # Conversão de timestamps para datetime
    #     df['DATA_INICIO_VIGENCIA'] = pd.to_datetime(df['DATA_INICIO_VIGENCIA'], unit='ms')
    #     df['DATA_FIM_VIGENCIA'] = pd.to_datetime(df['DATA_FIM_VIGENCIA'], unit='ms')

    #     today = datetime.today().date()

    #     # Seletor de período fixo para início da vigência
    #     periodo_inicio_options = {
    #         "Nenhum": None,
    #         "Últimos 30 dias": today - timedelta(days=30),
    #         "Últimos 60 dias": today - timedelta(days=60),
    #         "Últimos 90 dias": today - timedelta(days=90)
    #     }

    #     selected_periodo_inicio = st.sidebar.radio(
    #         "Filtro Rápido - Início da Vigência:",
    #         options=list(periodo_inicio_options.keys()),
    #         index=0  # Nenhum selecionado por padrão
    #     )

    #     # Seletor de período fixo para fim da vigência
    #     periodo_fim_options = {
    #         "Nenhum": None,
    #         "Próximos 30 dias": today + timedelta(days=30),
    #         "Próximos 60 dias": today + timedelta(days=60),
    #         "Próximos 90 dias": today + timedelta(days=90)
    #     }

    #     selected_periodo_fim = st.sidebar.radio(
    #         "Filtro Rápido - Fim da Vigência:",
    #         options=list(periodo_fim_options.keys()),
    #         index=0  # Nenhum selecionado por padrão
    #     )

    #     # Se não houver período fixo selecionado, ativa o filtro de data manual
    #     if periodo_inicio_options[selected_periodo_inicio] is None:
    #         min_data_inicio = df['DATA_INICIO_VIGENCIA'].min().date()
    #         max_data_inicio = df['DATA_INICIO_VIGENCIA'].max().date()
    #         selected_data_inicio = st.sidebar.slider(
    #             'Selecione o período de início da vigência:',
    #             min_value=min_data_inicio,
    #             max_value=max_data_inicio,
    #             value=(min_data_inicio, max_data_inicio)
    #         )
    #     else:
    #         selected_data_inicio = (periodo_inicio_options[selected_periodo_inicio], today)

    #     if periodo_fim_options[selected_periodo_fim] is None:
    #         min_data_fim = df['DATA_FIM_VIGENCIA'].min().date()
    #         max_data_fim = df['DATA_FIM_VIGENCIA'].max().date()
    #         selected_data_fim = st.sidebar.slider(
    #             'Selecione o período de fim da vigência:',
    #             min_value=min_data_fim,
    #             max_value=max_data_fim,
    #             value=(min_data_fim, max_data_fim)
    #         )
    #     else:
    #         selected_data_fim = (today, periodo_fim_options[selected_periodo_fim])

    #     # Novo filtro para a Situação do Contrato (DSC_SITUACAO)
    #     situacoes_disponiveis = df['DSC_SITUACAO'].dropna().unique().tolist()
    #     situacoes_disponiveis.sort()

    #     selected_situacoes = st.sidebar.multiselect(
    #         'Selecione a Situação do Contrato:',
    #         options=situacoes_disponiveis,
    #         default=situacoes_disponiveis
    #     )

    #     return selected_ugs_contratos, selected_ug_sigla_contratos, selected_data_inicio, selected_data_fim, selected_situacoes

    # ========= FILTROS DE CONTRATOS =========
    elif dashboard_name == 'Contratos':
        # Carregar o CSV contendo UG, descrição e sigla
        df_ug_info = pd.read_csv("./database/UGS-COD-NOME-SIGLA.csv")

        # Mapeamento UG -> Descrição e Sigla
        ugs_interesse_contratos = df_ug_info['UG'].tolist()
        siglas_ugs_interesse = df_ug_info['SIGLA_UG'].tolist()

        # Adicionando a opção "TODAS" na lista de seleção
        options_combined_contratos = ["TODAS"] + [
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

        # Verificar se "TODAS" foi selecionado
        if "TODAS" in selected_ug_sigla_contratos:
            selected_ugs_contratos = ugs_interesse_contratos  # Seleciona todas as UGs
        else:
            # Separar as UGs selecionadas (caso não tenha selecionado "TODAS")
            selected_ugs_contratos = [
                int(option.split(" - ")[0]) for option in selected_ug_sigla_contratos
            ]

        # Conversão de timestamps para datetime
        df['DATA_INICIO_VIGENCIA'] = pd.to_datetime(df['DATA_INICIO_VIGENCIA'], unit='ms')
        df['DATA_FIM_VIGENCIA'] = pd.to_datetime(df['DATA_FIM_VIGENCIA'], unit='ms')

        today = datetime.today().date()

        # Opções para filtros rápidos de períodos
        periodo_opcoes = {
            "Últimos 30 dias": today - timedelta(days=30),
            "Últimos 60 dias": today - timedelta(days=60),
            "Últimos 90 dias": today - timedelta(days=90)
        }

        # Seletor de múltiplos períodos para início da vigência
        selected_periodos_inicio = st.sidebar.multiselect(
            "Filtro Rápido - Início da Vigência:",
            options=list(periodo_opcoes.keys()),
            default=[]
        )

        # Seletor de múltiplos períodos para fim da vigência
        selected_periodos_fim = st.sidebar.multiselect(
            "Filtro Rápido - Fim da Vigência:",
            options=list(periodo_opcoes.keys()),
            default=[]
        )

        # Definir as datas com base nos períodos selecionados
        if selected_periodos_inicio:
            selected_data_inicio = (min([periodo_opcoes[p] for p in selected_periodos_inicio]), today)
        else:
            min_data_inicio = df['DATA_INICIO_VIGENCIA'].min().date()
            max_data_inicio = df['DATA_INICIO_VIGENCIA'].max().date()
            selected_data_inicio = st.sidebar.slider(
                'Selecione o período de início da vigência:',
                min_value=min_data_inicio,
                max_value=max_data_inicio,
                value=(min_data_inicio, max_data_inicio)
            )

        if selected_periodos_fim:
            selected_data_fim = (today, max([today + timedelta(days=int(p.split(" ")[1])) for p in selected_periodos_fim]))
        else:
            min_data_fim = df['DATA_FIM_VIGENCIA'].min().date()
            max_data_fim = df['DATA_FIM_VIGENCIA'].max().date()
            selected_data_fim = st.sidebar.slider(
                'Selecione o período de fim da vigência:',
                min_value=min_data_fim,
                max_value=max_data_fim,
                value=(min_data_fim, max_data_fim)
            )

        # Novo filtro para a Situação do Contrato (DSC_SITUACAO)
        situacoes_disponiveis = df['DSC_SITUACAO'].dropna().unique().tolist()
        situacoes_disponiveis.sort()

        selected_situacoes = st.sidebar.multiselect(
            'Selecione a Situação do Contrato:',
            options=situacoes_disponiveis,
            default=situacoes_disponiveis
        )

        return selected_ugs_contratos, selected_ug_sigla_contratos, selected_data_inicio, selected_data_fim, selected_situacoes

    
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
    

    # Chamada para renderizar o chatbot abaixo de todos os filtros
    render_chatbot()

def navigate_pages():
    page = st.sidebar.radio(
        'Navegação',
        ('Início', 'Despesas Detalhado', 'Diárias', 'Contratos', 'Servidores','Orçamento','Adiantamentos'), #, 'Combustível', ),
    )
    
    return page
