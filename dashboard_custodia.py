
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime
from dotenv import load_dotenv
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import tempfile

from header_component import header_dashboard
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import plotly.express as px


# -------------------
# Configuración inicial
# -------------------
st.set_page_config(page_title="Custodia de Vehículos FGN", layout="wide")

# Encabezado con logo y título
header_dashboard()
st.title("🚗 Alerta Vehículos con más de 180 días de custodia - Patio Único de Caldas")

# -------------------
# Cargar credenciales desde .env
# -------------------
load_dotenv()
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
SMTP_SERVER = os.getenv("SMTP_SERVER")
smtp_port_env = os.getenv("SMTP_PORT")
try:
    SMTP_PORT = int(smtp_port_env) if smtp_port_env is not None else 587
except ValueError:
    SMTP_PORT = 587

# -------------------
# Cargar datos
# -------------------
@st.cache_data
def load_data():
    df = pd.read_csv("data/VEHICULOS EN PATIO.csv")   ### 🔹 Archivo real que cargas
    
    # Convertir fechas (asegurando formato día/mes/año si aplica)
    df["FECHA ENTRADA"] = pd.to_datetime(df["FECHA ENTRADA"], errors="coerce", dayfirst=True)  ### 🔹 Conversión segura
    
    # 🔹 Eliminar columna vieja si viene en el archivo
    if "TIEMPO_CUSTODIA(DIAS)" in df.columns:
        df = df.drop(columns=["TIEMPO_CUSTODIA(DIAS)"])
    
    # 🔹 Calcular días en custodia dinámicamente
    hoy = datetime.today()
    df["TIEMPO_CUSTODIA(DIAS)"] = (hoy - df["FECHA ENTRADA"]).dt.days
    # 🔹 Forzar columna a tipo numérico para evitar errores posteriores
    df["TIEMPO_CUSTODIA(DIAS)"] = pd.to_numeric(df["TIEMPO_CUSTODIA(DIAS)"], errors="coerce")
    return df

df = load_data()

# -------------------
# Parámetro de alerta
# -------------------
DIAS_ALERTA = 180

# -------------------
# Tarjetas resumen por SECCIONAL
# -------------------
resumen = df.groupby("SECCIONAL").agg(
    TOTAL_VEHICULOS=("CODIGO UNICO", "count"),
    VEHICULOS_ALERTA=("TIEMPO_CUSTODIA(DIAS)", lambda x: (x.astype(float) > DIAS_ALERTA).sum())
).reset_index()

# CSS para tarjetas interactivas
st.markdown("""
    <style>
    div.stButton > button {
        background-color: #003366;
        color: white;
        border: none;
        padding: 20px;
        border-radius: 15px;
        width: 100%;
        height: 140px;
        text-align: center;
        font-size: 18px;
        font-weight: bold;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.25);
        transition: transform 0.2s, background-color 0.3s;
    }
    div.stButton > button:hover {
        transform: scale(1.05);
        background-color: #0055A4;
    }
    </style>
""", unsafe_allow_html=True)

cols = st.columns(len(resumen))
for idx, row in resumen.iterrows():
    with cols[idx]:
        if st.button(
            f"🏢 {row['SECCIONAL']}\n\n🚗 {row['TOTAL_VEHICULOS']} vehículos\n⚠️ {row['VEHICULOS_ALERTA']} en alerta",
            key=f"btn_{row['SECCIONAL']}"
        ):
            st.session_state["seccional_seleccionada"] = row["SECCIONAL"]

st.markdown("<div style='margin: 40px 0; border-top: 2px solid #e0e0e0;'></div>", unsafe_allow_html=True)

# -------------------
# Tarjetas resumen por REGIONALSECCIONAL
# -------------------
st.subheader("📌 Resumen por Dirección Seccional")

resumen_dep = df.groupby("REGIONALSECCIONAL").agg(
    TOTAL_VEHICULOS=("NRO PROCESO", "count"),
    VEHICULOS_ALERTA=("TIEMPO CUSTODIA(dias)", lambda x: (pd.to_numeric(x, errors='coerce') > DIAS_ALERTA).sum())
).reset_index()

cols = st.columns(len(resumen_dep))
for idx, row in resumen_dep.iterrows():
    with cols[idx]:
        if st.button(
            f"🏢 {row['REGIONALSECCIONAL']}\n\n🚗 {row['TOTAL_VEHICULOS']} vehículos\n⚠️ {row['VEHICULOS_ALERTA']} en alerta",
            key=f"btn_dep_{row['REGIONALSECCIONAL']}"
        ):
            st.session_state["dependencia_seleccionada"] = row["REGIONALSECCIONAL"]

st.markdown("<div style='margin: 40px 0; border-top: 2px solid #e0e0e0;'></div>", unsafe_allow_html=True)

# -------------------
# Filtros
# -------------------
dependencia = st.selectbox("Selecciona Dependencia", ["Todos"] + sorted(df["REGIONALSECCIONAL"].dropna().unique().tolist()))
responsable = st.selectbox("Selecciona Responsable", ["Todos"] + sorted(df["NOMBRE RESP"].dropna().unique().tolist()))
nro_proceso = st.text_input("Filtrar por Nro Proceso")

df_filtrado = df.copy()
if dependencia != "Todos":
    df_filtrado = df_filtrado[df_filtrado["REGIONALSECCIONAL"] == dependencia]
if responsable != "Todos":
    df_filtrado = df_filtrado[df_filtrado["NOMBRE RESP"] == responsable]
if nro_proceso:
    df_filtrado = df_filtrado[df_filtrado["NRO PROCESO"].astype(str).str.contains(nro_proceso, case=False)]

# -------------------
# Tabla de alertas con AgGrid
# -------------------
df_alerta = df_filtrado[pd.to_numeric(df_filtrado["TIEMPO CUSTODIA(dias)"], errors="coerce") > DIAS_ALERTA]
df_alerta.columns = [col.strip() for col in df_alerta.columns]

columnas_alerta = [
    "NRO PROCESO",
    "PLACA SIAF",
    "CLASE",
    "PLACA",
    "NUMERO MOTOR",
    "CHASIS",
    "FECHA ENTRADA",
    "TIEMPO CUSTODIA(dias)"
]
columnas_presentes = [col for col in columnas_alerta if col in df_alerta.columns]
df_alerta = df_alerta[columnas_presentes]
# Eliminar columnas duplicadas por nombre
df_alerta = df_alerta.loc[:,~df_alerta.columns.duplicated()]

st.subheader(f"📊 Vehículos en custodia más de {DIAS_ALERTA} días")
with st.expander("Ver detalles de vehículos en alerta"):
    gb = GridOptionsBuilder.from_dataframe(df_alerta)
    gb.configure_pagination(paginationAutoPageSize=True)
    gb.configure_side_bar()
    gb.configure_default_column(filter=True, sortable=True, resizable=True, editable=False)
    grid_options = gb.build()

    AgGrid(
        df_alerta,
        gridOptions=grid_options,
        enable_enterprise_modules=True,
        theme="alpine",
        height=400,
        fit_columns_on_grid_load=True,
        update_mode=GridUpdateMode.NO_UPDATE
    )



# -------------------
# Gráficos en pestañas
# -------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Custodia vs Alerta",
    "📈 Evolución de ingresos",
    "🔥 Concentración por Dependencia",
    "🏢 Vehículos por Bodega"
])

# Gráfico 1
with tab1:
    df_count = df_filtrado.groupby("REGIONALSECCIONAL").size().reset_index(name="Cantidad Vehículos")  # ✅ CAMBIO

    fig1 = px.bar(
        df_count,
        x="REGIONALSECCIONAL",
        y="Cantidad Vehículos",  # ✅ CAMBIO
        title="🚗 Vehículos por REGIONAL-SECCIONAL",
        text="Cantidad Vehículos",  # ✅ CAMBIO
        color="Cantidad Vehículos",  # ✅ CAMBIO
        color_continuous_scale="Blues"
    )
    fig1.update_traces(textposition="outside")
    st.plotly_chart(fig1, use_container_width=True)


# Gráfico 2
with tab2:
    df_plot = df_filtrado.copy()
    df_plot["FECHA ENTRADA"] = pd.to_datetime(df_plot["FECHA ENTRADA"])

    # ======================
    # 🔹 Gráfico anual
    # ======================
    df_plot["Año"] = df_plot["FECHA ENTRADA"].dt.year
    df_count_anual = df_plot.groupby("Año").size().reset_index(name="Cantidad Vehículos")

    fig2_anual = px.line(
        df_count_anual,
        x="Año",
        y="Cantidad Vehículos",
        markers=True,
        title="📈 Ingresos de vehículos por año con tendencia"
    )

    # Agregar línea de tendencia
    fig2_anual.add_traces(px.scatter(df_count_anual, x="Año", y="Cantidad Vehículos", trendline="ols").data[1])

    fig2_anual.update_layout(
        xaxis_title="Año",
        yaxis_title="Cantidad de Vehículos",
        legend_title=None
    )

    # ======================
    # 🔹 Gráfico mensual
    # ======================

with tab2:
    df_plot = df_filtrado.copy()
    df_plot["FECHA ENTRADA"] = pd.to_datetime(df_plot["FECHA ENTRADA"])
    df_plot["Mes"] = df_plot["FECHA ENTRADA"].dt.to_period("M").astype(str)

    df_count = df_plot.groupby("Mes").size().reset_index(name="Cantidad")

    fig2 = px.line(
        df_count,
        x="Mes",
        y="Cantidad",
        markers=True,
        title="📈 Evolución mensual de ingresos de vehículos"
    )

    fig2.update_layout(
        xaxis_title="Mes",
        yaxis_title="Cantidad de Vehículos",
        legend_title=None,
        yaxis=dict(dtick=10, range=[0, 100])  # 👉 Escala de 0 a 100, en pasos de 10
)

 
    # ======================
    # 🔹 Mostrar gráficos
    # ======================
    st.plotly_chart(fig2_anual, use_container_width=True)
    st.plotly_chart(fig2, use_container_width=True)
    


# Gráfico 3
with tab3:
    df_count_dep = df_filtrado.groupby("REGIONALSECCIONAL").size().reset_index(name="Cantidad Vehículos")  # ✅ CAMBIO

    fig3 = px.bar(
        df_count_dep,
        x="REGIONALSECCIONAL",
        y="Cantidad Vehículos",  # ✅ CAMBIO
        title="🏢 Vehículos por Dependencia",
        text="Cantidad Vehículos",  # ✅ CAMBIO
        color="Cantidad Vehículos",  # ✅ CAMBIO
        color_continuous_scale="Tealgrn"
    )
    fig3.update_traces(textposition="outside")
    st.plotly_chart(fig3, use_container_width=True)


# Gráfico 4
with tab4:
    df_plot = df_filtrado.copy()
    df_plot["Alerta"] = df_plot["TIEMPO_CUSTODIA(DIAS)"].apply(lambda x: "🔴 +180 días" if x > 180 else "🟢 <=180 días")
    df_count_bodega = df_plot.groupby(["PROCEDENCIA ", "Alerta"]).size().reset_index(name="Cantidad Vehículos")  # ✅ CAMBIO
    fig4 = px.bar(
        df_count_bodega,
        x="PROCEDENCIA ",
        y="Cantidad Vehículos",  # ✅ CAMBIO
        color="Alerta",
        barmode="group",
        title="📦 Vehículos por Procedencia y estado de custodia"
    )
    st.plotly_chart(fig4, use_container_width=True)


# -------------------
# Botón para descargar Excel
# -------------------
def to_excel(df):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        df.to_excel(tmp.name, index=False)
        return tmp.name

if not df_alerta.empty:
    excel_path = to_excel(df_alerta)
    with open(excel_path, "rb") as f:
        st.download_button(
            label="⬇️ Descargar Excel de Vehículos en Alerta",
            data=f,
            file_name="vehiculos_alerta.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

