import streamlit as st
import pandas as pd
import requests
import time
import os
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from dotenv import load_dotenv

# ==========================================
# 1. CONFIGURACIÓN INICIAL
# ==========================================
st.set_page_config(page_title="Steam Analytics Dashboard", layout="wide")
load_dotenv()
STEAM_API_KEY = os.getenv("STEAM_API_KEY")

RED_BASE = '#FF4B4B' 
RED_SCALE = 'Reds'
RED_DONUT = {'Windows': '#FF4B4B', 'MacOS': '#FF8080', 'Linux': '#FFB3B3'}
PLOT_TEMPLATE = "plotly_white"

# ==========================================
# 2. FUNCIONES DE EXTRACCIÓN (APIs)
# ==========================================
@st.cache_data(ttl=3600, show_spinner=False)
def load_steam_data(limite):
    url_top = f"https://api.steampowered.com/ISteamChartsService/GetGamesByConcurrentPlayers/v1/?key={STEAM_API_KEY}"
    res_top = requests.get(url_top).json()
    top_juegos = res_top.get('response', {}).get('ranks', [])[:limite]
    
    df_jugadores = pd.DataFrame(top_juegos)
    df_jugadores.rename(columns={'concurrent_in_game': 'jugadores_actuales'}, inplace=True)
    
    datos_tienda = []
    my_bar = st.progress(0, text=f"⏳ Descargando datos de {limite} juegos populares...")
    
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
        my_bar.progress((i + 1) / len(df_jugadores), text=f"⏳ Descargando datos de {limite} juegos populares...")
    my_bar.empty()
    return pd.merge(pd.DataFrame(datos_tienda), df_jugadores, on='appid', how='inner')

@st.cache_data(ttl=600, show_spinner=False)
def load_news_data(appid):
    url_news = f"https://api.steampowered.com/ISteamNews/GetNewsForApp/v0002/?appid={appid}&count=100&format=json"
    res_news = requests.get(url_news).json()
    noticias = res_news.get('appnews', {}).get('newsitems', [])
    df_noticias = pd.DataFrame(noticias)
    if not df_noticias.empty:
        df_noticias['fecha_dt'] = pd.to_datetime(df_noticias['date'], unit='s')
    return df_noticias

@st.cache_data(ttl=3600, show_spinner=False)
def load_player_profile(steamid):
    # 1. Datos del perfil
    url_sum = f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={STEAM_API_KEY}&steamids={steamid}"
    res_sum = requests.get(url_sum).json()
    perfil = res_sum.get('response', {}).get('players', [])
    
    # 2. Biblioteca de juegos
    url_games = f"http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={STEAM_API_KEY}&steamid={steamid}&include_appinfo=1&format=json"
    res_games = requests.get(url_games).json()
    juegos = res_games.get('response', {}).get('games', [])
    
    if not perfil or not juegos:
        return None, None, None

    df_juegos = pd.DataFrame(juegos)
    # Filtramos juegos con más de 0 minutos jugados
    df_jugados = df_juegos[df_juegos['playtime_forever'] > 0].copy()
    
    # 3. Obtener géneros de sus 15 juegos más jugados (para no tardar horas)
    top_15_jugados = df_jugados.nlargest(15, 'playtime_forever')
    generos_jugador = []
    
    my_bar = st.progress(0, text="⏳ Analizando ADN de tu biblioteca...")
    for i, appid in enumerate(top_15_jugados['appid']):
        url_store = f"https://store.steampowered.com/api/appdetails?appids={appid}&cc=es"
        res_store = requests.get(url_store).json()
        if res_store and str(appid) in res_store and res_store[str(appid)].get('success'):
            data = res_store[str(appid)]['data']
            mis_generos = [g['description'] for g in data.get('genres', [])]
            for gen in mis_generos:
                generos_jugador.append({'juego': data.get('name'), 'genero': gen, 'minutos': top_15_jugados.iloc[i]['playtime_forever']})
        time.sleep(1.2)
        my_bar.progress((i + 1) / len(top_15_jugados), text="⏳ Analizando ADN de tu biblioteca...")
    my_bar.empty()
    
    df_generos_jugador = pd.DataFrame(generos_jugador)
    return perfil[0], df_jugados, df_generos_jugador

# ==========================================
# INTERFAZ PRINCIPAL
# ==========================================
st.title("🎮 Dashboard de Análisis de Steam")
st.markdown("### Configuración de Análisis Global")
num_juegos = st.slider("🎯 Selecciona el número de juegos del Top a analizar:", 10, 100, 50, 10)
st.markdown("---")

df_super = load_steam_data(num_juegos)

tab1, tab2, tab3 = st.tabs(["📈 Tendencias", "📰 Noticias", "👤 Perfil de Jugador"])

# ==========================================
# PESTAÑA 1: TENDENCIAS
# ==========================================
with tab1:
    st.header(f"📈 Tendencias Actuales en el Top {num_juegos}")
    
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
            fig1 = px.bar(df_plot1, x='jugadores_actuales', y='nombre', orientation='h', title='🏆 Top 10 Juegos', color_discrete_sequence=[RED_BASE])
            st.plotly_chart(fig1, use_container_width=True, on_select="rerun", selection_mode="points", key="bar_chart")
        
        with col_g2:
            df_gen = df_filtrado.assign(genero=df_filtrado['generos'].str.split(', ')).explode('genero')
            df_g = df_gen.groupby('genero')['jugadores_actuales'].sum().reset_index()
            fig2 = px.treemap(df_g[df_g['jugadores_actuales']>0], path=['genero'], values='jugadores_actuales', title='🎭 Jugadores por Género', color='jugadores_actuales', color_continuous_scale=RED_SCALE)
            st.plotly_chart(fig2, use_container_width=True, on_select="rerun", selection_mode="points", key="treemap_chart")

        col_g3, col_g4 = st.columns(2)
        with col_g3:
            df_os = pd.DataFrame([('Windows', df_filtrado['windows'].sum()), ('MacOS', df_filtrado['mac'].sum()), ('Linux', df_filtrado['linux'].sum())], columns=['SO', 'Compatibles'])
            fig3 = px.pie(df_os, names='SO', values='Compatibles', hole=0.5, title='🖥️ Compatibilidad SO', color='SO', color_discrete_map=RED_DONUT)
            st.plotly_chart(fig3, use_container_width=True, on_select="rerun", selection_mode="points", key="donut_chart")
        
        with col_g4:
            df_scat = df_filtrado[df_filtrado['metacritic_nota'].notna()]
            if not df_scat.empty:
                fig4 = px.scatter(df_scat, x='precio_eur', y='metacritic_nota', size='jugadores_actuales', hover_name='nombre', title='💎 Precio vs Crítica', color='nombre')
                st.plotly_chart(fig4, use_container_width=True)

# ==========================================
# PESTAÑA 2: NOTICIAS (MATPLOTLIB TRANSPARENTE)
# ==========================================
with tab2:
    st.header("📰 Radar de Noticias Oficiales")
    if not df_super.empty:
        col_n1, col_n2 = st.columns([2, 1])
        with col_n1:
            juego_elegido = st.selectbox("🕹️ Selecciona un juego para analizar sus noticias:", df_super['nombre'].unique())
            appid_elegido = df_super[df_super['nombre'] == juego_elegido]['appid'].iloc[0]
        with col_n2:
            filtro_tiempo = st.radio("⏱️ Rango temporal:", ["Último Día", "Última Semana", "Último Mes", "Todo"], index=2)

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
                
                col_m1, col_m2 = st.columns(2)
                
                # GRÁFICA 1: BARRAS MATPLOTLIB (Cumpliendo el requisito base)
                with col_m1:
                    st.markdown("**Publicaciones por Categoría**")
                    conteo_cats = df_n_filtro['feedlabel'].value_counts().sort_values(ascending=True)
                    
                    fig_m1, ax_m1 = plt.subplots(figsize=(6, 4))
                    fig_m1.patch.set_alpha(0.0) # Fondo de figura transparente
                    ax_m1.patch.set_alpha(0.0)  # Fondo de ejes transparente
                    
                    ax_m1.barh(conteo_cats.index, conteo_cats.values, color=RED_BASE)
                    ax_m1.spines['top'].set_visible(False)
                    ax_m1.spines['right'].set_visible(False)
                    # Forzamos los textos a gris claro/oscuro para que se vean bien en modo claro/oscuro
                    ax_m1.tick_params(colors='gray')
                    for spine in ax_m1.spines.values(): spine.set_edgecolor('gray')
                    
                    st.pyplot(fig_m1, transparent=True)
                
                # GRÁFICA 2: LÍNEAS MATPLOTLIB
                with col_m2:
                    st.markdown("**Evolución de noticias en el tiempo**")
                    df_temporal = df_n_filtro.copy()
                    df_temporal['fecha_corta'] = df_temporal['fecha_dt'].dt.date
                    conteo_temporal = df_temporal.groupby('fecha_corta').size()
                    
                    fig_m2, ax_m2 = plt.subplots(figsize=(6, 4))
                    fig_m2.patch.set_alpha(0.0)
                    ax_m2.patch.set_alpha(0.0)
                    
                    ax_m2.plot(conteo_temporal.index, conteo_temporal.values, color=RED_BASE, marker='o', linewidth=2)
                    ax_m2.spines['top'].set_visible(False)
                    ax_m2.spines['right'].set_visible(False)
                    ax_m2.tick_params(colors='gray')
                    for spine in ax_m2.spines.values(): spine.set_edgecolor('gray')
                    
                    st.pyplot(fig_m2, transparent=True)
                
                st.subheader("Últimos Titulares")
                for _, row in df_n_filtro.head(5).iterrows():
                    st.markdown(f"🗓️ **{row['fecha_dt'].strftime('%d/%m/%Y')}** - [{row['title']}]({row['url']})")
            else:
                st.info(f"📭 No hay noticias en el periodo: {filtro_tiempo}.")

# ==========================================
# PESTAÑA 3: PERFIL DE JUGADOR (NUEVO)
# ==========================================
with tab3:
    st.header("👤 Análisis de ADN de Jugador")
    st.write("Introduce el SteamID64 de un perfil público (ej: `76561197960435530` - Robin Walker, creador de TF2).")
    
    steam_id_input = st.text_input("🔍 SteamID64:", max_chars=17)
    
    if steam_id_input and len(steam_id_input) == 17:
        perfil, df_juegos, df_generos_jugador = load_player_profile(steam_id_input)
        
        if perfil:
            st.markdown("---")
            col_p1, col_p2 = st.columns([1, 4])
            with col_p1:
                st.image(perfil.get('avatarfull'), width=150)
            with col_p2:
                st.subheader(perfil.get('personaname', 'Desconocido'))
                horas_totales = df_juegos['playtime_forever'].sum() / 60
                st.write(f"🎮 **Juegos en propiedad:** {len(df_juegos)}")
                st.write(f"⏱️ **Horas totales jugadas:** {int(horas_totales):,}".replace(',', '.'))
                if 'loccountrycode' in perfil:
                    st.write(f"🌍 **País:** {perfil['loccountrycode']}")

            if not df_juegos.empty and not df_generos_jugador.empty:
                col_j1, col_j2 = st.columns(2)
                
                with col_j1:
                    # Gráfica: Top Juegos Jugados (Convertido a horas)
                    df_juegos['horas'] = df_juegos['playtime_forever'] / 60
                    top_juegos_jug = df_juegos.nlargest(10, 'horas').sort_values('horas')
                    fig_p1 = px.bar(top_juegos_jug, x='horas', y='name', orientation='h', 
                                    title='🏆 Juegos con más horas', labels={'horas': 'Horas', 'name': ''}, 
                                    color_discrete_sequence=[RED_BASE], template=PLOT_TEMPLATE)
                    st.plotly_chart(fig_p1, use_container_width=True)
                
                with col_j2:
                    # Gráfica: Radar Plot de Categorías
                    radar_data = df_generos_jugador.groupby('genero')['minutos'].sum().reset_index()
                    radar_data['horas'] = radar_data['minutos'] / 60
                    # Para el radar necesitamos que se cierre el polígono
                    fig_p2 = px.line_polar(radar_data, r='horas', theta='genero', line_close=True,
                                           title='🕸️ ADN de Jugador (Radar de Géneros)',
                                           color_discrete_sequence=[RED_BASE], template=PLOT_TEMPLATE)
                    fig_p2.update_traces(fill='toself', fillcolor='rgba(255, 75, 75, 0.4)')
                    st.plotly_chart(fig_p2, use_container_width=True)
                
                # --- SISTEMA DE RECOMENDACIONES ---
                st.markdown("### 🎯 Recomendaciones basadas en tu ADN")
                # Sacamos los 3 géneros que más juega
                top_3_generos = radar_data.nlargest(3, 'horas')['genero'].tolist()
                
                # Filtramos df_super (las tendencias) para encontrar juegos que:
                # 1. Tengan alguno de esos 3 géneros.
                # 2. NO estén en la biblioteca del usuario.
                mis_appids = df_juegos['appid'].tolist()
                recomendaciones = df_super[~df_super['appid'].isin(mis_appids)]
                
                # Filtro por regex buscando cualquiera de los 3 géneros
                regex_generos = '|'.join(top_3_generos)
                recomendaciones = recomendaciones[recomendaciones['genero'].str.contains(regex_generos, na=False, regex=True) if 'genero' in recomendaciones.columns else recomendaciones['generos'].str.contains(regex_generos, na=False, regex=True)]
                
                if not recomendaciones.empty:
                    rec_finales = recomendaciones.nlargest(5, 'jugadores_actuales')
                    st.write(f"Porque juegas a **{', '.join(top_3_generos)}**, deberías probar los títulos más populares del momento que aún no tienes:")
                    for _, row in rec_finales.iterrows():
                        precio = f"{row['precio_eur']}€" if row['precio_eur'] > 0 else "Gratis"
                        st.info(f"✨ **{row['nombre']}** ({precio}) - *{row['jugadores_actuales']} jugadores actuales*")
                else:
                    st.write("¡Vaya! Ya tienes todos los juegos populares que encajan con tu estilo.")

            else:
                st.warning("Este perfil es privado o no tiene historial de horas jugadas público.")
        else:
            st.error("❌ No se ha encontrado ningún perfil con ese SteamID.")