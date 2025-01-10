import streamlit as st
import locale
import base64
from PIL import Image
from sidebar import load_sidebar
#from chatbot import render_chatbot  # Importar a função do chatbot

# Tente definir o locale para pt_BR. Se falhar, use o locale padrão do sistema
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_ALL, '')  # Fallback para o locale padrão do sistema

# Função de navegação para sincronizar com o sidebar
def navigate_to_dashboard(dashboard_name):
    st.session_state["selected_page"] = dashboard_name  # Atualiza a página atual na sessão

def run_dashboard():
    # Carregar o sidebar com o filtro de UG ou SIGLA para a página inicial
    load_sidebar(None, "Início")

    # Chame o chatbot para renderizar no sidebar
    #render_chatbot()

    # Exibir título da página
    st.title('Módulos disponíveis')

    # Carregar as imagens das miniaturas e textos explicativos
    image_paths = {
        "Despesas Detalhado": "src/assets/despesas_capab.png",
        "Diárias": "src/assets/diarias_capab.png",
        "Contratos": "src/assets/contratos_capab.png",
        "Servidores": "src/assets/servidores_capab.png"
    }
    
    dashboard_texts = {
        "Despesas Detalhado": "Painel detalhado com dados sobre despesas realizadas, oferecendo insights por mês e ano.",
        "Diárias": "Visualização das diárias pagas aos servidores, incluindo análises por unidade e períodos.",
        "Contratos": "Monitoramento de contratos ativos, com indicadores de valores e prazos para acompanhamento.",
        "Servidores": "Painel com dados dos servidores, permitindo análise de informações de folha de pagamento."
    }

    # Lista de dashboards para correspondência com o sidebar
    dashboards = ["Despesas Detalhado", "Diárias", "Contratos", "Servidores"]
    
    # Organizar as imagens em colunas
    cols = st.columns(4)
    for i, dashboard in enumerate(dashboards):
        with cols[i]:
            # Carregar a imagem e convertê-la para Base64 para evitar a expansão
            image = Image.open(image_paths[dashboard])
            with open(image_paths[dashboard], "rb") as file:
                image_data = file.read()
                encoded_image = base64.b64encode(image_data).decode()
            
            # Exibir a imagem com HTML para desativar a expansão
            st.markdown(
                f'<img src="data:image/png;base64,{encoded_image}" style="width:100%;height:auto;" alt="{dashboard}">',
                unsafe_allow_html=True
            )
            
            # Título centralizado
            st.markdown(f"<h4 style='text-align: center;'>{dashboard}</h4>", unsafe_allow_html=True)
            
            # Texto explicativo abaixo do título
            st.write(dashboard_texts[dashboard])

# Inicializar a sessão, se necessário
if "selected_page" not in st.session_state:
    st.session_state["selected_page"] = "Início"

# Executar o dashboard
if __name__ == "__main__":
    run_dashboard()
