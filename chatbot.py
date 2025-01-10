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
    st.sidebar.subheader("ALici - Inteligência Artificial da CGE")

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
            st.session_state.historico.append(f"**Alici:** {resposta_automatica}")

        # Limpar a pergunta após o envio
        st.session_state.input_pergunta = ""

    # Campo de entrada para a pergunta
    with input_col:
        pergunta_usuario = st.text_input("Sou a ALici, vamos conversar?", key="input_pergunta", on_change=process_message)

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

    # Aqui vamos construir um dicionário para capturar todas as linhas para as colunas relevantes
    dados_servidor_completo = {
        "Unidade": list(dados_servidor['Unidade']),
        "Unidade_Fil_Desc": list(dados_servidor['Unidade_Fil_Desc']),
        "Matricula": list(dados_servidor['Matricula']),
        "Nome_Funcionario": list(dados_servidor['Nome_Funcionario']),
        "CPF": list(dados_servidor['CPF']),
        "Data_Nascimento": list(dados_servidor['Data_Nascimento']),
        "Sexo_Desc": list(dados_servidor['Sexo_Desc']),
        "Grau_Instrucao_Desc": list(dados_servidor['Grau_Instrucao_Desc']),
        "Unidade_Emp_Desc": list(dados_servidor['Unidade_Emp_Desc']),
        "Funcao_Efetiva_Desc": list(dados_servidor['Funcao_Efetiva_Desc']),
        "Setor_Desc": list(dados_servidor['Setor_Desc']),
        "Carga_Horaria": list(dados_servidor['Carga_Horaria']),
        "Tipo_Folha_Desc": list(dados_servidor['Tipo_Folha_Desc']),
        "Vinculo": list(dados_servidor['Vinculo']),
        "Vinculo_Desc": list(dados_servidor['Vinculo_Desc']),
        "Funcao_Gratificada_Comissao": list(dados_servidor['Funcao_Gratificada_Comissao']),
        "Funcao_Gratificada_Comissao_Desc": list(dados_servidor['Funcao_Gratificada_Comissao_Desc']),
        "Nivel_Salarial_Funcao_Gratificada_Comissao_Desc": list(dados_servidor['Nivel_Salarial_Funcao_Gratificada_Comissao_Desc']),
        "Financ_Valor_Calculado": list(dados_servidor['Financ_Valor_Calculado']),
        "Financ_Verba": list(dados_servidor['Financ_Verba']),
        "Financ_Verba_Desc": list(dados_servidor['Financ_Verba_Desc']),
        "Ferias_Periodo_Aquisitivo_Inicial": list(dados_servidor['Ferias_Periodo_Aquisitivo_Inicial']),
        "Ferias_Periodo_Aquisitivo_Final": list(dados_servidor['Ferias_Periodo_Aquisitivo_Final']),
        "Ferias_Data_Ultima_Gozada": list(dados_servidor['Ferias_Data_Ultima_Gozada'])
    }

    return dados_servidor_completo

# Função para integrar os dados ao modelo LLM e gerar respostas naturais
def responder_com_dados(pergunta_usuario, dados_servidor):
    try:
        # Instanciar o modelo da Groq
        chat = ChatGroq(model='llama-3.1-70b-versatile')

        # Criar regras básicas para o chatbot e incluir os dados do servidor no contexto
        regras = """
            Você é um chatbot amigável e feminino, seu nome é ALici.
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
        error_message = str(e)

        # Verificar o código de erro e retornar a mensagem apropriada
        if '500' in error_message:
            return "API da IA - 500 Erro Interno do Servidor: Ocorreu um erro genérico no servidor. Tente a solicitação novamente mais tarde ou entre em contato com o suporte se o problema persistir."
        elif '502' in error_message:
            return "API da IA - 502 Bad Gateway: O servidor recebeu uma resposta inválida de um servidor upstream. Este pode ser um problema temporário; tentar novamente a solicitação pode resolvê-lo."
        elif '503' in error_message:
            return "API da IA - 503 Serviço Indisponível: O servidor não está pronto para lidar com a solicitação, geralmente devido à manutenção ou sobrecarga. Aguarde antes de tentar a solicitação novamente."
        else:
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
            - Você é um chatbot amigável e feminino, seu nome é ALici.
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