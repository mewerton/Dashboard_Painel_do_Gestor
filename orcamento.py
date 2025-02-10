import streamlit as st
import pandas as pd
import plotly.express as px
from sidebar import load_sidebar
from data_loader import load_dotacao_data, load_data  # Importa bases de DOTAÇÃO e DESPESAS

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
    df_despesas = load_data()

    if df_dotacao.empty or df_despesas.empty:
        st.error("Erro: Dados não carregados corretamente. Verifique se os arquivos .parquet estão na pasta correta no Google Drive.")
        return

    # Normalizar os nomes das colunas (mantendo maiúsculas para evitar erro)
    df_dotacao.columns = df_dotacao.columns.str.strip().str.upper()
    df_despesas.columns = df_despesas.columns.str.strip().str.upper()

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
        "Visão Geral", "Distribuição da Dotação", "Evolução Temporal", 
        "Execução Orçamentária", "Análises Complementares"
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

        #st.subheader("Comparação da Dotação e Despesas")

        # Agregar valores por ano
        df_execucao = df_dotacao_filtered.groupby("ANO")[["VALOR_ATUALIZADO", "VALOR_EMPENHADO", "VALOR_LIQUIDADO", "VALOR_PAGO"]].sum().reset_index()

        # Criar coluna formatada para exibição na barra
        df_execucao_melted = df_execucao.melt(id_vars=["ANO"], var_name="Tipo", value_name="Valor")
        df_execucao_melted["Valor_Abrev"] = df_execucao_melted["Valor"].apply(format_value_abbr)

        # Cores personalizadas
        colors = {
            "VALOR_ATUALIZADO": "#E55115",  # Laranja
            "VALOR_EMPENHADO": "#095AA2",  # Azul Gov
            "VALOR_LIQUIDADO": "#2E9D9F",  # Azul Claro
            "VALOR_PAGO": "#FCDC20"  # Amarelo
        }

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

        # # st.subheader("Restos a Pagar por Ano")
        # df_restos_pagar = df_despesas_filtered.groupby("ANO").agg({
        #     "VALOR_EMPENHADO": "sum", 
        #     "VALOR_LIQUIDADO": "sum", 
        #     "VALOR_PAGO": "sum"
        # }).reset_index()
        

    # # **Correção da lógica:**
    #     df_restos_pagar["RP_INSCRITOS"] = df_restos_pagar["VALOR_EMPENHADO"] - df_restos_pagar["VALOR_PAGO"]
    #     df_restos_pagar["RP_PAGOS"] = df_restos_pagar["VALOR_PAGO"]
    #     df_restos_pagar["RP_TOTAL"] = df_restos_pagar["RP_INSCRITOS"] + df_restos_pagar["RP_PAGOS"]  # Soma total

    #     # Renomear colunas para exibição correta na legenda
    #     df_restos_pagar = df_restos_pagar.rename(columns={
    #         "RP_INSCRITOS": "Inscritos",
    #         "RP_PAGOS": "Pagos"
    #     })

    #     # Criar gráfico de barras com nomes ajustados
    #     fig_rp_inscritos_pagos = px.bar(
    #         df_restos_pagar, x="ANO", y=["Inscritos", "Pagos"],
    #         title="RP Inscritos x RP Pagos por Ano",
    #         labels={"value": "Valor (R$)", "ANO": "Ano", "variable": "Tipo de RP"},
    #         barmode="group",
    #         color_discrete_map={"Inscritos": "#095AA2", "Pagos": "#538cbe"}
    #     )

    #     # Adicionar valores abreviados acima das barras
    #     for trace, column in zip(fig_rp_inscritos_pagos.data, ["Inscritos", "Pagos"]):
    #         trace.text = df_restos_pagar[column].apply(lambda x: format_value_abbr(x))
    #         trace.textposition = "outside"

    #     # Adicionar linha indicadora azul escura com suavização
    #     fig_rp_inscritos_pagos.add_trace(
    #         px.line(df_restos_pagar, x="ANO", y="RP_TOTAL", markers=True, line_shape="spline").data[0]
    #     )
    #     fig_rp_inscritos_pagos.data[-1].update(
    #         line=dict(color="#FCDC20", width=3),
    #         name="Soma Total",
    #         marker=dict(size=8, symbol="circle", color="#FCDC20")  # Marcadores arredondados
    #     )

    #     # Adicionar valores da soma total acima do grupo de barras
    #     for i, ano in enumerate(df_restos_pagar["ANO"]):
    #         total_value = df_restos_pagar.loc[df_restos_pagar["ANO"] == ano, "RP_TOTAL"].values[0]
    #         total_abbr = format_value_abbr(total_value)
            
    #         fig_rp_inscritos_pagos.add_annotation(
    #             x=ano, y=total_value,
    #             text=f"<b>{total_abbr}</b>",
    #             showarrow=False,
    #             font=dict(size=12, color="white"),
    #             yshift=15
    #         )

    #     st.plotly_chart(fig_rp_inscritos_pagos, use_container_width=True)

        # ================= Tabela para Comparação da Dotação e Execução Financeira =================
        st.subheader("📋 Tabela: Comparação da Dotação e Execução Financeira por Ano")

        df_execucao_table = df_execucao.copy()
        df_execucao_table["VALOR_ATUALIZADO"] = df_execucao_table["VALOR_ATUALIZADO"].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        df_execucao_table["VALOR_EMPENHADO"] = df_execucao_table["VALOR_EMPENHADO"].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        df_execucao_table["VALOR_LIQUIDADO"] = df_execucao_table["VALOR_LIQUIDADO"].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        df_execucao_table["VALOR_PAGO"] = df_execucao_table["VALOR_PAGO"].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        st.dataframe(df_execucao_table.rename(columns={
            "ANO": "Ano",
            "VALOR_ATUALIZADO": "Dotação Atualizada",
            "VALOR_EMPENHADO": "Empenhado",
            "VALOR_LIQUIDADO": "Liquidado",
            "VALOR_PAGO": "Pago"
        }))

        # # ================= Tabela para RP Inscritos x RP Pagos =================
        # st.subheader("Tabela: RP Inscritos x RP Pagos por Ano")

        # df_restos_pagar_table = df_restos_pagar.copy()
        # df_restos_pagar_table["Inscritos"] = df_restos_pagar_table["Inscritos"].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        # df_restos_pagar_table["Pagos"] = df_restos_pagar_table["Pagos"].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        # st.dataframe(df_restos_pagar_table.rename(columns={
        #     "ANO": "Ano",
        #     "Inscritos": "Restos a Pagar Inscritos",
        #     "Pagos": "Restos a Pagar Pagos"
        # }))


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


    # ================= TAB 3: EVOLUÇÃO TEMPORAL =================
    with tab3:
        st.subheader("📈 Evolução Temporal da Dotação")

        # Evolução da dotação ao longo dos anos
        df_ano = df_dotacao_filtered.groupby("ANO")["VALOR_DOTACAO_INICIAL"].sum().reset_index()
        fig_ano = px.line(df_ano, x="ANO", y="VALOR_DOTACAO_INICIAL", title="Evolução da Dotação ao Longo dos Anos")
        st.plotly_chart(fig_ano, use_container_width=True)

    # ================= TAB 4: EXECUÇÃO ORÇAMENTÁRIA =================
    with tab4:
        st.subheader("⚖️ Comparação da Dotação e Despesas")

        # Cálculo do Percentual de Execução da Dotação
        df_execucao = df_dotacao_filtered.groupby("ANO")["VALOR_DOTACAO_INICIAL"].sum().reset_index()
        df_execucao_despesas = df_despesas_filtered.groupby("ANO")["VALOR_EMPENHADO"].sum().reset_index()
        df_execucao = pd.merge(df_execucao, df_execucao_despesas, on="ANO", how="left").fillna(0)
        df_execucao["PERCENTUAL_EXECUCAO"] = (df_execucao["VALOR_EMPENHADO"] / df_execucao["VALOR_DOTACAO_INICIAL"]) * 100

        fig_execucao = px.bar(
            df_execucao, x="ANO", y="PERCENTUAL_EXECUCAO",
            text=df_execucao["PERCENTUAL_EXECUCAO"].apply(lambda x: f"{x:.2f}%"),
            title="Percentual de Execução da Dotação por Ano",
            labels={"ANO": "Ano", "PERCENTUAL_EXECUCAO": "Execução (%)"},
            color="PERCENTUAL_EXECUCAO",
            color_continuous_scale="Blues"
        )
        fig_execucao.update_traces(textposition="outside")
        st.plotly_chart(fig_execucao, use_container_width=True)

    # ================= TAB 5: ANÁLISES COMPLEMENTARES =================
    with tab5:
        st.subheader("📊 Análises Complementares e Comparações")

        # Ranking dos órgãos com maior execução orçamentária
        df_orgaos = df_despesas_filtered.groupby("UG")["VALOR_EMPENHADO"].sum().reset_index().nlargest(10, "VALOR_EMPENHADO")
        fig_orgaos = px.bar(df_orgaos, x="UG", y="VALOR_EMPENHADO", title="Top 10 Órgãos com Maior Execução Orçamentária")
        st.plotly_chart(fig_orgaos, use_container_width=True)

if __name__ == "__main__":
    run_dashboard()
