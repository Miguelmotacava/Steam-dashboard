import streamlit as st
import pandas as pd
import requests
import time
import os
import plotly.express as px
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 1. Configuración inicial
st.set_page_config(page_title="Steam Analytics Dashboard", layout="wide")
load_dotenv()
STEAM_API_KEY = os.getenv("STEAM_API_KEY")

# --- VARIABLES DE DISEÑO (ROJO STREAMLIT) ---
RED_BASE = '#FF4B4B' 
RED_SCALE = 'Reds'
RED_DONUT = {'Windows': '#FF4B4B', 'MacOS': '#FF8080', 'Linux': '#FFB3B3'}
PLOT_TEMPLATE = "plotly_white"

# 2. Función de Extracción de Juegos (Pestaña 1)
@st.cache_data(ttl=3600, show_spinner=False)
def load_steam_data(limite):
    url_top = f"https://api.steampowered.com/ISteamChartsService/GetGamesByConcurrentPlayers/v1/?key={STEAM_API_KEY}"
    res_top = requests.get(url_top).json()
    top_juegos = res_top.get('response', {}).get('ranks', [])[:limite]
    
    df_jugadores = pd.DataFrame(top_juegos)
    df_jugadores.rename(columns={'concurrent_in_game': 'jugadores_actuales'}, inplace=True)
    
    datos_tienda = []
    progress_text = f"⏳ Descargando datos de {limite} juegos..."
    my_bar = st.progress(0, text=progress_text)
    
    for i, appid in enumerate(df_jugadores['appid']):
        url_store = f"https://store.steampowered.com/api/appdetails?appids={appid}&cc=es"
        res_store = requests.get(url_store).json()
        if res_store and str(appid) in res_store and res_store[str(appid)].get('success'):
            data = res_store[str(appid)]['data']
            datos_tienda.append({
                'appid': appid, 'nombre': data.get('name', 'Desconocido'),
                'es_gratis': data.get('is_free', False),
                'precio_eur': data.get('price_overview', {}).get('final', 0) / 100 if not data.get('is_free', False) else 0.0,
                'metacritic_nota': data.get('metacritic', {}).get('score', None),
                'windows': data.get('platforms', {}).get('windows', False),
                'mac': data.get('platforms', {}).get('mac', False),
                'linux': data.get('platforms', {}).get('linux', False),
                'generos': ", ".join([g['description'] for g in data.get('genres', [])])
            })
        time.sleep(1.2)
        my_bar.progress((i + 1) / len(df_jugadores), text=progress_text)
    my_bar.empty()
    return pd.merge(pd.DataFrame(datos_tienda), df_jugadores, on='appid', how='inner')

# 3. Función de Extracción de Noticias (Pestaña 2)
@st.cache_data(ttl=600, show_spinner=False)
def load_news_data(appid):
    url_news = f"https://api.steampowered.com/ISteamNews/GetNewsForApp/v0002/?appid={appid}&count=100&format=json"
    res_news = requests.get(url_news).json()
    noticias = res_news.get('appnews', {}).get('newsitems', [])
    df_noticias = pd.DataFrame(noticias)
    if not df_noticias.empty:
        df_noticias['fecha_dt'] = pd.to_datetime(df_noticias['date'], unit='s')
    return df_noticias

# ==========================================
# INTERFAZ PRINCIPAL
# ==========================================
st.title("🎮 Dashboard de Análisis de Steam")
st.markdown("### Configuración de Análisis")
num_juegos = st.slider("🎯 Selecciona el número de juegos del Top a analizar:", 10, 100, 50, 10)
st.markdown("---")

df_super = load_steam_data(num_juegos)

tab1, tab2, tab3 = st.tabs(["📈 Tendencias", "📰 Noticias", "👤 Jugador"])

# ==========================================
# PESTAÑA 1: TENDENCIAS (Plotly)
# ==========================================
with tab1:
    st.header(f"📈 Tendencias Actuales en el Top {num_juegos}")
    
    # --- CAPTURAR CLICS (FILTROS CRUZADOS) ---
    filtro_treemap = None
    if "treemap_chart" in st.session_state:
        puntos = st.session_state["treemap_chart"].get("selection", {}).get("points", [])
        if puntos: filtro_treemap = puntos[0].get("label")

    filtro_donut = None
    if "donut_chart" in st.session_state:
        puntos = st.session_state["donut_chart"].get("selection", {}).get("points", [])
        if puntos: filtro_donut = puntos[0].get("label")

    filtro_barras = None
    if "bar_chart" in st.session_state:
        puntos = st.session_state["bar_chart"].get("selection", {}).get("points", [])
        if puntos: filtro_barras = puntos[0].get("y")

    # --- FILTROS MANUALES SUPERIORES ---
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1: juegos_sel = st.multiselect("🎮 Filtrar por Videojuego", options=df_super['nombre'].unique())
    with col_f2: plat_sel = st.selectbox("💻 Filtrar por Plataforma", ["Todas", "Windows", "MacOS", "Linux"])
    with col_f3:
        todos_gen = set()
        for gen in df_super['generos'].dropna(): todos_gen.update(gen.split(', '))
        gen_sel = st.selectbox("🎭 Filtrar por Género", ["Todos"] + sorted(list(todos_gen)))

    # --- APLICAR TODOS LOS FILTROS ---
    df_filtrado = df_super.copy()
    
    if juegos_sel: df_filtrado = df_filtrado[df_filtrado['nombre'].isin(juegos_sel)]
    if plat_sel != "Todas": df_filtrado = df_filtrado[df_filtrado[plat_sel.lower()] == True]
    if gen_sel != "Todos": df_filtrado = df_filtrado[df_filtrado['generos'].str.contains(gen_sel, na=False)]
    if filtro_treemap: df_filtrado = df_filtrado[df_filtrado['generos'].str.contains(filtro_treemap, na=False)]
    if filtro_donut: df_filtrado = df_filtrado[df_filtrado[filtro_donut.lower()] == True]
    if filtro_barras: df_filtrado = df_filtrado[df_filtrado['nombre'] == filtro_barras]

    if filtro_treemap or filtro_donut or filtro_barras:
        st.success("🖱️ **Filtro cruzado activo.** (Haz doble clic en el gráfico para limpiar la selección)")

    st.markdown("---")

    if not df_filtrado.empty:
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("👥 Jugadores Totales", f"{int(df_filtrado['jugadores_actuales'].sum()):,}".replace(',', '.'))
        kpi2.metric("🕹️ Juegos", len(df_filtrado))
        kpi3.metric("💸 Precio Medio", f"{df_filtrado[df_filtrado['precio_eur']>0]['precio_eur'].mean():.2f} €" if not df_filtrado[df_filtrado['precio_eur']>0].empty else "0.00 €")
        kpi4.metric("🎁 Juegos Gratuitos", int(df_filtrado['es_gratis'].sum()))

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            df_plot1 = df_filtrado.nlargest(10, 'jugadores_actuales').sort_values('jugadores_actuales')
            fig1 = px.bar(df_plot1, x='jugadores_actuales', y='nombre', orientation='h', title='🏆 Top 10 Juegos (¡Pincha una barra!)', color_discrete_sequence=[RED_BASE])
            st.plotly_chart(fig1, use_container_width=True, on_select="rerun", selection_mode="points", key="bar_chart")
        
        with col_g2:
            df_gen = df_filtrado.assign(genero=df_filtrado['generos'].str.split(', ')).explode('genero')
            df_g = df_gen.groupby('genero')['jugadores_actuales'].sum().reset_index()
            fig2 = px.treemap(df_g[df_g['jugadores_actuales']>0], path=['genero'], values='jugadores_actuales', title='🎭 Jugadores por Género (¡Pincha una caja!)', color='jugadores_actuales', color_continuous_scale=RED_SCALE)
            st.plotly_chart(fig2, use_container_width=True, on_select="rerun", selection_mode="points", key="treemap_chart")

        col_g3, col_g4 = st.columns(2)
        with col_g3:
            df_os = pd.DataFrame([('Windows', df_filtrado['windows'].sum()), ('MacOS', df_filtrado['mac'].sum()), ('Linux', df_filtrado['linux'].sum())], columns=['SO', 'Compatibles'])
            fig3 = px.pie(df_os, names='SO', values='Compatibles', hole=0.5, title='🖥️ Compatibilidad SO (¡Pincha un sector!)', color='SO', color_discrete_map=RED_DONUT)
            st.plotly_chart(fig3, use_container_width=True, on_select="rerun", selection_mode="points", key="donut_chart")
        
        with col_g4:
            df_scat = df_filtrado[df_filtrado['metacritic_nota'].notna()]
            if not df_scat.empty:
                fig4 = px.scatter(df_scat, x='precio_eur', y='metacritic_nota', size='jugadores_actuales', hover_name='nombre', title='💎 Precio vs Crítica', color='nombre')
                st.plotly_chart(fig4, use_container_width=True)

# ==========================================
# PESTAÑA 2: NOTICIAS (Bokeh)
# ==========================================
with tab2:
    st.header("📰 Radar de Noticias Oficiales")
    if not df_super.empty:
        col_n1, col_n2 = st.columns([2, 1])
        with col_n1:
            juego_elegido = st.selectbox("🕹️ Selecciona un juego para analizar sus noticias:", df_super['nombre'].unique())
            appid_elegido = df_super[df_super['nombre'] == juego_elegido]['appid'].iloc[0]
        with col_n2:
            filtro_tiempo = st.radio("⏱️ Rango temporal:", ["Último Día", "Última Semana", "Último Mes", "Todo (100 últ.)"], index=2)

        df_news = load_news_data(appid_elegido)
        if not df_news.empty:
            hoy = pd.Timestamp.now()
            if filtro_tiempo == "Último Día": df_n_filtro = df_news[df_news['fecha_dt'] >= (hoy - pd.Timedelta(days=1))]
            elif filtro_tiempo == "Última Semana": df_n_filtro = df_news[df_news['fecha_dt'] >= (hoy - pd.Timedelta(days=7))]
            elif filtro_tiempo == "Último Mes": df_n_filtro = df_news[df_news['fecha_dt'] >= (hoy - pd.Timedelta(days=30))]
            else: df_n_filtro = df_news.copy()

            st.markdown("---")
            if not df_n_filtro.empty:
                st.metric(label=f"Impactos informativos en {filtro_tiempo.lower()}", value=len(df_n_filtro))
                
                # Fila para las dos gráficas de Bokeh
                col_b1, col_b2 = st.columns(2)
                
                with col_b1:
                    # GRÁFICA 1: Categorías (Barras horizontales)
                    conteo_cats = df_n_filtro['feedlabel'].value_counts().reset_index()
                    conteo_cats.columns = ['Categoria', 'Cantidad']
                    source_cats = ColumnDataSource(conteo_cats)
                    
                    p_cats = figure(y_range=conteo_cats['Categoria'].tolist(), height=350, title=f"Publicaciones por Categoría", toolbar_location=None, tools="")
                    p_cats.hbar(y='Categoria', right='Cantidad', height=0.7, source=source_cats, color=RED_BASE, line_color="white")
                    p_cats.ygrid.grid_line_color = None
                    p_cats.xaxis.axis_label = "Número de publicaciones"
                    p_cats.outline_line_color = None
                    
                    hover_cats = HoverTool()
                    hover_cats.tooltips = [("Categoría", "@Categoria"), ("Publicaciones", "@Cantidad")]
                    p_cats.add_tools(hover_cats)
                    
                    st.bokeh_chart(p_cats, use_container_width=True)
                
                with col_b2:
                    # GRÁFICA 2: Evolución temporal (Líneas y Puntos)
                    # Agrupamos por fecha ignorando la hora
                    df_temporal = df_n_filtro.copy()
                    df_temporal['fecha_corta'] = df_temporal['fecha_dt'].dt.date
                    conteo_temporal = df_temporal.groupby('fecha_corta').size().reset_index(name='Cantidad')
                    # Aseguramos que es datetime para Bokeh
                    conteo_temporal['fecha_corta'] = pd.to_datetime(conteo_temporal['fecha_corta'])
                    
                    source_time = ColumnDataSource(conteo_temporal)
                    
                    p_time = figure(x_axis_type="datetime", height=350, title="Evolución de noticias en el tiempo", toolbar_location=None, tools="")
                    # Dibujamos línea y puntos en los vértices
                    p_time.line(x='fecha_corta', y='Cantidad', source=source_time, line_width=3, color=RED_BASE)
                    p_time.circle(x='fecha_corta', y='Cantidad', source=source_time, size=8, color=RED_BASE)
                    
                    p_time.xgrid.grid_line_color = None
                    p_time.yaxis.axis_label = "Número de publicaciones"
                    p_time.outline_line_color = None
                    
                    # Tooltip especial para formato de fecha
                    hover_time = HoverTool()
                    hover_time.tooltips = [("Fecha", "@fecha_corta{%F}"), ("Noticias", "@Cantidad")]
                    hover_time.formatters = {"@fecha_corta": "datetime"}
                    p_time.add_tools(hover_time)
                    
                    st.bokeh_chart(p_time, use_container_width=True)
                
                # Lista de titulares
                st.subheader("Últimos Titulares")
                for _, row in df_n_filtro.head(5).iterrows():
                    st.markdown(f"🗓️ **{row['fecha_dt'].strftime('%d/%m/%Y')}** - [{row['title']}]({row['url']})")
            else:
                st.info(f"📭 No hay noticias de '{juego_elegido}' en el periodo: {filtro_tiempo}.")
        else:
            st.error("❌ No hay historial de noticias disponible para este juego.")

# ==========================================
# PESTAÑA 3: JUGADOR
# ==========================================
with tab3:
    st.header("Estadísticas de Perfil de Jugador")
    st.info("Próximamente...")