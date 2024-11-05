import streamlit as st
import locale
from PIL import Image
from sidebar import load_sidebar

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

    # Exibir título e imagens de miniaturas
    st.title('Módulos disponíveis')

    # Carregar as imagens das miniaturas
    image_paths = {
        "Despesas Detalhado": "src/assets/despesas_capa.png",
        "Diárias": "src/assets/diarias_capa.png",
        "Contratos": "src/assets/contratos_capa.png",
        "Servidores": "src/assets/servidores_capa.png"
    }

    # Lista de dashboards para correspondência com o sidebar
    dashboards = ["Despesas Detalhado", "Diárias", "Contratos", "Servidores"]
    
    # Organizar as imagens em colunas
    cols = st.columns(4)
    for i, dashboard in enumerate(dashboards):
        with cols[i]:
            image = Image.open(image_paths[dashboard])
            st.image(image, use_column_width=True)
            
            # Botão para navegar ao dashboard selecionado
            # if st.button(f"Acessar {dashboard}", key=dashboard):
            #     navigate_to_dashboard(dashboard)  # Sincroniza com a navegação do sidebar
            
            st.write(dashboard)

# Inicializar a sessão, se necessário
if "selected_page" not in st.session_state:
    st.session_state["selected_page"] = "Início"

# Executar o dashboard
if __name__ == "__main__":
    run_dashboard()
