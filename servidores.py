import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import locale
from sidebar import load_sidebar  # Agora você usa a função centralizada do sidebar
from data_loader import load_servidores_data

# Configurar o locale para português do Brasil
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

def run_dashboard():
    # Carregar dados usando o módulo centralizado
    df = load_servidores_data()

    if df is None:
        st.error("Nenhum dado foi carregado. Por favor, verifique os arquivos de entrada.")
        return

    # Carregar o sidebar para "Servidores"
    selected_ugs = load_sidebar(df, "Servidores")

    # Exibir as métricas
    st.title('Dashboard de Servidores')

    # Gráfico 1: Distribuição por Grau de Instrução
    st.header('Distribuição por Grau de Instrução')
    grau_instrucao_counts = df['Grau_Instrucao_Desc'].value_counts()
    fig1 = px.bar(grau_instrucao_counts, 
                  x=grau_instrucao_counts.index, 
                  y=grau_instrucao_counts.values, 
                  labels={'x': 'Grau de Instrução', 'y': 'Contagem'})
    st.plotly_chart(fig1)

    # Gráfico 2: Distribuição de Sexo dos Funcionários
    st.header('Distribuição de Sexo dos Funcionários')
    sexo_counts = df['Sexo_Desc'].value_counts()
    fig2 = px.pie(values=sexo_counts.values, 
                  names=sexo_counts.index, 
                  title="Distribuição por Sexo", 
                  hole=0.3)
    st.plotly_chart(fig2)

    # Gráfico 3: Distribuição por Faixa Etária
    st.header('Distribuição por Faixa Etária')
    df['Data_Nascimento'] = pd.to_datetime(df['Data_Nascimento'], format='%Y%m%d')
    df['Idade'] = pd.to_datetime('today').year - df['Data_Nascimento'].dt.year
    fig3 = px.histogram(df, x='Idade', nbins=10, title='Distribuição por Faixa Etária')
    st.plotly_chart(fig3)

    # Gráfico 4: Distribuição de Valores Financeiros por Tipo de Verba
    st.header('Distribuição de Valores Financeiros por Tipo de Verba')
    df['Financ_Valor_Calculado'] = pd.to_numeric(df['Financ_Valor_Calculado'], errors='coerce')
    valores_verba = df.groupby('Financ_Verba_Desc')['Financ_Valor_Calculado'].sum().reset_index()
    fig4 = px.bar(valores_verba, x='Financ_Verba_Desc', y='Financ_Valor_Calculado',
                  title="Distribuição de Valores Financeiros por Verba",
                  labels={'Financ_Verba_Desc': 'Tipo de Verba', 'Financ_Valor_Calculado': 'Valor Total'})
    st.plotly_chart(fig4)

    # Gráfico 5: Distribuição de Funcionários por Unidade
    st.header('Distribuição de Funcionários por Unidade')
    unidade_counts = df['Unidade_Fil_Desc'].value_counts().reset_index()
    unidade_counts.columns = ['Unidade', 'Contagem']
    fig5 = px.bar(unidade_counts, x='Unidade', y='Contagem', 
                  title='Distribuição de Funcionários por Unidade', 
                  labels={'Unidade': 'Unidade', 'Contagem': 'Quantidade de Funcionários'})
    st.plotly_chart(fig5)

    # Gráfico 6: Custo Total de Funcionários por Unidade
    st.header('Custo Total de Funcionários por Unidade')
    custo_por_unidade = df.groupby('Unidade_Fil_Desc')['Financ_Valor_Calculado'].sum().reset_index()
    fig6 = px.bar(custo_por_unidade, x='Unidade_Fil_Desc', y='Financ_Valor_Calculado', 
                  title='Custo Total de Funcionários por Unidade', 
                  labels={'Unidade_Fil_Desc': 'Unidade', 'Financ_Valor_Calculado': 'Custo Total (R$)'})
    st.plotly_chart(fig6)

    # Gráfico 7: Comparação de Funcionários com e sem Função Gratificada
    st.header('Funcionários com e sem Função Gratificada')
    funcao_gratificada_counts = df['Funcao_Gratificada_Comissao_Desc'].value_counts().reset_index()
    funcao_gratificada_counts.columns = ['Função Gratificada', 'Contagem']
    fig7 = px.bar(funcao_gratificada_counts, x='Função Gratificada', y='Contagem', 
                  title='Funcionários com e sem Função Gratificada')
    st.plotly_chart(fig7)

    # Gráfico 8: Média Salarial por Função
    st.header('Média Salarial por Função')
    media_salarial_por_funcao = df.groupby('Funcao_Efetiva_Desc')['Financ_Valor_Calculado'].mean().reset_index()
    fig8 = px.bar(media_salarial_por_funcao, x='Funcao_Efetiva_Desc', y='Financ_Valor_Calculado', 
                  title='Média Salarial por Função', 
                  labels={'Funcao_Efetiva_Desc': 'Função', 'Financ_Valor_Calculado': 'Média Salarial (R$)'})
    st.plotly_chart(fig8)

if __name__ == "__main__":
    run_dashboard()