import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import locale
from sidebar import load_sidebar

# Configurar o locale para português do Brasil
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

def run_dashboard():
    @st.cache_data
    def load_data(file_path):
        try:
            # Carregar o arquivo Parquet
            df = pd.read_parquet(file_path)
            
            # Conversão das colunas de timestamp para datetime
            df['DATA_INICIO_VIGENCIA'] = pd.to_datetime(df['DATA_INICIO_VIGENCIA'], unit='ms')
            df['DATA_FIM_VIGENCIA'] = pd.to_datetime(df['DATA_FIM_VIGENCIA'], unit='ms')
            df['DATA_PUBLICACAO'] = pd.to_datetime(df['DATA_PUBLICACAO'], unit='ms')

            return df
        except FileNotFoundError:
            st.error(f"O arquivo {file_path} não foi encontrado.")
            return None
        except Exception as e:
            st.error(f"Ocorreu um erro ao carregar o arquivo: {e}")
            return None

    file_path = "./database/lista_contratos_siafe.parquet"
    df = load_data(file_path)

    if df is not None:
        # Carregar o sidebar específico para contratos
        selected_ugs, selected_data_inicio, selected_data_fim = load_sidebar(df, dashboard_name='Contratos')

        # Aplicar filtros ao dataframe
        df = df[df['UG'].isin(selected_ugs)]

        # Corrigir a comparação com as datas selecionadas no slider
        df = df[(df['DATA_INICIO_VIGENCIA'] >= pd.to_datetime(selected_data_inicio[0])) & (df['DATA_INICIO_VIGENCIA'] <= pd.to_datetime(selected_data_inicio[1]))]
        df = df[(df['DATA_FIM_VIGENCIA'] >= pd.to_datetime(selected_data_fim[0])) & (df['DATA_FIM_VIGENCIA'] <= pd.to_datetime(selected_data_fim[1]))]

        # Eliminar a coluna DIAS_VENCIDOS
        df = df.drop(columns=['DIAS_VENCIDOS'])

        # Eliminar linhas com valores em branco na coluna DSC_SITUACAO
        df = df[df['DSC_SITUACAO'].notna()]

        # Aplicar máscara de CPF/CNPJ na coluna CODIGO_CONTRATADA
        df['CODIGO_CONTRATADA'] = df['CODIGO_CONTRATADA'].apply(lambda x: '{}.{}.{}-{}'.format(x[:3], x[3:6], x[6:9], x[9:]))

        # Converter a coluna NOME_CONTRATO para maiúsculas
        df['NOME_CONTRATO'] = df['NOME_CONTRATO'].str.upper()

        # Tratamento de dados
        df['DATA_PUBLICACAO'] = pd.to_datetime(df['DATA_PUBLICACAO'], format='%d/%m/%Y', errors='coerce')

        numeric_cols = ['UG', 'CODIGO_CONTRATANTE', 'CODIGO_CONTRATADA', 'CODIGO_CONTRATO', 'COD_TIPO_LICITACAO', 'COD_SITUACAO']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        financial_cols = ['VALOR_CONCESSAO', 'VALOR_TOTAL', 'VALOR_MULTA', 'VALOR_GARANTIA', 'VALOR_ADITIVO']
        for col in financial_cols:
            df[col] = df[col].apply(pd.to_numeric, errors='coerce')

        if df['VALOR_PERCENTUAL_TERCEIR'].dtype == 'object':
            df['VALOR_PERCENTUAL_TERCEIR'] = df['VALOR_PERCENTUAL_TERCEIR'].str.replace('%', '').astype(float) / 100

        # Adicionar métricas ao painel
        selected_ug_description = "Descrição não encontrada"
    
        if selected_ugs:
            # Obter a descrição da UG selecionada
            ug_descriptions = df[df['UG'].isin(selected_ugs)]['DESCRICAO_UG'].unique()
            if len(ug_descriptions) > 0:
                selected_ug_description = ug_descriptions[0]  # Pegue a primeira descrição encontrada

        # Exibir o subtítulo com a descrição da UG selecionada
        st.markdown(f'<h3 style="font-size:20px;"> {selected_ug_description}</h3>', unsafe_allow_html=True)

        # Obter a quantidade de contratos e valor total
        quantidade_contratos = len(df)
        valor_total_contratos = df['VALOR_TOTAL'].sum()

        # Formatar valor total para moeda
        valor_total_formatado = locale.currency(valor_total_contratos, grouping=True)

        # Adicionar métricas ao painel
        st.subheader('Métricas da Contratos')
        col1, col2 = st.columns(2)

        col1.metric("Quantidade de Contratos", quantidade_contratos)
        col2.metric("Valor Total", valor_total_formatado)

        # Gráficos

        # 1. Gráfico de Barras Empilhadas
        fig = go.Figure()

        # Proporção de contratos por situação
        df_situacao = df.groupby('DSC_SITUACAO').size().reset_index(name='quantidade')
        fig.add_trace(go.Bar(x=df_situacao['DSC_SITUACAO'], y=df_situacao['quantidade'], name='Situação'))

        # Proporção de contratos por tipo de licitação
        df_licitacao = df.groupby('NOM_TIPO_LICITACAO').size().reset_index(name='quantidade')
        fig.add_trace(go.Bar(x=df_licitacao['NOM_TIPO_LICITACAO'], y=df_licitacao['quantidade'], name='Tipo de Licitação'))

        # Proporção de contratos por natureza
        df_natureza = df.groupby('NATUREZA_CONTRATO').size().reset_index(name='quantidade')
        fig.add_trace(go.Bar(x=df_natureza['NATUREZA_CONTRATO'], y=df_natureza['quantidade'], name='Natureza'))

        # Proporção de contratos por contratante
        df_contratante = df.groupby('NOME_CONTRATANTE').size().reset_index(name='quantidade')
        fig.add_trace(go.Bar(x=df_contratante['NOME_CONTRATANTE'], y=df_contratante['quantidade'], name='Contratante'))

        # 2. Gráfico de Rosca (Donut)

        col3, col4 = st.columns(2)

        with col3:

            fig_donut_situacao = px.pie(df_situacao, values='quantidade', names='DSC_SITUACAO', title='Proporção de Contratos por Situação', hole=0.4)
            st.plotly_chart(fig_donut_situacao)
        
        with col4:
            fig_donut_licitacao = px.pie(df_licitacao, values='quantidade', names='NOM_TIPO_LICITACAO', title='Proporção de Contratos por Tipo de Licitação', hole=0.4)
            st.plotly_chart(fig_donut_licitacao)

        # Valores de contratos por tipo de licitação
        df_valores_licitacao = df.groupby('NOM_TIPO_LICITACAO')['VALOR_TOTAL'].sum().reset_index()

        df_valores_licitacao['VALOR_FORMATADO'] = df_valores_licitacao['VALOR_TOTAL'].apply(
            lambda x: 'R$ {:,.2f}'.format(x).replace(',', 'X').replace('.', ',').replace('X', '.'))

        fig_valores_licitacao = go.Figure(go.Bar(
            x=df_valores_licitacao['VALOR_TOTAL'],
            y=df_valores_licitacao['NOM_TIPO_LICITACAO'],
            text=df_valores_licitacao['VALOR_FORMATADO'],
            textposition='auto',
            orientation='h',
            marker=dict(color='#095aa2')  # Define a cor das barras
        ))
        fig_valores_licitacao.update_layout(
            title='Valores Totais de Contratos por Tipo de Licitação',
            xaxis_title='Valor Total',
            yaxis_title='Tipo de Licitação',
            height=600
        )
        st.plotly_chart(fig_valores_licitacao, use_container_width=True)

        # Distribuição de contratos
        fig.update_traces(texttemplate='%{y}', textposition='auto')
        fig.update_layout(barmode='stack', title='Distribuição de Contratos', xaxis_title='Categoria', yaxis_title='Contagem')
        st.plotly_chart(fig, use_container_width=True)

        # Formatação desejada
        df['CODIGO_CONTRATO'] = df['CODIGO_CONTRATO'].astype(int).astype(str)
        df['UG'] = df['UG'].astype(int).astype(str)
        df['DATA_INICIO_VIGENCIA'] = pd.to_datetime(df['DATA_INICIO_VIGENCIA']).dt.strftime('%d/%m/%Y')
        df['DATA_FIM_VIGENCIA'] = pd.to_datetime(df['DATA_FIM_VIGENCIA']).dt.strftime('%d/%m/%Y')
        df['VALOR_TOTAL'] = df['VALOR_TOTAL'].apply(lambda x: locale.currency(x, grouping=True))

# Adicionar o título
        st.subheader('Contratos da Unidade Gestora')

# Campo de entrada para a palavra-chave de pesquisa
        keyword = st.text_input('Digite uma palavra-chave para filtrar os contratos:')

# Aplicar o filtro se uma palavra-chave for inserida
        if keyword:
            df = df[df.apply(lambda row: row.astype(str).str.contains(keyword, case=False).any(), axis=1)]

# Mostrar todos os contratos da coluna "CODIGO_CONTRATO" da UG filtrada
        st.write(df[['CODIGO_CONTRATO', 'UG', 'NOME_CONTRATANTE', 'NOME_CONTRATADA', 'NOME_CONTRATO', 'DATA_INICIO_VIGENCIA', 'DATA_FIM_VIGENCIA', 'VALOR_TOTAL', 'DSC_SITUACAO']])


if __name__ == "__main__":
    run_dashboard()



