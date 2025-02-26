import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sidebar import load_sidebar
from data_loader import load_dotacao_data, load_data, load_restos_data   # Importa bases de DOTAÇÃO e DESPESAS

# Função para formatar valores abreviados
def format_value_abbr(value):
    if value >= 1e12:
        return f"{value / 1e12:.1f}T"
    elif value >= 1e9:
        return f"{value / 1e9:.1f}B"
    elif value >= 1e6:
        return f"{value / 1e6:.1f}M"
    elif value >= 1e3:
        return f"{value / 1e3:.1f}K"
    else:
        return f"{value:.2f}"

# Função para formatar valores como moeda brasileira
def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# Dicionário de mapeamento das colunas para nomes formatados
colunas_formatadas = {
    "ANO": "Ano",
    "MES": "Mês",
    "DESCRICAO_UG": "Descrição da UG",
    "DESCRICAO_FUNCAO": "Descrição da Função",
    "DESCRICAO_NATUREZA3": "Natureza da Despesa",
    "DESCRICAO_NATUREZA4": "Detalhe da Despesa",
    "DESCRICAO_NATUREZA5": "Categoria da Despesa",
    "DESCRICAO_NATUREZA6": "Especificação da Despesa",
    "VALOR_DOTACAO_INICIAL": "Valor da Dotação Inicial",
    "VALOR_EMPENHADO": "Valor Empenhado",
    "VALOR_LIQUIDADO": "Valor Liquidado",
    "VALOR_PAGO": "Valor Pago"
}

def run_dashboard():
    # Carregar dados de dotação orçamentária e despesas
    df_dotacao = load_dotacao_data()
    df_despesas = load_data().copy()
    df_restos = load_restos_data()


    if df_dotacao.empty or df_despesas.empty or df_restos.empty:
        st.error("Erro: Dados não carregados corretamente. Verifique se os arquivos .parquet estão na pasta correta no Google Drive.")
        return

    # Normalizar os nomes das colunas (mantendo maiúsculas para evitar erro)
    df_dotacao.columns = df_dotacao.columns.str.strip().str.upper()
    df_despesas.columns = df_despesas.columns.str.strip().str.upper()
    df_restos.columns = df_restos.columns.str.strip().str.upper()

    # Garantir que as colunas necessárias existem
    required_columns_dotacao = {"ANO", "UG", "PODER", "UO", "FUNCAO", "VALOR_DOTACAO_INICIAL"}
    required_columns_despesas = {"ANO", "UG", "VALOR_EMPENHADO", "VALOR_LIQUIDADO", "VALOR_PAGO"}

    if not required_columns_dotacao.issubset(df_dotacao.columns):
        st.error(f"Erro: O dataset de dotação não contém todas as colunas necessárias: {required_columns_dotacao}")
        return

    if not required_columns_despesas.issubset(df_despesas.columns):
        st.error(f"Erro: O dataset de despesas não contém todas as colunas necessárias: {required_columns_despesas}")
        return

    # Carregar os filtros do sidebar
    filtros_sidebar = load_sidebar(df_dotacao, "Orçamento")

    if filtros_sidebar is None:
        st.error("Erro: Nenhuma UG foi selecionada. Selecione pelo menos uma UG no sidebar.")
        return

    selected_ugs_orcamento, selected_ano, selected_mes = filtros_sidebar

    # Garantir que MES seja numérico para evitar erros de comparação
    df_restos["MES"] = pd.to_numeric(df_restos["MES"], errors="coerce")

    # Garantir que UG está no mesmo formato (string)
    df_restos["UG"] = df_restos["UG"].astype(str)
    df_dotacao["UG"] = df_dotacao["UG"].astype(str)
    selected_ugs_orcamento = [str(ug) for ug in selected_ugs_orcamento]

    # Garantir que ANO é numérico
    df_restos["ANO"] = pd.to_numeric(df_restos["ANO"], errors="coerce")
    df_dotacao["ANO"] = pd.to_numeric(df_dotacao["ANO"], errors="coerce")
    selected_ano = [int(selected_ano[0]), int(selected_ano[1])]

    # Filtrar os dados conforme os filtros do sidebar
    df_dotacao_filtered = df_dotacao[df_dotacao["UG"].isin(selected_ugs_orcamento)]
    df_dotacao_filtered = df_dotacao_filtered[
        (df_dotacao_filtered["ANO"] >= selected_ano[0]) & 
        (df_dotacao_filtered["ANO"] <= selected_ano[1])
    ]

    df_despesas_filtered = df_despesas[df_despesas["UG"].isin(selected_ugs_orcamento)]
    df_despesas_filtered = df_despesas_filtered[
        (df_despesas_filtered["ANO"] >= selected_ano[0]) & 
        (df_despesas_filtered["ANO"] <= selected_ano[1])
    ]

    # Filtrar os datasets conforme os filtros selecionados, incluindo o mês 0
    df_restos_filtered = df_restos[df_restos["UG"].isin(selected_ugs_orcamento)]
    df_restos_filtered = df_restos_filtered[
        (df_restos_filtered["ANO"] >= selected_ano[0]) & 
        (df_restos_filtered["ANO"] <= selected_ano[1]) & 
        (df_restos_filtered["MES"].between(0, 12))  # Inclui mês 0 até 12
    ]

    # Definir um valor padrão para evitar erro caso a condição não seja atendida
    selected_ug_description = "Descrição não encontrada"

    if selected_ugs_orcamento:
        # Obter a descrição da UG selecionada
        ug_descriptions = df_dotacao_filtered[df_dotacao_filtered['UG'].isin(selected_ugs_orcamento)]['DESCRICAO_UG'].unique()
        if len(ug_descriptions) > 0:
            selected_ug_description = ug_descriptions[0]  # Pegue a primeira descrição encontrada

    # Exibir o subtítulo sem os colchetes
    st.markdown(f'<h3 style="font-size:20px;"> {selected_ug_description}</h3>', unsafe_allow_html=True)

    # Criar TABS para organizar os gráficos
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Visão Geral", "Distribuição da Dotação", "Restos a Pagar", 
        "Execução Orçamentária", "Indicadores Orçamentários"
    ])

       # ================= TAB 1: VISÃO GERAL =================
    with tab1:
        # Calcular os valores totais da dotação
        total_dotacao_inicial = df_dotacao_filtered["VALOR_DOTACAO_INICIAL"].sum()
        total_adicional = df_dotacao_filtered["VALOR_CREDITO_ADICIONAL"].sum()
        total_reduzido = df_dotacao_filtered["VALOR_REMANEJAMENTO"].sum()
        total_dotacao_atualizada = df_dotacao_filtered["VALOR_ATUALIZADO"].sum()

        # Exibir métricas no layout de colunas
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Dotação Inicial", f"R$ {total_dotacao_inicial:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        col2.metric("Adicional", f"R$ {total_adicional:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        col3.metric("Reduzido", f"R$ {total_reduzido:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        col4.metric("Dotação Atualizada", f"R$ {total_dotacao_atualizada:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        # Agregar valores por ano
        df_execucao = df_dotacao_filtered.groupby("ANO")[["VALOR_ATUALIZADO", "VALOR_EMPENHADO", "VALOR_LIQUIDADO", "VALOR_PAGO"]].sum().reset_index()

        # Criar coluna formatada para exibição na barra
        df_execucao_melted = df_execucao.melt(id_vars=["ANO"], var_name="Tipo", value_name="Valor")
        df_execucao_melted["Valor_Abrev"] = df_execucao_melted["Valor"].apply(format_value_abbr)

        # Mapeamento dos nomes das colunas para legendas mais amigáveis
        nome_legenda = {
            "VALOR_ATUALIZADO": "Dotação Atualizada",
            "VALOR_EMPENHADO": "Empenhado",
            "VALOR_LIQUIDADO": "Liquidado",
            "VALOR_PAGO": "Pago"
        }

        # Renomear os valores na coluna 'Tipo' usando o dicionário
        df_execucao_melted["Tipo"] = df_execucao_melted["Tipo"].map(nome_legenda)

        # Criar gráfico de barras agrupadas
        fig_execucao_completa = px.bar(
            df_execucao_melted, x="ANO", y="Valor", color="Tipo",
            text="Valor_Abrev",
            title="Comparação da Dotação e Execução Financeira por Ano",
            labels={"Valor": "Valor (R$)", "ANO": "Ano", "Tipo": "Execução"},
            barmode="group",
            color_discrete_sequence=px.colors.sequential.Turbo
        )

        fig_execucao_completa.update_traces(textposition="outside")

        # Exibir gráfico no Streamlit
        st.plotly_chart(fig_execucao_completa, use_container_width=True)

        # ================== MULTISELECT PARA FILTRAR A TABELA ==================
        st.subheader("Tabela de Comparação da Execução Financeira")

        # Opções disponíveis para filtragem
        opcoes_execucao = {
            "Dotação Atualizada": "VALOR_ATUALIZADO",
            "Empenhado": "VALOR_EMPENHADO",
            "Liquidado": "VALOR_LIQUIDADO",
            "Pago": "VALOR_PAGO"
        }

        # MultiSelect para selecionar quais execuções serão exibidas na tabela (inicialmente vazio)
        execucoes_selecionadas = st.multiselect(
            "Selecione as execuções para exibir na tabela:",
            list(opcoes_execucao.keys()),  # Opções legíveis
            default=[],  # Inicialmente vazio
        )

        # Se houver execuções selecionadas, exibir a tabela filtrada
        if execucoes_selecionadas:
            colunas_selecionadas = ["ANO"] + [opcoes_execucao[exec] for exec in execucoes_selecionadas]
            df_execucao_table = df_execucao[colunas_selecionadas].copy()

            # Formatar valores para moeda
            for col in df_execucao_table.columns:
                if col != "ANO":
                    df_execucao_table[col] = df_execucao_table[col].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

            # Renomear colunas para exibição amigável
            df_execucao_table = df_execucao_table.rename(columns={"ANO": "Ano"})
            for nome_legivel, nome_coluna in opcoes_execucao.items():
                df_execucao_table = df_execucao_table.rename(columns={nome_coluna: nome_legivel})

            # Exibir tabela
            st.dataframe(df_execucao_table)



    # ================= TAB 2: DISTRIBUIÇÃO DA DOTAÇÃO =================
    with tab2:
       
        # Calcular total da dotação apenas considerando valores na NATUREZA3
        total_natureza3 = df_dotacao_filtered["VALOR_DOTACAO_INICIAL"].sum()

        # Filtrar os valores por categoria de despesa com base em DESCRICAO_NATUREZA3
        custeio = df_dotacao_filtered[df_dotacao_filtered["DESCRICAO_NATUREZA3"] == "OUTRAS DESPESAS CORRENTES"]["VALOR_DOTACAO_INICIAL"].sum()
        investimentos = df_dotacao_filtered[df_dotacao_filtered["DESCRICAO_NATUREZA3"] == "INVESTIMENTOS"]["VALOR_DOTACAO_INICIAL"].sum()
        pessoal = df_dotacao_filtered[df_dotacao_filtered["DESCRICAO_NATUREZA3"] == "PESSOAL E ENCARGOS SOCIAIS"]["VALOR_DOTACAO_INICIAL"].sum()

        # Corrigir cálculo da métrica "Outros"
        outros = total_natureza3 - (custeio + investimentos + pessoal)

        # Exibir métricas no layout de colunas
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Custeio", f"R$ {custeio:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        col2.metric("Investimentos", f"R$ {investimentos:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        col3.metric("Pessoal", f"R$ {pessoal:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        col4.metric("Outros", f"R$ {outros:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        # Criar um layout de duas colunas para os gráficos
        col1, col2 = st.columns(2)
        with col1:
            # Criar DataFrame para o Gráfico de Pizza
            df_pizza = pd.DataFrame({
                "Categoria": ["Custeio", "Investimentos", "Pessoal", "Outros"], 
                "Valor": [custeio, investimentos, pessoal, outros]
            })

            # Formatar os valores em moeda brasileira
            df_pizza["Valor_Formatado"] = df_pizza["Valor"].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

            # Criar o Gráfico de Pizza com tooltip formatado corretamente
            fig_pizza = px.pie(
                df_pizza, 
                names="Categoria", 
                values="Valor", 
                title="Distribuição das Despesas da Natureza 3",
                hole=0.3  # Estilo Donut (removível se necessário)
            )

            # Customizar Tooltip para exibir apenas categoria e valor formatado como moeda brasileira
            fig_pizza.update_traces(
                textinfo="label+percent", 
                hovertemplate="<b>%{label}</b><br>%{customdata}<extra></extra>",
                customdata=df_pizza["Valor_Formatado"]
            )

            # Exibir o gráfico no Streamlit
            st.plotly_chart(fig_pizza, use_container_width=True)



        with col2:
            # Gráfico de Linha: Evolução Temporal das Despesas com suavização
            df_evolucao = df_dotacao_filtered.groupby("ANO")["VALOR_DOTACAO_INICIAL"].sum().reset_index()

            # Formatar os valores como moeda brasileira
            df_evolucao["Valor_Formatado"] = df_evolucao["VALOR_DOTACAO_INICIAL"].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

            fig_linha = px.line(
                df_evolucao, 
                x="ANO", 
                y="VALOR_DOTACAO_INICIAL", 
                markers=True, 
                title="Evolução da Dotação ao Longo dos Anos"
            )

            # Suavizar a linha e formatar o tooltip
            fig_linha.update_traces(
                line_shape='spline',  # Suavizar linha
                hovertemplate="<b>%{x}</b><br>%{customdata}<extra></extra>",  # Mostrar Ano e Valor formatado
                customdata=df_evolucao["Valor_Formatado"]
            )

            # Atualizar rótulo do eixo Y
            fig_linha.update_layout(
                yaxis_title="Valor da Dotação Inicial"
            )

            st.plotly_chart(fig_linha, use_container_width=True)


        # Criar um dicionário para mapear os nomes simplificados para os valores reais
        mapeamento_categorias = {
            "Custeio": "OUTRAS DESPESAS CORRENTES",
            "Investimentos": "INVESTIMENTOS",
            "Pessoal": "PESSOAL E ENCARGOS SOCIAIS",
            "Outros": None  # "Outros" será tratado separadamente
        }

        # Multiselect para escolha das categorias
        selecao = st.multiselect("Selecione as categorias para exibir detalhes:", list(mapeamento_categorias.keys()))

        # Filtrar os dados com base na seleção
        if selecao:
            valores_selecionados = [mapeamento_categorias[c] for c in selecao if mapeamento_categorias[c] is not None]
            df_selecionado = df_dotacao_filtered[df_dotacao_filtered["DESCRICAO_NATUREZA3"].isin(valores_selecionados)]
            
            # Adicionar "Outros" separadamente
            if "Outros" in selecao:
                df_outros = df_dotacao_filtered[~df_dotacao_filtered["DESCRICAO_NATUREZA3"].isin(["OUTRAS DESPESAS CORRENTES", "INVESTIMENTOS", "PESSOAL E ENCARGOS SOCIAIS"])]
                df_selecionado = pd.concat([df_selecionado, df_outros])

            # Selecionar apenas as colunas mais relevantes
            colunas_interessantes = list(colunas_formatadas.keys())
            df_selecionado = df_selecionado[colunas_interessantes]

            # Renomear colunas
            df_selecionado = df_selecionado.rename(columns=colunas_formatadas)

            # Formatar colunas numéricas
            df_selecionado["Ano"] = df_selecionado["Ano"].astype(int)  # Garantir que apareça sem formatação extra
            colunas_moeda = ["Valor da Dotação Inicial", "Valor Empenhado", "Valor Liquidado", "Valor Pago"]
            
            for coluna in colunas_moeda:
                df_selecionado[coluna] = df_selecionado[coluna].apply(formatar_moeda)

            # Exibir a tabela formatada
            st.dataframe(df_selecionado)


    # ================= TAB 3: RESTOS A PAGAR =================
    with tab3:
        # Converter colunas para numérico
        for col in ["VALOR_INSCRITO", "VALOR_INSCRITO_EXE_ANTERIOR", "VALOR_CANCELADO", "VALOR_BLOQUEADO", "VALOR_PAGO", "VALOR_A_PAGAR"]:
            df_restos_filtered[col] = pd.to_numeric(df_restos_filtered[col], errors="coerce").fillna(0)

        # Criar uma cópia do DataFrame excluindo o mês 12 SOMENTE para VALOR_INSCRITO
        df_restos_filtered_no_dezembro = df_restos_filtered[df_restos_filtered["MES"] != 12]

        # Calcular valores agregados por ano (para todas as colunas, sem exceções)
        df_restos_aggregated = df_restos_filtered.groupby("ANO").agg({
            "VALOR_INSCRITO_EXE_ANTERIOR": "sum",
            "VALOR_CANCELADO": "sum",
            "VALOR_BLOQUEADO": "sum",
            "VALOR_PAGO": "sum",
            "VALOR_A_PAGAR": "sum"
        }).reset_index()

        # Agora adicionamos a soma de VALOR_INSCRITO apenas com meses 1 a 11
        valor_inscrito_sem_mes_12 = df_restos_filtered_no_dezembro.groupby("ANO")["VALOR_INSCRITO"].sum().reset_index()

        # Mesclar as informações corretas no dataframe final
        df_restos_aggregated = df_restos_aggregated.merge(valor_inscrito_sem_mes_12, on="ANO", how="left")

        # Criar colunas formatadas para exibição NO TOPO DAS BARRAS (ABREVIADO)
        df_restos_aggregated["Inscrito Abrev"] = df_restos_aggregated["VALOR_INSCRITO"].apply(format_value_abbr)
        df_restos_aggregated["Pago Abrev"] = df_restos_aggregated["VALOR_PAGO"].apply(format_value_abbr)
        df_restos_aggregated["A Pagar Abrev"] = df_restos_aggregated["VALOR_A_PAGAR"].apply(format_value_abbr)

        # Criar colunas formatadas como moeda para HOVER
        df_restos_aggregated["VALOR_INSCRITO_FORMATADO"] = df_restos_aggregated["VALOR_INSCRITO"].apply(formatar_moeda)
        df_restos_aggregated["VALOR_PAGO_FORMATADO"] = df_restos_aggregated["VALOR_PAGO"].apply(formatar_moeda)
        df_restos_aggregated["VALOR_A_PAGAR_FORMATADO"] = df_restos_aggregated["VALOR_A_PAGAR"].apply(formatar_moeda)

        # Mapeamento de legendas para nomes amigáveis
        legenda_mapeada = {
            "VALOR_INSCRITO": "Valor Inscrito",
            "VALOR_PAGO": "Valor Pago",
            "VALOR_A_PAGAR": "Valor a Pagar"
        }

        # Criar gráfico de barras com valores formatados
        fig_restos = px.bar(
            df_restos_aggregated, 
            x="ANO", 
            y=["VALOR_INSCRITO", "VALOR_PAGO", "VALOR_A_PAGAR"],  
            labels={
                "value": "Valor (R$)", 
                "ANO": "Ano", 
                "variable": "Categoria"
            },
            barmode="group",
            title="Restos a Pagar: Valor Inscrito vs Pago vs A Pagar",
            text_auto=False,
            color_discrete_sequence=px.colors.sequential.PuBu_r
        )

        # Atualizar rótulos das barras com valores ABREVIADOS
        for trace, column in zip(fig_restos.data, ["Inscrito Abrev", "Pago Abrev", "A Pagar Abrev"]):
            trace.text = df_restos_aggregated[column]  # Exibir apenas o valor abreviado correto
            trace.textposition = "outside"

        # Ajustar o hover para exibir APENAS o valor correto da barra onde o mouse está passando
        for trace, column, hover_column in zip(
            fig_restos.data, 
            ["VALOR_INSCRITO", "VALOR_PAGO", "VALOR_A_PAGAR"],
            ["VALOR_INSCRITO_FORMATADO", "VALOR_PAGO_FORMATADO", "VALOR_A_PAGAR_FORMATADO"]
        ):
            trace.customdata = df_restos_aggregated[hover_column]  # Cada barra recebe apenas seu próprio valor formatado
            trace.hovertemplate = "<b>Ano:</b> %{x}<br><b>Valor:</b> %{customdata}<extra></extra>"

        # Atualizar a legenda com os nomes amigáveis
        fig_restos.for_each_trace(lambda t: t.update(name=legenda_mapeada[t.name]))

        # Exibir gráfico atualizado
        st.plotly_chart(fig_restos, use_container_width=True)

        # ================= Tabela reordenada =================
        st.subheader("Tabela Completa de Restos a Pagar por Ano")

        # Selecionar apenas as colunas relevantes e reordená-las
        df_restos_table = df_restos_aggregated[[
            "ANO",
            "VALOR_INSCRITO",
            "VALOR_INSCRITO_EXE_ANTERIOR",
            "VALOR_BLOQUEADO",
            "VALOR_CANCELADO",
            "VALOR_PAGO",
            "VALOR_A_PAGAR"
        ]].copy()

        # Formatar valores para exibição como moeda, exceto a coluna "ANO"
        for col in df_restos_table.columns:
            if col != "ANO":
                df_restos_table[col] = df_restos_table[col].apply(formatar_moeda)

        # Renomear colunas para exibição final
        df_restos_table = df_restos_table.rename(columns={
            "ANO": "Ano",
            "VALOR_INSCRITO": "Valor Inscrito",
            "VALOR_INSCRITO_EXE_ANTERIOR": "Valor Inscrito Exercício Anterior",
            "VALOR_BLOQUEADO": "Valor Bloqueado",
            "VALOR_CANCELADO": "Valor Cancelado",
            "VALOR_PAGO": "Valor Pago",
            "VALOR_A_PAGAR": "Valor a Pagar"
        })

        #  Remover linhas vazias no final da tabela
        df_restos_table = df_restos_table.loc[df_restos_table.iloc[:, 1:].notna().any(axis=1)]

        #  Exibir a tabela formatada ocupando toda a largura
        st.dataframe(
            df_restos_table.style.set_properties(**{'width': '100%'}),
            use_container_width=True
        )


    # ================= TAB 4: EXECUÇÃO ORÇAMENTÁRIA =================
    with tab4:

        # Garantir que UG e ANO são do mesmo tipo nos dataframes
        df_despesas["UG"] = df_despesas["UG"].astype(str)
        df_despesas["ANO"] = pd.to_numeric(df_despesas["ANO"], errors="coerce")

        df_dotacao["UG"] = df_dotacao["UG"].astype(str)
        df_dotacao["ANO"] = pd.to_numeric(df_dotacao["ANO"], errors="coerce")

        selected_ugs_orcamento = [str(ug) for ug in selected_ugs_orcamento]
        selected_ano = [int(selected_ano[0]), int(selected_ano[1])]

        # Verificar se os filtros realmente estão funcionando corretamente
        df_despesas_filtered = df_despesas[
            (df_despesas["UG"].isin(selected_ugs_orcamento)) & 
            (df_despesas["ANO"] >= selected_ano[0]) & 
            (df_despesas["ANO"] <= selected_ano[1])
        ]

        # Se ainda estiver vazio, mostrar quais UGs e ANOs deveriam ser filtrados
        if df_despesas_filtered.empty:
            st.warning("⚠️ Não há dados disponíveis para exibição com os filtros aplicados.")
            st.write("🔍 Debug: Nenhum dado encontrado para UGs e ANO selecionados")
 
        # Verificar se os DataFrames filtrados estão vazios
        if df_dotacao_filtered.empty or df_despesas_filtered.empty:
            st.warning("⚠️ Não há dados disponíveis para exibição com os filtros aplicados.")
        else:
            # Agregar valores por ano para cálculo da execução financeira
            df_execucao_financeira = df_dotacao_filtered.groupby("ANO").agg({
                "VALOR_DOTACAO_INICIAL": "sum",
                "VALOR_CREDITO_ADICIONAL": "sum",
                "VALOR_REMANEJAMENTO": "sum",
                "VALOR_ATUALIZADO": "sum"
            }).reset_index()

            df_despesas_agg = df_despesas_filtered.groupby("ANO").agg({
                "VALOR_EMPENHADO": "sum",
                "VALOR_LIQUIDADO": "sum",
                "VALOR_PAGO": "sum"
            }).reset_index()

            # Mesclar os dados de execução financeira com os dados de despesas
            df_execucao_financeira = df_execucao_financeira.merge(df_despesas_agg, on="ANO", how="left").fillna(0)

            # Calcular percentuais de execução
            df_execucao_financeira["% Execução Empenhada"] = (df_execucao_financeira["VALOR_EMPENHADO"] / df_execucao_financeira["VALOR_ATUALIZADO"]) * 100
            df_execucao_financeira["% Liquidação"] = (df_execucao_financeira["VALOR_LIQUIDADO"] / df_execucao_financeira["VALOR_ATUALIZADO"]) * 100
            df_execucao_financeira["% Pagamento"] = (df_execucao_financeira["VALOR_PAGO"] / df_execucao_financeira["VALOR_ATUALIZADO"]) * 100

            # Evitar divisão por zero e corrigir valores infinitos
            df_execucao_financeira.replace([float('inf'), float('-inf')], 0, inplace=True)
            df_execucao_financeira.fillna(0, inplace=True)

            # Criar um DataFrame para o gráfico de barras
            df_execucao_melted = df_execucao_financeira.melt(
                id_vars=["ANO"],
                value_vars=["% Execução Empenhada", "% Liquidação", "% Pagamento"],
                var_name="Métrica",
                value_name="Percentual"
            )

            # Criar gráfico de barras agrupadas
            fig_percentual_execucao = px.bar(
                df_execucao_melted,
                x="ANO",
                y="Percentual",
                color="Métrica",
                barmode="group",
                text=df_execucao_melted["Percentual"].apply(lambda x: f"{x:.1f}%"),
                title="Comparação dos Percentuais de Execução por Ano",
                labels={"ANO": "Ano", "Percentual": "Percentual (%)", "Métrica": "Tipo de Execução"},
                color_discrete_sequence=px.colors.sequential.Purpor_r
            )

            # Ajustes visuais
            fig_percentual_execucao.update_traces(textposition="outside")
            fig_percentual_execucao.update_layout(yaxis=dict(title="Percentual (%)", tickformat=".1f"))

            # Exibir gráfico acima da tabela
            st.plotly_chart(fig_percentual_execucao, use_container_width=True)

            # Formatar valores como moeda brasileira
            colunas_moeda = [
                "VALOR_DOTACAO_INICIAL", "VALOR_CREDITO_ADICIONAL", "VALOR_REMANEJAMENTO",
                "VALOR_ATUALIZADO", "VALOR_EMPENHADO", "VALOR_LIQUIDADO", "VALOR_PAGO"
            ]

            for coluna in colunas_moeda:
                df_execucao_financeira[coluna] = df_execucao_financeira[coluna].apply(formatar_moeda)

            # Formatar percentuais com 2 casas decimais
            colunas_percentuais = ["% Execução Empenhada", "% Liquidação", "% Pagamento"]
            for coluna in colunas_percentuais:
                df_execucao_financeira[coluna] = df_execucao_financeira[coluna].apply(lambda x: f"{x:.2f}%")

            # Renomear colunas para exibição
            df_execucao_financeira.rename(columns={
                "ANO": "Ano",
                "VALOR_DOTACAO_INICIAL": "Dotação Inicial",
                "VALOR_CREDITO_ADICIONAL": "Crédito Adicional",
                "VALOR_REMANEJAMENTO": "Redução de Dotação",
                "VALOR_ATUALIZADO": "Dotação Atualizada",
                "VALOR_EMPENHADO": "Empenhado",
                "VALOR_LIQUIDADO": "Liquidado",
                "VALOR_PAGO": "Pago"
            }, inplace=True)

            # Corrigir tipos para evitar erro de serialização do Apache Arrow
            for col in df_execucao_financeira.columns:
                if df_execucao_financeira[col].dtype == 'object':
                    df_execucao_financeira[col] = df_execucao_financeira[col].astype(str)  # Converter para string
                elif df_execucao_financeira[col].dtype == 'int64':
                    df_execucao_financeira[col] = pd.to_numeric(df_execucao_financeira[col], errors='coerce').astype('Int64')  # Garante compatibilidade

            # Remover linhas vazias no final da tabela
            df_execucao_financeira = df_execucao_financeira.loc[df_execucao_financeira.iloc[:, 1:].notna().any(axis=1)]

            # Exibir a tabela formatada abaixo do gráfico com largura total
            st.dataframe(
                df_execucao_financeira.style.set_properties(**{'width': '100%'}),
                use_container_width=True
            )

    # ================= TAB 5: INDICADORES =================
    with tab5:

        st.subheader("Indicadores Orçamentários")

        # Garantir que os valores não sejam zero para evitar divisão por zero
        valor_dotacao_atualizada = df_dotacao_filtered["VALOR_ATUALIZADO"].sum() or 1  # Se for 0, define como 1
        valor_empenhado = df_dotacao_filtered["VALOR_EMPENHADO"].sum() or 1
        valor_liquidado = df_dotacao_filtered["VALOR_LIQUIDADO"].sum()
        valor_pago = df_dotacao_filtered["VALOR_PAGO"].sum()

        # Cálculo dos percentuais
        empenho_dotacao = (valor_empenhado / valor_dotacao_atualizada) * 100
        credito_disponivel = ((valor_dotacao_atualizada - valor_empenhado) / valor_dotacao_atualizada) * 100
        pagamento_empenho = (valor_pago / valor_empenhado) * 100
        liquidacao_empenho = (valor_liquidado / valor_empenhado) * 100
        dotacao_paga = (valor_pago / valor_dotacao_atualizada) * 100

        # Criar colunas para os velocímetros
        col1, col2, col3 = st.columns(3)

        # Função para criar gráficos velocímetro (Gauge Chart) com valores em R$
        def criar_gauge(valor_percentual, valor_total, titulo, cor):
            return go.Figure(go.Indicator(
                mode="gauge+number",
                value=valor_percentual,
                number={"suffix": "%"},  # Mostra o percentual dentro do velocímetro
                title={
                    'text': f"<span style='font-size:20px; font-weight:bold;'>{titulo}</span><br><span style='font-size:18px;'>{formatar_moeda(valor_total)}</span>", 
                    'font': {'size': 16}  # Define tamanho base
                },  
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': cor},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 100], 'color': "gray"},
                    ]
                }
            ))


        # Criar e exibir os gráficos nos respectivos lugares
        with col1:
            st.plotly_chart(criar_gauge(empenho_dotacao, valor_empenhado, "Empenho da Dotação", "#FFD700"), use_container_width=True)

        with col2:
            st.plotly_chart(criar_gauge(credito_disponivel, valor_dotacao_atualizada - valor_empenhado, "Crédito Disponível", "#00FFFF"), use_container_width=True)

        with col3:
            st.plotly_chart(criar_gauge(pagamento_empenho, valor_pago, "Pagamento do Empenho", "#32CD32"), use_container_width=True)

        col4, col5 = st.columns(2)

        with col4:
            st.plotly_chart(criar_gauge(liquidacao_empenho, valor_liquidado, "Liquidação do Empenho", "#FF4500"), use_container_width=True)

        with col5:
            st.plotly_chart(criar_gauge(dotacao_paga, valor_pago, "Dotação Atualizada Paga", "#9400D3"), use_container_width=True)        


if __name__ == "__main__":
    run_dashboard()
