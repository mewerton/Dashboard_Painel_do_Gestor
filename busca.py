import streamlit as st
import pandas as pd
from data_loader import load_servidores_data

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

def extract_cpf_from_message(message):
    import re
    cpf_match = re.search(r'\b\d{11}\b', message)  # Procurar por um CPF de 11 dígitos na mensagem
    if cpf_match:
        return cpf_match.group(0)
    return None
