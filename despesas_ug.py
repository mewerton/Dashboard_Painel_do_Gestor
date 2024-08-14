import streamlit as st
import pandas as pd
import plotly.express as px
import locale
from sklearn.linear_model import LinearRegression
import numpy as np
from sklearn.metrics import mean_absolute_error

# Configurar o locale para português do Brasil
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

def run_dashboard():
    @st.cache_data
    def load_data(file_paths):
        dfs = []
        total_files = len(file_paths)
        with st.empty():
            progress_bar = st.progress(0)
            for i, file_path in enumerate(file_paths):
                try:
                    df = pd.read_excel(file_path, sheet_name=0)
                    dfs.append(df)
                except FileNotFoundError:
                    st.error(f"O arquivo {file_path} não foi encontrado.")
                except Exception as e:
                    st.error(f"Ocorreu um erro ao carregar o arquivo {file_path}: {e}")
            
                progress = (i + 1) / total_files
                progress_bar.progress(progress)
    
        if len(dfs) == 0:
            return None
        else:
            return pd.concat(dfs, ignore_index=True)

    file_paths = [
        "./database/despesa_empenhado_liquidado_pago_detalhado_2018.xlsx",
        "./database/despesa_empenhado_liquidado_pago_detalhado_2019.xlsx",
        "./database/despesa_empenhado_liquidado_pago_detalhado_2020.xlsx",
        "./database/despesa_empenhado_liquidado_pago_detalhado_2021.xlsx",
        "./database/despesa_empenhado_liquidado_pago_detalhado_2022.xlsx",
        "./database/despesa_empenhado_liquidado_pago_detalhado_2023.xlsx",
        "./database/despesa_empenhado_liquidado_pago_detalhado_2024.xlsx"
    ]
    df = load_data(file_paths)

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

    # Função para ajustar os dados dos anos da COVID-19 para a predição
    def adjust_for_covid(df, covid_years, pre_covid_years, post_covid_years):
        adjusted_df = df.copy()
        for year in covid_years:
            pre_covid_data = df[df['ANO'].isin(pre_covid_years)]
            post_covid_data = df[df['ANO'].isin(post_covid_years)]
            pre_covid_avg = pre_covid_data.groupby(['MES'])['VALOR_PAGO'].mean().reset_index()
            post_covid_avg = post_covid_data.groupby(['MES'])['VALOR_PAGO'].mean().reset_index()
            
            avg_crescent = pd.DataFrame()
            avg_crescent['MES'] = pre_covid_avg['MES']
            avg_crescent['VALOR_PAGO'] = (pre_covid_avg['VALOR_PAGO'] + post_covid_avg['VALOR_PAGO']) / 2
            
            adjusted_df.loc[adjusted_df['ANO'] == year, 'VALOR_PAGO'] = adjusted_df[adjusted_df['ANO'] == year]['MES'].map(avg_crescent.set_index('MES')['VALOR_PAGO'])
        
        return adjusted_df

    # Anos de COVID e períodos pré e pós COVID
    covid_years = [2020, 2021]
    pre_covid_years = [2018, 2019]
    post_covid_years = [2022, 2023]

    # Ajustar os dados para a predição
    df_for_prediction = adjust_for_covid(df, covid_years, pre_covid_years, post_covid_years)

    # Função para realizar análise preditiva por mês e calcular a acurácia
    def perform_predictive_analysis_by_month(df):
        future_data = []
        mae_values = []
        mape_values = []

        for mes in range(1, 13):
            df_mes = df[df['MES'] == mes]

            if df_mes.empty:
                continue

            # Preparar os dados para a regressão linear
            X = df_mes['ANO'].values.reshape(-1, 1)
            y = df_mes['VALOR_PAGO'].values

            # Verificar se existem valores zero em y para evitar divisão por zero
            if np.any(y == 0):
                continue

            # Treinar o modelo de regressão linear
            model = LinearRegression()
            model.fit(X, y)

            # Fazer previsões para o próximo ano
            next_year = df_mes['ANO'].max() + 1
            future_prediction = model.predict(np.array([[next_year]]))[0]

            # Calcular a acurácia (MAE) usando cross-validation
            y_pred = model.predict(X)
            mae = mean_absolute_error(y, y_pred)
            mae_values.append(mae)

            # Calcular o MAPE
            mape = np.mean(np.abs((y - y_pred) / y)) * 100
            mape_values.append(mape)

            # Armazenar o resultado
            future_data.append({'MES': mes, 'ANO': next_year, 'VALOR_PAGO_PREVISTO': future_prediction})

        # Calcular a média do MAE e do MAPE para todos os meses
        avg_mae = np.mean(mae_values) if mae_values else float('nan')
        avg_mape = np.mean(mape_values) if mape_values else float('nan')

        # Criar um DataFrame com as previsões futuras
        future_df = pd.DataFrame(future_data)

        return future_df, avg_mae, avg_mape

    # Filtrar dados apenas para as UGs específicas
    ugs_interesse_despesas = [
        520527, 540547, 540573, 140566, 300041, 300567, 540545, 250505, 510514, 510520, 
        520555, 520537, 410506, 410504, 510517, 410510, 520528, 410548, 530539, 530538, 
        410512, 530542, 130569, 130570, 130571, 130572, 410515, 510551, 530541, 510516, 
        510556, 520026, 520531, 530032, 530543, 540037, 540574, 540035, 510024, 510526, 
        520027, 520507, 540038, 520031, 520032, 520533, 350032, 360021, 510522, 260562, 
        530031, 520028, 910997, 510021, 510557, 110010, 340051, 340568, 190047, 190049, 
        190563, 190565, 540033, 510023, 510524, 510020, 410017, 410511, 410018, 410513, 
        520030, 520536, 540034, 110009, 110564, 540036, 210013, 110015, 370001, 110008, 
        110006, 410516, 520529, 520530, 520534, 530537, 990999, 520538, 380001, 520033
    ]

    ugs_default_despesas = [340051]

    if df is not None:
        # Filtrar dados apenas para o Poder Executivo
        df = df[df['PODER'] == 'EXE']

    # Sidebar com filtros
    selected_ugs_despesas = st.sidebar.multiselect(
        'Selecione a UG de interesse:',
        options=ugs_interesse_despesas,
        default=ugs_default_despesas
    )

    min_ano = int(df['ANO'].min())
    max_ano = int(df['ANO'].max())

    # Verificar se min_ano é igual a max_ano
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
        fig_ano = px.bar(df_ano, x='ANO', y='VALOR_PAGO', title='Despesas por Ano', labels={'VALOR_PAGO': 'Valor Pago'})
        fig_ano.update_traces(text=df_ano['VALOR_PAGO_ABREVIADO'], textposition='inside', hovertemplate='%{x}<br>%{text}')
        st.plotly_chart(fig_ano, use_container_width=True)

    with col6:
        # Gráfico de Despesas por Função
        df_funcao = df_filtered.groupby('DESCRICAO_FUNCAO')['VALOR_PAGO'].sum().reset_index()
        fig_funcao = px.pie(df_funcao, values='VALOR_PAGO', names='DESCRICAO_FUNCAO', title='Proporção das Despesas por Função', labels={'VALOR_PAGO': 'Valor Pago', 'DESCRICAO_FUNCAO': 'Função'})
        st.plotly_chart(fig_funcao, use_container_width=True)
    
    # Função para criar gráficos de barras horizontais
    def plot_bar_chart(df, group_col, title, x_label, y_label):
        df_grouped = df.groupby(group_col)['VALOR_PAGO'].sum().reset_index()
        df_grouped['VALOR_PAGO_FORMATADO'] = df_grouped['VALOR_PAGO'].apply(lambda x: locale.currency(x, grouping=True))
        fig = px.bar(df_grouped, x='VALOR_PAGO', y=group_col, orientation='h', title=title, labels={'VALOR_PAGO': x_label, group_col: y_label})
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
    fig_favorecido = px.bar(df_favorecido, x='VALOR_PAGO', y='NOME_FAVORECIDO', orientation='h', title='Despesas por Favorecido', labels={'VALOR_PAGO': 'Valor Pago', 'NOME_FAVORECIDO': 'Favorecido'})
    fig_favorecido.update_traces(text=df_favorecido['VALOR_PAGO_FORMATADO'], textposition='auto', insidetextanchor='end', hoverinfo='x+text')

    # Calcular a altura do gráfico com base no número de categorias
    num_categories_favorecido = df_favorecido.shape[0]
    fig_height_favorecido = max(400, num_categories_favorecido * 30)

    fig_favorecido.update_layout(yaxis={'categoryorder':'total ascending'}, height=fig_height_favorecido)
    st.plotly_chart(fig_favorecido, use_container_width=True)

    # Gráfico de Barras Empilhadas: Despesas por Natureza da Despesa
    # Agrupar as despesas por natureza
    df_natureza = df_filtered.groupby(['DESCRICAO_NATUREZA', 'DESCRICAO_NATUREZA1', 'DESCRICAO_NATUREZA2', 'DESCRICAO_NATUREZA3', 'DESCRICAO_NATUREZA4', 'DESCRICAO_NATUREZA5', 'DESCRICAO_NATUREZA6'])['VALOR_PAGO'].sum().reset_index()

    # Formatar os valores como moeda
    df_natureza['VALOR_PAGO_FORMATADO'] = df_natureza['VALOR_PAGO'].apply(lambda x: locale.currency(x, grouping=True))

    # Opções de seleção de naturezas
    opcoes_natureza = {
        'Natureza 1': 'DESCRICAO_NATUREZA1',
        'Natureza 2': 'DESCRICAO_NATUREZA2',
        'Natureza 3': 'DESCRICAO_NATUREZA3',
        'Natureza 4': 'DESCRICAO_NATUREZA4',
        'Natureza 5': 'DESCRICAO_NATUREZA5',
        'Natureza 6': 'DESCRICAO_NATUREZA6',
        'Natureza': 'DESCRICAO_NATUREZA'
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
        labels={coluna_selecionada: selecao_natureza, 'VALOR_PAGO': 'Valor Pago'}
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

    # Realizar a análise preditiva por mês e obter o MAE e o MAPE
    df_meses_ano = df_for_prediction.groupby(['MES', 'ANO'])['VALOR_PAGO'].sum().reset_index()
    future_df_by_month, avg_mae, avg_mape = perform_predictive_analysis_by_month(df_meses_ano)

    # Combinar dados históricos e previsões
    combined_df = pd.concat([df_meses_ano, future_df_by_month.rename(columns={'VALOR_PAGO_PREVISTO': 'VALOR_PAGO'})], ignore_index=True)

    # Gráfico de previsões futuras combinadas
    fig_combined = px.line(combined_df, x='MES', y='VALOR_PAGO', color='ANO', title='Comparação de Despesas nos Últimos Anos e Previsão de Despesas para os Próximos 12 Meses usando Inteligência Artificial', labels={'VALOR_PAGO': 'Valor Pago', 'MES': 'Mês'})
    fig_combined.update_traces(mode='lines+markers')
    st.plotly_chart(fig_combined, use_container_width=True)

    # Texto em letras pequenas abaixo do gráfico
    st.markdown(f"""
        <p style='font-size:11px'>
        Análise Mensal: Criamos um modelo de regressão linear separado para cada mês, utilizando os dados históricos desse mês. <br>
        Combinação de Dados: Combinamos os dados históricos com as previsões futuras para gerar um gráfico combinado. <br>
        Acurácia da Previsão: A precisão média das previsões (erro absoluto médio) é de <strong>{locale.currency(avg_mae, grouping=True)}</strong>.<br>
        Erro Percentual Médio Absoluto (MAPE): <strong>{avg_mape:.2f}%</strong>. <br>
        </p>
        """, unsafe_allow_html=True)

    # Função para gerar análise lógica
    def generate_logical_analysis(df, future_df):
        current_avg = df['VALOR_PAGO'].mean()

        predicted_max = future_df['VALOR_PAGO_PREVISTO'].max() if not future_df.empty else 0
        predicted_min = future_df['VALOR_PAGO_PREVISTO'].min() if not future_df.empty else 0
        predicted_avg = future_df['VALOR_PAGO_PREVISTO'].mean() if not future_df.empty else 0

        # Encontrar o mês atual e o próximo mês
        current_month = df['MES'].max()
        next_month = current_month + 1 if current_month < 12 else 1

        # Valores pagos no mês atual e previsto para o próximo mês
        current_month_value = df[df['MES'] == current_month]['VALOR_PAGO'].mean()
        next_month_prediction = future_df[future_df['MES'] == next_month]['VALOR_PAGO_PREVISTO'].values[0] if next_month in future_df['MES'].values else 0

        analysis_text = f"""
        <style>
        .analysis-text {{
            font-family: Arial, sans-serif;
            font-size: 16px;
            line-height: 1.5;
        }}
        </style>
        <div class="analysis-text">
        <p>Para os próximos 12 meses, a previsão indica que o valor máximo esperado das despesas será de <strong>{format_currency(predicted_max)}</strong>, 
        o valor mínimo previsto é de <strong>{format_currency(predicted_min)}</strong>, e a média prevista é de <strong>{format_currency(predicted_avg)}</strong>.</p>
        <p>Essas previsões sugerem uma tendência de <strong>{'aumento' if predicted_avg > current_avg else 'redução'}</strong> nas despesas. </p>
        </div>
        """
    
        return analysis_text

    # Gerar o texto para análise lógica
    logical_analysis_text = generate_logical_analysis(df_meses_ano, future_df_by_month)

    # Exibir o resultado da análise lógica
    st.subheader("Análise Preditiva dos Dados com Inteligência Artificial")
    st.markdown(logical_analysis_text, unsafe_allow_html=True)

    # Texto em letras pequenas abaixo do gráfico
    st.markdown("""
        <p style='font-size:11px'>
        Observação sobre a Previsão: <br>
        Considerando que utilizamos dados históricos de apenas 6 anos para prever o gasto do sétimo ano, é importante ressaltar que a precisão da previsão pode ser limitada. A utilização de uma amostra relativamente pequena de dados pode resultar em uma maior incerteza nas previsões futuras. Portanto, é possível que ocorram grandes disparidades entre os valores previstos e os valores reais devido à falta de informações abrangentes sobre os padrões de gastos ao longo do tempo.
        </p>
        """, unsafe_allow_html=True)

    # ============================= PAINEL DE DIÁRIAS ============================= 
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
