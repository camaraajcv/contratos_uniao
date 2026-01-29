import requests
import pandas as pd
import streamlit as st

BASE_URL = "https://api.portaldatransparencia.gov.br/api-de-dados/contratos"
HEADERS = {
    "chave-api-dados": st.secrets["PORTAL_TRANSPARENCIA_TOKEN"]
}

@st.cache_data(show_spinner=True)
def consultar_contratos(
    codigo_orgao: str,
    cnpj: str = None,
    data_inicio: str = None,
    data_fim: str = None,
    valor_minimo: float = None,
    max_paginas: int = 50
) -> pd.DataFrame:
    """
    Consulta contratos do Portal da Transparência.
    Retorna um DataFrame limpo.
    """
    if not codigo_orgao:
        raise ValueError("O parâmetro 'codigo_orgao' é obrigatório!")

    todos_dados = []
    pagina = 1

    while pagina <= max_paginas:
        params = {"pagina": pagina, "codigoOrgao": codigo_orgao}

        if cnpj:
            params["cpfCnpjFornecedor"] = cnpj
        if data_inicio:
            params["dataInicioVigencia"] = data_inicio
        if data_fim:
            params["dataFimVigencia"] = data_fim
        if valor_minimo:
            params["valorMinimo"] = valor_minimo

        response = requests.get(BASE_URL, headers=HEADERS, params=params)

        if response.status_code == 401:
            raise Exception("Token inválido ou expirado!")
        elif response.status_code != 200:
            raise Exception(f"Erro na API: {response.status_code} - {response.text}")

        dados = response.json()
        if not dados:  # sem mais registros
            break

        todos_dados.extend(dados)
        pagina += 1

    if not todos_dados:
        return pd.DataFrame()

    # Transformar em DataFrame
    df = pd.DataFrame(todos_dados)

    # Selecionar colunas principais (limpeza)
    colunas_desejadas = [
        "numeroContrato",
        "objeto",
        "valorInicial",
        "dataInicioVigencia",
        "dataFimVigencia",
        "nomeFornecedor",
        "cnpjFornecedor",
        "situacao",
        "orgaoSuperior",
        "orgao"
    ]

    df = df[[col for col in colunas_desejadas if col in df.columns]]

    # Padronizar datas
    for col in ["dataInicioVigencia", "dataFimVigencia"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Padronizar valores
    if "valorInicial" in df.columns:
        df["valorInicial"] = pd.to_numeric(df["valorInicial"], errors="coerce")

    return df
