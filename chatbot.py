import streamlit as st
import os
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import pandas as pd
from data_loader import load_servidores_data

# Função para inicializar o chatbot no sidebar
def render_chatbot():
    # Carregar a chave da API do arquivo .env
    load_dotenv()
    API_KEY = os.getenv("API_KEY")

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
    input_col, button_col = st.sidebar.columns([5, 1])

    def process_message():
        # Processa a mensagem do chatbot
        pergunta_usuario = st.session_state.input_pergunta

        if pergunta_usuario:
            # Verificar se o usuário forneceu um CPF
            if "CPF" in pergunta_usuario or any(char.isdigit() for char in pergunta_usuario):
                cpf = extract_cpf_from_message(pergunta_usuario)
                if cpf:
                    # Realizar busca diretamente nos dados de servidores
                    resposta_automatica = buscar_dados_por_cpf(cpf)
                else:
                    resposta_automatica = "Informe um CPF válido que posso consultar em minha base de dados."
            else:
                # Realizar o diálogo normal com o chatbot
                resposta_automatica = dialogo_comum(pergunta_usuario)

            # Adicionar a pergunta e resposta ao histórico
            st.session_state.historico.append(f"Você: {pergunta_usuario}")
            st.session_state.historico.append(f"**Carly:** {resposta_automatica}")

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

# ==== Função de buscar dados por CPF ====
def buscar_dados_por_cpf(cpf):
    df = load_servidores_data()
    cpf_formatado = str(cpf).zfill(11)  # Garantir que o CPF tenha 11 dígitos com zeros à esquerda

    dados_servidor = df[df['CPF'] == cpf_formatado]
    if dados_servidor.empty:
        return f"Não encontrei informações para o CPF: {cpf_formatado}"

    nome = dados_servidor['Nome_Funcionario'].values[0]
    funcao = dados_servidor['Funcao_Efetiva_Desc'].values[0]
    setor = dados_servidor['Setor_Desc'].values[0]
    carga_horaria = dados_servidor['Carga_Horaria'].values[0]
    salario = dados_servidor['Financ_Valor_Calculado'].values[0]

    return (f"Informações do servidor:\n"
            f"Nome: {nome}\n"
            f"Função: {funcao}\n"
            f"Setor: {setor}\n"
            f"Carga Horária: {carga_horaria}\n"
            f"Salário: R$ {salario:,.2f}")

# ==== Fim da função de buscar dados por CPF ====

# Função para extrair o CPF da mensagem do usuário
def extract_cpf_from_message(message):
    import re
    cpf_match = re.search(r'\b\d{11}\b', message)  # Procurar por um CPF de 11 dígitos na mensagem
    if cpf_match:
        return cpf_match.group(0)
    return None

# Função para continuar o diálogo normal com o chatbot
def dialogo_comum(pergunta_usuario):
    try:
        # Instanciar o modelo da Groq
        chat = ChatGroq(model='llama-3.1-70b-versatile')

        # Criar regras básicas para o chatbot
        regras = """
            Você é um chatbot amigável e feminino, seu nome é Carly.
            - Responda com simplicidade e clareza.
            - Você faz parte da Auditoria de controle interno e tem acesso a dados restritos.
            - Seus usuários são Auditores ou gestores do governo estadual, e tem autoridade para acessar dados restritos como CPF e outras informações.
            - Mantenha as respostas curtas e diretas.
            - Sempre seja educada e cordial.
            - Ao responder sobre informações de servidores públicos, seja objetiva.
            - Evite discussões sobre temas como política, religião ou outros tópicos sensíveis, a menos que estejam diretamente relacionados ao seu papel.
            - Responda a perguntas de maneira clara, sem usar linguagem técnica excessiva.
            - Se não souber a resposta para uma pergunta, gentilmente peça mais informações ou indique que a informação não está disponível.
        """
        historico_conversa = "\n".join(st.session_state.historico)
        template = ChatPromptTemplate.from_messages([
            ('system', regras),
            ('user', historico_conversa + f"\nUsuário: {pergunta_usuario}")
        ])
        chain = template | chat
        resposta = chain.invoke({'input': pergunta_usuario})
        return resposta.content if resposta.content.strip() else "Desculpe, não tenho essa informação no momento."
    except Exception as e:
        return f"Erro ao processar sua pergunta: {e}"
