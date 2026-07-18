import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Observatorio de movilidad urbana",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILOS CORPORATIVOS ---
st.markdown("""
<style>
    h1, h2, h3 { font-family: 'Segoe UI', sans-serif; }
    
    .kpi-card {
        background-color: rgba(0, 119, 182, 0.1); 
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-left: 5px solid #48CAE4; 
    }
    .kpi-title {
        font-size: 0.85rem;
        text-transform: uppercase;
        font-weight: 600;
        margin-bottom: 5px;
        opacity: 0.9;
        color: white; 
    }
    .kpi-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: white; 
    }
    .kpi-delta {
        font-size: 0.85rem;
        font-weight: 600;
    }
    .positive-delta { color: #2ECC71; } 
    .negative-delta { color: #FF6B6B; } 
    .neutral-delta { color: #90E0EF; } 
</style>
""", unsafe_allow_html=True)

BLUE_PALETTE = ['#00E5FF', '#48CAE4', '#90E0EF', '#00B4D8', '#0077B6', '#80D8FF']

# --- CARGA DE DATOS ---
@st.cache_data
def load_and_prep_data():
    try:
        conn = sqlite3.connect("movilidad_urbana.db")
        # Cache-buster: recarga forzada tras descargar el clima de los 365 días
        df = pd.read_sql("SELECT * FROM usos_vs_clima", conn)
        conn.close()
        
        if df.empty: return df
            
        df['dia_transporte'] = pd.to_datetime(df['dia_transporte'])
        df['dia_semana'] = df['dia_transporte'].dt.day_name()
        dias_es = {'Monday': '1-Lunes', 'Tuesday': '2-Martes', 'Wednesday': '3-Miércoles',
                   'Thursday': '4-Jueves', 'Friday': '5-Viernes', 'Saturday': '6-Sábado', 'Sunday': '7-Domingo'}
        df['dia_semana_es'] = df['dia_semana'].map(dias_es)
        df['es_finde'] = df['dia_semana'].isin(['Saturday', 'Sunday'])
        
        df = df[~df['tipo_transporte'].str.contains('Lancha', case=False, na=False)]
        # Limpieza de nombres de provincias rotos (Encoding) usando Regex para evitar problemas de mayúsculas/minúsculas
        df['provincia'] = df['provincia'].str.replace(r'.*Aut.*Buenos.*', 'Buenos Aires', regex=True, case=False)
        df['provincia'] = df['provincia'].str.replace(r'C\.a\.b\.a.*', 'Buenos Aires', regex=True, case=False)
        df['provincia'] = df['provincia'].str.replace(r'^CABA$', 'Buenos Aires', regex=True, case=False)
        df['provincia'] = df['provincia'].str.replace(r'.*Entre R.*', 'Entre Ríos', regex=True, case=False)
        df['provincia'] = df['provincia'].str.replace(r'.*R.*o N.*', 'Río Negro', regex=True, case=False)
        df['provincia'] = df['provincia'].str.replace(r'.*Neuqu.*', 'Neuquén', regex=True, case=False)
        df['provincia'] = df['provincia'].str.replace(r'Tucuman', 'Tucumán', regex=True, case=False)
        df['provincia'] = df['provincia'].str.replace(r'Cordoba', 'Córdoba', regex=True, case=False)
        
        # Al analizar las empresas operadoras (Emova/Subte, Trenes Argentinos, DOTA), los datos "Jn" o faltantes pertenecen al AMBA
        df['provincia'] = df['provincia'].str.replace(r'Jn', 'Buenos Aires', regex=True, case=False)
        df['provincia'] = df['provincia'].str.replace(r'Desconocida', 'Buenos Aires', regex=True, case=False)
        df['provincia'] = df['provincia'].str.replace(r'Sin Datos de Provincia', 'Buenos Aires', regex=True, case=False)
        
        # Análisis de los datos revela que el 100% de la jurisdicción faltante pertenece a Emova (Subte), por ende es jurisdicción CABA
        df['jurisdiccion'] = df['jurisdiccion'].fillna('CABA').astype(str)
        df['jurisdiccion'] = df['jurisdiccion'].str.replace(r'C\.a\.b\.a.*', 'CABA', regex=True, case=False)
        df['jurisdiccion'] = df['jurisdiccion'].str.replace(r'Desconocida', 'CABA', regex=True, case=False)
        df['jurisdiccion'] = df['jurisdiccion'].str.replace(r'Sin Datos de Jurisdicción', 'CABA', regex=True, case=False)
        df['jurisdiccion'] = df['jurisdiccion'].apply(lambda x: 'CABA' if x.upper() == 'CABA' else x.title())
        
        df['tipo_transporte'] = df['tipo_transporte'].str.capitalize()
        df['linea'] = df['linea'].astype(str).str.replace('BSAS_LINEA_', '', case=False)
        df['municipio'] = df['municipio'].str.title()
        
        # Arreglo de encoding (caracteres mal formados)
        df['nombre_empresa'] = df['nombre_empresa'].astype(str)
        df['nombre_empresa'] = df['nombre_empresa'].str.replace('ï¿½', 'ñ', regex=False)
        df['nombre_empresa'] = df['nombre_empresa'].str.replace(r'ñ+', 'ñ', regex=True) # Limpia eñes duplicadas
        df['nombre_empresa'] = df['nombre_empresa'].str.title()
        
        return df
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()

df_raw = load_and_prep_data()
if df_raw.empty: st.stop()

# --- BARRA LATERAL ---
st.sidebar.title("Panel de control")
min_date, max_date = df_raw['dia_transporte'].min().date(), df_raw['dia_transporte'].max().date()
date_range = st.sidebar.date_input("Periodo de análisis", (min_date, max_date), min_value=min_date, max_value=max_date)

if len(date_range) == 2:
    start_date, end_date = date_range
    df = df_raw[(df_raw['dia_transporte'].dt.date >= start_date) & (df_raw['dia_transporte'].dt.date <= end_date)]
else:
    df = df_raw.copy()

if 'provincia' in df.columns:
    provincias = ["Todas"] + sorted(df['provincia'].unique().tolist())
    selected_prov = st.sidebar.selectbox("Provincia geográfica", provincias)
    if selected_prov != "Todas": df = df[df['provincia'] == selected_prov]

if 'selected_prov' in locals() and selected_prov == "Buenos Aires":
    jurisdicciones = ["Todas"] + sorted(df['jurisdiccion'].unique().tolist())
    selected_jur = st.sidebar.selectbox("Jurisdicción administrativa", jurisdicciones)
    if selected_jur != "Todas": df = df[df['jurisdiccion'] == selected_jur]


# --- HEADER ---
st.title("Dashboard analítico de movilidad urbana")
st.markdown("Plataforma de business intelligence para la monitorización de flujos de transporte terrestre.")
st.markdown("---")


# --- KPIs ---
daily_totals = df.groupby('dia_transporte').agg(
    pasajeros=('cantidad', 'sum'), lluvia=('precipitacion_total', 'mean'), temp_max=('temp_max', 'mean')
).reset_index()

# 1. Resiliencia Lluvia
d_lluvia = daily_totals[daily_totals['lluvia'] > 0]['pasajeros'].mean()
d_seco = daily_totals[daily_totals['lluvia'] == 0]['pasajeros'].mean()
imp_lluvia = ((d_lluvia - d_seco) / d_seco) * 100 if pd.notna(d_lluvia) and d_seco > 0 else 0

# 2. Resiliencia Calor (Umbral dinámico: si no hay > 30, usamos el percentil 80 de los datos)
umbral_calor = 30.0 if daily_totals['temp_max'].max() > 30 else daily_totals['temp_max'].quantile(0.8)
d_calor = daily_totals[daily_totals['temp_max'] >= umbral_calor]['pasajeros'].mean()
d_fresco = daily_totals[daily_totals['temp_max'] < umbral_calor]['pasajeros'].mean()
imp_calor = ((d_calor - d_fresco) / d_fresco) * 100 if pd.notna(d_calor) and d_fresco > 0 else 0

# 3. Fin de Semana
daily_wknd = df.groupby(['dia_transporte', 'es_finde'])['cantidad'].sum().reset_index()
p_lab = daily_wknd[~daily_wknd['es_finde']]['cantidad'].mean()
p_fin = daily_wknd[daily_wknd['es_finde']]['cantidad'].mean()
imp_finde = ((p_fin - p_lab) / p_lab) * 100 if pd.notna(p_fin) and p_lab > 0 else 0

# 4. Top Empresa
if not df.empty:
    top_empresa = df.groupby('nombre_empresa')['cantidad'].sum().idxmax()
    pasajeros_top = df.groupby('nombre_empresa')['cantidad'].sum().max()
else:
    top_empresa = "Sin Datos"
    pasajeros_top = 0


# RENDER KPIs
c1, c2, c3, c4 = st.columns(4)
def render_kpi(col, title, value, delta_text, d_type="neutral"):
    cls = "positive-delta" if d_type=="pos" else "negative-delta" if d_type=="neg" else "neutral-delta"
    # Agregamos font-size más chico y line-height ajustado para que nombres muy largos puedan hacer wrap sin romper la tarjeta
    col.markdown(f'<div class="kpi-card"><div class="kpi-title">{title}</div><div class="kpi-value" style="font-size: 1.3rem; line-height: 1.2;">{value}</div><div class="kpi-delta {cls}">{delta_text}</div></div>', unsafe_allow_html=True)

render_kpi(c1, "Impacto lluvias", f"{d_lluvia if pd.notna(d_lluvia) else 0:,.0f} pas/día".replace(",", "."), f"{imp_lluvia:+.1f}% vs secos", "neg" if imp_lluvia < 0 else "pos")
render_kpi(c2, f"Impacto calor (≥{umbral_calor:.0f}°C)", f"{d_calor if pd.notna(d_calor) else 0:,.0f} pas/día".replace(",", "."), f"{imp_calor:+.1f}% vs templados", "neg" if imp_calor < 0 else "pos")
render_kpi(c3, "Fin de semana", f"{p_fin if pd.notna(p_fin) else 0:,.0f} pas/día".replace(",", "."), f"{imp_finde:+.1f}% vs laborales", "neg" if imp_finde < 0 else "pos")
cuota = (pasajeros_top / df['cantidad'].sum()) * 100 if df['cantidad'].sum() > 0 else 0
render_kpi(c4, "Empresa líder", str(top_empresa), f"{cuota:.1f}% cuota de mercado", "neutral")


# --- SERIE DE TIEMPO (FULL WIDTH) ---
st.markdown("<br><hr><br>", unsafe_allow_html=True)
st.subheader("Evolución temporal de la demanda")
st.markdown("Media móvil de 7 días aplicada para apreciar la tendencia excluyendo la caída de los fines de semana.")

df_ts = df.groupby(['dia_transporte', 'tipo_transporte'])['cantidad'].sum().reset_index()
df_ts.sort_values('dia_transporte', inplace=True)
df_ts['tendencia'] = df_ts.groupby('tipo_transporte')['cantidad'].transform(lambda x: x.rolling(7, min_periods=1).mean())

fig_ts = px.line(
    df_ts, x="dia_transporte", y="tendencia", color="tipo_transporte", 
    color_discrete_sequence=BLUE_PALETTE, 
    labels={"dia_transporte": "Fecha", "tendencia": "Pasajeros (Media 7 días)", "tipo_transporte": "Modo"}
)
fig_ts.update_traces(fill='tozeroy', fillcolor='rgba(0, 180, 216, 0.05)', line=dict(width=3))

fig_ts.update_layout(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", 
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    hovermode="x unified"
)
fig_ts.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128, 128, 128, 0.2)')
fig_ts.update_xaxes(showgrid=False)
st.plotly_chart(fig_ts, use_container_width=True)


# --- BLOQUE SECUNDARIO (2 COLS) ---
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Resiliencia climática (lluvias)")
    df_clima = df.copy()
    df_clima['Clima'] = np.where(df_clima['precipitacion_total'] > 0, 'Lluvia', 'Seco')
    fig_imp = px.bar(df_clima.groupby(['tipo_transporte', 'Clima'])['cantidad'].mean().reset_index(),
                     x="tipo_transporte", y="cantidad", color="Clima", barmode="group", text_auto=".2s",
                     color_discrete_map={"Seco": "#48CAE4", "Lluvia": "#023E8A"})
    fig_imp.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", legend_title_text=None)
    st.plotly_chart(fig_imp, use_container_width=True)

with col_b:
    st.subheader("Mapa de concentración semanal")
    st.markdown("Volumen **promedio** de pasajeros por cada día de la semana.")
    # 1. Agrupamos por fecha exacta para tener el total diario por medio de transporte
    df_daily = df.groupby(['dia_transporte', 'dia_semana_es', 'tipo_transporte'])['cantidad'].sum().reset_index()
    # 2. Calculamos el promedio de esos días (Ej: Promedio de todos los martes)
    df_heat = df_daily.groupby(['dia_semana_es', 'tipo_transporte'])['cantidad'].mean().reset_index()
    
    hp = df_heat.pivot(index='tipo_transporte', columns='dia_semana_es', values='cantidad').fillna(0)
    fig_heat = go.Figure(data=go.Heatmap(z=hp.values, x=[d.split('-')[1] for d in hp.columns], y=hp.index,
                                         colorscale='Blues', text=hp.values, texttemplate="%{text:.2s}"))
    fig_heat.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_heat, use_container_width=True)


# --- BLOQUE TERCIARIO (FULL WIDTH) ---
st.markdown("<br>", unsafe_allow_html=True)
st.subheader("Cuota de mercado por empresa (top 10)")
st.markdown("Volumen de pasajeros gestionados por las principales empresas concesionarias.")

df_emp = df.groupby('nombre_empresa')['cantidad'].sum().sort_values(ascending=False).nlargest(10).reset_index()
df_emp = df_emp.sort_values(by="cantidad", ascending=True) # Sort ascending for horizontal bar chart

fig_emp = px.bar(
    df_emp, x="cantidad", y="nombre_empresa", orientation='h', text_auto=".3s",
    color="cantidad", color_continuous_scale="Blues",
    labels={"cantidad": "Pasajeros Movilizados", "nombre_empresa": "Empresa"}
)
fig_emp.update_traces(textposition="outside")
fig_emp.update_layout(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    coloraxis_showscale=False,
    height=400
)
fig_emp.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128, 128, 128, 0.2)')
fig_emp.update_yaxes(showgrid=False)
st.plotly_chart(fig_emp, use_container_width=True)
