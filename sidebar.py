import streamlit as st

def load_sidebar(df):
    ugs_interesse_despesas = [
        520527, 540547, 540573, 140566, 300041, 300567, 540545, 250505, 510514, 510520, 
        520555, 520537, 410506, 410504, 510517, 410510, 520528, 410548, 530539, 530538, 
        410512, 530542, 130569, 130570, 130571, 130572, 410515, 510551, 530541, 510516, 
        510556, 520026, 520531, 530032, 530543, 540037, 540574, 540035, 510024, 510526, 
        520027, 520507, 540038, 520031, 520032, 520533, 350032, 360021, 510522, 260562, 
        530031, 520028, 910997, 510021, 510557, 110010, 340051, 340568, 190047, 190049, 
        190563, 190565, 540033, 510023, 510524, 510020, 410017, 410511, 410018, 410513, 
        520030, 520536, 540034, 110009, 110564, 540036, 210013, 110015, 370001, 110008, 
        110006, 410516, 520529, 520530, 520534, 530537, 990999, 520538, 380001, 520033
    ]

    ugs_default_despesas = [340051]

    selected_ugs_despesas = st.sidebar.multiselect(
        'Selecione a UG de interesse:',
        options=ugs_interesse_despesas,
        default=ugs_default_despesas
    )

    min_ano = int(df['ANO'].min())
    max_ano = int(df['ANO'].max())

    if min_ano == max_ano:
        min_ano = max_ano - 1  # Ajustar para evitar erro no slider

    selected_ano = st.sidebar.slider(
        'Selecione o Ano:',
        min_value=min_ano,
        max_value=max_ano,
        value=(min_ano, max_ano)
    )

    min_mes = 1
    max_mes = 12
    selected_mes = st.sidebar.slider(
        'Selecione o Mês:',
        min_value=min_mes,
        max_value=max_mes,
        value=(min_mes, max_mes)
    )

    return selected_ugs_despesas, selected_ano, selected_mes

def navigate_pages():
    page = st.sidebar.radio(
        'Navegação',
        ('Despesas UG', 'Diárias')
    )
    return page
