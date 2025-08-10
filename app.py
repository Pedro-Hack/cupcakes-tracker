# app.py - Aplicación completa para seguimiento y control de producción de cupcakes
import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# =========================
# Config
# =========================
st.set_page_config(page_title="Cupcakes - Producción", layout="wide")
# auto-refresh (10s)
st_autorefresh(interval=10_000, key="auto_refresh")

# Scope Google
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
SHEET_NAME = "lista_cupcakes"  # Cambia si tu hoja tiene otro nombre
COL_N = "N°"
COL_SABOR = "Sabor"
COL_ESTADO_RAW = "Estado (✅)"  # nombre tal cual en la hoja

# =========================
# Autenticación (local o nube)
# =========================
def get_gspread_client():
    if os.path.exists("credentials.json"):
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", SCOPE)
    else:
        # usar st.secrets: debe existir el bloque "gcp_service_account" (ver instrucciones)
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), SCOPE)
    return gspread.authorize(creds)

# conectar
try:
    client = get_gspread_client()
    sheet = client.open(SHEET_NAME).sheet1
except Exception as e:
    st.error("❌ Error conectando a Google Sheets. Revisa credentials y el nombre de la hoja.")
    st.exception(e)
    st.stop()

# =========================
# Cargar datos
# =========================
def load_df():
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    # si la hoja está vacía o tiene otro formato, detener
    if df.empty and len(data) == 0:
        st.warning("La hoja está vacía. Agrega datos o usa la función 'Agregar producción'.")
        return df
    # Renombrar columna de estado a 'Estado' para trabajar más cómodo
    if COL_ESTADO_RAW in df.columns:
        df = df.rename(columns={COL_ESTADO_RAW: "Estado"})
    elif "Estado" not in df.columns:
        # no se encontró la columna de estado esperada
        st.error(f"No se encontró la columna '{COL_ESTADO_RAW}' ni 'Estado' en la hoja.")
    return df

df = load_df()

# Si df vacío por error, igual dejamos seguir para permitir agregar producción
if df.empty:
    # crear columnas esperadas si no existen (solo para UI)
    df = pd.DataFrame(columns=[COL_N, COL_SABOR, "Estado"])

# =========================
# Utilidades
# =========================
def find_cell_by_N(n_value):
    """Busca la celda donde aparece el número N° (busca como string). Retorna cell o None."""
    try:
        cell = sheet.find(str(int(n_value)))
        return cell
    except Exception:
        return None

def update_estado_by_row(cell_row, col_name, nuevo_estado):
    """Actualiza la celda de la columna col_name en la fila cell_row (fila en hoja)."""
    # averiguar índice de columna en la hoja según df.columns
    # construir encabezados desde sheet.row_values(1)
    headers = sheet.row_values(1)
    try:
        col_index = headers.index(col_name) + 1
    except ValueError:
        # si no existe, intentar usar raw name
        if col_name == "Estado":
            try:
                col_index = headers.index(COL_ESTADO_RAW) + 1
            except ValueError:
                # como fallback usar columna 3
                col_index = 3
        else:
            col_index = 3
    sheet.update_cell(cell_row, col_index, nuevo_estado)

def append_new_cupcake(n_value, sabor, estado="PENDIENTE"):
    """Agrega una fila nueva al final con N°, Sabor, Estado (usa order de la hoja actual)."""
    # obtener headers actuales para respetar orden
    headers = sheet.row_values(1)
    # construir fila en el orden de headers
    row = []
    for h in headers:
        if h == COL_N:
            row.append(str(n_value))
        elif h == COL_SABOR:
            row.append(sabor)
        elif h == COL_ESTADO_RAW:
            row.append(estado)
        elif h == "Estado":  # en caso la hoja tenga 'Estado' en vez de 'Estado (✅)'
            row.append(estado)
        else:
            row.append("")  # columna extra vacía
    sheet.append_row(row, value_input_option="USER_ENTERED")

# =========================
# Interfaz superior: métricas rápidas
# =========================
st.title("🧁 Cupcakes - Seguimiento de Producción")
st.markdown("Control en tiempo real — modifica estados, agrega producción y visualiza dashboards.")

# recargar df actual antes de mostrar métricas
df = load_df()

# Asegurar columna 'Estado' presente
if "Estado" not in df.columns and COL_ESTADO_RAW in df.columns:
    df = df.rename(columns={COL_ESTADO_RAW: "Estado"})

# definir estados ordenados
estados_possible = ["PENDIENTE", "EN EL HORNO", "OK", "DEFECTUOSO"]
colores_estado = {
    "PENDIENTE": "#FFCC00",
    "EN EL HORNO": "#FF6600",
    "OK": "#33CC33",
    "DEFECTUOSO": "#FF3333"
}

# Mostrar métricas (barra superior)
counts = {s: int((df["Estado"] == s).sum()) if "Estado" in df.columns else 0 for s in estados_possible}
cols = st.columns(len(estados_possible))
for i, s in enumerate(estados_possible):
    cols[i].metric(label=s, value=counts[s])

st.markdown("---")

# =========================
# Gráfico 1: Cupcakes por Estado (barra horizontal)
# =========================
df_estado = pd.DataFrame({"Estado": estados_possible})
if "Estado" in df.columns:
    vc = df["Estado"].value_counts()
    df_estado["Cantidad"] = df_estado["Estado"].map(lambda x: int(vc.get(x, 0)))
else:
    df_estado["Cantidad"] = 0

fig_estado = px.bar(
    df_estado,
    x="Cantidad",
    y="Estado",
    orientation="h",
    color="Estado",
    color_discrete_map=colores_estado,
    category_orders={"Estado": estados_possible},
    title="📦 Cupcakes por Estado"
)
fig_estado.update_traces(text=df_estado["Cantidad"], textposition="outside")
fig_estado.update_layout(xaxis_title="Cantidad", yaxis_title="", height=380)
st.plotly_chart(fig_estado, use_container_width=True)

# =========================
# Gráfico 2: Producción por Sabor (ordenado)
# =========================
if COL_SABOR in df.columns:
    df_sabor = df.groupby(COL_SABOR)[COL_N].count().reset_index()
    df_sabor.columns = ["Sabor", "Cantidad"]
    df_sabor = df_sabor.sort_values("Cantidad", ascending=False)
else:
    df_sabor = pd.DataFrame(columns=["Sabor", "Cantidad"])

fig_sabor = px.bar(
    df_sabor,
    x="Sabor",
    y="Cantidad",
    color="Sabor",
    text="Cantidad",
    title="🍰 Producción por Sabor"
)
fig_sabor.update_traces(textposition="outside")
fig_sabor.update_layout(xaxis_title="Sabor", yaxis_title="Cantidad", height=420)
st.plotly_chart(fig_sabor, use_container_width=True)

st.markdown("---")

# =========================
# Panel izquierdo: tabla y filtros
# =========================
left, right = st.columns([2, 1])

with left:
    st.subheader("📋 Producción (detalle)")
    # filtros interactivos
    sabores_list = sorted(df[COL_SABOR].unique().tolist()) if COL_SABOR in df.columns else []
    filtro_sabor = st.multiselect("Filtrar por sabor", options=["Todos"] + sabores_list, default=["Todos"])
    filtro_estado = st.multiselect("Filtrar por estado", options=["Todos"] + estados_possible, default=["Todos"])

    df_view = df.copy()
    if "Todos" not in filtro_sabor:
        df_view = df_view[df_view[COL_SABOR].isin(filtro_sabor)]
    if "Todos" not in filtro_estado:
        df_view = df_view[df_view["Estado"].isin(filtro_estado)]
    st.dataframe(df_view, use_container_width=True, height=400)

with right:
    st.subheader("🔧 Acciones rápidas")

    # === Actualizar estado por sabor + rango ===
    st.markdown("**Actualizar estado (por sabor + rango)**")
    sabores_opts = ["Todos"] + (sorted(df[COL_SABOR].unique()) if COL_SABOR in df.columns else [])
    sabor_sel = st.selectbox("Sabor (aplicar a)", sabores_opts)
    min_id = int(df[COL_N].min()) if not df.empty else 1
    max_id = int(df[COL_N].max()) if not df.empty else 1
    desde = st.number_input("Desde (N°)", min_value=min_id, max_value=max_id, value=min_id, step=1)
    hasta = st.number_input("Hasta (N°)", min_value=min_id, max_value=max_id, value=max_id, step=1)
    nuevo_estado = st.selectbox("Nuevo estado", estados_possible)
    if st.button("Actualizar estado en rango"):
        if desde > hasta:
            st.error("El número 'Desde' no puede ser mayor que 'Hasta'.")
        else:
            rango_df = df[(df[COL_N] >= desde) & (df[COL_N] <= hasta)]
            if sabor_sel != "Todos":
                rango_df = rango_df[rango_df[COL_SABOR] == sabor_sel]
            if rango_df.empty:
                st.warning("No se encontraron cupcakes con esos filtros.")
            else:
                updated = 0
                for _, row in rango_df.iterrows():
                    cell = find_cell_by_N(row[COL_N])
                    if cell:
                        update_estado_by_row(cell.row, "Estado", nuevo_estado)
                        updated += 1
                st.success(f"Se actualizaron {updated} cupcakes a '{nuevo_estado}'.")
                # recargar df
                df = load_df()

    st.markdown("---")

    # === Agregar producción por lote ===
    st.markdown("**Agregar producción (lote)**")
    nuevo_sabor = st.selectbox("Sabor a agregar", options=(sorted(df[COL_SABOR].unique()) if COL_SABOR in df.columns else ["Chocolate", "Limón con amapola"]))
    cantidad_nueva = st.number_input("Cantidad a agregar", min_value=1, max_value=5000, value=10, step=1)
    estado_inicial = st.selectbox("Estado inicial", options=estados_possible, index=0)
    if st.button("Agregar lote"):
        # calcular próximo N°
        prox = int(df[COL_N].max()) + 1 if not df.empty else 1
        added = 0
        for i in range(cantidad_nueva):
            append_new_cupcake(prox + i, nuevo_sabor, estado_inicial)
            added += 1
        st.success(f"Se agregaron {added} cupcakes de '{nuevo_sabor}' (N° {prox} a {prox + added - 1}).")
        df = load_df()

    st.markdown("---")

    # === Actualizar un solo cupcake por N° (opcional) ===
    st.markdown("**Actualizar un N° específico**")
    if not df.empty:
        id_list = sorted(df[COL_N].tolist())
    else:
        id_list = []
    id_sel = st.number_input("N°", min_value=(min(id_list) if id_list else 1), max_value=(max(id_list) if id_list else 1), value=(min(id_list) if id_list else 1), step=1)
    estado_unico = st.selectbox("Nuevo estado (único)", options=estados_possible, key="estado_unico")
    if st.button("Actualizar N° seleccionado"):
        cell = find_cell_by_N(id_sel)
        if cell:
            update_estado_by_row(cell.row, "Estado", estado_unico)
            st.success(f"Se actualizó N° {id_sel} → {estado_unico}")
            df = load_df()
        else:
            st.error("No se encontró el N° en la hoja.")

st.markdown("---")
st.caption("App conectada a Google Sheets. Si subes a Streamlit Cloud usa st.secrets para las credenciales.")




