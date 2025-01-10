import streamlit as st
import pandas as pd
import plotly.express as px
import locale
from sidebar import load_sidebar
from data_loader import load_data
#from chatbot import render_chatbot  # Importar a função do chatbot
from analyzer import botao_analise

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

    # # Função para formatar valores monetários abreviados
    # def format_currency(value):
    #     if value >= 1e6:
    #         return locale.currency(value / 1e6, grouping=True) + ' M'
    #     elif value >= 1e3:
    #         return locale.currency(value / 1e3, grouping=True) + ' K'
    #     else:
    #         return locale.currency(value, grouping=True)

    # Função para formatar valores monetários abreviados
    def format_currency(value):
        if value >= 1e9:
            return f"R$ {value / 1e9:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + ' B'
        elif value >= 1e6:
            return f"R$ {value / 1e6:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + ' M'
        elif value >= 1e3:
            return f"R$ {value / 1e3:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + ' K'
        else:
            return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


   
    # Carregar o sidebar
    selected_ugs_despesas, selected_ano, selected_mes = load_sidebar(df, "despesas_ug")

    # Chame o chatbot para renderizar no sidebar
    #render_chatbot()

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
    #valor_total_formatado = locale.currency(valor_total_despesas, grouping=True)

    valor_total_formatado = f"R$ {valor_total_despesas:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


    # Adicionar métricas ao painel
    selected_ug_description = "Descrição não encontrada"

    if selected_ugs_despesas:
        # Obter a descrição da UG selecionada
        ug_descriptions = df_filtered[df_filtered['UG'].isin(selected_ugs_despesas)]['DESCRICAO_UG'].unique()
        if len(ug_descriptions) > 0:
            selected_ug_description = ug_descriptions[0]  # Pegue a primeira descrição encontrada

    # Exibir o subtítulo com a descrição da UG selecionada
    st.markdown(f'<h3 style="font-size:20px;"> {selected_ug_description}</h3>', unsafe_allow_html=True)
    
    # Dividindo em abas
    tab1, tab2, tab3, tab4 = st.tabs(["Visão Geral das Despesas", "Despesas por Subfunção e Fonte", "Despesas por Favorecido e Natureza","Detalhamento das Despesas"])

    with tab1:

        col1, col2 = st.columns(2)

        # Exibir a métrica de valor total
        col1.metric("Valor Total", valor_total_formatado)

        # Gráfico de Despesas por Ano
        col5, col6 = st.columns(2)

        with col5:
            # Preparar dados para o gráfico de despesas por ano
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
            # Preparar dados para o gráfico de despesas por função
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

    # Gráfico de Despesas Mensais do Ano Corrente
        st.markdown("### Despesas Mensais do Ano Corrente")
        ano_corrente = df_filtered['ANO'].max()

        # Mapear os números dos meses para os nomes dos meses
        meses_map = {
            1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho',
            7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
        }

        df_ano_corrente = df_filtered[df_filtered['ANO'] == ano_corrente].groupby('MES')['VALOR_PAGO'].sum().reset_index()
        df_ano_corrente['MES'] = df_ano_corrente['MES'].map(meses_map)
        df_ano_corrente['VALOR_PAGO_ABREVIADO'] = df_ano_corrente['VALOR_PAGO'].apply(format_currency)

        fig_corrente = px.bar(
            df_ano_corrente,
            x='MES',
            y='VALOR_PAGO',
            title=f'Despesas Mensais do Ano Corrente ({ano_corrente})',
            labels={'MES': 'Mês', 'VALOR_PAGO': 'Valor Pago'},
            text='VALOR_PAGO_ABREVIADO',
            color_discrete_sequence=['#41b8d5']
        )
        fig_corrente.update_layout(
            xaxis=dict(categoryorder='array', categoryarray=list(meses_map.values()))
        )
        fig_corrente.update_traces(
            textposition='outside',
            hovertemplate='%{x}<br>%{text}'
        )
        st.plotly_chart(fig_corrente, use_container_width=True)

        # Criar tabela de gastos mensais do ano corrente
        df_ano_corrente['VALOR_PAGO'] = df_ano_corrente['VALOR_PAGO'].apply(format_currency)

        # Preparar tabelas ocultas para análise
        tabela_ano = df_ano[['ANO', 'VALOR_PAGO']]
        tabela_funcao = df_funcao[['DESCRICAO_FUNCAO', 'VALOR_PAGO']]
        tabela_ano_corrente = df_ano_corrente[['MES', 'VALOR_PAGO']]

        # Contexto dos filtros
        filtros = {
            "UGs Selecionadas": selected_ug_description,
            "Período Selecionado (Ano)": f"{selected_ano[0]} a {selected_ano[1]}",
            "Meses Selecionados": f"{selected_mes[0]} a {selected_mes[1]}"
        }

        # Adicionar botão de análise com IA
        st.markdown("---")  # Linha divisória para separação visual
        st.subheader("Análise com Inteligência Artificial")

        botao_analise(
            titulo="Análise das Despesas por Ano, Função e Ano Corrente",
            tabelas=[
                ("Despesas por Ano", tabela_ano),
                ("Despesas por Função", tabela_funcao),
                ("Despesas Mensais do Ano Corrente", tabela_ano_corrente)
            ],
            botao_texto="Analisar com Inteligência Artificial",
            filtros=filtros,
            key="botao_analise_tab1"
        )
        
    with tab2:

        # Função para criar gráficos de barras horizontais
        def plot_bar_chart(df, group_col, title, x_label, y_label, color='#E55115'):
            df_grouped = df.groupby(group_col)['VALOR_PAGO'].sum().reset_index()
            df_grouped['VALOR_PAGO_FORMATADO'] = df_grouped['VALOR_PAGO'].apply(
                lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if pd.notnull(x) else "R$ 0,00"
            )

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
            fig.update_traces(
                text=df_grouped['VALOR_PAGO_FORMATADO'], 
                textposition='auto', 
                insidetextanchor='end', 
                hoverinfo='x+text'
            )
        
            # Calcular a altura do gráfico com base no número de categorias
            num_categories = df_grouped.shape[0]
            fig_height = max(400, num_categories * 30)
        
            fig.update_layout(yaxis={'categoryorder':'total ascending'}, height=fig_height)
            st.plotly_chart(fig, use_container_width=True)

            return df_grouped  # Retornar a tabela gerada para análise

        # Criar tabelas invisíveis e gráficos
        st.markdown("### Gráficos de Despesas por Subfunção e Fonte de Recurso")

        # Gráfico de Barras: Despesas por Subfunção
        tabela_subfuncao = plot_bar_chart(df_filtered, 'DESCRICAO_SUB_FUNCAO', 'Despesas por Subfunção', 'Valor Pago', 'Subfunção')

        # Gráfico de Barras: Despesas por Fonte de Recurso
        tabela_fonte = plot_bar_chart(df_filtered, 'DESCRICAO_FONTE', 'Despesas por Fonte de Recurso', 'Valor Pago', 'Fonte de Recurso')

        # Preparar tabelas para análise
        tabela_subfuncao = tabela_subfuncao[['DESCRICAO_SUB_FUNCAO', 'VALOR_PAGO']]
        tabela_fonte = tabela_fonte[['DESCRICAO_FONTE', 'VALOR_PAGO']]

        # Contexto dos filtros
        filtros = {
            "UGs Selecionadas": selected_ug_description,
            "Período Selecionado (Ano)": f"{selected_ano[0]} a {selected_ano[1]}",
            "Meses Selecionados": f"{selected_mes[0]} a {selected_mes[1]}"
        }

        # Adicionar botão de análise com IA
        st.markdown("---")  # Linha divisória para separação visual
        st.subheader("Análise com Inteligência Artificial")

        botao_analise(
            titulo="Análise das Despesas por Subfunção e Fonte de Recurso",
            tabelas=[
                ("Despesas por Subfunção", tabela_subfuncao),
                ("Despesas por Fonte de Recurso", tabela_fonte)
            ],
            botao_texto="Analisar com Inteligência Artificial",
            filtros=filtros,
            key="botao_analise_tab2"
        )

    with tab3:

        # Gráfico de Barras: Despesas por Favorecido
        df_favorecido = df_filtered.groupby('NOME_FAVORECIDO')['VALOR_PAGO'].sum().reset_index()
        df_favorecido = df_favorecido.sort_values(by='VALOR_PAGO', ascending=False).head(10)  # Exibir os 10 maiores favorecidos
        df_favorecido['VALOR_PAGO_FORMATADO'] = df_favorecido['VALOR_PAGO'].apply(
            lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if pd.notnull(x) else "R$ 0,00"
        )

        # Criar o gráfico de barras horizontais com a cor especificada
        fig_favorecido = px.bar(
            df_favorecido, 
            x='VALOR_PAGO', 
            y='NOME_FAVORECIDO', 
            orientation='h', 
            title='Despesas por Favorecido', 
            labels={'VALOR_PAGO': 'Valor Pago', 'NOME_FAVORECIDO': 'Favorecido'},
            color_discrete_sequence=['#E55115']
        )
        fig_favorecido.update_traces(
            text=df_favorecido['VALOR_PAGO_FORMATADO'], 
            textposition='auto', 
            insidetextanchor='end', 
            hoverinfo='x+text'
        )

        # Ajustar altura do gráfico dinamicamente
        num_categories_favorecido = df_favorecido.shape[0]
        fig_height_favorecido = max(400, num_categories_favorecido * 30)
        fig_favorecido.update_layout(yaxis={'categoryorder':'total ascending'}, height=fig_height_favorecido)

        # Exibir o gráfico
        st.plotly_chart(fig_favorecido, use_container_width=True)

        # Gráfico de Barras Empilhadas: Despesas por Natureza da Despesa
        opcoes_natureza = {
            'Natureza 1': 'DESCRICAO_NATUREZA1',
            'Natureza 2': 'DESCRICAO_NATUREZA2',
            'Natureza 3': 'DESCRICAO_NATUREZA3',
            'Natureza 4': 'DESCRICAO_NATUREZA4',
            'Natureza 5': 'DESCRICAO_NATUREZA5',
            'Natureza 6': 'DESCRICAO_NATUREZA6'
        }

        # Caixa de seleção para escolher a natureza
        selecao_natureza = st.selectbox(
            'Selecione a Natureza que deseja exibir no gráfico:',
            list(opcoes_natureza.keys()),
            index=5
        )

        # Filtrar a coluna selecionada
        coluna_selecionada = opcoes_natureza[selecao_natureza]

        # Agrupar os dados pela natureza selecionada e somar os valores pagos
        df_natureza = df_filtered.groupby(coluna_selecionada)['VALOR_PAGO'].sum().reset_index()
        df_natureza = df_natureza[df_natureza['VALOR_PAGO'] > 0]
        df_natureza['VALOR_PAGO_FORMATADO'] = df_natureza['VALOR_PAGO'].apply(format_currency)

        # Criar gráfico de barras
        height = max(600, len(df_natureza) * 30)
        fig_natureza = px.bar(
            df_natureza,
            x=coluna_selecionada,
            y='VALOR_PAGO',
            text='VALOR_PAGO_FORMATADO',
            title=f'Despesas por {selecao_natureza}',
            labels={coluna_selecionada: selecao_natureza, 'VALOR_PAGO': 'Valor Pago'},
            color_discrete_sequence=['#095aa2']
        )
        fig_natureza.update_traces(textposition='outside')
        fig_natureza.update_layout(height=height)

        # Exibir o gráfico
        st.plotly_chart(fig_natureza, use_container_width=True)

        # Preparar tabelas para análise
        tabela_favorecido = df_favorecido[['NOME_FAVORECIDO', 'VALOR_PAGO']]
        tabela_natureza = df_natureza[[coluna_selecionada, 'VALOR_PAGO']]

        # Contexto dos filtros
        filtros = {
            "UGs Selecionadas": selected_ug_description,
            "Período Selecionado (Ano)": f"{selected_ano[0]} a {selected_ano[1]}",
            "Meses Selecionados": f"{selected_mes[0]} a {selected_mes[1]}",
            "Natureza Selecionada": selecao_natureza
        }

        # Adicionar botão de análise com IA
        st.markdown("---")
        st.subheader("Análise com Inteligência Artificial")

        botao_analise(
            titulo="Análise das Despesas por Favorecido e Natureza",
            tabelas=[
                ("Despesas por Favorecido", tabela_favorecido),
                (f"Despesas por {selecao_natureza}", tabela_natureza)
            ],
            botao_texto="Analisar com Inteligência Artificial",
            filtros=filtros,
            key="botao_analise_tab3"
        )

    with tab4:

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
