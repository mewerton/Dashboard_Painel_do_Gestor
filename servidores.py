import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import locale
from sidebar import load_sidebar  # Agora você usa a função centralizada do sidebar
from data_loader import load_servidores_data
from chatbot import render_chatbot  # Importar a função do chatbot

# Configurar o locale para português do Brasil
#locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

# Dicionário para renomear as colunas para exibição
colunas_exibicao = {
    'Nome_Funcionario': 'Nome do Funcionário',
    'CPF': 'CPF',
    'Funcao_Efetiva_Desc': 'Função',
    'Setor_Desc': 'Setor',
    'Carga_Horaria': 'Carga Horária',
    'Financ_Valor_Calculado': 'Valor Calculado (R$)'
}

# Função para formatar valores em Real
def formatar_valores(df):
    df['Financ_Valor_Calculado'] = df['Financ_Valor_Calculado'].apply(
        lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )
    return df

# Tente definir o locale para pt_BR. Se falhar, use o locale padrão do sistema
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_ALL, '')  # Fallback para o locale padrão do sistema

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

    # Verifique se nenhuma Unidade foi selecionada
    if not selected_unidade:
        st.warning("Nenhuma Unidade selecionada. Por favor, selecione uma Unidade para visualizar os dados.")
        return  # Encerra a função aqui se nenhuma unidade foi selecionada
    else:
        # Converter selected_unidade para o formato com zeros à esquerda
        selected_unidade = str(selected_unidade).zfill(8)

        # Filtrar o DataFrame com base na Unidade selecionada
        filtered_df = df[df['Unidade'] == selected_unidade].copy()  # Adiciona .copy() após o filtro

        if filtered_df.empty:
            st.warning(f"Nenhum dado encontrado para a Unidade {selected_unidade}.")
            return


    # Exibir as métricas
    #st.title('Dashboard de Servidores')
    
    # Dividindo em abas
    tab1, tab2, tab3, tab4 = st.tabs(["Instrução", "Idade/Verbas", "Salários","Pesquisa"])

    with tab1:
        # Gráficos 1 e 2 em uma linha
        col1, col2 = st.columns([3, 1])

        # Gráfico de Distribuição por Grau de Instrução, agrupado por Sexo
        with col1:
            grau_instrucao_sexo_counts = filtered_df.groupby(['Grau_Instrucao_Desc', 'Sexo_Desc']).size().reset_index(name='Quantidade')
            total_counts = grau_instrucao_sexo_counts.groupby('Grau_Instrucao_Desc')['Quantidade'].sum().reset_index()
            total_counts = total_counts.sort_values(by='Quantidade', ascending=False)
            grau_instrucao_sexo_counts['Grau_Instrucao_Desc'] = pd.Categorical(grau_instrucao_sexo_counts['Grau_Instrucao_Desc'], categories=total_counts['Grau_Instrucao_Desc'], ordered=True)
            grau_instrucao_sexo_counts = grau_instrucao_sexo_counts.sort_values('Grau_Instrucao_Desc')
            
            fig1 = px.bar(
                grau_instrucao_sexo_counts,
                x='Grau_Instrucao_Desc',
                y='Quantidade',
                color='Sexo_Desc',
                title="Distribuição por Grau de Instrução e Sexo",
                labels={'Grau_Instrucao_Desc': 'Grau de Instrução', 'Quantidade': 'Quantidade'},
                color_discrete_sequence=['#9B59B6', '#F1C40F'],
                barmode='group'
            )
            fig1.update_traces(texttemplate='%{y}', textposition='outside')
            fig1.update_layout(
                xaxis_title="Grau de Instrução",
                yaxis_title="Quantidade",
                hovermode="x",
                showlegend=False,
                height=600
            )
            st.plotly_chart(fig1)

        with col2:
            sexo_counts = filtered_df['Sexo_Desc'].value_counts()
            fig2 = px.pie(
                values=sexo_counts.values, 
                names=sexo_counts.index, 
                title="Distribuição de Sexo dos Funcionários",
                opacity=0.9,
                hole=0.3
            )
            fig2.update_traces(marker=dict(colors=['#9B59B6', '#F1C40F ']))
            fig2.update_traces(hovertemplate='%{label}<br>Total: %{value}')
            fig2.update_layout(showlegend=False)
            st.plotly_chart(fig2)
            
        # Multiselect para escolher graus de instrução
        selected_graus = st.multiselect(
            'Selecione o(s) Grau(s) de Instrução para visualizar servidores:',
            options=grau_instrucao_sexo_counts['Grau_Instrucao_Desc'].unique(),
            help="Escolha um ou mais níveis de Grau de Instrução para exibir a tabela de servidores.",
            placeholder="Escolha uma opção"
        )

        if selected_graus:
            filtered_table = filtered_df[filtered_df['Grau_Instrucao_Desc'].isin(selected_graus)].copy()
            filtered_table['CPF'] = filtered_table['CPF'].apply(lambda x: x[:-4] + '****' if pd.notnull(x) else x)
            filtered_table = formatar_valores(filtered_table)
            
            st.header('Servidores por Grau de Instrução Selecionado')
            st.write(filtered_table[['Nome_Funcionario', 'CPF', 'Funcao_Efetiva_Desc', 'Setor_Desc', 'Carga_Horaria', 'Financ_Valor_Calculado']].rename(columns=colunas_exibicao))
            
            st.write(f"Total de servidores exibidos: {len(filtered_table)}")
            # Soma do valor total da coluna 'Financ_Valor_Calculado'
            # Remover o símbolo "R$ " e aplicar o formato adequado para conversão
            total_valor = (
                filtered_table['Financ_Valor_Calculado']
                .str.replace('R\$', '', regex=True)  # Remover o símbolo "R$" usando regex
                .str.replace('.', '', regex=False)   # Remover pontos (separador de milhares)
                .str.replace(',', '.', regex=False)  # Converter vírgula para ponto (para formato float)
                .astype(float)
                .sum()
            )

            # Exibir o valor total formatado em reais
            st.write(f"Valor total calculado: R$ {total_valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    with tab2:
        # Gráficos 3 e 4 em uma linha
        col3, col4 = st.columns([4, 1])

        # Gráfico de Distribuição por Faixa Etária
        with col3:
            # Calcular idade para cada funcionário e garantir que a coluna Idade esteja precisa
            filtered_df['Data_Nascimento'] = pd.to_datetime(filtered_df['Data_Nascimento'], format='%Y%m%d')
            filtered_df['Idade'] = pd.to_datetime('today').year - filtered_df['Data_Nascimento'].dt.year

            # Agrupar por idade para obter a quantidade de funcionários em cada faixa etária
            idade_counts = filtered_df['Idade'].value_counts().reset_index()
            idade_counts.columns = ['Idade', 'Quantidade']
            idade_counts = idade_counts.sort_values(by='Idade')  # Organizar por idade

            # Criar o histograma usando os valores calculados
            fig3 = px.bar(
                idade_counts, 
                x='Idade', 
                y='Quantidade', 
                title='Distribuição por Faixa Etária',
                color_discrete_sequence=["#2E9D9F"]  # Cor em tons de azul
            )

            fig3.update_traces(
                marker_line=dict(width=0.5),  # Borda leve nas barras
                hovertemplate="Idade: %{x}<br>Quantidade: %{y}"  # Exibir idade e quantidade no hover
            )
            
            fig3.update_layout(
                xaxis_title="Idade",
                yaxis_title="Quantidade",
                hovermode="x",
            )
            
            st.plotly_chart(fig3)

        # Gráfico de Distribuição de Valores Financeiros por Tipo de Verba
        with col4:
            # Remover valores NaN nas colunas de interesse
            filtered_df = filtered_df.dropna(subset=['Financ_Verba_Desc', 'Financ_Valor_Calculado'])
            
            # Certificar que Financ_Valor_Calculado está em formato numérico
            filtered_df['Financ_Valor_Calculado'] = pd.to_numeric(filtered_df['Financ_Valor_Calculado'], errors='coerce')
            
            # Agrupar dados por tipo de verba
            valores_verba = filtered_df.groupby('Financ_Verba_Desc')['Financ_Valor_Calculado'].sum().reset_index()
            
            fig4 = px.bar(
                valores_verba,
                x='Financ_Verba_Desc',
                y='Financ_Valor_Calculado',
                title="Valores Financeiros por Verba",
                labels={'Financ_Verba_Desc': 'Tipo de Verba', 'Financ_Valor_Calculado': 'Valor Total'},
                color='Financ_Verba_Desc',
                color_discrete_sequence=["#009933"]
            )
            fig4.update_traces(texttemplate='R$ %{y:,.2f}', textposition='outside')
            fig4.update_layout(
                xaxis_title="Tipo de Verba",
                yaxis_title="Valor Total",
                showlegend=False
            )
            st.plotly_chart(fig4)

        # Filtro de Idade com intervalo de seleção
        st.write("### Filtrar Servidores por Faixa Etária")

        # Valores únicos de idade para o filtro
        unique_ages = sorted(idade_counts['Idade'].unique())
        min_age, max_age = min(unique_ages), max(unique_ages)

        # Slider de intervalo de idade
        selected_age_range = st.slider(
            "Selecione o intervalo de Idade:",
            min_value=min_age,
            max_value=max_age,
            value=(min_age, max_age),  # Intervalo padrão selecionado
            step=1,
            format="%d"
        )

        # Filtrar a tabela com base na faixa etária selecionada e garantir que seja uma cópia
        filtered_table = filtered_df.loc[
            (filtered_df['Idade'] >= selected_age_range[0]) & 
            (filtered_df['Idade'] <= selected_age_range[1])
        ].copy()  # Adiciona `.copy()` para evitar o erro

        # Ocultar os últimos 4 dígitos do CPF e formatar a coluna `Financ_Valor_Calculado`
        filtered_table['CPF'] = filtered_table['CPF'].apply(lambda x: x[:-4] + '****' if pd.notnull(x) else x)

        # Aplicar a formatação de valores em Real e renomear as colunas para exibição
        formatar_valores(filtered_table)
    
        # Exibir a tabela formatada apenas se houver uma faixa de idade selecionada
        if not filtered_table.empty:
            st.header(f"Servidores com idade entre {selected_age_range[0]} e {selected_age_range[1]}")
            st.write(filtered_table[['Nome_Funcionario', 'CPF', 'Funcao_Efetiva_Desc', 'Setor_Desc', 'Carga_Horaria', 'Financ_Valor_Calculado']].rename(columns=colunas_exibicao))

            # Contagem de servidores exibidos
            st.write(f"Total de servidores exibidos: {len(filtered_table)}")

            # Soma do valor total da coluna 'Financ_Valor_Calculado'
            # Remover o símbolo "R$ " e aplicar o formato adequado para conversão
            total_valor = (
                filtered_table['Financ_Valor_Calculado']
                .str.replace('R\$', '', regex=True)  # Remover o símbolo "R$" usando regex
                .str.replace('.', '', regex=False)   # Remover pontos (separador de milhares)
                .str.replace(',', '.', regex=False)  # Converter vírgula para ponto (para formato float)
                .astype(float)
                .sum()
            )

            # Exibir o valor total formatado em reais
            st.write(f"Valor total calculado: R$ {total_valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        else:
            st.write("Nenhum servidor encontrado para o intervalo de idade selecionado.")


    with tab3:
        # Gráfico de Média Salarial por Função
        media_salarial_por_funcao = filtered_df.groupby('Funcao_Efetiva_Desc')['Financ_Valor_Calculado'].mean().reset_index()

        # Normalizar os valores para definir a intensidade das cores
        norm = (media_salarial_por_funcao['Financ_Valor_Calculado'] - media_salarial_por_funcao['Financ_Valor_Calculado'].min()) / (media_salarial_por_funcao['Financ_Valor_Calculado'].max() - media_salarial_por_funcao['Financ_Valor_Calculado'].min())

        # Criar a figura usando o gráfico de barras do Plotly
        fig8 = go.Figure(data=[
            go.Bar(
                x=media_salarial_por_funcao['Funcao_Efetiva_Desc'],
                y=media_salarial_por_funcao['Financ_Valor_Calculado'],
                marker=dict(
                    color=['#E55115' if np.isnan(v) else f'rgba(229, 81, 21, {v + 0.3})' for v in norm]  # Ajusta transparência baseada na normalização
                ),
                text=[f'R$ {y:,.2f}' for y in media_salarial_por_funcao['Financ_Valor_Calculado']],
                textposition='outside'
            )
        ])

        # Atualizar o layout do gráfico
        fig8.update_layout(
            title='Média Salarial por Função',
            xaxis_title="Função",
            yaxis_title="Média Salarial (R$)",
            showlegend=False,
            height=600
        )

        st.plotly_chart(fig8)

        # Multiselect para selecionar funções específicas
        selected_funcoes = st.multiselect(
            'Selecione a(s) Função(ões) para visualizar os servidores:',
            options=media_salarial_por_funcao['Funcao_Efetiva_Desc'].unique(),
            help="Escolha uma ou mais funções para exibir a tabela de servidores.",
            placeholder="Escolha uma opção"
        )

        # Exibir a tabela se pelo menos uma função for selecionada
        if selected_funcoes:
            # Filtrar o DataFrame para as funções selecionadas
            filtered_table = filtered_df[filtered_df['Funcao_Efetiva_Desc'].isin(selected_funcoes)].copy()
            
            # Ocultar os últimos 4 dígitos do CPF visualmente usando .loc para evitar o aviso
            filtered_table.loc[:, 'CPF'] = filtered_table['CPF'].apply(lambda x: x[:-4] + '****' if pd.notnull(x) else x)
            
            # Aplicar a formatação de valores em Real e renomear as colunas para exibição
            formatar_valores(filtered_table)

            # Exibir a tabela com os servidores filtrados e colunas renomeadas
            st.header('Servidores por Função Selecionada')
            st.write(filtered_table[['Nome_Funcionario', 'CPF', 'Funcao_Efetiva_Desc', 'Setor_Desc', 'Carga_Horaria', 'Financ_Valor_Calculado']].rename(columns=colunas_exibicao))

            # Contagem de servidores exibidos
            st.write(f"Total de servidores exibidos: {len(filtered_table)}")

            # Soma do valor total da coluna 'Financ_Valor_Calculado'
            # Remover o símbolo "R$ " e aplicar o formato adequado para conversão
            total_valor = (
                filtered_table['Financ_Valor_Calculado']
                .str.replace('R\$', '', regex=True)  # Remover o símbolo "R$" usando regex
                .str.replace('.', '', regex=False)   # Remover pontos (separador de milhares)
                .str.replace(',', '.', regex=False)  # Converter vírgula para ponto (para formato float)
                .astype(float)
                .sum()
            )

            # Exibir o valor total formatado em reais
            st.write(f"Valor total calculado: R$ {total_valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))


    with tab4:
        # Campo de pesquisa por palavra-chave
        search_term = st.text_input('Pesquisar Servidores por Nome ou CPF:')

        # Filtrar DataFrame baseado no termo de pesquisa (case-insensitive)
        if search_term:
            filtered_table = filtered_df[
                filtered_df['Nome_Funcionario'].astype(str).str.contains(search_term, case=False, na=False) |
                filtered_df['CPF'].astype(str).str.contains(search_term, case=False, na=False)
            ].copy()  # Adiciona .copy() para evitar o alerta
        else:
            filtered_table = filtered_df.copy()  # Adiciona .copy() para manter consistência

        # Verificar se o resultado da pesquisa está vazio
        if filtered_table.empty:
            st.warning("Nenhum dado encontrado com o termo de pesquisa informado.")
        else:
            # Ocultar os últimos 4 dígitos do CPF visualmente
            filtered_table['CPF'] = filtered_table['CPF'].apply(lambda x: x[:-4] + '****' if pd.notnull(x) else x)

            # Aplicar a formatação de valores em Real e renomear as colunas para exibição
            formatar_valores(filtered_table)

            # Exibir a tabela com os servidores filtrados e colunas renomeadas
            st.header('Servidores da Unidade Selecionada')
            st.write(filtered_table[['Nome_Funcionario', 'CPF', 'Funcao_Efetiva_Desc', 'Setor_Desc', 'Carga_Horaria', 'Financ_Valor_Calculado']].rename(columns=colunas_exibicao).reset_index(drop=True))

            # Contagem de servidores exibidos
            st.write(f"Total de servidores exibidos: {len(filtered_table)}")

            # Soma do valor total da coluna 'Financ_Valor_Calculado'
            # Remover o símbolo "R$ " e aplicar o formato adequado para conversão
            total_valor = (
                filtered_table['Financ_Valor_Calculado']
                .str.replace('R\$', '', regex=True)  # Remover o símbolo "R$" usando regex
                .str.replace('.', '', regex=False)   # Remover pontos (separador de milhares)
                .str.replace(',', '.', regex=False)  # Converter vírgula para ponto (para formato float)
                .astype(float)
                .sum()
            )

            # Exibir o valor total formatado em reais
            st.write(f"Valor total calculado: R$ {total_valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))


if __name__ == "__main__":
    run_dashboard()
