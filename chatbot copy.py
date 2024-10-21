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
                        nome = st.session_state.dados_servidor['Nome_Funcionario']
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

# ==== Função de buscar dados por CPF ==== 
@st.cache_resource
def buscar_dados_por_cpf(cpf):
    df = load_servidores_data()
    cpf_formatado = str(cpf).zfill(11)  # Garantir que o CPF tenha 11 dígitos com zeros à esquerda

    dados_servidor = df[df['CPF'] == cpf_formatado]
    if dados_servidor.empty:
        return None

    # Retornar um dicionário com todas as informações do servidor
    return {
        "Unidade": dados_servidor['Unidade'].values[0],
        "Unidade_Fil_Desc": dados_servidor['Unidade_Fil_Desc'].values[0],
        "Matricula": dados_servidor['Matricula'].values[0],
        "Nome_Funcionario": dados_servidor['Nome_Funcionario'].values[0],
        "CPF": dados_servidor['CPF'].values[0],
        "Data_Nascimento": dados_servidor['Data_Nascimento'].values[0],
        "Sexo_Desc": dados_servidor['Sexo_Desc'].values[0],
        "Grau_Instrucao_Desc": dados_servidor['Grau_Instrucao_Desc'].values[0],
        "Unidade_Emp_Desc": dados_servidor['Unidade_Emp_Desc'].values[0],
        "Funcao_Efetiva_Desc": dados_servidor['Funcao_Efetiva_Desc'].values[0],
        "Setor_Desc": dados_servidor['Setor_Desc'].values[0],
        "Carga_Horaria": dados_servidor['Carga_Horaria'].values[0],
        "Tipo_Folha_Desc": dados_servidor['Tipo_Folha_Desc'].values[0],
        "Vinculo": dados_servidor['Vinculo'].values[0],
        "Vinculo_Desc": dados_servidor['Vinculo_Desc'].values[0],
        "Funcao_Gratificada_Comissao": dados_servidor['Funcao_Gratificada_Comissao'].values[0],
        "Funcao_Gratificada_Comissao_Desc": dados_servidor['Funcao_Gratificada_Comissao_Desc'].values[0],
        "Nivel_Salarial_Funcao_Gratificada_Comissao_Desc": dados_servidor['Nivel_Salarial_Funcao_Gratificada_Comissao_Desc'].values[0],
        "Financ_Valor_Calculado": dados_servidor['Financ_Valor_Calculado'].values[0],
        "Financ_Verba": dados_servidor['Financ_Verba'].values[0],
        "Financ_Verba_Desc": dados_servidor['Financ_Verba_Desc'].values[0],
        "Ferias_Periodo_Aquisitivo_Inicial": dados_servidor['Ferias_Periodo_Aquisitivo_Inicial'].values[0],
        "Ferias_Periodo_Aquisitivo_Final": dados_servidor['Ferias_Periodo_Aquisitivo_Final'].values[0],
        "Ferias_Data_Ultima_Gozada": dados_servidor['Ferias_Data_Ultima_Gozada'].values[0]
    }

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
            - Verifique no histórico de conversa, se você já se apresentou ao uauário, não precisa se apresentar novamente, a não quer que ele peça.
            - Para pesquisar informações sobre um serivod, é necessário informar o CPF.
            - Sem o CPF não pode buscar dados de um servidor.
            - Use os dados que foram fornecidos sobre o servidor ao responder as perguntas.
            - Mantenha as respostas curtas e diretas.
            - Não precisa ficar cumprimentando o usuário em todas respostas com "Olá" ou alguma cumprimentação parecida, se você já cumprimentou uma vez no dia, não precisa mais.
            - Sempre seja educada e cordial.
            - Se não souber a resposta para uma pergunta, peça mais informações ou indique que a informação não está disponível.
        """

        # Preparar os dados do servidor para serem passados ao LLM
        dados_servidor_str = "\n".join([f"{key}: {value}" for key, value in dados_servidor.items()])
        prompt_completo = f"Dados do servidor:\n{dados_servidor_str}\n\nUsuário: {pergunta_usuario}"

        template = ChatPromptTemplate.from_messages([
            ('system', regras),
            ('user', prompt_completo)
        ])

        chain = template | chat
        resposta = chain.invoke({'input': pergunta_usuario})
        return resposta.content if resposta.content.strip() else "Desculpe, não tenho essa informação no momento."
    except Exception as e:
        return f"Erro ao processar sua pergunta: {e}"

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
            - Verifique no histórico de conversa, se você já se apresentou ao uauário, não precisa se apresentar novamente, a não quer que ele peça.
            - Responda com simplicidade e clareza.
            - Você faz parte da Auditoria de controle interno e tem acesso a dados restritos.
            - Seus usuários são Auditores ou gestores do governo estadual, e têm autoridade para acessar dados restritos como CPF e outras informações.
            - Para pesquisar informações sobre um serivod, é necessário informar o CPF.
            - Sem o CPF não pode buscar dados de um servidor.
            - Mantenha as respostas curtas e diretas.
            - Sempre seja educada e cordial.
            - Evite discussões sobre temas como política, religião ou outros tópicos sensíveis.
            - Responda a perguntas de maneira clara, sem usar linguagem técnica excessiva.
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
