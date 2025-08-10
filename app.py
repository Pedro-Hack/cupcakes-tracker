import streamlit as st
import pandas as pd
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
from datetime import datetime

# =========================
# CONFIGURACIÓN GOOGLE SHEETS
# =========================
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Cargar credenciales desde st.secrets
google_creds = st.secrets["google_credentials"]
creds_dict = dict(google_creds)  # Asegura formato dict
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

# Conectar con Google Sheets
client = gspread.authorize(creds)
sheet = client.open("lista_cupcakes").sheet1

# =========================
# FUNCIONES AUXILIARES
# =========================
def load_data():
    data = sheet.get_all_records()
    return pd.DataFrame(data)

def save_row(row_data):
    sheet.append_row(row_data)

def update_status_range(sabor, estado, desde, hasta):
    data = sheet.get_all_records()
    for i, row in enumerate(data, start=2):  # Empieza en 2 por el encabezado
        if row["Sabor"] == sabor and desde <= row["N°"] <= hasta:
            sheet.update_cell(i, 3, estado)  # Columna 3 = Estado (✅)

# =========================
# INTERFAZ STREAMLIT
# =========================
st.set_page_config(page_title="Cupcakes Tracker", layout="wide")
st.title("📊 Seguimiento de Producción de Cupcakes")

menu = st.sidebar.radio("Menú", ["Ver Producción", "Agregar Producción", "Actualizar Producción"])

# =========================
# SECCIÓN VER PRODUCCIÓN
# =========================
if menu == "Ver Producción":
    df = load_data()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Producción por Sabor")
        sabor_count = df["Sabor"].value_counts().reset_index()
        sabor_count.columns = ["Sabor", "Cantidad"]
        fig1 = px.bar(sabor_count, x="Sabor", y="Cantidad", text="Cantidad", title="Cantidad por Sabor")
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.subheader("Producción por Estado")
        estado_count = df["Estado (✅)"].value_counts().reset_index()
        estado_count.columns = ["Estado", "Cantidad"]
        fig2 = px.pie(estado_count, names="Estado", values="Cantidad", title="Distribución por Estado", hole=0.4)
        st.plotly_chart(fig2, use_container_width=True)

    st.dataframe(df)

# =========================
# SECCIÓN AGREGAR PRODUCCIÓN
# =========================
elif menu == "Agregar Producción":
    st.subheader("Agregar Nueva Producción")
    sabor = st.selectbox("Selecciona el sabor", ["Chocolate", "Vainilla", "Fresa", "Red Velvet"])
    cantidad = st.number_input("Cantidad a agregar", min_value=1, step=1)
    estado_inicial = st.selectbox("Estado inicial", ["Pendiente", "En Producción", "Listo"])
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if st.button("Agregar"):
        df = load_data()
        next_id = max(df["N°"]) + 1 if not df.empty else 1
        for i in range(cantidad):
            save_row([next_id + i, sabor, estado_inicial])
        st.success(f"{cantidad} cupcakes agregados con sabor {sabor}.")

# =========================
# SECCIÓN ACTUALIZAR PRODUCCIÓN
# =========================
elif menu == "Actualizar Producción":
    st.subheader("Actualizar Estado por Rango")
    df = load_data()

    sabor = st.selectbox("Selecciona el sabor a modificar", df["Sabor"].unique())
    desde = st.number_input("Desde ID", min_value=int(df["N°"].min()), max_value=int(df["N°"].max()))
    hasta = st.number_input("Hasta ID", min_value=int(df["N°"].min()), max_value=int(df["N°"].max()), value=int(df["N°"].max()))
    nuevo_estado = st.selectbox("Nuevo Estado", ["Pendiente", "En Producción", "Listo"])

    if st.button("Actualizar Estado"):
        update_status_range(sabor, nuevo_estado, desde, hasta)
        st.success(f"Estados actualizados de {desde} a {hasta} para sabor {sabor}.")









