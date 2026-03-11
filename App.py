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

# =========================
# COLUNAS CONTROLE
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

# =========================
# MERGE
# =========================

df = posicao.merge(
    controle,
    on="Conta",
    how="left"
)

df["Carteira"] = df["Carteira"].astype(str).str.strip()
df["Status"] = df["Status"].astype(str).str.strip()
df["Observações"] = df["Observações"].astype(str).str.strip()

# =========================
# SIDEBAR FILTROS
# =========================

st.sidebar.header("Filtros")

contas = st.sidebar.multiselect(
    "Conta",
    sorted(df["Conta"].dropna().unique())
)

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

observacoes = st.sidebar.multiselect(
    "Observações",
    sorted(df["Observações"].dropna().unique())
)

somente_sem_obs = st.sidebar.checkbox(
    "Mostrar apenas contas sem observações"
)

# =========================
# ABAS
# =========================

aba1, aba2 = st.tabs(["Posições", "Resumo por Conta"])

# =========================
# ABA 1
# =========================

with aba1:

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

    valor_total = df_filtrado["Valor Bruto"].sum()

    valor_total_formatado = (
        f"R$ {valor_total:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )

    st.metric(
        "Valor Investido",
        valor_total_formatado
    )

    df_download = df_filtrado.copy()

    if "Data" in df_filtrado.columns:
        df_filtrado["Data"] = pd.to_datetime(
            df_filtrado["Data"],
            errors="coerce"
        ).dt.strftime("%d/%m/%Y")

    def formatar_real(valor):
        if pd.isna(valor):
            return ""
        return (
            f"R$ {valor:,.2f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

    colunas_reais = [
        "Valor Bruto",
        "Valor Líquido",
        "IR",
        "IOF"
    ]

    for col in colunas_reais:
        if col in df_filtrado.columns:
            df_filtrado[col] = df_filtrado[col].apply(formatar_real)

    st.dataframe(
        df_filtrado,
        use_container_width=True,
        height=600
    )

    def gerar_excel(df):

        output = BytesIO()

        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Dados")

        output.seek(0)

        return output


    excel_file = gerar_excel(df_download)

    st.download_button(
        label="Baixar Excel",
        data=excel_file,
        file_name="posicoes_filtradas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# =========================
# ABA 2 - RESUMO
# =========================

with aba2:

    st.subheader("Resumo por Conta")

    df_resumo = df.copy()

    if carteira:
        df_resumo = df_resumo[df_resumo["Carteira"].isin(carteira)]

    if status:
        df_resumo = df_resumo[df_resumo["Status"].isin(status)]

    # informações da conta
    info_conta = (
        df_resumo[["Conta", "Carteira", "Status", "Observações"]]
        .drop_duplicates()
    )

    total_conta = (
        df_resumo
        .groupby("Conta")["Valor Bruto"]
        .sum()
        .reset_index(name="Valor Bruto Total")
    )

    produtos_caixa = [
        "BLUEMETRIX RF ATIVO FIRF",
        "BTG Tesouro Selic FIRFRefDI"
    ]

    caixa = (
        df_resumo[df_resumo["Produto"].isin(produtos_caixa)]
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

    resumo = total_conta.merge(caixa, on="Conta", how="left")
    resumo = resumo.merge(acoes, on="Conta", how="left")
    resumo = resumo.merge(info_conta, on="Conta", how="left")

    resumo = resumo.fillna(0)

    resumo = resumo[
        [
            "Conta",
            "Carteira",
            "Status",
            "Observações",
            "Valor Bruto Total",
            "Caixa",
            "Ações"
        ]
    ]

    def formatar_real(valor):
        return (
            f"R$ {valor:,.2f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

    resumo_formatado = resumo.copy()

    for col in ["Valor Bruto Total", "Caixa", "Ações"]:
        resumo_formatado[col] = resumo_formatado[col].apply(formatar_real)

    st.dataframe(
        resumo_formatado,
        use_container_width=True,
        height=600
    )

    def gerar_excel_resumo(df):

        output = BytesIO()

        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Resumo")

        output.seek(0)

        return output


    excel_resumo = gerar_excel_resumo(resumo)

    st.download_button(
        label="Baixar Excel do Resumo",
        data=excel_resumo,
        file_name="resumo_por_conta.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
