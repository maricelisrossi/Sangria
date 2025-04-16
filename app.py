
import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
from openpyxl import load_workbook

st.set_page_config(page_title="Processador de Sangria", layout="centered")
st.title("📊 Processador de Sangria")

uploaded_file = st.file_uploader("Envie seu arquivo Excel (.xlsx ou .xlsm)", type=["xlsx", "xlsm"])

if uploaded_file:
    df_dados = pd.read_excel(uploaded_file, sheet_name="Sheet")

    st.subheader("Prévia dos dados da aba 'Sheet'")
    st.dataframe(df_dados.head())

    if st.button("Processar Sangria"):
        st.info("🔄 Processando arquivo... Aguarde...")
        df = df_dados.copy()
        df["Loja"] = np.nan
        df["Data"] = np.nan
        df["Funcionário"] = np.nan

        data_atual = None
        funcionario_atual = None
        loja_atual = None
        linhas_validas = []

        for i, row in df.iterrows():
            valor = str(row["Hora"]).strip()
            if valor.startswith("Loja:"):
                loja = valor.split("Loja:")[1].split("(Total")[0].strip()
                if "-" in loja:
                    loja = loja.split("-", 1)[1].strip()
                loja_atual = loja or "Loja nao cadastrada"
            elif valor.startswith("Data:"):
                try:
                    data_atual = pd.to_datetime(valor.split("Data:")[1].split("(Total")[0].strip(), dayfirst=True)
                except:
                    data_atual = pd.NaT
            elif valor.startswith("Funcionário:"):
                funcionario_atual = valor.split("Funcionário:")[1].split("(Total")[0].strip()
            else:
                if pd.notna(row["Valor(R$)"]) and pd.notna(row["Hora"]):
                    df.at[i, "Data"] = data_atual
                    df.at[i, "Funcionário"] = funcionario_atual
                    df.at[i, "Loja"] = loja_atual
                    linhas_validas.append(i)

        df = df.loc[linhas_validas].copy()
        df.ffill(inplace=True)

        df["Descrição"] = df["Descrição"].astype(str).str.strip().str.lower()
        df["Funcionário"] = df["Funcionário"].astype(str).str.strip()
        df["Valor(R$)"] = pd.to_numeric(df["Valor(R$)"], errors="coerce")

        dias_semana = {
            0: 'segunda-feira',
            1: 'terça-feira',
            2: 'quarta-feira',
            3: 'quinta-feira',
            4: 'sexta-feira',
            5: 'sábado',
            6: 'domingo'
        }
        df["Dia da Semana"] = df["Data"].dt.dayofweek.map(dias_semana)

        df["Mês"] = df["Data"].dt.month.map({
            1: 'jan', 2: 'fev', 3: 'mar', 4: 'abr',
            5: 'mai', 6: 'jun', 7: 'jul', 8: 'ago',
            9: 'set', 10: 'out', 11: 'nov', 12: 'dez'
        })
        df["Ano"] = df["Data"].dt.year

        df_final = df[[
            "Data", "Dia da Semana", "Loja",
            "Funcionário", "Hora", "Descrição", "Meio de recebimento", "Valor(R$)", "Mês", "Ano"
        ]].copy()

        df_final["Data"] = pd.to_datetime(df_final["Data"], errors="coerce").dt.strftime("%d/%m/%Y")

        periodo_min = pd.to_datetime(df_final["Data"], dayfirst=True, errors="coerce").min().strftime("%d/%m/%Y")
        periodo_max = pd.to_datetime(df_final["Data"], dayfirst=True, errors="coerce").max().strftime("%d/%m/%Y")
        valor_total = df_final["Valor(R$)"].sum()

        st.subheader("📅 Período e Valor Processado")
        st.markdown(f"**Período:** {periodo_min} até {periodo_max}")
        st.markdown(f"**Valor Total:** R$ {valor_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        st.subheader("🔍 Tabela final antes de exportar")
        st.dataframe(df_final.head(30))

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_final.to_excel(writer, index=False, sheet_name="Sangria")
        output.seek(0)

        st.download_button("📥 Baixar resultado", data=output, file_name="Sangria_estruturada.xlsx")
