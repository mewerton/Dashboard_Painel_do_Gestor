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
    
    # Agrupar por favorecido e calcular o valor total pago
    df_total_por_favorecido = df_diarias.groupby('NOME_FAVORECIDO')['VALOR_PAGO'].sum().reset_index()

    # Filtrar para exibir apenas valores maiores que 0
    df_total_por_favorecido = df_total_por_favorecido[df_total_por_favorecido['VALOR_PAGO'] > 0]

    # Ordenar por valor total pago, do maior para o menor
    df_total_por_favorecido = df_total_por_favorecido.sort_values(by='VALOR_PAGO', ascending=True)

    # Formatar os valores como moeda brasileira
    df_total_por_favorecido['VALOR_PAGO_FORMATADO'] = df_total_por_favorecido['VALOR_PAGO'].apply(lambda x: locale.currency(x, grouping=True))

    # Criar o gráfico de barras horizontais
    fig_favorecido = px.bar(
        df_total_por_favorecido,
        x='VALOR_PAGO', 
        y='NOME_FAVORECIDO',
        orientation='h',  # Barras horizontais
        title='Total de Diárias Recebidas por Favorecido',
        labels={'VALOR_PAGO': 'Valor Pago', 'NOME_FAVORECIDO': 'Favorecido'},
        text='VALOR_PAGO_FORMATADO',  # Exibir o valor formatado em cada barra
        color_discrete_sequence=['#095aa2']  # Define a cor das barras
    )

    # Ajustar o hover para mostrar apenas o nome e o valor formatado
    fig_favorecido.update_traces(
        hovertemplate='%{y}<br>%{text}<extra></extra>'  # Exibe nome e valor formatado, oculta "extra" info
    )

    # Ajustar layout e formatação dos valores
    fig_favorecido.update_layout(
        xaxis_title='Valor Total Pago (R$)',
        yaxis_title='Favorecido',
        height=600  # Ajuste a altura conforme necessário
    )

    # Exibir o gráfico
    st.plotly_chart(fig_favorecido, use_container_width=True)

    # Adicionar a tabela de Favorecidos das Diárias com filtro por palavra-chave e cálculo do valor total filtrado
    st.subheader('Favorecidos das Diárias')

# Campo de entrada para a palavra-chave de pesquisa
    keyword = st.text_input('Digite uma palavra-chave para filtrar a tabela:')

# Inicializar uma variável para controlar a exibição da tabela
    mostrar_tabela = False

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

# Se o usuário digitou algo no campo de pesquisa, mostrar a tabela com o filtro
    if keyword:
        df_favorecidos = df_favorecidos[df_favorecidos.apply(lambda row: row.astype(str).str.contains(keyword, case=False).any(), axis=1)]
        mostrar_tabela = True  # Sempre mostrar a tabela ao pesquisar

# Se o usuário não digitou nada, mostrar o botão para exibir a tabela completa
    if not keyword:
        if st.button('Exibir tudo'):
            mostrar_tabela = True  # Mostrar a tabela ao clicar no botão

# Calcular o valor total das linhas filtradas
    valor_total_filtrado = df_favorecidos['Valor Pago'].sum()

# Exibir a tabela apenas se a variável mostrar_tabela for True
    if mostrar_tabela:
    # Exibir a tabela
        st.dataframe(df_favorecidos.style.format({'Valor Pago': 'R$ {:,.2f}'}))

    # Exibir o valor total das linhas filtradas
        st.markdown(f"**Valor total pago das linhas filtradas:** R$ {valor_total_filtrado:,.2f}")






if __name__ == "__main__":
    run_dashboard()
