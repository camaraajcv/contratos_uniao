import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from io import BytesIO
import time

# --- Função progressiva para consultar contratos ---
def consultar_contratos_progressivo(codigo_orgao: str, ug_executora: str,
                                    valor_minimo: float = None, max_paginas: int = 500) -> pd.DataFrame:
    """
    Consulta todas as páginas de contratos de um órgão, filtra por UG executora e contratos vigentes.
    Mostra progressivamente os resultados.
    """
    BASE_URL = "https://api.portaldatransparencia.gov.br/api-de-dados/contratos"
    HEADERS = {"chave-api-dados": st.secrets["PORTAL_TRANSPARENCIA_TOKEN"]}

    registros_filtrados = []
    pagina = 1
    hoje = pd.Timestamp.today()

    progresso_text = st.empty()
    progresso_bar = st.progress(0)

    while pagina <= max_paginas:
        # ✅ Enviar sempre codigoOrgao em cada requisição
        params = {
            "pagina": pagina,
            "codigoOrgao": codigo_orgao
        }
        if valor_minimo:
            params["valorMinimo"] = valor_minimo

        response = requests.get(BASE_URL, headers=HEADERS, params=params)

        if response.status_code != 200:
            raise Exception(f"Erro na API: {response.status_code} - {response.text}")

        dados = response.json()
        if not dados:
            break

        # Processar e filtrar apenas os contratos da UG executora e vigentes
        for c in dados:
            codigo_ug_exec = c.get("unidadeGestoraCompras", {}).get("codigo")
            data_fim = c.get("dataFimVigencia")
            if codigo_ug_exec == ug_executora and data_fim and pd.to_datetime(data_fim, errors="coerce") >= hoje:
                registros_filtrados.append({
                    "numeroContrato": c.get("numero") or c.get("numeroContrato"),
                    "objeto": c.get("objeto"),
                    "situacao": c.get("situacaoContrato"),
                    "valorInicial": c.get("valorInicialCompra"),
                    "valorFinal": c.get("valorFinalCompra"),
                    "dataInicioVigencia": c.get("dataInicioVigencia"),
                    "dataFimVigencia": c.get("dataFimVigencia"),
                    "nomeFornecedor": c.get("fornecedor", {}).get("nome") or c.get("fornecedor", {}).get("razaoSocialReceita"),
                    "cnpjFornecedor": c.get("fornecedor", {}).get("cnpjFormatado") or c.get("fornecedor", {}).get("cnpj"),
                    "codigoUGExecutora": codigo_ug_exec,
                    "nomeUGExecutora": c.get("unidadeGestoraCompras", {}).get("nome"),
                    "codigoUGResponsavel": c.get("unidadeGestora", {}).get("codigo"),
                    "nomeUGResponsavel": c.get("unidadeGestora", {}).get("nome"),
                    "codigoOrgao": c.get("unidadeGestora", {}).get("orgaoVinculado", {}).get("codigoSIAFI"),
                    "nomeOrgao": c.get("unidadeGestora", {}).get("orgaoVinculado", {}).get("nome")
                })

        # Atualiza barra de progresso e mensagem
        progresso_text.text(f"Consultando página {pagina}...")
        progresso_bar.progress(min(pagina / max_paginas, 1.0))

        pagina += 1
        time.sleep(0.1)  # Pequena pausa para não sobrecarregar a API

    df = pd.DataFrame(registros_filtrados)

    # Converter datas e valores
    for col in ["dataInicioVigencia", "dataFimVigencia"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    df["valorInicial"] = pd.to_numeric(df["valorInicial"], errors="coerce")
    df["valorFinal"] = pd.to_numeric(df["valorFinal"], errors="coerce")

    return df

# --- Streamlit App ---
st.set_page_config(page_title="Contratos Vigentes – Governo Federal", layout="wide")
st.title("📄 Contratos Vigentes – Governo Federal (Progressivo)")

# Sidebar
with st.sidebar:
    st.header("🔍 Filtros obrigatórios")
    codigo_orgao = st.text_input("Código do Órgão")
    ug_executora = st.text_input("Código da UG Executora (UG de Compras)")
    valor_minimo = st.number_input("Valor mínimo do contrato", min_value=0.0, step=1000.0)
    buscar = st.button("🔎 Buscar contratos vigentes")

# Rodar busca
if buscar:
    if not codigo_orgao or not ug_executora:
        st.warning("Digite o Código do Órgão e da UG Executora para prosseguir!")
    else:
        try:
            st.info("Consultando todas as páginas do órgão, filtrando contratos vigentes...")
            df = consultar_contratos_progressivo(
                codigo_orgao=codigo_orgao,
                ug_executora=ug_executora,
                valor_minimo=valor_minimo if valor_minimo > 0 else None,
                max_paginas=500  # Pode ajustar para órgãos muito grandes
            )

            if df.empty:
                st.warning("Nenhum contrato vigente encontrado para os filtros informados.")
            else:
                st.success(f"{len(df)} contratos vigentes encontrados")
                st.dataframe(df, use_container_width=True)

                # Download Excel
                output = BytesIO()
                df.to_excel(output, index=False, engine="openpyxl")
                excel_bytes = output.getvalue()

                st.download_button(
                    "⬇️ Baixar Excel",
                    data=excel_bytes,
                    file_name="contratos_vigentes_progressivo.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

        except Exception as e:
            st.error(str(e))
