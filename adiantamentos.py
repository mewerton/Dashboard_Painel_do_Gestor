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
        (df_adiantamentos["ANO"].astype(int).between(int(selected_ano[0]), int(selected_ano[1]))) &
        (df_adiantamentos["NUM_MES"].astype(int).between(int(selected_mes[0]), int(selected_mes[1]))) &
        (df_adiantamentos["UG"].astype(str).isin(map(str, selected_ugs)))
    ]

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
            tabela_formatada = tabela_pivot.applymap(formatar_moeda)

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
        st.write("Gráficos serão adicionados em breve...")

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
