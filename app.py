import streamlit as st
import pandas as pd
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

st.set_page_config(page_title="Producción Cupcakes", page_icon="🧁", layout="wide")

# ==============================
# AUTENTICACIÓN GOOGLE SHEETS
# ==============================
google_creds_json = st.secrets["google_credentials"]
google_creds_dict = json.loads(google_creds_json)

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds_dict, scope)
client = gspread.authorize(creds)

# Abrir hoja de cálculo
SPREADSHEET_NAME = "Cupcakes Produccion"
WORKSHEET_NAME = "Produccion"
sheet = client.open(lista_cupcakes).worksheet(WORKSHEET_NAME)

# ==============================
# FUNCIONES
# ==============================
def cargar_datos():
    data = sheet.get_all_records()
    return pd.DataFrame(data)

def guardar_fila(fila):
    sheet.append_row(fila)

def actualizar_estado(sabor, fecha_inicio, fecha_fin, nuevo_estado):
    df = cargar_datos()
    df['Fecha'] = pd.to_datetime(df['Fecha'], format="%Y-%m-%d")
    mask = (df['Sabor'] == sabor) & (df['Fecha'] >= fecha_inicio) & (df['Fecha'] <= fecha_fin)
    indices = df[mask].index

    if len(indices) == 0:
        st.warning("No se encontraron registros para actualizar.")
        return

    for idx in indices:
        cell = sheet.find(str(df.at[idx, 'ID']))
        sheet.update_cell(cell.row, df.columns.get_loc("Estado") + 1, nuevo_estado)

    st.success(f"Se actualizaron {len(indices)} registros a '{nuevo_estado}'.")

# ==============================
# INTERFAZ
# ==============================
st.title("🧁 Seguimiento Producción de Cupcakes")

# Cargar datos
df = cargar_datos()

# Contadores
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("En Producción", len(df[df["Estado"] == "Producción"]))
with col2:
    st.metric("Listos", len(df[df["Estado"] == "Listo"]))
with col3:
    st.metric("Entregados", len(df[df["Estado"] == "Entregado"]))

st.markdown("---")

# ==============================
# SECCIÓN: ACTUALIZAR PRODUCCIÓN
# ==============================
st.header("📦 Actualizar Producción")

sabores = df["Sabor"].unique()
sabor_sel = st.selectbox("Selecciona el sabor", sabores)

fecha_inicio = st.date_input("Desde", datetime.now())
fecha_fin = st.date_input("Hasta", datetime.now())

nuevo_estado = st.selectbox("Nuevo estado", ["Producción", "Listo", "Entregado"])

if st.button("Actualizar"):
    actualizar_estado(sabor_sel, pd.to_datetime(fecha_inicio), pd.to_datetime(fecha_fin), nuevo_estado)

st.markdown("---")

# ==============================
# TABLA DE REGISTROS
# ==============================
st.subheader("📋 Registros de Producción")
st.dataframe(df, use_container_width=True)







