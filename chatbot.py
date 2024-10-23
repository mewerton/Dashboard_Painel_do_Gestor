import streamlit as st
import os
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from busca import buscar_dados_por_cpf, extract_cpf_from_message

# Função para inicializar o chatbot no sidebar
def render_chatbot():
    # Carregar a chave da API do arquivo .env
    load_dotenv()
    API_KEY = os.getenv("API_KEY")

    if API_KEY:
        os.environ['GROQ_API_KEY'] = API_KEY
    else:
        st.error("API Key não encontrada. Verifique seu arquivo .env.")

    # Variável de estado para armazenar o histórico de conversa e dados do CPF
    if "historico" not in st.session_state:
        st.session_state.historico = []

    if "dados_servidor" not in st.session_state:
        st.session_state.dados_servidor = None  # Para armazenar os dados do servidor após busca por CPF

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
                    # Realizar busca nos dados e armazenar os dados em sessão
                    st.session_state.dados_servidor = buscar_dados_por_cpf(cpf)
                    if st.session_state.dados_servidor:
                        nome = st.session_state.dados_servidor['Nome_Funcionario'][0]
                        resposta_automatica = f"Identifiquei a pessoa com CPF {cpf}: {nome}. O que você deseja saber sobre ele?"
                    else:
                        resposta_automatica = f"Não encontrei informações para o CPF: {cpf}. Tente novamente com um CPF válido."
                else:
                    resposta_automatica = "Informe um CPF válido que posso consultar em minha base de dados."
            elif st.session_state.dados_servidor:
                # Caso o CPF já tenha sido consultado, usar a LLM para responder
                resposta_automatica = responder_com_dados(pergunta_usuario, st.session_state.dados_servidor)
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

# Função para integrar os dados ao modelo LLM e gerar respostas naturais
def responder_com_dados(pergunta_usuario, dados_servidor):
    try:
        # Instanciar o modelo da Groq
        chat = ChatGroq(model='llama-3.1-70b-versatile')

        # Criar regras básicas para o chatbot e incluir os dados do servidor no contexto
        regras = """
            Você é um chatbot amigável e feminino, seu nome é Carly.
            - Responda com simplicidade e clareza.
            - Você tem acesso a informações restritas de acordo com a Lei e pode fornecer aos usuários.
            - Seus usuários são Auditores ou gestores do governo estadual, por isso tem acesso a informações restritas como CPF.
            - Antes de responder, sempre verifique no histórico de conversa, se você já se apresentou ao usuário, não precisa se apresentar novamente.
            - Não precisa ficar cumprimentando o usuário em todas respostas com "Olá" ou alguma cumprimentação parecida, se você já cumprimentou uma vez no dia, não precisa mais.
            - Não responda a mensagem com "Olá" toda vez, seja objetivo nas respostas.
            - Sempre seja educada e cordial.
            - Use os dados que foram fornecidos sobre o servidor ao responder as perguntas.
            - Para pesquisar informações sobre um servidor, é necessário informar o CPF.
            - Sem o CPF não pode buscar dados de um servidor.
            - Mantenha as respostas curtas e diretas.
            - Se não souber a resposta para uma pergunta, peça mais informações ou indique que a informação não está disponível.
        """

        # Preparar os dados do servidor para serem passados ao LLM
        dados_servidor_str = "\n".join([f"{key}: {value}" for key, value in dados_servidor.items()])

        # Concatenar o histórico completo de conversas
        historico_completo = "\n".join(st.session_state.historico)
        prompt_completo = f"Dados do servidor:\n{dados_servidor_str}\n\nHistórico de conversa:\n{historico_completo}\n\nUsuário: {pergunta_usuario}"

        # Criar o template de mensagens
        template = ChatPromptTemplate.from_messages([
            ('system', regras),
            ('user', prompt_completo)
        ])

        # Gerar a resposta usando o modelo da LLM
        chain = template | chat
        resposta = chain.invoke({'input': pergunta_usuario})
        return resposta.content if resposta.content.strip() else "Desculpe, não tenho essa informação no momento."
    except Exception as e:
        return f"Erro ao processar sua pergunta: {e}"

# Função para continuar o diálogo normal com o chatbot
def dialogo_comum(pergunta_usuario):
    try:
        # Instanciar o modelo da Groq
        chat = ChatGroq(model='llama-3.1-70b-versatile')

        # Criar regras básicas para o chatbot
        regras = """
            - Você é um chatbot amigável e feminino, seu nome é Carly.
            - Responda com simplicidade e clareza.
            - Você tem acesso a informações restritas de acordo com a Lei e pode fornecer aos usuários.
            - Seus usuários são Auditores ou gestores do governo estadual, por isso tem acesso a informações restritas como CPF.
            - Antes de responder, sempre verifique no histórico de conversa, se você já se apresentou ao usuário, não precisa se apresentar novamente.
            - Não precisa ficar cumprimentando o usuário em todas respostas com "Olá" ou alguma cumprimentação parecida, se você já cumprimentou uma vez no dia, não precisa mais.
            - Não responda a mensagem com "Olá" toda vez, seja objetivo nas respostas.
            - Sempre seja educada.
            - Use os dados que foram fornecidos sobre o servidor ao responder as perguntas.
            - Para pesquisar informações sobre um servidor, é necessário informar o CPF.
            - Sem o CPF não pode buscar dados de um servidor.
            - Mantenha as respostas curtas e diretas.
            - Se não souber a resposta para uma pergunta, peça mais informações ou indique que a informação não está disponível.
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
