import streamlit as st
import os
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv

# Função para inicializar o chatbot no sidebar
def render_chatbot():
    # Carregar a chave da API do arquivo .env
    load_dotenv()
    API_KEY = os.getenv("API_KEY")

    # Verificar se a API_KEY está carregada corretamente
    #st.sidebar.write(f"API Key: {API_KEY}")  # Verifique se isso exibe a chave no sidebar

    if API_KEY:
        os.environ['GROQ_API_KEY'] = API_KEY
    else:
        st.error("API Key não encontrada. Verifique seu arquivo .env.")

    # Variável de estado para armazenar o histórico de conversa
    if "historico" not in st.session_state:
        st.session_state.historico = []

    # Adicionando o chatbot no sidebar com um botão de envio personalizado
    st.sidebar.subheader("Carly - Inteligência Artificial da CGE")

    # Colocando o input e o botão em uma única linha, sem o label acima do input
    input_col, button_col = st.sidebar.columns([5, 1])  # Ajuste as proporções das colunas

    def process_message():
        # Processa a mensagem do chatbot
        pergunta_usuario = st.session_state.input_pergunta

        if pergunta_usuario:
            try:
                # Instanciar o modelo da Groq
                chat = ChatGroq(model='llama-3.1-70b-versatile')

                # Criar regras básicas para o chatbot (temporário)
                regras = "Você é um chatbot amigável e feminino, seu nome é Carly, responda com simplicidade."

                # Histórico de conversa anterior
                historico_conversa = "\n".join(st.session_state.historico)

                # Preparar o prompt para o chatbot
                template = ChatPromptTemplate.from_messages([
                    ('system', regras),
                    ('user', historico_conversa + f"\nUsuário: {pergunta_usuario}")
                ])

                # Interação com o chatbot
                chain = template | chat
                resposta = chain.invoke({'input': pergunta_usuario})

                # Verificar se o modelo conseguiu responder
                if resposta.content.strip():
                    resposta_automatica = resposta.content
                else:
                    resposta_automatica = "Desculpe, não tenho essa informação no momento."

                # Adicionar a pergunta e resposta ao histórico
                st.session_state.historico.append(f"Você: {pergunta_usuario}")
                st.session_state.historico.append(f"**Carly:** {resposta_automatica}")

            except Exception as e:
                st.sidebar.error(f"Erro ao processar a mensagem: {e}")

        # Limpar a pergunta após o envio
        st.session_state.input_pergunta = ""

    # Campo de entrada para a pergunta
    with input_col:
        pergunta_usuario = st.text_input("Sou a Carly, vamos conversar?", key="input_pergunta", on_change=process_message)

    # Botão de envio personalizado com ícone de seta
    with button_col:
        st.markdown("""
            <style>
            .stButton button {
                height: 3.3em;
                padding-top: 0;
                padding-bottom: 0;
            }
            </style>
        """, unsafe_allow_html=True)
        st.button("➤", key="send_button", on_click=process_message)

    # Exibir o histórico de conversa no sidebar
    if st.session_state.historico:
        st.sidebar.subheader("Histórico de Conversas")
        for i, msg in enumerate(reversed(st.session_state.historico)):
            st.sidebar.write(msg)
            if i % 2 != 0:
                st.sidebar.divider()
