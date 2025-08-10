import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Producción Cupcakes", layout="wide")

# --- CONEXIÓN GOOGLE SHEETS ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Obtenemos las credenciales directamente del secrets
google_creds_dict = st.secrets["google_credentials"]

creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds_dict, scope)
client = gspread.authorize(creds)

# Nombre de la hoja de Google Sheets
SHEET_NAME = "Produccion"
sheet = client.open(lista_cupcakes).sheet1

# --- FUNCIONES ---
def load_data():
    data = sheet.get_all_records()
    return pd.DataFrame(data)

def update_production(sabor, estado_origen, estado_destino, cantidad):
    df = load_data()
    indices = df[(df["Sabor"] == sabor) & (df["Estado (✅)"] == estado_origen)].index
    if len(indices) < cantidad:
        st.error("No hay suficientes registros para mover.")
        return

    for i in indices[:cantidad]:
        sheet.update_cell(i + 2, df.columns.get_loc("Estado (✅)") + 1, estado_destino)
    st.success(f"Se movieron {cantidad} '{sabor}' de '{estado_origen}' a '{estado_destino}'.")

# --- UI ---
st.title("📦 Seguimiento de Producción de Cupcakes")

df = load_data()

# --- CONTADORES ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("En Producción", df[df["Estado (✅)"] == "Producción"].shape[0])
with col2:
    st.metric("En Decorado", df[df["Estado (✅)"] == "Decorado"].shape[0])
with col3:
    st.metric("Listos", df[df["Estado (✅)"] == "Listo"].shape[0])

st.divider()

# --- SECCIÓN ACTUALIZAR PRODUCCIÓN ---
st.subheader("🔄 Actualizar Producción")

col_a, col_b, col_c, col_d = st.columns(4)

sabores = sorted(df["Sabor"].unique())
estados = df["Estado (✅)"].unique()

with col_a:
    sabor_sel = st.selectbox("Sabor", sabores)
with col_b:
    estado_origen = st.selectbox("Desde", estados)
with col_c:
    estado_destino = st.selectbox("Hasta", estados)
with col_d:
    cantidad = st.number_input("Cantidad a mover", min_value=1, step=1)

if st.button("Mover producción"):
    update_production(sabor_sel, estado_origen, estado_destino, cantidad)

st.divider()

# --- VISTA TABLA ---
st.subheader("📋 Datos de Producción")
st.dataframe(df, use_container_width=True)









