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
            df = pd.read_excel(file_path, sheet_name=0)
            return df
        except FileNotFoundError:
            st.error(f"O arquivo {file_path} não foi encontrado.")
            return None
        except Exception as e:
            st.error(f"Ocorreu um erro ao carregar o arquivo: {e}")
            return None

    file_path = "./database/lista_contratos_siafe_gerado_em_03-06-2024.xlsx"
    df = load_data(file_path)

    if df is not None:
        # Carregar o sidebar específico para contratos
        selected_ugs, selected_data_inicio, selected_data_fim = load_sidebar(df, dashboard_name='Contratos')

        # Aplicar filtros ao dataframe
        df = df[df['UG'].isin(selected_ugs)]
        df = df[(df['DATA_INICIO_VIGENCIA'] >= pd.to_datetime(selected_data_inicio[0])) & (df['DATA_INICIO_VIGENCIA'] <= pd.to_datetime(selected_data_inicio[1]))]
        df = df[(df['DATA_FIM_VIGENCIA'] >= pd.to_datetime(selected_data_fim[0])) & (df['DATA_FIM_VIGENCIA'] <= pd.to_datetime(selected_data_fim[1]))]

        # Filtrar contratos ativos
        df = df[df['DSC_FLG_ATIVO'] == 'Ativo']

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

        # Obter a quantidade de contratos e valor total
        quantidade_contratos = len(df)
        valor_total_contratos = df['VALOR_TOTAL'].sum()

        # Formatar valor total para moeda
        valor_total_formatado = locale.currency(valor_total_contratos, grouping=True)

        # Adicionar métricas ao painel
        st.subheader('Métricas da UG Filtrada')
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

        fig.update_layout(barmode='stack', title='Distribuição de Contratos', xaxis_title='Categoria', yaxis_title='Contagem')
        st.plotly_chart(fig, use_container_width=True)

        # 2. Gráfico de Pizza
        # fig_pizza_situacao = px.pie(df_situacao, values='quantidade', names='DSC_SITUACAO', title='Proporção de Contratos por Situação')
        # st.plotly_chart(fig_pizza_situacao)

        # fig_pizza_licitacao = px.pie(df_licitacao, values='quantidade', names='NOM_TIPO_LICITACAO', title='Proporção de Contratos por Tipo de Licitação')
        # st.plotly_chart(fig_pizza_licitacao)

        # fig_pizza_natureza = px.pie(df_natureza, values='quantidade', names='NATUREZA_CONTRATO', title='Proporção de Contratos por Natureza')
        # st.plotly_chart(fig_pizza_natureza)

        # fig_pizza_contratante = px.pie(df_contratante, values='quantidade', names='NOME_CONTRATANTE', title='Proporção de Contratos por Contratante')
        # st.plotly_chart(fig_pizza_contratante)

        # 2. Gráfico de Rosca (Donut)
        fig_donut_situacao = px.pie(df_situacao, values='quantidade', names='DSC_SITUACAO', title='Proporção de Contratos por Situação', hole=0.4)
        st.plotly_chart(fig_donut_situacao)

        fig_donut_licitacao = px.pie(df_licitacao, values='quantidade', names='NOM_TIPO_LICITACAO', title='Proporção de Contratos por Tipo de Licitação', hole=0.4)
        st.plotly_chart(fig_donut_licitacao)

        fig_donut_natureza = px.pie(df_natureza, values='quantidade', names='NATUREZA_CONTRATO', title='Proporção de Contratos por Natureza', hole=0.4)
        st.plotly_chart(fig_donut_natureza)

        fig_donut_contratante = px.pie(df_contratante, values='quantidade', names='NOME_CONTRATANTE', title='Proporção de Contratos por Contratante', hole=0.4)
        st.plotly_chart(fig_donut_contratante)

        # 3. Gráfico de Linha
        df_tempo_inicio = df.groupby(df['DATA_INICIO_VIGENCIA'].dt.to_period('M')).size().reset_index(name='quantidade')
        df_tempo_fim = df.groupby(df['DATA_FIM_VIGENCIA'].dt.to_period('M')).size().reset_index(name='quantidade')
        df_publicacao = df.groupby(df['DATA_PUBLICACAO'].dt.to_period('M')).size().reset_index(name='quantidade')

        df_tempo_inicio['DATA_INICIO_VIGENCIA'] = df_tempo_inicio['DATA_INICIO_VIGENCIA'].astype(str)
        df_tempo_fim['DATA_FIM_VIGENCIA'] = df_tempo_fim['DATA_FIM_VIGENCIA'].astype(str)
        df_publicacao['DATA_PUBLICACAO'] = df_publicacao['DATA_PUBLICACAO'].astype(str)

        fig_linha = go.Figure()
        fig_linha.add_trace(go.Scatter(x=df_tempo_inicio['DATA_INICIO_VIGENCIA'], y=df_tempo_inicio['quantidade'], mode='lines', name='Início de Vigência'))
        fig_linha.add_trace(go.Scatter(x=df_tempo_fim['DATA_FIM_VIGENCIA'], y=df_tempo_fim['quantidade'], mode='lines', name='Fim de Vigência'))
        fig_linha.add_trace(go.Scatter(x=df_publicacao['DATA_PUBLICACAO'], y=df_publicacao['quantidade'], mode='lines', name='Publicação'))

        fig_linha.update_layout(title='Número de Contratos ao Longo do Tempo', xaxis_title='Data', yaxis_title='Contagem')
        st.plotly_chart(fig_linha)

        # 4. Gráfico de Barras Horizontais de Valores de Contratos por Categoria
        st.subheader('Valores de Contratos por Categoria')

        # Valores de contratos por contratante
        df_valores_contratante = df.groupby('NOME_CONTRATANTE')['VALOR_TOTAL'].sum().reset_index()

        df_valores_contratante['VALOR_FORMATADO'] = df_valores_contratante['VALOR_TOTAL'].apply(
            lambda x: 'R$ {:,.2f}'.format(x).replace(',', 'X').replace('.', ',').replace('X', '.'))

        fig_valores_contratante = go.Figure(go.Bar(
            x=df_valores_contratante['VALOR_TOTAL'],
            y=df_valores_contratante['NOME_CONTRATANTE'],
            text=df_valores_contratante['VALOR_FORMATADO'],
            textposition='auto',
            orientation='h'
        ))
        fig_valores_contratante.update_layout(
            title='Valores Totais de Contratos por Contratante',
            xaxis_title='Valor Total',
            yaxis_title='Contratante',
            height=600
        )
        st.plotly_chart(fig_valores_contratante, use_container_width=True)

        # Valores de contratos por tipo de licitação
        df_valores_licitacao = df.groupby('NOM_TIPO_LICITACAO')['VALOR_TOTAL'].sum().reset_index()

        df_valores_licitacao['VALOR_FORMATADO'] = df_valores_licitacao['VALOR_TOTAL'].apply(
            lambda x: 'R$ {:,.2f}'.format(x).replace(',', 'X').replace('.', ',').replace('X', '.'))

        fig_valores_licitacao = go.Figure(go.Bar(
            x=df_valores_licitacao['VALOR_TOTAL'],
            y=df_valores_licitacao['NOM_TIPO_LICITACAO'],
            text=df_valores_licitacao['VALOR_FORMATADO'],
            textposition='auto',
            orientation='h'
        ))
        fig_valores_licitacao.update_layout(
            title='Valores Totais de Contratos por Tipo de Licitação',
            xaxis_title='Valor Total',
            yaxis_title='Tipo de Licitação',
            height=600
        )
        st.plotly_chart(fig_valores_licitacao, use_container_width=True)

        # Valores de contratos por natureza
        df_valores_natureza = df.groupby('NATUREZA_CONTRATO')['VALOR_TOTAL'].sum().reset_index()

        df_valores_natureza['VALOR_FORMATADO'] = df_valores_natureza['VALOR_TOTAL'].apply(
            lambda x: 'R$ {:,.2f}'.format(x).replace(',', 'X').replace('.', ',').replace('X', '.'))

        fig_valores_natureza = go.Figure(go.Bar(
            x=df_valores_natureza['VALOR_TOTAL'],
            y=df_valores_natureza['NATUREZA_CONTRATO'],
            text=df_valores_natureza['VALOR_FORMATADO'],
            textposition='auto',
            orientation='h'
        ))
        fig_valores_natureza.update_layout(
            title='Valores Totais de Contratos por Natureza',
            xaxis_title='Valor Total',
            yaxis_title='Natureza',
            height=600
        )
        st.plotly_chart(fig_valores_natureza, use_container_width=True)

        # Formatação desejada
        df['CODIGO_CONTRATO'] = df['CODIGO_CONTRATO'].astype(int).astype(str)
        df['UG'] = df['UG'].astype(int).astype(str)
        df['DATA_INICIO_VIGENCIA'] = pd.to_datetime(df['DATA_INICIO_VIGENCIA']).dt.strftime('%d/%m/%Y')
        df['DATA_FIM_VIGENCIA'] = pd.to_datetime(df['DATA_FIM_VIGENCIA']).dt.strftime('%d/%m/%Y')
        df['VALOR_TOTAL'] = df['VALOR_TOTAL'].apply(lambda x: locale.currency(x, grouping=True))

        # Mostrar todos os contratos da coluna "CODIGO_CONTRATO" da UG filtrada
        st.subheader('Contratos da Unidade Gestora')
        st.write(df[['CODIGO_CONTRATO', 'UG', 'NOME_CONTRATANTE', 'NOME_CONTRATADA', 'NOME_CONTRATO', 'DATA_INICIO_VIGENCIA', 'DATA_FIM_VIGENCIA', 'VALOR_TOTAL', 'DSC_SITUACAO']])

        # Verificar se a planilha 'ADITIVOS_REAJUSTES' está presente no arquivo Excel
        if 'ADITIVOS_REAJUSTES' in pd.ExcelFile(file_path).sheet_names:
            df_aditivos_reajustes = pd.read_excel(file_path, sheet_name='ADITIVOS_REAJUSTES')

            # Formatar o COD_CONTRATO da aba ADITIVOS_REAJUSTES
            df_aditivos_reajustes['COD_CONTRATO'] = df_aditivos_reajustes['COD_CONTRATO'].astype(int).astype(str)
            df_aditivos_reajustes['DATA_VIGENCIA_INICIAL'] = pd.to_datetime(df_aditivos_reajustes['DATA_VIGENCIA_INICIAL']).dt.strftime('%d/%m/%Y')
            df_aditivos_reajustes['DATA_VIGENCIA_FINAL'] = pd.to_datetime(df_aditivos_reajustes['DATA_VIGENCIA_FINAL']).dt.strftime('%d/%m/%Y')
            df_aditivos_reajustes['DATA_CELEBRACAO'] = pd.to_datetime(df_aditivos_reajustes['DATA_CELEBRACAO']).dt.strftime('%d/%m/%Y')
            df_aditivos_reajustes['DATA_PUBLICACAO'] = pd.to_datetime(df_aditivos_reajustes['DATA_PUBLICACAO']).dt.strftime('%d/%m/%Y')
            df_aditivos_reajustes['DSC_OBJETO'] = df_aditivos_reajustes['DSC_OBJETO'].str.upper()
            df_aditivos_reajustes['VALOR'] = df_aditivos_reajustes['VALOR'].apply(lambda x: locale.currency(x, grouping=True))

            # Filtrar ADITIVOS_REAJUSTES pelos CODIGO_CONTRATO da UG filtrada
            df_aditivos_reajustes_ug = df_aditivos_reajustes[df_aditivos_reajustes['COD_CONTRATO'].isin(df['CODIGO_CONTRATO'])]

            st.subheader('Informações de Aditivos/Reajustes')

            # Exibir tabela com informações de ADITIVOS_REAJUSTES
            st.write(df_aditivos_reajustes_ug)

            # Adicionar filtro para digitar o COD_CONTRATO
            selected_cod_contrato = st.text_input('Digite o código do contrato e veja todos aditivos:')

            # Verificar se o contrato digitado é válido
            if selected_cod_contrato.strip() != '':
                # Filtrar os dados dos aditivos/reajustes com base no COD_CONTRATO selecionado
                df_aditivos_contrato = df_aditivos_reajustes_ug[df_aditivos_reajustes_ug['COD_CONTRATO'] == selected_cod_contrato]

                # Mostrar as informações dos aditivos/reajustes do contrato selecionado
                st.write(f'Informações do contrato {selected_cod_contrato}:')
                st.write(df_aditivos_contrato)
            else:
                st.warning('Por favor, digite o código do contrato.')
        else:
            st.error('A aba ADITIVOS_REAJUSTES não está presente no arquivo Excel.')

if __name__ == "__main__":
    run_dashboard()



