import streamlit as st
import plotly.express as px
import locale
from sidebar import load_sidebar
from data_loader import load_data

# Configurar o locale para português do Brasil
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

def run_dashboard():
    # Carregar dados usando o módulo centralizado
    df = load_data()

    if df is None:
        st.error("Nenhum dado foi carregado. Por favor, verifique os arquivos de entrada.")
        return

    # Carregar o sidebar
    selected_ugs_despesas, selected_ano, selected_mes = load_sidebar(df, "diarias")

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
        fig_mensal = px.line(
            df_mensal, 
            x='MES', 
            y=['VALOR_EMPENHADO', 'VALOR_PAGO'], 
            title='Evolução Mensal das Despesas',
            markers=True,  # Adiciona pontos nos dados
            line_shape='spline',  # Linhas suaves
            labels={'MES': 'Mês', 'value': 'Valor'},
            color_discrete_sequence=['#31356e', '#41b8d5']  # Definindo as cores das linhas
        )
        st.plotly_chart(fig_mensal)

    with col4:
        df_categoria = df_diarias.groupby('DESCRICAO_NATUREZA')[['VALOR_EMPENHADO', 'VALOR_PAGO']].sum().reset_index()
        fig_pizza = px.pie(
            df_categoria,
            values='VALOR_PAGO',
            names='DESCRICAO_NATUREZA',
            title='Proporção das Despesas com Diárias',
            hole=0.4,  # Adiciona um buraco no meio para criar um gráfico de rosca
            color_discrete_sequence=['#095aa2', '#042b4d']  # Define as cores desejadas
        )
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

    # Adicionar a tabela de Favorecidos das Diárias com filtro por palavra-chave e cálculo do valor total filtrado
    st.subheader('Favorecidos das Diárias')

    # Campo de entrada para a palavra-chave de pesquisa
    keyword = st.text_input('Digite uma palavra-chave para filtrar a tabela:')

    # Agrupar os dados de favorecidos
    df_favorecidos = df_diarias.groupby(['NOME_FAVORECIDO', 'DESCRICAO_NATUREZA', 'COD_PROCESSO', 'NOTA_EMPENHO', 'OBSERVACAO_NE']).agg({'VALOR_PAGO': 'sum', 'MES': 'count'}).reset_index()
    
    # Renomear colunas e reordenar
    df_favorecidos = df_favorecidos.rename(columns={
        'NOME_FAVORECIDO': 'Favorecido',
        'DESCRICAO_NATUREZA': 'Natureza',
        'VALOR_PAGO': 'Valor Pago',
        'COD_PROCESSO': 'Código do Processo',
        'NOTA_EMPENHO': 'Nota de Empenho',
        'OBSERVACAO_NE': 'Observação',
        'MES': 'Quantidade'
    })[['Favorecido', 'Natureza', 'Valor Pago', 'Código do Processo', 'Nota de Empenho', 'Observação', 'Quantidade']]

    # Aplicar filtro baseado na palavra-chave
    if keyword:
        df_favorecidos = df_favorecidos[df_favorecidos.apply(lambda row: row.astype(str).str.contains(keyword, case=False).any(), axis=1)]

    # Calcular o valor total das linhas filtradas
    valor_total_filtrado = df_favorecidos['Valor Pago'].sum()

    # Exibir a tabela
    st.dataframe(df_favorecidos.style.format({'Valor Pago': 'R$ {:,.2f}'}))

    # Exibir o valor total das linhas filtradas
    st.markdown(f"**Valor total pago das linhas filtradas:** R$ {valor_total_filtrado:,.2f}")

if __name__ == "__main__":
    run_dashboard()
