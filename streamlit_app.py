import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# CONFIGURAÇÕES DO GOOGLE SHEETS
SHEET_URL = "https://docs.google.com/spreadsheets/d/1CWroXtTSvr_FRt5dDCo-ppoo05xMnCpC3BSc8iYidjo/edit?usp=drive_link"
SCOPE = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

# USANDO ARQUIVO DE CREDENCIAIS JSON
@st.cache_resource
def load_gsheet():
    creds = Credentials.from_service_account_file("credenciais.json", scopes=SCOPE)
    client = gspread.authorize(creds)
    sheet = client.open_by_url(SHEET_URL)
    return sheet

sheet = load_gsheet()
estoque_ws = sheet.worksheet("Estoque")
movimentacao_ws = sheet.worksheet("Movimentacoes")

def load_data():
    estoque = pd.DataFrame(estoque_ws.get_all_records())
    movimentacoes = pd.DataFrame(movimentacao_ws.get_all_records())
    return estoque, movimentacoes

def save_estoque(df):
    estoque_ws.clear()
    estoque_ws.update([df.columns.values.tolist()] + df.values.tolist())

def save_movimentacoes(df):
    movimentacao_ws.clear()
    movimentacao_ws.update([df.columns.values.tolist()] + df.values.tolist())

estoque_df, movimentacoes_df = load_data()

barracas = [
    'Fogaça', 'Cachorro quente', 'Pizza', 'Sopa', 'Milho', 'Churrasco',
    'Doces', 'Pastel', 'Vinho e quentão', 'Bebidas', 'Bingo',
    'Brincadeiras - Boca do palhaço', 'Brincadeiras - Canaleta', 'Brincadeiras - pesca'
]

st.title("📦 Sistema de Controle de Estoque - Quermesse")

menu = st.sidebar.selectbox("Menu", ["Cadastrar Item", "Dar Alta no Estoque", "Dar Baixa no Estoque", "Relatório de Estoque"])

def atualizar_estoque(item, quantidade, tipo, barraca=None):
    global estoque_df, movimentacoes_df
    if item not in estoque_df['Item'].values:
        st.warning("Item não encontrado no estoque.")
        return

    idx = estoque_df[estoque_df['Item'] == item].index[0]
    if tipo == "Alta":
        estoque_df.at[idx, 'Quantidade'] += quantidade
    elif tipo == "Baixa":
        if estoque_df.at[idx, 'Quantidade'] >= quantidade:
            estoque_df.at[idx, 'Quantidade'] -= quantidade
        else:
            st.warning("Quantidade insuficiente no estoque.")
            return

    nova_mov = {
        'Data': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'Item': item,
        'Quantidade': quantidade,
        'Tipo': tipo,
        'Barraca': barraca or ''
    }
    movimentacoes_df = pd.concat([movimentacoes_df, pd.DataFrame([nova_mov])], ignore_index=True)

    save_estoque(estoque_df)
    save_movimentacoes(movimentacoes_df)
    st.success(f"{tipo} registrada com sucesso para {item}")

if menu == "Cadastrar Item":
    st.subheader("➕ Cadastrar Novo Item")
    novo_item = st.text_input("Nome do item")
    unidade = st.text_input("Unidade de medida (ex: Kg, Lata, Unid)")
    if st.button("Cadastrar"):
        if novo_item.strip() == "" or unidade.strip() == "":
            st.warning("Preencha todos os campos.")
        elif novo_item in estoque_df['Item'].values:
            st.warning("Item já existe.")
        else:
            nova_linha = pd.DataFrame([{'Item': novo_item, 'Quantidade': 0, 'Unidade': unidade}])
            estoque_df = pd.concat([estoque_df, nova_linha], ignore_index=True)
            save_estoque(estoque_df)
            st.success("Item cadastrado com sucesso.")

elif menu == "Dar Alta no Estoque":
    st.subheader("⬆️ Dar Alta no Estoque")
    if estoque_df.empty:
        st.info("Nenhum item cadastrado.")
    else:
        item = st.selectbox("Item", estoque_df['Item'])
        qtd = st.number_input("Quantidade a adicionar", min_value=1, step=1)
        if st.button("Registrar Alta"):
            atualizar_estoque(item, qtd, "Alta")

elif menu == "Dar Baixa no Estoque":
    st.subheader("⬇️ Dar Baixa no Estoque")
    if estoque_df.empty:
        st.info("Nenhum item cadastrado.")
    else:
        item = st.selectbox("Item", estoque_df['Item'])
        qtd = st.number_input("Quantidade a dar baixa", min_value=1, step=1)
        barraca = st.selectbox("Barraca", barracas)
        if st.button("Registrar Baixa"):
            atualizar_estoque(item, qtd, "Baixa", barraca)

elif menu == "Relatório de Estoque":
    st.subheader("📊 Relatório Atual do Estoque")
    st.dataframe(estoque_df[['Item', 'Quantidade', 'Unidade']])
    st.download_button("📥 Baixar CSV", estoque_df.to_csv(index=False).encode("utf-8"), file_name="estoque_quermesse.csv", mime="text/csv")

    st.subheader("📜 Histórico de Movimentações")
    st.dataframe(movimentacoes_df)
