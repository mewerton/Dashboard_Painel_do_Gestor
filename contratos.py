import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import locale
from sidebar import load_sidebar
from data_loader import load_contracts_data
#from chatbot import render_chatbot  # Importar a função do chatbot

# Tente definir o locale para pt_BR. Se falhar, use o locale padrão do sistema
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_ALL, '')  # Fallback para o locale padrão do sistema

# Dicionário para renomear as colunas para exibição
colunas_exibicao = {
    'CODIGO_CONTRATO': 'Código do Contrato',
    'UG': 'Unidade Gestora',
    'NOME_CONTRATANTE': 'Contratante',
    'NOME_CONTRATADA': 'Contratada',
    'VALOR_TOTAL': 'Valor Total (R$)',
    'NOME_CONTRATO': 'Nome do Contrato',
    'DATA_INICIO_VIGENCIA': 'Início da Vigência',
    'DATA_FIM_VIGENCIA': 'Fim da Vigência',
    'DSC_SITUACAO': 'Situação'
}

# Funções para formatação
def formatar_valor(valor):
    """Formatar o valor como moeda no padrão brasileiro."""
    if pd.notnull(valor):
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return 'R$ 0,00'

def formatar_numero(numero):
    """Formatar números inteiros com zeros à esquerda."""
    return str(int(numero)).zfill(8)

def formatar_data(data):
    """Formatar data no formato DD/MM/AAAA."""
    return pd.to_datetime(data).dt.strftime('%d/%m/%Y')

def run_dashboard():
    # Carregar os datasets de contratos e aditivos usando o data_loader
    df_aditivos, df_contratos = load_contracts_data()

    if df_contratos.empty or df_aditivos.empty:
        st.error("Nenhum dado de contratos ou aditivos foi carregado.")
        return

    # Carregar o sidebar específico para contratos
    selected_ugs, selected_ug_sigla_contratos, selected_data_inicio, selected_data_fim, selected_situacoes = load_sidebar(df_contratos, dashboard_name='Contratos')
    
    # Chame o chatbot para renderizar no sidebar
    #render_chatbot()

    # Aplicar filtros ao dataframe de contratos
    df_contratos = df_contratos[df_contratos['UG'].isin(selected_ugs)]

    # Corrigir a comparação com as datas selecionadas no slider
    df_contratos = df_contratos[(df_contratos['DATA_INICIO_VIGENCIA'] >= pd.to_datetime(selected_data_inicio[0])) &
                                (df_contratos['DATA_INICIO_VIGENCIA'] <= pd.to_datetime(selected_data_inicio[1]))]
    df_contratos = df_contratos[(df_contratos['DATA_FIM_VIGENCIA'] >= pd.to_datetime(selected_data_fim[0])) &
                                (df_contratos['DATA_FIM_VIGENCIA'] <= pd.to_datetime(selected_data_fim[1]))]
    
    # Aplicar filtro de situação do contrato
    df_contratos = df_contratos[df_contratos['DSC_SITUACAO'].isin(selected_situacoes)]

    # Eliminar a coluna DIAS_VENCIDOS e linhas em branco na coluna DSC_SITUACAO
    df_contratos = df_contratos.drop(columns=['DIAS_VENCIDOS'])
    df_contratos = df_contratos[df_contratos['DSC_SITUACAO'].notna()]

    # Aplicar máscara de CPF/CNPJ na coluna CODIGO_CONTRATADA
    df_contratos['CODIGO_CONTRATADA'] = df_contratos['CODIGO_CONTRATADA'].apply(lambda x: '{}.{}.{}-{}'.format(x[:3], x[3:6], x[6:9], x[9:]))


    # Converter a coluna NOME_CONTRATO para maiúsculas
    df_contratos['NOME_CONTRATO'] = df_contratos['NOME_CONTRATO'].str.upper()

    # Tratamento de dados
    df_contratos['DATA_PUBLICACAO'] = pd.to_datetime(df_contratos['DATA_PUBLICACAO'], format='%d/%m/%Y', errors='coerce')

    numeric_cols = ['UG', 'CODIGO_CONTRATANTE', 'CODIGO_CONTRATADA', 'CODIGO_CONTRATO', 'COD_TIPO_LICITACAO', 'COD_SITUACAO']
    for col in numeric_cols:
        df_contratos[col] = pd.to_numeric(df_contratos[col], errors='coerce')
        
    financial_cols = ['VALOR_CONCESSAO', 'VALOR_TOTAL', 'VALOR_MULTA', 'VALOR_GARANTIA', 'VALOR_ADITIVO']
    for col in financial_cols:
        df_contratos[col] = df_contratos[col].apply(pd.to_numeric, errors='coerce')

    if df_contratos['VALOR_PERCENTUAL_TERCEIR'].dtype == 'object':
        df_contratos['VALOR_PERCENTUAL_TERCEIR'] = df_contratos['VALOR_PERCENTUAL_TERCEIR'].str.replace('%', '').astype(float) / 100


    # Adicionar métricas ao painel
    if "TODAS" in selected_ug_sigla_contratos:
        selected_ug_description = "TODOS ÓRGÃOS"
    else:
        selected_ug_description = "Descrição não encontrada"
        if selected_ugs:
            ug_descriptions = df_contratos[df_contratos['UG'].isin(selected_ugs)]['DESCRICAO_UG'].unique()
            if len(ug_descriptions) > 0:
                selected_ug_description = ug_descriptions[0]  # Pegue a primeira descrição encontrada

    # Exibir o subtítulo com a descrição da UG selecionada ou "TODOS ÓRGÃOS"
    st.markdown(f'<h3 style="font-size:20px;"> {selected_ug_description}</h3>', unsafe_allow_html=True)

     
    # Dividindo em abas
    tab1, tab2, tab3 = st.tabs(["Métricas dos Contratos", "Distribuição por Licitação", "Detalhes e Aditivos"])
    

    with tab1:
        # Obter a quantidade de contratos e valor total
        quantidade_contratos = len(df_contratos)
        valor_total_contratos = df_contratos['VALOR_TOTAL'].sum()

        # Formatar valor total para moeda
        #valor_total_formatado = locale.currency(valor_total_contratos, grouping=True)
        valor_total_formatado = f"R$ {valor_total_contratos:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        # Adicionar métricas ao painel
        st.subheader('Métricas da Contratos')
        col1, col2 = st.columns(2)

        col1.metric("Quantidade de Contratos", quantidade_contratos)
        col2.metric("Valor Total", valor_total_formatado)

        # Gráficos

        # 1. Gráfico de Barras Empilhadas
        fig = go.Figure()

        # Proporção de contratos por situação
        df_situacao = df_contratos.groupby('DSC_SITUACAO').size().reset_index(name='quantidade')
        fig.add_trace(go.Bar(x=df_situacao['DSC_SITUACAO'], y=df_situacao['quantidade'], name='Situação'))

        # Proporção de contratos por tipo de licitação
        df_licitacao = df_contratos.groupby('NOM_TIPO_LICITACAO').size().reset_index(name='quantidade')
        fig.add_trace(go.Bar(x=df_licitacao['NOM_TIPO_LICITACAO'], y=df_licitacao['quantidade'], name='Tipo de Licitação'))

        # Proporção de contratos por natureza
        df_natureza = df_contratos.groupby('NATUREZA_CONTRATO').size().reset_index(name='quantidade')
        fig.add_trace(go.Bar(x=df_natureza['NATUREZA_CONTRATO'], y=df_natureza['quantidade'], name='Natureza'))

        # Proporção de contratos por contratante
        df_contratante = df_contratos.groupby('NOME_CONTRATANTE').size().reset_index(name='quantidade')
        fig.add_trace(go.Bar(x=df_contratante['NOME_CONTRATANTE'], y=df_contratante['quantidade'], name='Contratante'))

        # 2. Gráfico de Rosca (Donut)

        col3, col4 = st.columns(2)

        with col3:

            fig_donut_situacao = px.pie(df_situacao, values='quantidade', names='DSC_SITUACAO', title='Proporção de Contratos por Situação', hole=0.4)
            st.plotly_chart(fig_donut_situacao)
            
        with col4:
            fig_donut_licitacao = px.pie(df_licitacao, values='quantidade', names='NOM_TIPO_LICITACAO', title='Proporção de Contratos por Tipo de Licitação', hole=0.4)
            st.plotly_chart(fig_donut_licitacao)
        
        # Distribuição de contratos
        fig = go.Figure()

        # Lista de categorias que queremos exibir (removendo "Contratante")
        categorias_permitidas = ['DSC_SITUACAO', 'NOM_TIPO_LICITACAO', 'NATUREZA_CONTRATO']

        # Criar os gráficos apenas para as categorias permitidas
        if 'DSC_SITUACAO' in df_contratos.columns:
            df_situacao = df_contratos.groupby('DSC_SITUACAO').agg(
                quantidade=('CODIGO_CONTRATO', 'count'),
                valor_total=('VALOR_TOTAL', 'sum')
            ).reset_index()

            # Formatar os valores para exibição no hover
            df_situacao['valor_formatado'] = df_situacao['valor_total'].apply(formatar_valor)

            fig.add_trace(go.Bar(
                x=df_situacao['DSC_SITUACAO'],
                y=df_situacao['quantidade'],
                name='Situação',
                text=df_situacao['quantidade'],  # Mantém o número de contratos visível
                textposition="outside",  # Garante que os números apareçam fora da barra
                hovertext=df_situacao.apply(lambda row: f"Quantidade: {row['quantidade']}<br>Valor Total: {row['valor_formatado']}", axis=1),
                hoverinfo="text"
            ))

        if 'NOM_TIPO_LICITACAO' in df_contratos.columns:
            df_licitacao = df_contratos.groupby('NOM_TIPO_LICITACAO').agg(
                quantidade=('CODIGO_CONTRATO', 'count'),
                valor_total=('VALOR_TOTAL', 'sum')
            ).reset_index()

            df_licitacao['valor_formatado'] = df_licitacao['valor_total'].apply(formatar_valor)

            fig.add_trace(go.Bar(
                x=df_licitacao['NOM_TIPO_LICITACAO'],
                y=df_licitacao['quantidade'],
                name='Tipo de Licitação',
                text=df_licitacao['quantidade'],
                textposition="outside",
                hovertext=df_licitacao.apply(lambda row: f"Quantidade: {row['quantidade']}<br>Valor Total: {row['valor_formatado']}", axis=1),
                hoverinfo="text"
            ))

        if 'NATUREZA_CONTRATO' in df_contratos.columns:
            df_natureza = df_contratos.groupby('NATUREZA_CONTRATO').agg(
                quantidade=('CODIGO_CONTRATO', 'count'),
                valor_total=('VALOR_TOTAL', 'sum')
            ).reset_index()

            df_natureza['valor_formatado'] = df_natureza['valor_total'].apply(formatar_valor)

            fig.add_trace(go.Bar(
                x=df_natureza['NATUREZA_CONTRATO'],
                y=df_natureza['quantidade'],
                name='Natureza',
                text=df_natureza['quantidade'],
                textposition="outside",
                hovertext=df_natureza.apply(lambda row: f"Quantidade: {row['quantidade']}<br>Valor Total: {row['valor_formatado']}", axis=1),
                hoverinfo="text"
            ))

        # Atualizar layout
        fig.update_layout(
            barmode='stack',
            title='Distribuição de Contratos',
            xaxis_title='Categoria',
            yaxis_title='Contagem'
        )

        # Exibir o gráfico no Streamlit
        st.plotly_chart(fig, use_container_width=True)

        # Calcular a quantidade de contratos e valor total por UG
        df_ug_contratos = df_contratos.groupby('UG').agg(
            quantidade=('CODIGO_CONTRATO', 'count'),
            valor_total=('VALOR_TOTAL', 'sum')
        ).reset_index()

        # Filtrar apenas UGs com pelo menos 1 contrato
        df_ug_contratos = df_ug_contratos[df_ug_contratos['quantidade'] > 0]

        # Mapear a sigla da UG usando o dataset original
        df_ug_info = pd.read_csv("./database/UGS-COD-NOME-SIGLA.csv")
        df_ug_contratos = df_ug_contratos.merge(df_ug_info[['UG', 'SIGLA_UG']], on='UG', how='left')

        # Ordenar os valores por quantidade de contratos
        df_ug_contratos = df_ug_contratos.sort_values(by='quantidade', ascending=True)

        # Formatar valores para exibição
        df_ug_contratos['valor_formatado'] = df_ug_contratos['valor_total'].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        df_ug_contratos['label'] = df_ug_contratos.apply(lambda row: f"Quantidade: {row['quantidade']} | Valor: {row['valor_formatado']}", axis=1)

        # Definir altura dinâmica do gráfico (mínimo de 400, máximo de 1200)
        altura_minima_por_barra = 30  # Mantém um tamanho mínimo adequado para cada barra
        altura_base = 400  # Altura mínima do gráfico
        altura_maxima = 2400  # Altura máxima do gráfico

        altura_grafico = max(altura_base, min(altura_maxima, len(df_ug_contratos) * altura_minima_por_barra))

        # Criar gráfico de barras horizontais garantindo que os rótulos fiquem visíveis corretamente
        fig_ug_contratos = go.Figure(go.Bar(
            y=df_ug_contratos['SIGLA_UG'],  # Sigla da UG no eixo Y
            x=df_ug_contratos['quantidade'],  # Quantidade de contratos no eixo X
            orientation='h',  # Barras horizontais
            marker=dict(color='#095aa2'),  # Cor das barras
            text=df_ug_contratos['label'],  # Texto dentro das barras
            textposition='auto',  # Deixa o Plotly decidir se coloca dentro ou fora conforme o espaço
            insidetextfont=dict(size=12),  # Define o tamanho mínimo da fonte dentro da barra
            outsidetextfont=dict(size=12)  # Mantém o tamanho da fonte fora da barra se necessário
        ))

        fig_ug_contratos.update_layout(
            title="Quantidade de Contratos por UG",
            xaxis_title="Quantidade de Contratos",
            yaxis_title="UG (Sigla)",
            height=altura_grafico,  # Define altura dinâmica
            yaxis=dict(
                tickfont=dict(size=12),  # Mantém a fonte das siglas no eixo Y legível
            )
        )

        # Exibir o gráfico no Streamlit
        st.plotly_chart(fig_ug_contratos, use_container_width=True)


    # Aplicar as funções nas abas
    with tab2:
        # Agrupamento e formatação para o gráfico
        df_valores_licitacao = df_contratos.groupby('NOM_TIPO_LICITACAO')['VALOR_TOTAL'].sum().reset_index()
        df_valores_licitacao['VALOR_FORMATADO'] = df_valores_licitacao['VALOR_TOTAL'].apply(formatar_valor)

        fig_valores_licitacao = go.Figure(go.Bar(
            x=df_valores_licitacao['VALOR_TOTAL'],
            y=df_valores_licitacao['NOM_TIPO_LICITACAO'],
            text=df_valores_licitacao['VALOR_FORMATADO'],
            textposition='auto',
            orientation='h',
            marker=dict(color='#095aa2')
        ))
        fig_valores_licitacao.update_layout(
            title='Valores Totais de Contratos por Tipo de Licitação',
            xaxis_title='Valor Total',
            yaxis_title='Tipo de Licitação',
            height=600
        )
        st.plotly_chart(fig_valores_licitacao, use_container_width=True)

        # Multiselect para tipos de licitação
        selected_licitacoes = st.multiselect(
            'Selecione o(s) Tipo(s) de Licitação para visualizar os contratos:',
            options=df_valores_licitacao['NOM_TIPO_LICITACAO'].unique(),
            help="Escolha um ou mais tipos de licitação para exibir a tabela de contratos.",
            placeholder="Escolha uma opção"
        )

        # Exibir tabela se pelo menos um tipo de licitação for selecionado
        if selected_licitacoes:
            # Filtrar o DataFrame para os tipos de licitação selecionados
            filtered_table = df_contratos[df_contratos['NOM_TIPO_LICITACAO'].isin(selected_licitacoes)].copy()

            # Aplicar formatações
            filtered_table['VALOR_TOTAL'] = filtered_table['VALOR_TOTAL'].apply(formatar_valor)
            filtered_table['CODIGO_CONTRATO'] = filtered_table['CODIGO_CONTRATO'].apply(formatar_numero)
            filtered_table['UG'] = filtered_table['UG'].apply(formatar_numero)
            filtered_table['DATA_INICIO_VIGENCIA'] = formatar_data(filtered_table['DATA_INICIO_VIGENCIA'])
            filtered_table['DATA_FIM_VIGENCIA'] = formatar_data(filtered_table['DATA_FIM_VIGENCIA'])

            # Exibir tabela de contratos filtrados com títulos renomeados
            st.header('Contratos por Tipo de Licitação Selecionado')
            st.write(
                filtered_table[['CODIGO_CONTRATO', 'UG', 'NOME_CONTRATANTE', 'NOME_CONTRATADA', 'VALOR_TOTAL', 
                                'NOME_CONTRATO', 'DATA_INICIO_VIGENCIA', 'DATA_FIM_VIGENCIA', 'DSC_SITUACAO']]
                .rename(columns=colunas_exibicao).reset_index(drop=True)
            )

            st.write(f"Total de contratos exibidos: {len(filtered_table)}")

            # Calcular e exibir o valor total dos contratos filtrados
            total_valor_contratos = filtered_table['VALOR_TOTAL'].str.replace('R$ ', '').str.replace('.', '').str.replace(',', '.').astype(float).sum()
            st.write(f"Valor total dos contratos exibidos: {formatar_valor(total_valor_contratos)}")


    with tab3:
        # Aplicar formatações de valores, números e datas na aba de visualização completa de contratos
        df_contratos['VALOR_TOTAL'] = df_contratos['VALOR_TOTAL'].apply(formatar_valor)
        df_contratos['CODIGO_CONTRATO'] = df_contratos['CODIGO_CONTRATO'].apply(formatar_numero)
        df_contratos['UG'] = df_contratos['UG'].apply(formatar_numero)
        df_contratos['DATA_INICIO_VIGENCIA'] = formatar_data(df_contratos['DATA_INICIO_VIGENCIA'])
        df_contratos['DATA_FIM_VIGENCIA'] = formatar_data(df_contratos['DATA_FIM_VIGENCIA'])

        st.subheader('Contratos da Unidade Gestora')
        keyword = st.text_input('Digite uma palavra-chave para filtrar os contratos:')

        if keyword:
            df_contratos = df_contratos[df_contratos.apply(lambda row: row.astype(str).str.contains(keyword, case=False).any(), axis=1)]

        # Exibir DataFrame com títulos renomeados
        st.write(df_contratos[['CODIGO_CONTRATO', 'UG', 'NOME_CONTRATANTE', 'NOME_CONTRATADA', 'VALOR_TOTAL', 'NOME_CONTRATO', 'DATA_INICIO_VIGENCIA', 'DATA_FIM_VIGENCIA', 'DSC_SITUACAO']].rename(columns=colunas_exibicao))

        if df_aditivos is not None:
            df_aditivos_filtrados = df_aditivos[df_aditivos['COD_CONTRATO'].isin(df_contratos['CODIGO_CONTRATO'].astype(int))].copy()
            df_aditivos_filtrados['VALOR_FORMATADO'] = df_aditivos_filtrados['VALOR'].apply(formatar_valor)
            df_aditivos_filtrados['COD_CONTRATO'] = df_aditivos_filtrados['COD_CONTRATO'].apply(formatar_numero)
            df_aditivos_filtrados['DATA_VIGENCIA_INICIAL'] = formatar_data(df_aditivos_filtrados['DATA_VIGENCIA_INICIAL'])
            df_aditivos_filtrados['DATA_VIGENCIA_FINAL'] = formatar_data(df_aditivos_filtrados['DATA_VIGENCIA_FINAL'])
            df_aditivos_filtrados['DATA_PUBLICACAO'] = formatar_data(df_aditivos_filtrados['DATA_PUBLICACAO'])

            st.subheader('Aditivos e Reajustes dos Contratos Exibidos')
            st.write(df_aditivos_filtrados[['COD_CONTRATO', 'TIPO', 'NUM_ORIGINAL', 'NUM_PROCESSO', 'DATA_VIGENCIA_INICIAL', 'DATA_VIGENCIA_FINAL', 'DATA_PUBLICACAO', 'VALOR_FORMATADO', 'DSC_OBJETO']].rename(columns=colunas_exibicao))

            valor_total_aditivos = df_aditivos_filtrados['VALOR'].sum()
            st.markdown(f"**Valor total dos Aditivos/Reajustes filtrados: {formatar_valor(valor_total_aditivos)}**")


if __name__ == "__main__":
    run_dashboard()