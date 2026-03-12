import streamlit as st
import pandas as pd
from PIL import Image
from io import BytesIO

st.set_page_config(page_title="Posição de Clientes", layout="wide")

# =========================
# LOGO
# =========================

logo = Image.open("logo.branca.png")
st.image(logo, width=200)

st.title("Posição Consolidada de Clientes")

# =========================
# FUNÇÃO LIMPAR CONTA
# =========================

def limpar_conta(coluna):
    return (
        coluna.astype(str)
        .str.replace(".0", "", regex=False)
        .str.strip()
        .str.lstrip("0")
    )

# =========================
# FORMATAÇÃO REAL
# =========================

def formatar_real(valor):
    if pd.isna(valor):
        return ""
    return (
        f"R$ {valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )

# =========================
# GERAR EXCEL
# =========================

def gerar_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return output

# =========================
# CARREGAR DADOS
# =========================

@st.cache_data
def carregar_dados():

    posicao = pd.read_excel("Posição.xlsx")

    controle = pd.read_excel(
        "Controle de Contratos - Atualizado 2026.xlsx",
        sheet_name="BTG",
        header=1
    )

    posicao.columns = posicao.columns.str.strip()
    controle.columns = controle.columns.str.strip()

    posicao["Conta"] = limpar_conta(posicao["Conta"])
    controle["Conta"] = limpar_conta(controle["Conta"])

    return posicao, controle


posicao, controle = carregar_dados()

controle = controle[
    [
        "Conta",
        "Status",
        "Situação",
        "Carteira",
        "Observações"
    ]
]

df = posicao.merge(
    controle,
    on="Conta",
    how="left"
)

df = df[df["Carteira"].notna()]

# =========================
# SIDEBAR FILTROS
# =========================

st.sidebar.header("Filtros")

contas = st.sidebar.multiselect("Conta", sorted(df["Conta"].dropna().unique()))
carteira = st.sidebar.multiselect("Carteira", sorted(df["Carteira"].dropna().unique()))
status = st.sidebar.multiselect("Status", sorted(df["Status"].dropna().unique()))
situacao = st.sidebar.multiselect("Situação", sorted(df["Situação"].dropna().unique()))
mercado = st.sidebar.multiselect("Mercado", sorted(df["Mercado"].dropna().unique()))
submercado = st.sidebar.multiselect("Sub Mercado", sorted(df["Sub Mercado"].dropna().unique()))
ativo = st.sidebar.multiselect("Ativo", sorted(df["Ativo"].dropna().unique()))
produto = st.sidebar.multiselect("Produto", sorted(df["Produto"].dropna().unique()))
observacoes = st.sidebar.multiselect("Observações", sorted(df["Observações"].dropna().unique()))

somente_sem_obs = st.sidebar.checkbox("Mostrar apenas contas sem observações")

# =========================
# APLICAR FILTROS
# =========================

df_filtrado = df.copy()

if contas:
    df_filtrado = df_filtrado[df_filtrado["Conta"].isin(contas)]

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

if observacoes:
    df_filtrado = df_filtrado[df_filtrado["Observações"].isin(observacoes)]

if somente_sem_obs:
    df_filtrado = df_filtrado[
        (df_filtrado["Observações"].isna()) |
        (df_filtrado["Observações"].astype(str).str.strip() == "")
    ]

# =========================
# MÉTRICA
# =========================

valor_total = df_filtrado["Valor Bruto"].sum()
st.metric("Valor Investido", formatar_real(valor_total))

# =========================
# TABS
# =========================

aba1, aba2, aba3, aba4 = st.tabs(
    ["Posições", "Resumo por Conta", "Mercados", "Vencimentos"]
)

# =========================
# ABA 1 - POSIÇÕES
# =========================

with aba1:

    df_exibir = df_filtrado.copy()

    if "Data" in df_exibir.columns:
        df_exibir["Data"] = pd.to_datetime(
            df_exibir["Data"],
            errors="coerce"
        ).dt.strftime("%d/%m/%Y")

    for col in ["Valor Bruto", "Valor Líquido", "IR", "IOF"]:
        if col in df_exibir.columns:
            df_exibir[col] = df_exibir[col].apply(formatar_real)

    st.dataframe(df_exibir, use_container_width=True, height=600)

    excel = gerar_excel(df_filtrado)

    st.download_button(
        "Baixar Excel",
        data=excel,
        file_name="posicoes_filtradas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        key="download_posicoes"
    )

# =========================
# ABA 2 - RESUMO POR CONTA
# =========================

with aba2:

    df_resumo = df_filtrado.copy()

    resumo = (
        df_resumo
        .groupby(["Conta", "Carteira", "Status", "Observações"])["Valor Bruto"]
        .sum()
        .reset_index()
    )

    caixa_produtos = [
        "BLUEMETRIX RF ATIVO FIRF",
        "BTG Tesouro Selic FIRFRefDI"
    ]

    caixa = (
        df_resumo[df_resumo["Produto"].isin(caixa_produtos)]
        .groupby("Conta")["Valor Bruto"]
        .sum()
        .reset_index(name="Caixa")
    )

    acoes = (
        df_resumo[df_resumo["Sub Mercado"] == "ACAO"]
        .groupby("Conta")["Valor Bruto"]
        .sum()
        .reset_index(name="Ações")
    )

    resumo = resumo.merge(caixa, on="Conta", how="left")
    resumo = resumo.merge(acoes, on="Conta", how="left")
    resumo = resumo.fillna(0)

    resumo_formatado = resumo.copy()

    for col in ["Valor Bruto", "Caixa", "Ações"]:
        resumo_formatado[col] = resumo_formatado[col].apply(formatar_real)

    st.dataframe(resumo_formatado, use_container_width=True)

    excel = gerar_excel(resumo)

    st.download_button(
        "Baixar Excel",
        data=excel,
        file_name="resumo_contas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        key="download_resumo"
    )

# =========================
# ABA 3 - MERCADOS
# =========================

with aba3:

    df_graf = df.copy()

    if carteira:
        df_graf = df_graf[df_graf["Carteira"].isin(carteira)]

    if status:
        df_graf = df_graf[df_graf["Status"].isin(status)]

    mercado_resumo = (
        df_graf
        .groupby("Mercado")["Valor Bruto"]
        .sum()
        .reset_index()
    )

    total = mercado_resumo["Valor Bruto"].sum()

    mercado_resumo["%"] = (
        mercado_resumo["Valor Bruto"] / total * 100
    )

    st.bar_chart(
        mercado_resumo.set_index("Mercado")["Valor Bruto"]
    )

    mercado_formatado = mercado_resumo.copy()

    mercado_formatado["Valor Bruto"] = mercado_formatado["Valor Bruto"].apply(formatar_real)
    mercado_formatado["%"] = mercado_formatado["%"].apply(lambda x: f"{x:.2f}%")

    st.dataframe(mercado_formatado, use_container_width=True)

    excel = gerar_excel(mercado_resumo)

    st.download_button(
        "Baixar Excel",
        data=excel,
        file_name="mercados.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        key="download_mercados"
    )

# =========================
# ABA 4 - VENCIMENTOS
# =========================

with aba4:

    df_venc = df.copy()

    if carteira:
        df_venc = df_venc[df_venc["Carteira"].isin(carteira)]

    if status:
        df_venc = df_venc[df_venc["Status"].isin(status)]

    df_venc["Vencimento"] = pd.to_datetime(
        df_venc["Vencimento"],
        errors="coerce"
    )

    df_venc = df_venc.dropna(subset=["Vencimento"])

    df_venc["Ano-Mês"] = df_venc["Vencimento"].dt.to_period("M").astype(str)

    venc = (
        df_venc
        .groupby("Ano-Mês")["Valor Bruto"]
        .sum()
        .reset_index()
        .sort_values("Ano-Mês")
    )

    total = venc["Valor Bruto"].sum()
    venc["%"] = venc["Valor Bruto"] / total * 100

    st.bar_chart(
        venc.set_index("Ano-Mês")["Valor Bruto"]
    )

    venc_formatado = venc.copy()
    venc_formatado["Valor Bruto"] = venc_formatado["Valor Bruto"].apply(formatar_real)
    venc_formatado["%"] = venc_formatado["%"].apply(lambda x: f"{x:.2f}%")

    st.dataframe(venc_formatado, use_container_width=True)

    excel = gerar_excel(venc)

    st.download_button(
        "Baixar Excel",
        data=excel,
        file_name="vencimentos.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    total = venc["Valor Bruto"].sum()

    venc["%"] = venc["Valor Bruto"] / total * 100

    st.bar_chart(
        venc.set_index("Ano-Mês")["Valor Bruto"]
    )

    st.dataframe(venc, use_container_width=True)

    excel = gerar_excel(venc)

    st.download_button(
        "Baixar Excel",
        data=excel,
        file_name="vencimentos.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        key="download_vencimentos"
    )
