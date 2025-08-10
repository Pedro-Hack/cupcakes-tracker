import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# Configuración de página
st.set_page_config(page_title="Cupcakes Tracker", page_icon="🧁", layout="wide")

# -------------------------------
# Conexión con Google Sheets
# -------------------------------
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
client = gspread.authorize(creds)

# Nombre de tu hoja de Google Sheets
SHEET_NAME = "lista_cupcakes"
sheet = client.open(SHEET_NAME).sheet1

# -------------------------------
# Funciones auxiliares
# -------------------------------
def load_data():
    data = sheet.get_all_records()
    return pd.DataFrame(data)

def save_row(row_data):
    sheet.append_row(row_data)

def update_state_range(start_id, end_id, new_state):
    data = load_data()
    for idx in range(len(data)):
        if start_id <= int(data.loc[idx, "ID"]) <= end_id:
            sheet.update_cell(idx + 2, data.columns.get_loc("Estado") + 1, new_state)

# -------------------------------
# Cargar datos
# -------------------------------
df = load_data()

# Asegurarse de que ID sea numérico
df["ID"] = pd.to_numeric(df["ID"], errors="coerce")

# -------------------------------
# Título y descripción
# -------------------------------
st.title("🧁 Cupcakes - Seguimiento de Producción")
st.write("Control en tiempo real — modifica estados, agrega producción y visualiza dashboards.")

# -------------------------------
# KPIs
# -------------------------------
col1, col2, col3, col4 = st.columns(4)
estados = ["PENDIENTE", "EN EL HORNO", "OK", "DEFECTUOSO"]

with col1:
    st.metric("PENDIENTE", int((df["Estado"] == "PENDIENTE").sum()))
with col2:
    st.metric("EN EL HORNO", int((df["Estado"] == "EN EL HORNO").sum()))
with col3:
    st.metric("OK", int((df["Estado"] == "OK").sum()))
with col4:
    st.metric("DEFECTUOSO", int((df["Estado"] == "DEFECTUOSO").sum()))

# -------------------------------
# Gráfico de barras simple y correcto
# -------------------------------
counts = df["Estado"].value_counts().reindex(estados, fill_value=0).reset_index()
counts.columns = ["Estado", "Cantidad"]

fig = px.bar(
    counts,
    x="Cantidad",
    y="Estado",
    color="Estado",
    orientation="h",
    color_discrete_map={
        "PENDIENTE": "#FFD700",
        "EN EL HORNO": "#FF8C00",
        "OK": "#32CD32",
        "DEFECTUOSO": "#FF4500"
    },
    text="Cantidad"
)

fig.update_layout(
    title="Cupcakes por Estado",
    xaxis_title="Cantidad",
    yaxis_title="",
    showlegend=False,
    height=400
)

st.plotly_chart(fig, use_container_width=True)

# -------------------------------
# Formulario para nueva producción
# -------------------------------
st.subheader("➕ Agregar nueva producción")
with st.form("add_production_form"):
    cantidad = st.number_input("Cantidad de cupcakes", min_value=1, value=10)
    estado_inicial = st.selectbox("Estado inicial", estados, index=0)
    submitted = st.form_submit_button("Agregar")
    if submitted:
        next_id = df["ID"].max() + 1 if not df.empty else 1
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for i in range(cantidad):
            save_row([next_id + i, estado_inicial, fecha])
        st.success(f"{cantidad} cupcakes agregados con estado '{estado_inicial}'")
        st.experimental_rerun()

# -------------------------------
# Formulario para cambiar estado por rango
# -------------------------------
st.subheader("✏️ Cambiar estado por rango de IDs")
with st.form("update_state_form"):
    start_id = st.number_input("Desde ID", min_value=1)
    end_id = st.number_input("Hasta ID", min_value=1)
    new_state = st.selectbox("Nuevo estado", estados)
    submitted_update = st.form_submit_button("Actualizar")
    if submitted_update:
        update_state_range(start_id, end_id, new_state)
        st.success(f"Estados actualizados para IDs entre {start_id} y {end_id}")
        st.experimental_rerun()

# -------------------------------
# Mostrar tabla
# -------------------------------
st.subheader("📋 Producción actual")
st.dataframe(df)





