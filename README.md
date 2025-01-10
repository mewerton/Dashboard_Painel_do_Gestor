## Painel do Gestor

# Visão Geral
Este é um painel desenvolvido utilizando o Streamlit para gerenciar despesas, diárias e contratos. O painel permite a visualização de dados com vários filtros e exibe gráficos e tabelas interativas.

# Funcionalidades
Despesas Detalhado: Painel detalhado para visualização de despesas.
Diárias: Painel para visualizar diárias recebidas.
Contratos: Painel para gerenciamento de contratos.

# Instalação
Siga os passos abaixo para baixar e instalar o projeto na sua máquina Windows.

# Pré-requisitos
Antes de iniciar, certifique-se de que você tenha instalado:

Python 3.8+
Git

# Passo 1: Clonar o Repositório
Primeiro, você precisa clonar o projeto do GitHub. Abra o Prompt de Comando ou o PowerShell e execute o comando abaixo:

git clone https://github.com/mewerton/painelgestor

# Passo 2: Configurar o Ambiente Virtual
No Windows, é altamente recomendado utilizar um ambiente virtual para gerenciar as dependências do projeto. Para criar e ativar um ambiente virtual, execute os comandos abaixo no Prompt de Comando ou PowerShell:

# Criar o ambiente virtual
python -m venv venv

# Ativar o ambiente virtual
venv\Scripts\activate

Você verá o nome do ambiente venv no início da linha do prompt, indicando que ele está ativo.

# Passo 3: Instalar as Dependências
Com o ambiente virtual ativado, instale as bibliotecas necessárias listadas no arquivo requirements.txt. Isso pode ser feito com o seguinte comando:
pip install -r requirements.txt

# Passo 5: Criar arquivo config.toml

Algumas chaves são necessárias para executar o projeto: 
FOLDER_ID = "XXXXXX"
LOGIN_FOLDER_ID = "XXXXXX"
CONTRATOS_FOLDER_ID = "XXXXXX"
API_KEY = "XXXXXX"
FOLHA_FOLDER_ID = "XXXXXX"
CREDENTIALS_FILE = "XXXXXX"

# Passo 6: Executar a Aplicação
Agora que todas as dependências estão instaladas, você pode rodar o painel com o Streamlit. Use o seguinte comando no Prompt de Comando ou PowerShell:
streamlit run app.py

Isso abrirá o painel diretamente no seu navegador padrão. Se tudo estiver configurado corretamente, você verá a interface do Painel do Gestor.

# Solução de Problemas
Se encontrar problemas durante a instalação ou execução do projeto, siga estas dicas:

Verifique a Instalação do Python: Certifique-se de que o Python está instalado corretamente e incluído no PATH do sistema.
Dependências: Verifique se todas as bibliotecas do requirements.txt foram instaladas corretamente.
Ambiente Virtual: Verifique se o ambiente virtual está ativado antes de instalar as dependências e rodar o projeto.
Versão do Streamlit: Certifique-se de que a versão do Streamlit é compatível com o código. Se necessário, atualize utilizando pip install --upgrade streamlit.
