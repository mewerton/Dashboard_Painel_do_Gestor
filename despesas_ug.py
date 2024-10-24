import streamlit as st
import pandas as pd
import plotly.express as px
import locale
from sidebar import load_sidebar
from data_loader import load_data
from chatbot import render_chatbot  # Importar a função do chatbot

# Configurar o locale para português do Brasil
#locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

# Tente definir o locale para pt_BR. Se falhar, use o locale padrão do sistema
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_ALL, '')  # Fallback para o locale padrão do sistema

def run_dashboard():
    # Carregar dados usando o módulo centralizado
    df = load_data()

    if df is None:
        st.error("Nenhum dado foi carregado. Por favor, verifique os arquivos de entrada.")
        return

    # Função para formatar valores monetários abreviados
    def format_currency(value):
        if value >= 1e6:
            return locale.currency(value / 1e6, grouping=True) + ' M'
        elif value >= 1e3:
            return locale.currency(value / 1e3, grouping=True) + ' K'
        else:
            return locale.currency(value, grouping=True)

   
    # Carregar o sidebar
    selected_ugs_despesas, selected_ano, selected_mes = load_sidebar(df, "despesas_ug")

    # Chame o chatbot para renderizar no sidebar
    render_chatbot()

    if df is not None:
        # Filtrar dados apenas para o Poder Executivo
        df = df[df['PODER'] == 'EXE']


    # Aplicar filtros ao dataframe
    df_filtered = df[df['UG'].isin(selected_ugs_despesas)]
    df_filtered = df_filtered[(df_filtered['ANO'] >= selected_ano[0]) & (df_filtered['ANO'] <= selected_ano[1])]
    df_filtered = df_filtered[(df_filtered['MES'] >= selected_mes[0]) & (df_filtered['MES'] <= selected_mes[1])]

    # Eliminar linhas com valores em branco nas colunas de interesse
    df_filtered = df_filtered.dropna(subset=['UO', 'UG', 'ANO', 'MES'])

    # Tratamento de dados
    df_filtered['VALOR_EMPENHADO'] = df_filtered['VALOR_EMPENHADO'].apply(pd.to_numeric, errors='coerce')
    df_filtered['VALOR_LIQUIDADO'] = df_filtered['VALOR_LIQUIDADO'].apply(pd.to_numeric, errors='coerce')
    df_filtered['VALOR_PAGO'] = df_filtered['VALOR_PAGO'].apply(pd.to_numeric, errors='coerce')

    # Obter a quantidade de despesas e valor total
    quantidade_despesas = len(df_filtered)
    valor_total_despesas = df_filtered['VALOR_PAGO'].sum()

    # Formatar valor total para moeda
    valor_total_formatado = locale.currency(valor_total_despesas, grouping=True)

    # Adicionar métricas ao painel
    selected_ug_description = "Descrição não encontrada"

    if selected_ugs_despesas:
        # Obter a descrição da UG selecionada
        ug_descriptions = df_filtered[df_filtered['UG'].isin(selected_ugs_despesas)]['DESCRICAO_UG'].unique()
        if len(ug_descriptions) > 0:
            selected_ug_description = ug_descriptions[0]  # Pegue a primeira descrição encontrada

    # Exibir o subtítulo com a descrição da UG selecionada
    st.markdown(f'<h3 style="font-size:20px;"> {selected_ug_description}</h3>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    col1.metric("Quantidade de Despesas", quantidade_despesas)
    col2.metric("Valor Total", valor_total_formatado)

    # Gráfico de Setores: Despesas por Função
    col5, col6 = st.columns(2)

    with col5:
        # Gráfico de Despesas por Ano
        df_ano = df_filtered.groupby('ANO')['VALOR_PAGO'].sum().reset_index()
        df_ano['VALOR_PAGO_ABREVIADO'] = df_ano['VALOR_PAGO'].apply(format_currency)

    # Criar o gráfico de barras com valores abreviados
        fig_ano = px.bar(
            df_ano, 
            x='ANO', 
            y='VALOR_PAGO', 
            title='Despesas por Ano', 
            labels={'VALOR_PAGO': 'Valor Pago'}, 
            color_discrete_sequence=['#41b8d5']
        )

    # Atualizar traços para definir a cor do texto dentro das barras
        fig_ano.update_traces(
            text=df_ano['VALOR_PAGO_ABREVIADO'], 
            textposition='inside', 
            textfont_color='white',  # Define a cor do texto dentro das barras como branco
            hovertemplate='%{x}<br>%{text}'
        )

        st.plotly_chart(fig_ano, use_container_width=True)

    with col6:
    # Gráfico de Despesas por Função
        df_funcao = df_filtered.groupby('DESCRICAO_FUNCAO')['VALOR_PAGO'].sum().reset_index()
        fig_funcao = px.pie(
            df_funcao, 
            values='VALOR_PAGO', 
            names='DESCRICAO_FUNCAO', 
            title='Proporção das Despesas por Função', 
            labels={'VALOR_PAGO': 'Valor Pago', 'DESCRICAO_FUNCAO': 'Função'},
            hole=0.4,  # Adiciona o parâmetro hole para criar um gráfico de rosca
            color_discrete_sequence=['#2d8bba','#2f5f98', '#41b8d5', '#31356e', '#042b4d']  # Define as cores personalizadas
        )
        st.plotly_chart(fig_funcao, use_container_width=True)

    # Função para criar gráficos de barras horizontais
    def plot_bar_chart(df, group_col, title, x_label, y_label, color='#E55115'):
        df_grouped = df.groupby(group_col)['VALOR_PAGO'].sum().reset_index()
        df_grouped['VALOR_PAGO_FORMATADO'] = df_grouped['VALOR_PAGO'].apply(lambda x: locale.currency(x, grouping=True))
    
    # Criar o gráfico de barras horizontais com a cor especificada
        fig = px.bar(
            df_grouped, 
            x='VALOR_PAGO', 
            y=group_col, 
            orientation='h', 
            title=title, 
            labels={'VALOR_PAGO': x_label, group_col: y_label},
            color_discrete_sequence=[color]  # Define a cor das barras
        )
        fig.update_traces(text=df_grouped['VALOR_PAGO_FORMATADO'], textposition='auto', insidetextanchor='end', hoverinfo='x+text')
    
    # Calcular a altura do gráfico com base no número de categorias
        num_categories = df_grouped.shape[0]
        fig_height = max(400, num_categories * 30)
    
        fig.update_layout(yaxis={'categoryorder':'total ascending'}, height=fig_height)
        st.plotly_chart(fig, use_container_width=True)

    # Gráfico de Barras: Despesas por Subfunção
    plot_bar_chart(df_filtered, 'DESCRICAO_SUB_FUNCAO', 'Despesas por Subfunção', 'Valor Pago', 'Subfunção')

    # Gráfico de Barras: Despesas por Fonte de Recurso
    plot_bar_chart(df_filtered, 'DESCRICAO_FONTE', 'Despesas por Fonte de Recurso', 'Valor Pago', 'Fonte de Recurso')

    # Gráfico de Barras: Despesas por Favorecido
    df_favorecido = df_filtered.groupby('NOME_FAVORECIDO')['VALOR_PAGO'].sum().reset_index()
    df_favorecido = df_favorecido.sort_values(by='VALOR_PAGO', ascending=False).head(10)  # Exibir os 10 maiores favorecidos
    df_favorecido['VALOR_PAGO_FORMATADO'] = df_favorecido['VALOR_PAGO'].apply(lambda x: locale.currency(x, grouping=True))

    # Criar o gráfico de barras horizontais com a cor especificada
    fig_favorecido = px.bar(
        df_favorecido, 
        x='VALOR_PAGO', 
        y='NOME_FAVORECIDO', 
        orientation='h', 
        title='Despesas por Favorecido', 
        labels={'VALOR_PAGO': 'Valor Pago', 'NOME_FAVORECIDO': 'Favorecido'},
        color_discrete_sequence=['#E55115']  # Define a cor das barras
    )
    fig_favorecido.update_traces(text=df_favorecido['VALOR_PAGO_FORMATADO'], textposition='auto', insidetextanchor='end', hoverinfo='x+text')

    # Calcular a altura do gráfico com base no número de categorias
    num_categories_favorecido = df_favorecido.shape[0]
    fig_height_favorecido = max(400, num_categories_favorecido * 30)

    fig_favorecido.update_layout(yaxis={'categoryorder':'total ascending'}, height=fig_height_favorecido)
    st.plotly_chart(fig_favorecido, use_container_width=True)


    # Gráfico de Barras Empilhadas: Despesas por Natureza da Despesa
    # Agrupar as despesas por natureza
    df_natureza = df_filtered.groupby(['DESCRICAO_NATUREZA1', 'DESCRICAO_NATUREZA2', 'DESCRICAO_NATUREZA3', 'DESCRICAO_NATUREZA4', 'DESCRICAO_NATUREZA5', 'DESCRICAO_NATUREZA6'])['VALOR_PAGO'].sum().reset_index()

    # Formatar os valores como moeda
    df_natureza['VALOR_PAGO_FORMATADO'] = df_natureza['VALOR_PAGO'].apply(lambda x: locale.currency(x, grouping=True))

    # Opções de seleção de naturezas
    opcoes_natureza = {
        'Natureza 1': 'DESCRICAO_NATUREZA1',
        'Natureza 2': 'DESCRICAO_NATUREZA2',
        'Natureza 3': 'DESCRICAO_NATUREZA3',
        'Natureza 4': 'DESCRICAO_NATUREZA4',
        'Natureza 5': 'DESCRICAO_NATUREZA5',
        'Natureza 6': 'DESCRICAO_NATUREZA6'
        #'Natureza': 'DESCRICAO_NATUREZA'
    }

    # Caixa de seleção para escolher a natureza
    selecao_natureza = st.selectbox(
        'Selecione a Natureza que deseja exibir no gráfico:',
        list(opcoes_natureza.keys()),
        index=5  # Define "Natureza 6" como padrão
    )

    # Filtrando a coluna selecionada
    coluna_selecionada = opcoes_natureza[selecao_natureza]

    # Agrupando os dados pela natureza selecionada e somando os valores pagos
    df_agrupado = df_filtered.groupby(coluna_selecionada)['VALOR_PAGO'].sum().reset_index()

    # Filtrando os valores maiores que 0
    df_agrupado = df_agrupado[df_agrupado['VALOR_PAGO'] > 0]

    # Formatando os valores em real brasileiro
    df_agrupado['VALOR_PAGO_FORMATADO'] = df_agrupado['VALOR_PAGO'].apply(format_currency)

    # Definindo a altura do gráfico dinamicamente
    num_barras = len(df_agrupado)
    height = max(600, num_barras * 30)  # Ajusta a altura com base no número de barras

    # Criando o gráfico de barras com os valores visíveis
    fig_bar = px.bar(
        df_agrupado,
        x=coluna_selecionada,
        y='VALOR_PAGO',
        text='VALOR_PAGO_FORMATADO',
        title=f'Despesas por {selecao_natureza}',
        labels={coluna_selecionada: selecao_natureza, 'VALOR_PAGO': 'Valor Pago'},
        color_discrete_sequence=['#095aa2']  # Define a cor das barras
    )

    # Atualizando o layout do gráfico
    fig_bar.update_traces(textposition='outside')
    fig_bar.update_layout(
        uniformtext_minsize=5,
        uniformtext_mode='hide',
        height=height  # Define a altura do gráfico
    )

    # Exibindo o gráfico no Streamlit
    st.plotly_chart(fig_bar, use_container_width=True)

    # Adicionar uma tabela detalhada com informações de despesas por natureza
    st.subheader('Despesas - Detalhado')
    df_detalhado = df_filtered[['DESCRICAO_NATUREZA', 'NOME_FAVORECIDO', 'TIPO_LICITACAO', 'UG_EMITENTE', 'NOTA_EMPENHO', 'COD_PROCESSO', 'NOME_CONTRATO', 'OBSERVACAO_NE', 'VALOR_PAGO']]

    # Ajustar o limite de células permitidas para renderização
    pd.set_option("styler.render.max_elements", 999999)  # Altere este número para o total de células do seu dataframe

    # Campo de entrada para a palavra-chave de pesquisa
    keyword = st.text_input('Digite uma palavra-chave para filtrar a tabela:')

    # Inicializar uma variável para controlar a exibição da tabela
    mostrar_tabela = False

    # Se o usuário digitou algo no campo de pesquisa, mostrar a tabela com o filtro
    if keyword:
        df_detalhado = df_detalhado[df_detalhado.apply(lambda row: row.astype(str).str.contains(keyword, case=False).any(), axis=1)]
        mostrar_tabela = True  # Sempre mostrar a tabela ao pesquisar

    # Se o usuário não digitou nada, mostrar o botão para exibir a tabela completa
    if not keyword:
        if st.button('Exibir tudo'):
            mostrar_tabela = True  # Mostrar a tabela ao clicar no botão

    # Opções de exibição de valores
    col7, col8, col9 = st.columns(3)

    with col7:
        exibir_positivos = st.checkbox('Exibir valores positivos', value=True)

    with col8:
        exibir_zerados = st.checkbox('Exibir valores zerados', value=True)

    with col9:
        exibir_negativos = st.checkbox('Exibir valores negativos', value=True)

    # Filtrar o dataframe com base nas opções de exibição
    if not exibir_positivos:
        df_detalhado = df_detalhado[df_detalhado['VALOR_PAGO'] <= 0]
    if not exibir_zerados:
        df_detalhado = df_detalhado[df_detalhado['VALOR_PAGO'] != 0]
    if not exibir_negativos:
        df_detalhado = df_detalhado[df_detalhado['VALOR_PAGO'] >= 0]

    # Calcular o valor total das linhas filtradas
    valor_total_filtrado = df_detalhado['VALOR_PAGO'].sum()

    # Exibir a tabela apenas se a variável mostrar_tabela for True
    if mostrar_tabela:
        # Configurar a formatação de valores na exibição usando o st.dataframe
        st.dataframe(
            df_detalhado.rename(columns={
                'DESCRICAO_NATUREZA': 'Natureza',
                'NOME_FAVORECIDO': 'Favorecido',
                'TIPO_LICITACAO': 'Tipo Licitação',
                'UG_EMITENTE': 'UG Emitente',
                'NOTA_EMPENHO': 'Nota de Empenho',
                'COD_PROCESSO': 'Código do Processo',
                'NOME_CONTRATO': 'Nome do Contrato',
                'OBSERVACAO_NE': 'Observação',
                'VALOR_PAGO': 'Valor Pago'
            }).style.format({'Valor Pago': 'R$ {:,.2f}'})
        )

        # Exibir o valor total das linhas filtradas
        st.markdown(f"**Valor total pago das linhas filtradas:** R$ {valor_total_filtrado:,.2f}")





if __name__ == "__main__":
    run_dashboard()
