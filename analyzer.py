import os
import streamlit as st
from langchain_groq import ChatGroq
from dotenv import load_dotenv

# Carregar a chave da API do arquivo .env
def carregar_chave_api():
    load_dotenv()
    API_KEY = os.getenv("API_KEY")

    if API_KEY:
        os.environ['GROQ_API_KEY'] = API_KEY  # Configura a chave globalmente
        return True
    else:
        st.error("API Key não encontrada. Verifique seu arquivo .env.")
        return False

def analisar_tabelas(titulo, tabelas, contexto_filtros=""):
    """
    Analisa uma ou mais tabelas fornecidas e gera um resumo com a LLM.

    Args:
    - titulo (str): Título ou contexto da análise, para exibir no prompt.
    - tabelas (list of tuples): Lista de tabelas no formato [(nome_tabela, df), ...].
    - contexto_filtros (str): Contexto adicional sobre os filtros aplicados.

    Returns:
    - str: Resultado da análise gerada pela LLM.
    """
    try:
        # Verificar se a chave da API foi carregada corretamente
        if not carregar_chave_api():
            return "Erro: Não foi possível carregar a chave da API."

        # Criar o modelo LLM
        chat = ChatGroq(model='llama3-8b-8192')

        # Preparar o prompt
        prompt = f"Contexto: {titulo}\n\n"
        prompt += f"Filtros aplicados:\n{contexto_filtros}\n\n"
        for nome_tabela, tabela in tabelas:
            prompt += f"Tabela: {nome_tabela}\n{tabela.to_string(index=False)}\n\n"

        prompt += "Analise as tabelas considerando os filtros fornecidos. Forneça insights detalhados sobre os dados apresentados. Se tiver a necessidade de responder informações que contanha valores, faça isso usando tabelas e valores em moeda BRL que usa a ',' para separar os centavos e '.' para informar 'milhares', 'milhões','bilhões' e 'trilhões'. Use texto simples para respostas e não use valores dentro dos textos, valores apenas em tabelas para melhor entendendimento do usuário. Responda em Português Brasileiro"

        # Enviar para a LLM como uma string
        resposta = chat.invoke(prompt)  # Passar o prompt diretamente como string
        return resposta.content if resposta.content.strip() else "Não foi possível gerar uma análise no momento."
    except Exception as e:
        return f"Erro ao processar a análise: {str(e)}"

# Função para criar um botão de análise
def botao_analise(titulo, tabelas, botao_texto="Analisar com Inteligência Artificial", filtros=None, key=None):
    """
    Exibe um botão e, ao clicar, analisa as tabelas fornecidas.

    Args:
    - titulo (str): Título ou contexto da análise.
    - tabelas (list of tuples): Lista de tabelas no formato [(nome_tabela, df), ...].
    - botao_texto (str): Texto do botão a ser exibido.
    - filtros (dict): Informações adicionais de contexto, como filtros aplicados.
    - key (str): Chave única para o botão.

    Returns:
    - None
    """
    if st.button(botao_texto, key=key):
        contexto_filtros = ""
        if filtros:
            contexto_filtros = "\n".join([f"{key}: {value}" for key, value in filtros.items()])

        resultado_analise = analisar_tabelas(titulo, tabelas, contexto_filtros)
        st.markdown(f"### Resultado da Análise:\n{resultado_analise}")
