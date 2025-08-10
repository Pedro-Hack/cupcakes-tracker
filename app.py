import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# ========================
# 1. Configuración
# ========================
st.set_page_config(page_title="Seguimiento de Cupcakes", layout="wide")
st_autorefresh(interval=10_000, key="data_refresh")

# ========================
# 2. Conexión a Google Sheets
# ========================
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open("lista_cupcakes").sheet1

# ========================
# 3. Cargar datos
# ========================
data = sheet.get_all_records()
df = pd.DataFrame(data)

# ========================
# 4. Métricas por estado
# ========================
st.title("🍰 Seguimiento de Producción de Cupcakes")

estados = ["PENDIENTE", "EN EL HORNO", "OK", "DEFECTUOSO"]
colores = {"PENDIENTE": "gray", "EN EL HORNO": "orange", "OK": "green", "DEFECTUOSO": "red"}

cols = st.columns(len(estados))
for i, estado in enumerate(estados):
    cantidad = (df["Estado (✅)"] == estado).sum()
    cols[i].metric(label=estado, value=int(cantidad))

# ========================
# 5. Gráfico de barras agrupado
# ========================
st.subheader("📈 Estado de Producción por Sabor")
df_grouped = df.groupby(["Sabor", "Estado (✅)"]).size().reset_index(name="Cantidad")

fig_bar = px.bar(
    df_grouped,
    x="Sabor",
    y="Cantidad",
    color="Estado (✅)",
    barmode="group",
    title="Producción por Sabor y Estado",
    color_discrete_map=colores
)
st.plotly_chart(fig_bar, use_container_width=True)

# ========================
# 6. Gráfico de pastel
# ========================
st.subheader("🥧 Distribución General de Estados")
df_estado = df["Estado (✅)"].value_counts().reset_index()
df_estado.columns = ["Estado", "Cantidad"]

fig_pie = px.pie(
    df_estado,
    names="Estado",
    values="Cantidad",
    title="Distribución de Estados",
    color="Estado",
    color_discrete_map=colores
)
st.plotly_chart(fig_pie, use_container_width=True)

# ========================
# 7. Formulario para cambiar estado (por sabor + rango)
# ========================
st.subheader("✏️ Actualizar Estado de Cupcakes por Sabor y Rango")

sabores = ["Todos"] + sorted(df["Sabor"].unique())
sabor_seleccionado = st.selectbox("Filtrar por sabor", sabores)

min_id = int(df["N°"].min())
max_id = int(df["N°"].max())

desde = st.number_input("Cupcake N° desde", min_value=min_id, max_value=max_id, value=min_id)
hasta = st.number_input("Cupcake N° hasta", min_value=min_id, max_value=max_id, value=max_id)
nuevo_estado = st.selectbox("Nuevo Estado", estados)

if st.button("Actualizar Estado en Rango"):
    if desde > hasta:
        st.error("❌ El número 'desde' no puede ser mayor que 'hasta'.")
    else:
        # Filtrar por rango
        rango_df = df[(df["N°"] >= desde) & (df["N°"] <= hasta)]
        
        # Filtrar por sabor (si no es "Todos")
        if sabor_seleccionado != "Todos":
            rango_df = rango_df[rango_df["Sabor"] == sabor_seleccionado]
        
        if rango_df.empty:
            st.warning("⚠️ No hay cupcakes que cumplan con esos filtros.")
        else:
            for _, row in rango_df.iterrows():
                cell = sheet.find(str(row["N°"]))
                if cell:
                    sheet.update_cell(cell.row, 3, nuevo_estado)  # Columna 3 = Estado (✅)
            st.success(f"✅ Se actualizaron {len(rango_df)} cupcakes al estado '{nuevo_estado}'")
