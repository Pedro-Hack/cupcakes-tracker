import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# ===== CONFIGURACIÓN GOOGLE SHEETS =====
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# Nombre de tu hoja de cálculo
sheet = client.open("lista_cupcakes").sheet1

# ===== FUNCIONES =====
def load_data():
    data = sheet.get_all_records()
    return pd.DataFrame(data)

def save_row(row_data):
    sheet.append_row(row_data)

def update_rows(sabor, nuevo_estado, desde_id, hasta_id):
    records = sheet.get_all_records()
    for idx, row in enumerate(records, start=2):  # empieza en 2 porque la fila 1 es encabezado
        if row["Sabor"] == sabor and desde_id <= row["N°"] <= hasta_id:
            sheet.update_cell(idx, 3, nuevo_estado)  # col 3 = Estado (✅)

# ===== INTERFAZ =====
st.sidebar.title("Menú")
menu = st.sidebar.radio("Selecciona una opción", ["📊 Dashboard", "➕ Agregar Producción", "✏️ Actualizar Producción"])

df = load_data()

# ===== DASHBOARD =====
if menu == "📊 Dashboard":
    st.title("📦 Control Producción Cupcakes")

    # ---- MÉTRICAS RÁPIDAS ----
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total producidos", len(df))
    col2.metric("✅ OK", df[df["Estado (✅)"] == "OK"].shape[0])
    col3.metric("🔥 En el horno", df[df["Estado (✅)"] == "EN EL HORNO"].shape[0])
    col4.metric("❌ Defectuosos", df[df["Estado (✅)"] == "DEFECTUOSO"].shape[0])

    st.markdown("---")

    # ---- PRODUCCIÓN POR SABOR ----
    df_sabor = df.groupby("Sabor").size().reset_index(name="Cantidad").sort_values(by="Sabor")
    fig_sabor = px.bar(
        df_sabor, x="Sabor", y="Cantidad", color="Sabor", text="Cantidad",
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig_sabor.update_traces(textposition="outside")
    fig_sabor.update_layout(title="Producción por Sabor", yaxis_title="Cantidad", xaxis_title="Sabor", showlegend=False)

    # ---- PRODUCCIÓN POR ESTADO ----
    estado_order = ["OK", "EN EL HORNO", "DEFECTUOSO"]
    colores_estado = {"OK": "#28a745", "EN EL HORNO": "#fd7e14", "DEFECTUOSO": "#dc3545"}

    df_estado = df.groupby("Estado (✅)").size().reset_index(name="Cantidad")
    df_estado["Estado (✅)"] = pd.Categorical(df_estado["Estado (✅)"], categories=estado_order, ordered=True)
    df_estado = df_estado.sort_values("Estado (✅)")

    fig_estado = px.bar(
        df_estado, x="Estado (✅)", y="Cantidad", color="Estado (✅)", text="Cantidad",
        color_discrete_map=colores_estado
    )
    fig_estado.update_traces(textposition="outside")
    fig_estado.update_layout(title="Producción por Estado", yaxis_title="Cantidad", xaxis_title="Estado", showlegend=True)

    # ---- PIE CHART ----
    fig_pie = px.pie(
        df_estado, names="Estado (✅)", values="Cantidad", color="Estado (✅)",
        color_discrete_map=colores_estado, hole=0.4
    )
    fig_pie.update_traces(textinfo="label+percent", pull=[0.05, 0.05, 0.1])
    fig_pie.update_layout(title="Distribución por Estado")

    col_a, col_b = st.columns(2)
    col_a.plotly_chart(fig_sabor, use_container_width=True)
    col_b.plotly_chart(fig_estado, use_container_width=True)
    st.plotly_chart(fig_pie, use_container_width=True)

# ===== AGREGAR PRODUCCIÓN =====
elif menu == "➕ Agregar Producción":
    st.subheader("➕ Agregar nueva producción")
    sabor = st.selectbox("Sabor", ["Chocolate", "Limón con amapola", "Vainilla"])
    cantidad = st.number_input("Cantidad a agregar", min_value=1, step=1)
    estado_inicial = st.selectbox("Estado inicial", ["OK", "EN EL HORNO", "DEFECTUOSO"])

    if st.button("Guardar producción"):
        next_id = df["N°"].max() + 1 if not df.empty else 1
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for i in range(cantidad):
            save_row([next_id + i, sabor, estado_inicial, fecha])
        st.success(f"✅ Se agregaron {cantidad} cupcakes de {sabor} con estado {estado_inicial}")

# ===== ACTUALIZAR PRODUCCIÓN =====
elif menu == "✏️ Actualizar Producción":
    st.subheader("✏️ Actualizar producción existente")
    sabor = st.selectbox("Selecciona el sabor", df["Sabor"].unique())
    nuevo_estado = st.selectbox("Nuevo estado", ["OK", "EN EL HORNO", "DEFECTUOSO"])
    desde_id = st.number_input("Desde N°", min_value=int(df["N°"].min()), max_value=int(df["N°"].max()))
    hasta_id = st.number_input("Hasta N°", min_value=int(df["N°"].min()), max_value=int(df["N°"].max()))

    if st.button("Actualizar estado"):
        update_rows(sabor, nuevo_estado, desde_id, hasta_id)
        st.success(f"✅ Estado actualizado a {nuevo_estado} para {sabor} del N° {desde_id} al N° {hasta_id}")









