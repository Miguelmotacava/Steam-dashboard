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
    # Pedimos hasta 100 noticias del juego seleccionado
    url_news = f"https://api.steampowered.com/ISteamNews/GetNewsForApp/v0002/?appid={appid}&count=100&format=json"
    res_news = requests.get(url_news).json()
    noticias = res_news.get('appnews', {}).get('newsitems', [])
    df_noticias = pd.DataFrame(noticias)
    
    if not df_noticias.empty:
        # Convertimos la fecha Unix a formato Fecha/Hora normal de Python
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
    
    GREEN_BASE, GREEN_SCALE = '#2e7d32', 'Greens'
    GREEN_DONUT = {'Windows': '#1b5e20', 'MacOS': '#66bb6a', 'Linux': '#a5d6a7'}
    
    # Filtros Cruzados (Session State)
    filtro_treemap = st.session_state.get("treemap_chart", {}).get("selection", {}).get("points", [{}])[0].get("label") if "treemap_chart" in st.session_state and st.session_state["treemap_chart"].get("selection", {}).get("points") else None
    filtro_donut = st.session_state.get("donut_chart", {}).get("selection", {}).get("points", [{}])[0].get("label") if "donut_chart" in st.session_state and st.session_state["donut_chart"].get("selection", {}).get("points") else None

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1: juegos_sel = st.multiselect("🎮 Filtrar por Videojuego", options=df_super['nombre'].unique())
    with col_f2: plat_sel = st.selectbox("💻 Filtrar por Plataforma", ["Todas", "Windows", "MacOS", "Linux"])
    with col_f3:
        todos_gen = set()
        for gen in df_super['generos'].dropna(): todos_gen.update(gen.split(', '))
        gen_sel = st.selectbox("🎭 Filtrar por Género", ["Todos"] + sorted(list(todos_gen)))

    df_filtrado = df_super.copy()
    if juegos_sel: df_filtrado = df_filtrado[df_filtrado['nombre'].isin(juegos_sel)]
    if plat_sel != "Todas": df_filtrado = df_filtrado[df_filtrado[plat_sel.lower()] == True]
    if gen_sel != "Todos": df_filtrado = df_filtrado[df_filtrado['generos'].str.contains(gen_sel, na=False)]
    if filtro_treemap: df_filtrado = df_filtrado[df_filtrado['generos'].str.contains(filtro_treemap, na=False)]
    if filtro_donut: df_filtrado = df_filtrado[df_filtrado[filtro_donut.lower()] == True]

    st.markdown("---")

    if not df_filtrado.empty:
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("👥 Jugadores Totales", f"{int(df_filtrado['jugadores_actuales'].sum()):,}".replace(',', '.'))
        kpi2.metric("🕹️ Juegos", len(df_filtrado))
        kpi3.metric("💸 Precio Medio", f"{df_filtrado[df_filtrado['precio_eur']>0]['precio_eur'].mean():.2f} €" if not df_filtrado[df_filtrado['precio_eur']>0].empty else "0.00 €")
        kpi4.metric("🎁 Juegos Gratuitos", int(df_filtrado['es_gratis'].sum()))

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            fig1 = px.bar(df_filtrado.nlargest(10, 'jugadores_actuales').sort_values('jugadores_actuales'), x='jugadores_actuales', y='nombre', orientation='h', title='🏆 Top 10 Juegos', color_discrete_sequence=[GREEN_BASE])
            st.plotly_chart(fig1, use_container_width=True)
        with col_g2:
            df_gen = df_filtrado.assign(genero=df_filtrado['generos'].str.split(', ')).explode('genero')
            df_g = df_gen.groupby('genero')['jugadores_actuales'].sum().reset_index()
            fig2 = px.treemap(df_g[df_g['jugadores_actuales']>0], path=['genero'], values='jugadores_actuales', title='🎭 Jugadores por Género', color='jugadores_actuales', color_continuous_scale=GREEN_SCALE)
            st.plotly_chart(fig2, use_container_width=True, on_select="rerun", key="treemap_chart")

        col_g3, col_g4 = st.columns(2)
        with col_g3:
            df_os = pd.DataFrame([('Windows', df_filtrado['windows'].sum()), ('MacOS', df_filtrado['mac'].sum()), ('Linux', df_filtrado['linux'].sum())], columns=['SO', 'Compatibles'])
            fig3 = px.pie(df_os, names='SO', values='Compatibles', hole=0.5, title='🖥️ Compatibilidad SO', color='SO', color_discrete_map=GREEN_DONUT)
            st.plotly_chart(fig3, use_container_width=True, on_select="rerun", key="donut_chart")
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
            # Selector de juego (usamos el top cargado previamente)
            juego_elegido = st.selectbox("🕹️ Selecciona un juego para analizar sus noticias:", df_super['nombre'].unique())
            appid_elegido = df_super[df_super['nombre'] == juego_elegido]['appid'].iloc[0]
        
        with col_n2:
            # Selector temporal (widget de Streamlit)
            filtro_tiempo = st.radio("⏱️ Rango temporal:", ["Último Día", "Última Semana", "Último Mes", "Todo (100 últ.)"], index=2)

        # Cargar datos
        df_news = load_news_data(appid_elegido)
        
        if not df_news.empty:
            # Filtrar por fecha
            hoy = pd.Timestamp.now()
            if filtro_tiempo == "Último Día":
                df_n_filtro = df_news[df_news['fecha_dt'] >= (hoy - pd.Timedelta(days=1))]
            elif filtro_tiempo == "Última Semana":
                df_n_filtro = df_news[df_news['fecha_dt'] >= (hoy - pd.Timedelta(days=7))]
            elif filtro_tiempo == "Último Mes":
                df_n_filtro = df_news[df_news['fecha_dt'] >= (hoy - pd.Timedelta(days=30))]
            else:
                df_n_filtro = df_news.copy()

            st.markdown("---")

            if not df_n_filtro.empty:
                # KPI de noticias
                st.metric(label=f"Impactos informativos en {filtro_tiempo.lower()}", value=len(df_n_filtro))
                
                # --- GRÁFICA DE BOKEH ---
                # Agrupamos las noticias por su categoría (feedlabel) para ver qué tipo de contenido publican
                conteo_cats = df_n_filtro['feedlabel'].value_counts().reset_index()
                conteo_cats.columns = ['Categoria', 'Cantidad']
                
                # Convertimos datos para Bokeh
                source = ColumnDataSource(conteo_cats)
                
                # Creamos la figura Bokeh (Requisito del laboratorio)
                p = figure(
                    y_range=conteo_cats['Categoria'].tolist(), 
                    height=350, 
                    title=f"Distribución de Publicaciones por Categoría ({juego_elegido})",
                    toolbar_location=None, 
                    tools=""
                )
                
                # Hacemos las barras horizontales usando nuestro verde principal
                p.hbar(y='Categoria', right='Cantidad', height=0.7, source=source, color="#2e7d32", line_color="white")
                
                # Limpiamos el diseño
                p.ygrid.grid_line_color = None
                p.xaxis.axis_label = "Número de publicaciones"
                p.outline_line_color = None
                
                # Añadimos un HoverTool (Interactividad)
                hover = HoverTool()
                hover.tooltips = [("Categoría", "@Categoria"), ("Publicaciones", "@Cantidad")]
                p.add_tools(hover)
                
                # Renderizamos en Streamlit
                st.bokeh_chart(p, use_container_width=True)
                
                # Añadimos el listado real de noticias por si el usuario quiere leerlas
                st.subheader("Últimos Titulares")
                for _, row in df_n_filtro.head(5).iterrows():
                    st.markdown(f"🗓️ **{row['fecha_dt'].strftime('%d/%m/%Y')}** - [{row['title']}]({row['url']})")
                    
            else:
                st.info(f"📭 Los desarrolladores de '{juego_elegido}' no han publicado noticias en el periodo: {filtro_tiempo}.")
        else:
            st.error("❌ No hay historial de noticias disponible para este juego.")

with tab3:
    st.header("Estadísticas de Perfil de Jugador")
    st.info("Próximamente...")