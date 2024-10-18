import streamlit as st
import pandas as pd
import plotly.express as px
import locale
from sidebar import load_sidebar  # Agora você usa a função centralizada do sidebar
from data_loader import load_servidores_data
from chatbot import render_chatbot  # Importar a função do chatbot

# Configurar o locale para português do Brasil
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

def run_dashboard():
    # Carregar dados usando o módulo centralizado
    df = load_servidores_data()

    if df is None:
        st.error("Nenhum dado foi carregado. Por favor, verifique os arquivos de entrada.")
        return

    # Ajustar a coluna 'Unidade' para ter zeros à esquerda usando .loc para evitar SettingWithCopyWarning
    df['Unidade'] = df['Unidade'].astype(str).str.zfill(8)

    # Remover aspas dos CPFs e ajustar a coluna para string
    df['CPF'] = df['CPF'].astype(str).str.replace('"', '').str.zfill(11)

    # Tratamento de dados para selecionar o menor código de vínculo (Vinculo) para cada CPF
    #df_sorted = df.sort_values(by=['CPF', 'Vinculo'])  # Ordena primeiro pelo CPF e depois pelo código de vínculo
    #df = df_sorted.drop_duplicates(subset=['CPF'], keep='first').copy()  # Adiciona .copy() após a remoção de duplicatas

    # Ordena o DataFrame para garantir que "TOTAL VANTAGENS" seja priorizado
    df_sorted = df.sort_values(by=['CPF', 'Financ_Verba_Desc'], ascending=[True, False])

    # Filtrar as linhas onde 'Financ_Verba_Desc' é 'TOTAL VANTAGENS'
    df_total_vantagens = df_sorted[df_sorted['Financ_Verba_Desc'] == 'TOTAL VANTAGENS'].copy()

    # Agora selecionamos o menor código de vínculo (Vinculo) para cada CPF, garantindo que as linhas de "TOTAL VANTAGENS" sejam mantidas
    df = df_sorted.drop_duplicates(subset=['CPF'], keep='first').copy()

    # Unimos o DataFrame original com as informações de "TOTAL VANTAGENS" para garantir que essa informação seja preservada
    df = pd.merge(df, df_total_vantagens[['CPF', 'Financ_Valor_Calculado']], on='CPF', suffixes=('', '_salario_bruto'), how='left')


    # Carregar o sidebar para "Servidores" e obter a Unidade
    selected_unidade = load_sidebar(df, "Servidores")

     # Chame o chatbot para renderizar no sidebar
    render_chatbot()

    if selected_unidade is None:
        st.warning("Nenhuma Unidade selecionada. Exibindo todos os dados disponíveis.")
        filtered_df = df.copy()  # Certifica-se de que é uma cópia
    else:
        # Converter selected_unidade para o formato com zeros à esquerda
        selected_unidade = str(selected_unidade).zfill(8)

        # Filtrar o DataFrame com base na Unidade selecionada
        filtered_df = df[df['Unidade'] == selected_unidade].copy()  # Adiciona .copy() após o filtro

        if filtered_df.empty:
            st.warning(f"Nenhum dado encontrado para a Unidade {selected_unidade}.")
            return


    # Exibir as métricas
    st.title('Dashboard de Servidores')

     # Gráficos 1 e 2 em uma linha
    col1, col2 = st.columns(2)

    with col1:
        st.header('Distribuição por Grau de Instrução')
        grau_instrucao_counts = filtered_df['Grau_Instrucao_Desc'].value_counts()
        fig1 = px.bar(grau_instrucao_counts, 
                      x=grau_instrucao_counts.index, 
                      y=grau_instrucao_counts.values, 
                      labels={'x': 'Grau de Instrução', 'y': 'Contagem'})
        st.plotly_chart(fig1)

    with col2:
        st.header('Distribuição de Sexo dos Funcionários')
        sexo_counts = filtered_df['Sexo_Desc'].value_counts()
        fig2 = px.pie(values=sexo_counts.values, 
                      names=sexo_counts.index, 
                      title="Distribuição por Sexo", 
                      hole=0.3)
        st.plotly_chart(fig2)

    # Gráficos 3 e 4 em uma linha
    col3, col4 = st.columns(2)

    with col3:
        st.header('Distribuição por Faixa Etária')
        filtered_df['Data_Nascimento'] = pd.to_datetime(filtered_df['Data_Nascimento'], format='%Y%m%d')
        filtered_df['Idade'] = pd.to_datetime('today').year - filtered_df['Data_Nascimento'].dt.year
        fig3 = px.histogram(filtered_df, x='Idade', nbins=10, title='Distribuição por Faixa Etária')
        st.plotly_chart(fig3)

    with col4:
        st.header('Distribuição de Valores Financeiros por Tipo de Verba')
        filtered_df['Financ_Valor_Calculado'] = pd.to_numeric(filtered_df['Financ_Valor_Calculado'], errors='coerce')
        valores_verba = filtered_df.groupby('Financ_Verba_Desc')['Financ_Valor_Calculado'].sum().reset_index()
        fig4 = px.bar(valores_verba, x='Financ_Verba_Desc', y='Financ_Valor_Calculado',
                      title="Distribuição de Valores Financeiros por Verba",
                      labels={'Financ_Verba_Desc': 'Tipo de Verba', 'Financ_Valor_Calculado': 'Valor Total'})
        st.plotly_chart(fig4)

    # Gráfico 7: Comparação de Funcionários com e sem Função Gratificada
    st.header('Funcionários com e sem Função Gratificada')
    funcao_gratificada_counts = filtered_df['Funcao_Gratificada_Comissao_Desc'].value_counts().reset_index()
    funcao_gratificada_counts.columns = ['Função Gratificada', 'Contagem']
    fig7 = px.bar(funcao_gratificada_counts, x='Função Gratificada', y='Contagem', 
                  title='Funcionários com e sem Função Gratificada')
    st.plotly_chart(fig7)

    # Gráfico 8: Média Salarial por Função
    st.header('Média Salarial por Função')
    media_salarial_por_funcao = filtered_df.groupby('Funcao_Efetiva_Desc')['Financ_Valor_Calculado'].mean().reset_index()
    fig8 = px.bar(media_salarial_por_funcao, x='Funcao_Efetiva_Desc', y='Financ_Valor_Calculado', 
                  title='Média Salarial por Função', 
                  labels={'Funcao_Efetiva_Desc': 'Função', 'Financ_Valor_Calculado': 'Média Salarial (R$)'})
    st.plotly_chart(fig8)

    # Campo de pesquisa por palavra-chave
    search_term = st.text_input('Pesquisar Servidores por Nome ou CPF:')

    # Filtrar DataFrame baseado no termo de pesquisa (case-insensitive)
    if search_term:
        filtered_table = filtered_df[
            filtered_df['Nome_Funcionario'].str.contains(search_term, case=False, na=False) | 
            filtered_df['CPF'].str.contains(search_term, case=False, na=False)
        ]
    else:
        filtered_table = filtered_df

    # Exibir a tabela com os servidores filtrados
    st.header('Servidores da Unidade Selecionada')
    st.write(filtered_table[['Nome_Funcionario', 'CPF', 'Funcao_Efetiva_Desc', 'Setor_Desc', 'Carga_Horaria', 'Financ_Valor_Calculado']].reset_index(drop=True))

    # Contagem de servidores exibidos
    st.write(f"Total de servidores exibidos: {len(filtered_table)}")

    # Soma do valor total da coluna 'Financ_Valor_Calculado'
    total_valor = filtered_table['Financ_Valor_Calculado'].sum()
    st.write(f"Valor total calculado: R$ {total_valor:,.2f}")

if __name__ == "__main__":
    run_dashboard()
