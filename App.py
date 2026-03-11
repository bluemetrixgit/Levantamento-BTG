import streamlit as st
import pandas as pd

st.set_page_config(page_title="Posição de Clientes", layout="wide")

# =========================
# LOGO
# =========================

st.image("logo.branca.png", width=200)

st.title("Posição Consolidada de Clientes")

# =========================
# LEITURA DOS ARQUIVOS
# =========================

@st.cache_data
def carregar_dados():

    posicao = pd.read_excel("Posição.xlsx")

    controle = pd.read_excel(
        "Controle de Contratos - Atualizado 2026.xlsx",
        sheet_name="BTG",
        header=1
    )

    return posicao, controle


posicao, controle = carregar_dados()

# =========================
# SELEÇÃO DE COLUNAS
# =========================

controle = controle[
    [
        "Conta",
        "Status",
        "Situação",
        "Carteira",
        "Observações"
    ]
]

# garantir mesmo tipo
posicao["Conta"] = posicao["Conta"].astype(str)
controle["Conta"] = controle["Conta"].astype(str)

# =========================
# MERGE
# =========================

df = posicao.merge(
    controle,
    on="Conta",
    how="left"
)

# =========================
# SIDEBAR FILTROS
# =========================

st.sidebar.header("Filtros")

carteira = st.sidebar.multiselect(
    "Carteira",
    sorted(df["Carteira"].dropna().unique())
)

status = st.sidebar.multiselect(
    "Status",
    sorted(df["Status"].dropna().unique())
)

situacao = st.sidebar.multiselect(
    "Situação",
    sorted(df["Situação"].dropna().unique())
)

mercado = st.sidebar.multiselect(
    "Mercado",
    sorted(df["Mercado"].dropna().unique())
)

submercado = st.sidebar.multiselect(
    "Sub Mercado",
    sorted(df["Sub Mercado"].dropna().unique())
)

ativo = st.sidebar.multiselect(
    "Ativo",
    sorted(df["Ativo"].dropna().unique())
)

produto = st.sidebar.multiselect(
    "Produto",
    sorted(df["Produto"].dropna().unique())
)

# =========================
# APLICAR FILTROS
# =========================

df_filtrado = df.copy()

if carteira:
    df_filtrado = df_filtrado[df_filtrado["Carteira"].isin(carteira)]

if status:
    df_filtrado = df_filtrado[df_filtrado["Status"].isin(status)]

if situacao:
    df_filtrado = df_filtrado[df_filtrado["Situação"].isin(situacao)]

if mercado:
    df_filtrado = df_filtrado[df_filtrado["Mercado"].isin(mercado)]

if submercado:
    df_filtrado = df_filtrado[df_filtrado["Sub Mercado"].isin(submercado)]

if ativo:
    df_filtrado = df_filtrado[df_filtrado["Ativo"].isin(ativo)]

if produto:
    df_filtrado = df_filtrado[df_filtrado["Produto"].isin(produto)]

# =========================
# MÉTRICAS
# =========================

valor_total = df_filtrado["Valor Bruto"].sum()

st.metric(
    "Valor Investido",
    f"R$ {valor_total:,.2f}"
)

# =========================
# TABELA
# =========================

st.dataframe(
    df_filtrado,
    use_container_width=True,
    height=600
)
