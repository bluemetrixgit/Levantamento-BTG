import streamlit as st
import pandas as pd
from PIL import Image

st.set_page_config(page_title="Posição de Clientes", layout="wide")

# =========================
# LOGO
# =========================

logo = Image.open("logo.branca.png")
st.image(logo, width=200)

st.title("Posição Consolidada de Clientes")

# =========================
# FUNÇÃO PADRONIZAR CONTA
# =========================

def limpar_conta(coluna):
    return (
        coluna.astype(str)
        .str.replace(".0", "", regex=False)
        .str.strip()
        .str.lstrip("0")
    )

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

    # limpar nomes das colunas
    posicao.columns = posicao.columns.str.strip()
    controle.columns = controle.columns.str.strip()

    # padronizar contas
    posicao["Conta"] = limpar_conta(posicao["Conta"])
    controle["Conta"] = limpar_conta(controle["Conta"])

    return posicao, controle


posicao, controle = carregar_dados()

# =========================
# COLUNAS DO CONTROLE
# =========================

controle = controle[
    [
        "Conta",
        "Carteira",
        "Observações",
        "Status",
        "Situação"
    ]
]

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

observação = st.sidebar.multiselect(
    "Observações",
    sorted(df["Observações"].dropna().unique())
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
# MÉTRICA DE VALOR
# =========================

valor_total = df_filtrado["Valor Bruto"].sum()

st.metric(
    "Valor Bruto",
    f"R$ {valor_total:,.2f}"
)

# =========================
# FORMATAÇÃO
# =========================

# Data no formato brasileiro
if "Data" in df_filtrado.columns:
    df_filtrado["Data"] = pd.to_datetime(df_filtrado["Data"], errors="coerce").dt.strftime("%d/%m/%Y")

# função para formatar reais
def formatar_real(valor):
    if pd.isna(valor):
        return ""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# colunas monetárias
colunas_reais = [
    "Valor Bruto",
    "Valor Líquido",
    "IR",
    "IOF"
]

for col in colunas_reais:
    if col in df_filtrado.columns:
        df_filtrado[col] = df_filtrado[col].apply(formatar_real)

# =========================
# TABELA
# =========================

st.dataframe(
    df_filtrado,
    use_container_width=True,
    height=600
)
