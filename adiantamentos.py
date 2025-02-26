import streamlit as st
import locale
import pandas as pd
import plotly.express as px
from sidebar import load_sidebar
from data_loader import load_adiantamentos_data

# Ativar a configuração para evitar downcasting futuro no Pandas
pd.set_option('future.no_silent_downcasting', True)

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
colunas_formatadas_adiantamentos = {
    "ANO": "Ano",
    "NUM_MES": "Mês",
    "UG": "Unidade Gestora",
    "DESCRICAO_UG": "Descrição da UG",
    "COD_CREDOR": "Código do Credor",
    "NOM_CREDOR": "Nome do Credor",
    "EMPENHO": "Número do Empenho",
    "EMPENHO_OBS": "Observação do Empenho",
    "EMPENHO_PRODUTO": "Produto Relacionado ao Empenho",
    "VALOR_DIARIAS_A_COMPROVAR": "Valor de Diárias a Comprovar",
    "VALOR_DIARIAS_COMPROVADAS": "Valor de Diárias Comprovadas",
    "VALOR_ADIANTAMENTOS_A_COMPROVAR": "Valor de Adiantamentos a Comprovar",
    "VALOR_ADIANTAMENTOS_COMPROVADOS": "Valor de Adiantamentos Comprovados"
}


def run_dashboard():
    # Carregar dados usando o módulo centralizado
    df_adiantamentos = load_adiantamentos_data()

    if df_adiantamentos is None or df_adiantamentos.empty:
        st.error("Nenhum dado foi carregado. Por favor, verifique os arquivos de entrada.")
        return

    # Carregar o sidebar
    selected_ugs, selected_ano, selected_mes = load_sidebar(df_adiantamentos, "Adiantamentos")

    # Filtrar os dados conforme seleção
    df_filtered = df_adiantamentos[
        (df_adiantamentos["ANO"].between(selected_ano[0], selected_ano[1])) &
        (df_adiantamentos["NUM_MES"].between(selected_mes[0], selected_mes[1])) &
        (df_adiantamentos["UG"].astype(str).isin(map(str, selected_ugs)))
    ].copy()  # <- Adicionando .copy() aqui evita o erro!

    # Criar tabs para organização dos gráficos
    tab1, tab2, tab3, tab4 = st.tabs(["Visão Geral", "Eficiência", "Órgãos & Credores", "Comparativos"])

    # ========= TAB 1: VISÃO GERAL =========
    with tab1:
        st.subheader("Evolução dos Adiantamentos ao Longo dos Anos")

        if not df_filtered.empty:
            # Convertendo valores para float
            df_filtered["VALOR_ADIANTAMENTOS_COMPROVADOS"] = df_filtered["VALOR_ADIANTAMENTOS_COMPROVADOS"].astype(float)

            # Agregar valores totais por ano
            df_evolucao = df_filtered.groupby("ANO")["VALOR_ADIANTAMENTOS_COMPROVADOS"].sum().reset_index()

            # Aplicar formatação abreviada aos valores do eixo Y para exibição no gráfico
            df_evolucao["VALOR_FORMATADO"] = df_evolucao["VALOR_ADIANTAMENTOS_COMPROVADOS"].apply(format_value_abbr)

            # Criar coluna formatada para exibição no hover (tooltip)
            df_evolucao["VALOR_HOVER"] = df_evolucao["VALOR_ADIANTAMENTOS_COMPROVADOS"].apply(formatar_moeda)

            # Criar gráfico de linha suavizado
            fig1 = px.line(
                df_evolucao, 
                x="ANO", 
                y="VALOR_ADIANTAMENTOS_COMPROVADOS",
                markers=True, 
                title="Total de Adiantamentos Comprovados por Ano",
                line_shape='spline',
                text="VALOR_FORMATADO",  # Exibir valores abreviados no gráfico
                labels={"ANO": colunas_formatadas_adiantamentos["ANO"], "VALOR_ADIANTAMENTOS_COMPROVADOS": "Valor Total"}  # Nomes formatados
            )

            # Ajustar a suavização da linha
            fig1.update_traces(line=dict(smoothing=0.8))

            # Ajustar posição dos textos para ficar mais afastado dos pontos
            fig1.update_traces(textposition="top center")  # Move os valores para cima e centralizados

            # Atualizar tooltip (hover) para mostrar valores formatados como moeda
            fig1.update_traces(
                hovertemplate="Ano: %{x}<br>Valor: %{customdata}"
            )

            # Adicionar dados personalizados para hover (valores formatados em moeda)
            fig1.update_traces(customdata=df_evolucao["VALOR_HOVER"])

            fig1.update_layout(
                yaxis_title="Valor Total (abreviado)", 
                xaxis_title="Ano"
            )

            # Exibir gráfico na primeira coluna
            col1, col2 = st.columns(2)  
            col1.plotly_chart(fig1, use_container_width=True)

            # ========= GRÁFICO 2: Comparação Mensal dos Adiantamentos =========

            # Agregar valores totais por mês (independente do ano)
            df_mensal = df_filtered.groupby("NUM_MES")["VALOR_ADIANTAMENTOS_COMPROVADOS"].sum().reset_index()

            # Aplicar formatação abreviada para exibição no gráfico
            df_mensal["VALOR_FORMATADO"] = df_mensal["VALOR_ADIANTAMENTOS_COMPROVADOS"].apply(format_value_abbr)

            # Criar coluna formatada para exibição no hover (tooltip)
            df_mensal["VALOR_HOVER"] = df_mensal["VALOR_ADIANTAMENTOS_COMPROVADOS"].apply(formatar_moeda)

            # Criar gráfico de barras
            fig2 = px.bar(
                df_mensal, 
                x="NUM_MES", 
                y="VALOR_ADIANTAMENTOS_COMPROVADOS",
                title="Total de Adiantamentos Comprovados por Mês",
                text="VALOR_FORMATADO",
                labels={"NUM_MES": colunas_formatadas_adiantamentos["NUM_MES"], "VALOR_ADIANTAMENTOS_COMPROVADOS": "Valor Total"}  # Nomes formatados
            )

            # Atualizar tooltip (hover) para mostrar valores formatados como moeda
            fig2.update_traces(
                hovertemplate="Mês: %{x}<br>Valor: %{customdata}"
            )

            # Adicionar dados personalizados para hover (valores formatados em moeda)
            fig2.update_traces(customdata=df_mensal["VALOR_HOVER"])

            fig2.update_layout(
                xaxis_title="Mês", 
                yaxis_title="Valor Total (abreviado)", 
                xaxis=dict(tickmode="linear")
            )

            # Exibir gráfico na segunda coluna
            col2.plotly_chart(fig2, use_container_width=True)

        else:
            st.warning("Nenhum dado disponível para o período selecionado.")

        # ======= TABELA COMPARATIVA =======
        st.markdown("---")  # Linha divisória para organização
        st.subheader("Comparação Mensal dos Adiantamentos por Ano")

        # Criar multiselect para o usuário escolher os anos que deseja comparar
        anos_disponiveis = sorted(df_filtered["ANO"].unique())
        anos_selecionados = st.multiselect("Selecione os anos para comparar:", anos_disponiveis, default=anos_disponiveis)

        if anos_selecionados:
            # Filtrar os dados pelos anos selecionados
            df_comparativo = df_filtered[df_filtered["ANO"].isin(anos_selecionados)]

            # Agregar os valores mensais por ano
            df_tabela = df_comparativo.groupby(["NUM_MES", "ANO"])["VALOR_ADIANTAMENTOS_COMPROVADOS"].sum().reset_index()

            # Criar uma tabela pivoteada (Meses como índice e Anos como colunas)
            tabela_pivot = df_tabela.pivot(index="NUM_MES", columns="ANO", values="VALOR_ADIANTAMENTOS_COMPROVADOS")

            # Substituir valores NaN por 0
            tabela_pivot = tabela_pivot.fillna(0)

            # Converter os números dos meses para string antes de adicionar "TOTAL"
            tabela_pivot.index = tabela_pivot.index.astype(str)

            # Calcular os totais por ano
            totais_anos = tabela_pivot.sum().to_frame().T  # Criar uma linha com totais
            totais_anos.index = ["TOTAL"]  # Nome da linha de totais

            # Concatenar a linha de totais à tabela original
            tabela_pivot = pd.concat([tabela_pivot, totais_anos])

            # Renomear o índice do mês para usar o nome formatado
            tabela_pivot.index.name = colunas_formatadas_adiantamentos["NUM_MES"]

            # Aplicar formatação de moeda aos valores da tabela
            tabela_formatada = tabela_pivot.map(formatar_moeda)

            # Exibir a tabela no Streamlit
            st.dataframe(
                tabela_formatada.style.set_caption("Comparação de Adiantamentos por Mês"),
                use_container_width=True
            )

        else:
            st.warning("Selecione pelo menos um ano para visualizar a comparação.")

    # ========= TAB 2: EFICIÊNCIA =========
    with tab2:
        st.subheader("Eficiência na Comprovação dos Adiantamentos")

        if not df_filtered.empty:
            # Converter valores para float (caso ainda estejam como string)
            df_filtered["VALOR_ADIANTAMENTOS_A_COMPROVAR"] = df_filtered["VALOR_ADIANTAMENTOS_A_COMPROVAR"].astype(float)
            df_filtered["VALOR_ADIANTAMENTOS_COMPROVADOS"] = df_filtered["VALOR_ADIANTAMENTOS_COMPROVADOS"].astype(float)

            # Criar dataframe de comparação
            df_comprovacao = pd.DataFrame({
                "Categoria": [
                    colunas_formatadas_adiantamentos["VALOR_ADIANTAMENTOS_A_COMPROVAR"],
                    colunas_formatadas_adiantamentos["VALOR_ADIANTAMENTOS_COMPROVADOS"]
                ],
                "Valor": [
                    df_filtered["VALOR_ADIANTAMENTOS_A_COMPROVAR"].sum(),
                    df_filtered["VALOR_ADIANTAMENTOS_COMPROVADOS"].sum()
                ]
            })

            # Criar gráfico de barras empilhadas com nomes amigáveis
            fig_comprovacao = px.bar(
                df_comprovacao, 
                x="Categoria", 
                y="Valor",
                text=df_comprovacao["Valor"].apply(formatar_moeda),  # Formatar valores corretamente
                title="Adiantamentos a Comprovar vs. Comprovados",
                color="Categoria",
                color_discrete_sequence=["#FF5733", "#33FF57"],  # Cores vibrantes
                labels={"Categoria": "Tipo de Adiantamento", "Valor": "Total (R$)"}
            )

            fig_comprovacao.update_traces(textposition="outside")
            fig_comprovacao.update_layout(yaxis_title="Valor Total", xaxis_title="Categoria")

            # Exibir gráfico no Streamlit
            st.plotly_chart(fig_comprovacao, use_container_width=True)

        else:
            st.warning("Nenhum dado disponível para o período selecionado.")

        # ========= GRÁFICO 2: Eficiência na Comprovação por Ano =========
        st.subheader("Taxa de Eficiência na Comprovação por Ano")

        # Agregar valores totais por ano
        df_eficiencia = df_filtered.groupby("ANO")[["VALOR_ADIANTAMENTOS_COMPROVADOS", "VALOR_ADIANTAMENTOS_A_COMPROVAR"]].sum().reset_index()

        # Calcular a taxa de eficiência (evita divisão por zero)
        df_eficiencia["Taxa de Eficiência (%)"] = df_eficiencia.apply(
            lambda row: (row["VALOR_ADIANTAMENTOS_COMPROVADOS"] / (row["VALOR_ADIANTAMENTOS_A_COMPROVAR"] + row["VALOR_ADIANTAMENTOS_COMPROVADOS"]) * 100)
            if (row["VALOR_ADIANTAMENTOS_A_COMPROVAR"] + row["VALOR_ADIANTAMENTOS_COMPROVADOS"]) > 0 else 0, axis=1
        )

        # Formatar os valores para exibição no hover
        df_eficiencia["Taxa_Formatada"] = df_eficiencia["Taxa de Eficiência (%)"].apply(lambda x: f"{x:.1f}%")

        # Criar gráfico de linhas da eficiência
        fig_eficiencia = px.line(
            df_eficiencia,
            x="ANO",
            y="Taxa de Eficiência (%)",
            markers=True,
            title="Evolução da Eficiência na Comprovação por Ano",
            text="Taxa_Formatada",  # Exibir valores percentuais no gráfico
            labels={"ANO": colunas_formatadas_adiantamentos["ANO"], "Taxa de Eficiência (%)": "Eficiência (%)"},
            line_shape="spline"
        )

        # Ajustar suavização e tooltip
        fig_eficiencia.update_traces(
            line=dict(smoothing=0.8),
            textposition="top center",
            hovertemplate="Ano: %{x}<br>Eficiência: %{y:.1f}%"
        )

        # Atualizar layout
        fig_eficiencia.update_layout(yaxis_title="Eficiência (%)", xaxis_title="Ano")

        # Exibir o gráfico no Streamlit
        st.plotly_chart(fig_eficiencia, use_container_width=True)

        # ========= GRÁFICO 3: Eficiência por Unidade Gestora =========
        st.subheader("Eficiência na Comprovação por Unidade Gestora")

        # Agregar valores por UG
        df_eficiencia_ug = df_filtered.groupby(["UG", "DESCRICAO_UG"])[["VALOR_ADIANTAMENTOS_COMPROVADOS", "VALOR_ADIANTAMENTOS_A_COMPROVAR"]].sum().reset_index()

        # Calcular a eficiência para cada UG (evita divisão por zero)
        df_eficiencia_ug["Eficiência (%)"] = df_eficiencia_ug.apply(
            lambda row: (row["VALOR_ADIANTAMENTOS_COMPROVADOS"] / (row["VALOR_ADIANTAMENTOS_A_COMPROVAR"] + row["VALOR_ADIANTAMENTOS_COMPROVADOS"]) * 100)
            if (row["VALOR_ADIANTAMENTOS_A_COMPROVAR"] + row["VALOR_ADIANTAMENTOS_COMPROVADOS"]) > 0 else 0, axis=1
        )

        # Ordenar por eficiência em ordem decrescente
        df_eficiencia_ug = df_eficiencia_ug.sort_values(by="Eficiência (%)", ascending=False)

        # Limitar para exibir apenas as 10 UGs mais eficientes (opcional)
        df_eficiencia_ug = df_eficiencia_ug.head(10)

        # Formatar valores para exibição no hover
        df_eficiencia_ug["Eficiência_Formatada"] = df_eficiencia_ug["Eficiência (%)"].apply(lambda x: f"{x:.1f}%")

        # Criar gráfico de barras horizontais
        fig_eficiencia_ug = px.bar(
            df_eficiencia_ug,
            x="Eficiência (%)",
            y="DESCRICAO_UG",
            orientation="h",
            text="Eficiência_Formatada",
            title="Eficiência na Comprovação por Unidade Gestora",
            labels={"DESCRICAO_UG": colunas_formatadas_adiantamentos["DESCRICAO_UG"], "Eficiência (%)": "Eficiência (%)"},
            color="Eficiência (%)",
            color_continuous_scale=px.colors.sequential.Blues  # Paleta de cores suave
        )

        # Ajustar hover e layout
        fig_eficiencia_ug.update_traces(
            textposition="outside",
            hovertemplate="UG: %{y}<br>Eficiência: %{x:.1f}%"
        )

        fig_eficiencia_ug.update_layout(
            xaxis_title="Eficiência (%)",
            yaxis_title="Unidade Gestora",
            coloraxis_showscale=False  # Remove escala de cor para melhorar estética
        )

        # Exibir gráfico no Streamlit
        st.plotly_chart(fig_eficiencia_ug, use_container_width=True)

        # ========= GRÁFICO: Eficiência na Comprovação =========
        st.subheader("Relação entre Valor do Adiantamento e Eficiência na Comprovação")

        # Criar um novo dataframe para análise de eficiência
        df_eficiencia = df_filtered.copy()

        # Substituir valores ausentes por 0 para evitar problemas
        df_eficiencia["VALOR_ADIANTAMENTOS_A_COMPROVAR"].fillna(0, inplace=True)
        df_eficiencia["VALOR_ADIANTAMENTOS_COMPROVADOS"].fillna(0, inplace=True)

        # Calcular a eficiência de cada registro (evitar divisão por zero)
        df_eficiencia["Eficiência (%)"] = df_eficiencia.apply(
            lambda row: (row["VALOR_ADIANTAMENTOS_COMPROVADOS"] / row["VALOR_ADIANTAMENTOS_A_COMPROVAR"] * 100)
            if row["VALOR_ADIANTAMENTOS_A_COMPROVAR"] > 0 else None, axis=1
        )

        # Remover possíveis valores NaN antes do gráfico
        df_eficiencia = df_eficiencia.dropna(subset=["Eficiência (%)"])

        # Criar gráfico de dispersão com linha de tendência
        fig_eficiencia = px.scatter(
            df_eficiencia,
            x="VALOR_ADIANTAMENTOS_A_COMPROVAR",
            y="Eficiência (%)",
            title="Correlação entre Valor do Adiantamento e Eficiência na Comprovação",
            labels={
                "VALOR_ADIANTAMENTOS_A_COMPROVAR": colunas_formatadas_adiantamentos["VALOR_ADIANTAMENTOS_A_COMPROVAR"],
                "Eficiência (%)": "Eficiência na Comprovação (%)"
            },
            trendline="ols",  # Adiciona uma linha de regressão para tendência
            color_discrete_sequence=["#FFAA33"]  # Cor vibrante para destacar os pontos
        )

        # Ajustar hover para mostrar valores formatados corretamente
        fig_eficiencia.update_traces(
            hovertemplate=f"{colunas_formatadas_adiantamentos['VALOR_ADIANTAMENTOS_A_COMPROVAR']}: %{{x}}<br>Eficiência: %{{y:.2f}}%"
        )

        # Ajustar layout do gráfico
        fig_eficiencia.update_layout(
            xaxis_title=colunas_formatadas_adiantamentos["VALOR_ADIANTAMENTOS_A_COMPROVAR"],
            yaxis_title="Eficiência (%)",
            showlegend=False
        )

        # Exibir gráfico no Streamlit
        st.plotly_chart(fig_eficiencia, use_container_width=True)



    # ========= TAB 3: ÓRGÃOS & CREDORES =========
    with tab3:
        st.subheader("Órgãos e Credores com Maior Uso de Adiantamentos")
        st.write("Gráficos serão adicionados em breve...")

    # ========= TAB 4: COMPARATIVOS =========
    with tab4:
        st.subheader("Comparação de Adiantamentos com Outras Despesas")
        st.write("Gráficos serão adicionados em breve...")

if __name__ == "__main__":
    run_dashboard()
