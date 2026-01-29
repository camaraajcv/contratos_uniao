import streamlit as st

API_TOKEN = st.secrets["PORTAL_TRANSPARENCIA_TOKEN"]

BASE_URL = "https://api.portaldatransparencia.gov.br/api-de-dados/contratos"
st.write("Token carregado?", bool(st.secrets.get("PORTAL_TRANSPARENCIA_TOKEN")))