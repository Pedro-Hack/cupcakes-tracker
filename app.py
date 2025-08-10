import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px

# ========================
# CARGAR CREDENCIALES DESDE SECRETS
# ========================
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Cargar desde secrets
creds_dict = st.secrets["gcp_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

sheet = client.open("Cupcakes Produccion").sheet1

# ========================
# FUNCIONES AUXILIARES
# ========================
def load_data():
    data = sheet.get_all_records()
    return pd.DataFrame(data)

def save_row(row_data):
    sheet.append_row(row_data)

def update_state_by_range(sabor, desde, hasta, nuevo_estado):
    df = load_data()
    for index, row in df.iterrows():
        if row["Sabor"] == sabor and desde <= row["N°"] <= hasta:
            cell = sheet.find(str(row["N°"]))
            sheet.update_cell(cell.row, 3, nuevo_estado)  # Columna 3 = Estado (✅)

# ========================
# APP STREAMLIT
# ========================
st.set_page_config(page_title="Control Producción Cupcakes", layout="wide")
st.title("📦 Control Producción Cupcakes")

menu = st.sidebar.radio("Menú", ["📊 Dashboard", "➕ Agregar Producción", "✏️ Actualizar Producción"])

# ========================
# DASHBOARD
# ========================
if menu == "📊 Dashboard":
    df = load_data()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Producción por Sabor")
        fig_sabor = px.histogram(df, x="Sabor", color="Sabor", text_auto=True)
        st.plotly_chart(fig_sabor, use_container_width=True)

    with col2:
        st.subheader("Producción por Estado")
        fig_estado = px.histogram(df, x="Estado (✅)", color="Estado (✅)", text_auto=True)
        st.plotly_chart(fig_estado, use_container_width=True)

    st.subheader("Datos completos")
    st.dataframe(df)

# ========================
# AGREGAR PRODUCCIÓN
# ========================
elif menu == "➕ Agregar Producción":
    df = load_data()
    next_id = df["N°"].max() + 1 if not df.empty else 1

    sabor = st.selectbox("Sabor", ["Vainilla", "Chocolate", "Fresa", "Red Velvet"])
    cantidad = st.number_input("Cantidad", min_value=1, step=1)
    estado_inicial = st.selectbox("Estado inicial", ["PENDIENTE", "EN PROCESO", "TERMINADO"])

    if st.button("Agregar Producción"):
        for i in range(cantidad):
            save_row([next_id + i, sabor, estado_inicial])
        st.success(f"{cantidad} registros agregados correctamente.")

# ========================
# ACTUALIZAR PRODUCCIÓN
# ========================
elif menu == "✏️ Actualizar Producción":
    df = load_data()
    sabor_sel = st.selectbox("Seleccionar Sabor", df["Sabor"].unique())
    desde = st.number_input("Desde N°", min_value=int(df["N°"].min()), step=1)
    hasta = st.number_input("Hasta N°", min_value=int(df["N°"].min()), step=1)
    nuevo_estado = st.selectbox("Nuevo Estado", ["PENDIENTE", "EN PROCESO", "TERMINADO"])

    if st.button("Actualizar Estado"):
        update_state_by_range(sabor_sel, desde, hasta, nuevo_estado)
        st.success(f"Estados actualizados para {sabor_sel} del N° {desde} al {hasta}")







