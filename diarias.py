import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
            title='Evolução Mensal das Diárias',
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

#===========================================================================================
    # Contagem dos servidores que receberam diárias em 3, 4-5, e 6 ou mais meses consecutivos
    
    # Adicionar a tabela de Favorecidos das Diárias com filtro por palavra-chave e cálculo do valor total filtrado
    st.subheader('Servidores recebendo Diárias Consecutivas')

# Identificar o último mês e ano no dataset
    ultimo_ano = df_diarias['ANO'].max()
    ultimo_mes = df_diarias[df_diarias['ANO'] == ultimo_ano]['MES'].max()

# Função para contar servidores consecutivos sem duplicações
    def contar_servidores_consecutivos(meses, servidores_contabilizados):
        servidores_consecutivos = 0
        servidores = df_diarias['NOME_FAVORECIDO'].unique()
    
        for servidor in servidores:
            if servidor in servidores_contabilizados:
                continue  # Pular servidores que já foram contabilizados
        
            df_servidor = df_diarias[df_diarias['NOME_FAVORECIDO'] == servidor]
            df_servidor = df_servidor.sort_values(by=['ANO', 'MES'], ascending=False)
        
            consecutivos = 0
            mes_atual = ultimo_mes
            ano_atual = ultimo_ano
        
            for _ in range(meses):
                if df_servidor[(df_servidor['ANO'] == ano_atual) & (df_servidor['MES'] == mes_atual)].shape[0] > 0:
                    consecutivos += 1
                else:
                    break
            
                # Ajustar para o mês anterior
                mes_atual -= 1
                if mes_atual == 0:
                    mes_atual = 12
                    ano_atual -= 1
        
            if consecutivos == meses:
                servidores_consecutivos += 1
                servidores_contabilizados.add(servidor)  # Adicionar o servidor à lista de contabilizados
    
        return servidores_consecutivos

# Set para rastrear servidores já contabilizados
    servidores_contabilizados = set()

# Contar servidores sem duplicação
    servidores_6_ou_mais_meses = contar_servidores_consecutivos(6, servidores_contabilizados)
    servidores_4_5_meses = contar_servidores_consecutivos(4, servidores_contabilizados) + contar_servidores_consecutivos(5, servidores_contabilizados)
    servidores_3_meses = contar_servidores_consecutivos(3, servidores_contabilizados)

# Função para criar gráfico de velocímetro
    def criar_grafico_velocimetro(titulo, valor, max_valor, cores):
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=valor,
            title={'text': titulo},
            gauge={'axis': {'range': [0, max_valor]},
                'steps': [
                    {'range': [0, max_valor/3], 'color': cores[0]},
                    {'range': [max_valor/3, 2*max_valor/3], 'color': cores[1]},
                    {'range': [2*max_valor/3, max_valor], 'color': cores[2]},
                    ],
                    'bar': {'color': '#042441'}  # Cor do ponteiro
            }
        ))
        return fig

# Máximo para o velocímetro
    max_valor = max(servidores_3_meses, servidores_4_5_meses, servidores_6_ou_mais_meses)

    col1, col2, col3 = st.columns(3)

# Gráfico de velocímetro para 3 meses
    with col1:
        fig_3_meses = criar_grafico_velocimetro('Últimos 3 meses', servidores_3_meses, max_valor, ['#FCDC20', '#FCDC20', '#FCDC20'])
        st.plotly_chart(fig_3_meses)

# Gráfico de velocímetro para 4-5 meses
    with col2:
        fig_4_5_meses = criar_grafico_velocimetro('Últimos 4-5 meses', servidores_4_5_meses, max_valor, ['#E55115', '#E55115', '#E55115'])
        st.plotly_chart(fig_4_5_meses)

# Gráfico de velocímetro para 6 ou mais meses
    with col3:
        fig_6_ou_mais_meses = criar_grafico_velocimetro('Últimos 6 ou mais', servidores_6_ou_mais_meses, max_valor, ['#ff0000', '#ff0000', '#ff0000'])
        st.plotly_chart(fig_6_ou_mais_meses)

#======= Tabela dos servidores que receberam diárias nos ultimos meses consecutivos

# Função para obter os detalhes dos servidores que receberam diárias consecutivas
    def obter_servidores_consecutivos(meses, servidores_contabilizados):
        servidores_detalhes = []
        servidores = df_diarias['NOME_FAVORECIDO'].unique()
    
        for servidor in servidores:
            if servidor in servidores_contabilizados:
                continue  # Pular servidores que já foram contabilizados
        
            df_servidor = df_diarias[df_diarias['NOME_FAVORECIDO'] == servidor]
            df_servidor = df_servidor.sort_values(by=['ANO', 'MES'], ascending=False)
        
            consecutivos = 0
            mes_atual = ultimo_mes
            ano_atual = ultimo_ano
            valor_total = 0
        
            for _ in range(meses):
                df_mes = df_servidor[(df_servidor['ANO'] == ano_atual) & (df_servidor['MES'] == mes_atual)]
                if df_mes.shape[0] > 0:
                    consecutivos += 1
                    valor_total += df_mes['VALOR_PAGO'].sum()
                else:
                    break
            
                # Ajustar para o mês anterior
                mes_atual -= 1
                if mes_atual == 0:
                    mes_atual = 12
                    ano_atual -= 1
        
            if consecutivos == meses:
                servidores_detalhes.append({'Nome do Servidor': servidor, 'Valor Total Pago': valor_total})
                servidores_contabilizados.add(servidor)  # Adicionar o servidor à lista de contabilizados
    
        return servidores_detalhes

# Set para rastrear servidores já contabilizados
    servidores_contabilizados = set()

# Obter detalhes dos servidores para 6 ou mais meses primeiro
    servidores_6_ou_mais_meses_detalhes = obter_servidores_consecutivos(6, servidores_contabilizados)

# Obter detalhes dos servidores para 4 e 5 meses
    servidores_4_meses_detalhes = obter_servidores_consecutivos(4, servidores_contabilizados)
    servidores_5_meses_detalhes = obter_servidores_consecutivos(5, servidores_contabilizados)
    servidores_4_5_meses_detalhes = servidores_4_meses_detalhes + servidores_5_meses_detalhes

# Obter detalhes dos servidores para 3 meses
    servidores_3_meses_detalhes = obter_servidores_consecutivos(3, servidores_contabilizados)

# Criar DataFrames para cada grupo
    df_3_meses = pd.DataFrame(servidores_3_meses_detalhes)
    df_4_5_meses = pd.DataFrame(servidores_4_5_meses_detalhes)
    df_6_ou_mais_meses = pd.DataFrame(servidores_6_ou_mais_meses_detalhes)

# Formatar o valor total como moeda, se a coluna existir
    if not df_3_meses.empty:
        df_3_meses['Valor Total Pago'] = df_3_meses['Valor Total Pago'].apply(lambda x: locale.currency(x, grouping=True))
    else:
        df_3_meses = pd.DataFrame([{'Nome do Servidor': '-', 'Valor Total Pago': '-'}])  # Tabela vazia

    if not df_4_5_meses.empty:
        df_4_5_meses['Valor Total Pago'] = df_4_5_meses['Valor Total Pago'].apply(lambda x: locale.currency(x, grouping=True))
    else:
        df_4_5_meses = pd.DataFrame([{'Nome do Servidor': '-', 'Valor Total Pago': '-'}])  # Tabela vazia

    if not df_6_ou_mais_meses.empty:
        df_6_ou_mais_meses['Valor Total Pago'] = df_6_ou_mais_meses['Valor Total Pago'].apply(lambda x: locale.currency(x, grouping=True))
    else:
        df_6_ou_mais_meses = pd.DataFrame([{'Nome do Servidor': '-', 'Valor Total Pago': '-'}])  # Tabela vazia

# Exibir as tabelas
    st.markdown("### Tabelas dos Servidores com Diárias Consecutivas")
    col9, col10, col11 = st.columns(3)

    with col9:
        st.subheader('Servidores - 3 Meses')
        st.dataframe(df_3_meses)

    with col10:
        st.subheader('Servidores - 4-5 Meses')
        st.dataframe(df_4_5_meses)

    with col11:
        st.subheader('Servidores - 6 ou Mais Meses')
        st.dataframe(df_6_ou_mais_meses)

#======= Gráfico de servidores que também recebem diárias de outros órgãos além do filtrado
    st.subheader('Servidores Recebendo Diárias de Diferentes UGs')

# Array com as UGs de interesse
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

# Filtrar as diárias apenas das UGs de interesse
    df_ugs_interesse = df_diarias[df_diarias['UG'].isin(ugs_interesse_despesas)]

# Obter os servidores da UG filtrada pelo sidebar
    servidores_ug_filtrada = df_filtered['NOME_FAVORECIDO'].unique()

# Filtrar os servidores que receberam de outras UGs além da UG filtrada
    servidores_outras_ugs = df_ugs_interesse[df_ugs_interesse['NOME_FAVORECIDO'].isin(servidores_ug_filtrada)]
    servidores_outras_ugs = servidores_outras_ugs[~servidores_outras_ugs['UG'].isin(selected_ugs_despesas)]

# Agrupar por servidor e calcular o valor total recebido de outras UGs
    df_servidores_outras_ugs = servidores_outras_ugs.groupby('NOME_FAVORECIDO')['VALOR_PAGO'].sum().reset_index()
    df_servidores_outras_ugs = df_servidores_outras_ugs.rename(columns={'NOME_FAVORECIDO': 'Nome do Servidor', 'VALOR_PAGO': 'Valor de Outras UGs'})

# Verificar se há dados para exibir no gráfico
    if not df_servidores_outras_ugs.empty:
    # Criar o gráfico de barras horizontal
        fig_outras_ugs = px.bar(
            df_servidores_outras_ugs,
            x='Valor de Outras UGs',
            y='Nome do Servidor',
            orientation='h',
            title='Servidores Recebendo Diárias de Outras UGs',
            labels={'Valor de Outras UGs': 'Valor Pago', 'Nome do Servidor': 'Servidor'},
            text='Valor de Outras UGs'
        )

    # Formatar os valores no eixo x como moeda
        fig_outras_ugs.update_traces(texttemplate='R$ %{x:,.2f}', textposition='outside')
        fig_outras_ugs.update_layout(
            xaxis_tickformat='R$,.2f',
            yaxis_title='',
            xaxis_title='Valor Pago'
        )

        st.plotly_chart(fig_outras_ugs)
    else:
        st.write('Nenhum servidor recebeu diárias de outras UGs além da UG filtrada.')

if __name__ == "__main__":
    run_dashboard()
