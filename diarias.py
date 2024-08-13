    # Filtrar dados de diárias
    df_diarias = df[df['DESCRICAO_NATUREZA6'].isin(['DIARIAS - CIVIL', 'DIARIAS - MILITAR'])]

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
        df_tipo = df_diarias.groupby('DESCRICAO_NATUREZA6')[['VALOR_EMPENHADO', 'VALOR_PAGO']].sum().reset_index()
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