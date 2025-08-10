import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# -------------------------
# CONFIGURACIÓN DE GOOGLE SHEETS
# -------------------------
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

google_creds = {
    "type": st.secrets["type"],
    "project_id": st.secrets["project_id"],
    "private_key_id": st.secrets["private_key_id"],
    "private_key": st.secrets["private_key"],
    "client_email": st.secrets["client_email"],
    "client_id": st.secrets["client_id"],
    "auth_uri": st.secrets["auth_uri"],
    "token_uri": st.secrets["token_uri"],
    "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
    "client_x509_cert_url": st.secrets["client_x509_cert_url"]
}

creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds, scope)
client = gspread.authorize(creds)
sheet = client.open("lista_cupcakes").sheet1

# -------------------------
# LECTURA DE DATOS
# -------------------------
def load_data():
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    return df

# -------------------------
# FUNCIÓN PARA ACTUALIZAR RANGO
# -------------------------
def update_range(sabor, desde, hasta, nuevo_estado):
    df = load_data()
    for i in range(len(df)):
        if df.loc[i, "Sabor"] == sabor and desde <= df.loc[i, "N°"] <= hasta:
            sheet.update_cell(i + 2, df.columns.get_loc("Estado (✅)") + 1, nuevo_estado)

# -------------------------
# DISEÑO PRINCIPAL
# -------------------------
st.set_page_config(page_title="Producción Cupcakes", layout="wide")
st.title("📊 Seguimiento de Producción de Cupcakes")

df = load_data()

# -------------------------
# CONTADORES
# -------------------------
col1, col2, col3, col4 = st.columns(4)

estado_counts = df["Estado (✅)"].value_counts()

col1.metric("Pendiente 🟡", estado_counts.get("Pendiente", 0))
col2.metric("En proceso 🔵", estado_counts.get("En proceso", 0))
col3.metric("Entregado 🟢", estado_counts.get("Entregado", 0))
col4.metric("Cancelado 🔴", estado_counts.get("Cancelado", 0))

st.divider()

# -------------------------
# SECCIÓN PARA ACTUALIZAR PRODUCCIÓN
# -------------------------
st.subheader("✏️ Actualizar Producción")

sabores = df["Sabor"].unique().tolist()
sabor_sel = st.selectbox("Selecciona un sabor", sabores)
desde = st.number_input("Desde N°", min_value=int(df["N°"].min()), max_value=int(df["N°"].max()), step=1)
hasta = st.number_input("Hasta N°", min_value=int(df["N°"].min()), max_value=int(df["N°"].max()), step=1)

nuevo_estado = st.selectbox("Nuevo Estado", ["Pendiente", "En proceso", "Entregado", "Cancelado"])

if st.button("Actualizar"):
    update_range(sabor_sel, desde, hasta, nuevo_estado)
    st.success(f"Producción de {sabor_sel} actualizada de {desde} a {hasta} → {nuevo_estado}")

st.divider()

# -------------------------
# MOSTRAR TABLA
# -------------------------
st.subheader("📋 Datos de Producción")
st.dataframe(df, use_container_width=True)









