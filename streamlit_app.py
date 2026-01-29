import streamlit as st
import requests
import pandas as pd

# --- Função consultar_contratos ---
@st.cache_data(show_spinner=True)
def consultar_contratos(codigo_orgao: str, cnpj: str = None,
                        data_inicio: str = None, data_fim: str = None,
                        valor_minimo: float = None, max_paginas: int = 50) -> pd.DataFrame:
    BASE_URL = "https://api.portaldatransparencia.gov.br/api-de-dados/contratos"
    HEADERS = {"chave-api-dados": st.secrets["PORTAL_TRANSPARENCIA_TOKEN"]}

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

        if response.status_code != 200:
            raise Exception(f"Erro na API: {response.status_code} - {response.text}")

        dados = response.json()
        if not dados:
            break

        todos_dados.extend(dados)
        pagina += 1

    if not todos_dados:
        return pd.DataFrame()

    # Transformar JSON em DataFrame limpo
    registros = []
    for c in todos_dados:
        registros.append({
            "numeroContrato": c.get("numero") or c.get("numeroContrato"),
            "objeto": c.get("objeto"),
            "situacao": c.get("situacaoContrato"),
            "valorInicial": c.get("valorInicialCompra"),
            "valorFinal": c.get("valorFinalCompra"),
            "dataInicioVigencia": c.get("dataInicioVigencia"),
            "dataFimVigencia": c.get("dataFimVigencia"),
            "nomeFornecedor": c.get("fornecedor", {}).get("nome") or c.get("fornecedor", {}).get("razaoSocialReceita"),
            "cnpjFornecedor": c.get("fornecedor", {}).get("cnpjFormatado") or c.get("fornecedor", {}).get("cnpj"),
            "codigoOrgao": c.get("unidadeGestora", {}).get("orgaoVinculado", {}).get("codigoSIAFI"),
            "nomeOrgao": c.get("unidadeGestora", {}).get("orgaoVinculado", {}).get("nome")
        })

    df = pd.DataFrame(registros)

    # Converter datas e valores
    for col in ["dataInicioVigencia", "dataFimVigencia"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    df["valorInicial"] = pd.to_numeric(df["valorInicial"], errors="coerce")
    df["valorFinal"] = pd.to_numeric(df["valorFinal"], errors="coerce")

    return df
# --- Fim da função ---


# --- Streamlit app ---
st.set_page_config(page_title="Consulta de Contratos – Governo Federal", layout="wide")
st.title("📄 Consulta de Contratos – Governo Federal")

with st.sidebar:
    st.header("🔍 Filtros")
    codigo_orgao = st.text_input("Código do Órgão (obrigatório)")
    cnpj = st.text_input("CNPJ do Fornecedor (opcional)")
    data_inicio = st.date_input("Data inicial da vigência (opcional)", value=None)
    data_fim = st.date_input("Data final da vigência (opcional)", value=None)
    valor_minimo = st.number_input("Valor mínimo do contrato (opcional)", min_value=0.0, step=1000.0)
    buscar = st.button("🔎 Buscar contratos")

if buscar:
    if not codigo_orgao:
        st.warning("Digite o código do órgão antes de buscar!")
    else:
        with st.spinner("Consultando contratos..."):
            try:
                df = consultar_contratos(
                    codigo_orgao=codigo_orgao,
                    cnpj=cnpj if cnpj else None,
                    data_inicio=data_inicio.strftime("%Y-%m-%d") if data_inicio else None,
                    data_fim=data_fim.strftime("%Y-%m-%d") if data_fim else None,
                    valor_minimo=valor_minimo if valor_minimo > 0 else None
                )

                if df.empty:
                    st.warning("Nenhum contrato encontrado para os filtros informados.")
                else:
                    st.success(f"{len(df)} contratos encontrados")
                    st.dataframe(df, use_container_width=True)

                    # Download Excel
                    excel_bytes = df.to_excel(index=False, engine="openpyxl")
                    st.download_button(
                        "⬇️ Baixar Excel",
                        data=excel_bytes,
                        file_name="contratos_governo_federal.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            except Exception as e:
                st.error(str(e))
