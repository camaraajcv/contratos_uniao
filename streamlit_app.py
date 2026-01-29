import streamlit as st
import requests

API_TOKEN = st.secrets["PORTAL_TRANSPARENCIA_TOKEN"]

url = "https://api.portaldatransparencia.gov.br/api-de-dados/contratos"

headers = {
    "chave-api-dados": API_TOKEN
}

params = {
    "pagina": 1,
    "codigoOrgao": "52921"
}

response = requests.get(url, headers=headers, params=params)

st.write("Status code:", response.status_code)

if response.status_code == 200:
    dados = response.json()
    st.write("Quantidade de registros:", len(dados))
    st.json(dados[0])
else:
    st.error(response.text)
