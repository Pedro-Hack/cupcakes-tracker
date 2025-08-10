import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
import pandas as pd
import plotly.express as px

# Alcance de Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Detectar si estamos en local o en Streamlit Cloud
if os.path.exists("credentials.json"):
    # Modo local
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
else:
    # Modo nube
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)

# Conexión a Google Sheets
client = gspread.authorize(creds)
sheet = client.open("lista_cupcakes").sheet1

# Cargar datos en DataFrame
data = sheet.get_all_records()
df = pd.DataFrame(data)

# Contadores por estado
estado_counts = df["Estado (✅)"].value_counts().to_dict()

# Mostrar métricas
st.subheader("📊 Estado de Producción")
cols = st.columns(len(estado_counts))
for i, (estado, cantidad) in enumerate(estado_counts.items()):
    cols[i].metric(estado, cantidad)

# Gráfico por sabor
fig = px.bar(
    df.groupby("Sabor")["N°"].count().reset_index(),
    x="Sabor",
    y="N°",
    color="Sabor",
    title="Producción por Sabor"
)
st.plotly_chart(fig, use_container_width=True)

# Formulario para actualizar estado por rango
st.subheader("✏️ Actualizar Estados por Rango")
with st.form("update_form"):
    desde = st.number_input("Desde (N°)", min_value=1, step=1)
    hasta = st.number_input("Hasta (N°)", min_value=1, step=1)
    nuevo_estado = st.selectbox("Nuevo Estado", ["EN EL HORNO", "PENDIENTE", "OK", "DEFECTUOSO"])
    submit = st.form_submit_button("Actualizar")

    if submit:
        for i in range(len(df)):
            if desde <= df.loc[i, "N°"] <= hasta:
                sheet.update_cell(i + 2, df.columns.get_loc("Estado (✅)") + 1, nuevo_estado)
        st.success(f"Estados actualizados de {desde} a {hasta} → {nuevo_estado}")


