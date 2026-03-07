import streamlit as st
import pandas as pd
import requests
import time
import os
import matplotlib.pyplot as plt
import plotly.express as px
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
# 2. FUNCIONES DE EXTRACCIÓN (APIs SEGURAS)
# ==========================================
@st.cache_data(ttl=3600, show_spinner=False)
def load_steam_data(limite):
    url_top = f"https://api.steampowered.com/ISteamChartsService/GetGamesByConcurrentPlayers/v1/?key={STEAM_API_KEY}"
    try:
        res_top = requests.get(url_top).json()
        top_juegos = res_top.get('response', {}).get('ranks', [])[:limite]
    except Exception:
        return pd.DataFrame()
    
    df_jugadores = pd.DataFrame(top_juegos)
    if df_jugadores.empty: return pd.DataFrame()
    df_jugadores.rename(columns={'concurrent_in_game': 'jugadores_actuales'}, inplace=True)
    
    datos_tienda = []
    my_bar = st.progress(0, text=f"⏳ Descargando datos de {limite} juegos populares...")
    
    for i, appid in enumerate(df_jugadores['appid']):
        url_store = f"https://store.steampowered.com/api/appdetails?appids={appid}&cc=es"
        try:
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
        except Exception:
            pass # Si falla un juego, seguimos con el siguiente
        time.sleep(1.2)
        my_bar.progress((i + 1) / len(df_jugadores), text=f"⏳ Descargando datos de {limite} juegos populares...")
    
    my_bar.empty()
    if not datos_tienda: return pd.DataFrame()
    return pd.merge(pd.DataFrame(datos_tienda), df_jugadores, on='appid', how='inner')

@st.cache_data(ttl=600, show_spinner=False)
def load_news_data(appid):
    url_news = f"https://api.steampowered.com/ISteamNews/GetNewsForApp/v0002/?appid={appid}&count=100&format=json"
    try:
        res_news = requests.get(url_news).json()
        noticias = res_news.get('appnews', {}).get('newsitems', [])
        df_noticias = pd.DataFrame(noticias)
        if not df_noticias.empty:
            df_noticias['fecha_dt'] = pd.to_datetime(df_noticias['date'], unit='s')
        return df_noticias
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=3600, show_spinner=False)
def load_player_profile(steamid):
    try:
        url_sum = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={STEAM_API_KEY}&steamids={steamid}"
        res_sum = requests.get(url_sum).json()
        perfil = res_sum.get('response', {}).get('players', [])
        
        url_games = f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={STEAM_API_KEY}&steamid={steamid}&include_appinfo=1&format=json"
        res_games = requests.get(url_games).json()
        juegos = res_games.get('response', {}).get('games', [])
    except Exception:
        return None, None, None

    if not perfil or not juegos:
        return None, None, None

    df_juegos = pd.DataFrame(juegos)
    if 'playtime_forever' not in df_juegos.columns: return perfil[0], pd.DataFrame(), pd.DataFrame()
    df_jugados = df_juegos[df_juegos['playtime_forever'] > 0].copy()
    
    top_15_jugados = df_jugados.nlargest(15, 'playtime_forever')
    generos_jugador = []
    
    my_bar = st.progress(0, text="⏳ Analizando ADN de tu biblioteca...")
    for i, appid in enumerate(top_15_jugados['appid']):
        try:
            url_store = f"https://store.steampowered.com/api/appdetails?appids={appid}&cc=es"
            res_store = requests.get(url_store).json()
            if res_store and str(appid) in res_store and res_store[str(appid)].get('success'):
                data = res_store[str(appid)]['data']
                for gen in [g['description'] for g in data.get('genres', [])]:
                    generos_jugador.append({'juego': data.get('name'), 'genero': gen, 'minutos': top_15_jugados.iloc[i]['playtime_forever']})
        except Exception:
            pass
        time.sleep(1.2)
        my_bar.progress((i + 1) / len(top_15_jugados), text="⏳ Analizando ADN de tu biblioteca...")
    my_bar.empty()
    
    return perfil[0], df_jugados, pd.DataFrame(generos_jugador)

@st.cache_data(ttl=86400, show_spinner=False)
def load_all_apps():
    # Descarga la lista maestra de todos los juegos de Steam
    try:
        url = "https://api.steampowered.com/ISteamApps/GetAppList/v2/"
        res = requests.get(url).json()
        apps = res.get('applist', {}).get('apps', [])
        df = pd.DataFrame(apps)
        return df[df['name'] != '']
    except Exception:
        return pd.DataFrame()

# ==========================================
# INTERFAZ PRINCIPAL
# ==========================================
st.title("🎮 Dashboard de Análisis de Steam")
st.markdown("### Configuración de Análisis Global")
num_juegos = st.slider("🎯 Selecciona el número de juegos del Top a analizar:", 10, 100, 50, 10)
st.markdown("---")

df_super = load_steam_data(num_juegos)

# Reordenamos la creación de pestañas
tab1, tab2, tab3, tab4 = st.tabs(["📈 Tendencias", "🔎 Buscador Global", "📰 Noticias", "👤 Perfil de Jugador"])

# ==========================================
# PESTAÑA 1: TENDENCIAS
# ==========================================
with tab1:
    st.header(f"📈 Tendencias Actuales en el Top {num_juegos}")
    
    if df_super.empty:
        st.error("Error al conectar con Steam. Inténtalo de nuevo en unos minutos.")
    else:
        # Captura segura de filtros cruzados
        filtro_treemap = st.session_state.get("treemap_chart", {}).get("selection", {}).get("points", [{}])[0].get("label") if "treemap_chart" in st.session_state else None
        filtro_donut = st.session_state.get("donut_chart", {}).get("selection", {}).get("points", [{}])[0].get("label") if "donut_chart" in st.session_state else None
        filtro_barras = st.session_state.get("bar_chart", {}).get("selection", {}).get("points", [{}])[0].get("y") if "bar_chart" in st.session_state else None

        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1: juegos_sel = st.multiselect("🎮 Filtrar por Videojuego", options=df_super['nombre'].unique())
        with col_f2: plat_sel = st.selectbox("💻 Filtrar por Plataforma", ["Todas", "Windows", "MacOS", "Linux"])
        with col_f3:
            todos_gen = set()
            for gen in df_super['generos'].dropna(): todos_gen.update(gen.split(', '))
            gen_sel = st.selectbox("🎭 Filtrar por Género", ["Todos"] + sorted(list(todos_gen)))

        df_filtrado = df_super.copy()
        
        # Filtros manuales
        if juegos_sel: df_filtrado = df_filtrado[df_filtrado['nombre'].isin(juegos_sel)]
        if plat_sel != "Todas": df_filtrado = df_filtrado[df_filtrado[plat_sel.lower()] == True]
        if gen_sel != "Todos": df_filtrado = df_filtrado[df_filtrado['generos'].str.contains(gen_sel, na=False)]
        
        # Filtros cruzados
        if filtro_treemap: df_filtrado = df_filtrado[df_filtrado['generos'].str.contains(filtro_treemap, na=False)]
        if filtro_donut:
            if filtro_donut == 'Windows': df_filtrado = df_filtrado[df_filtrado['windows'] == True]
            elif filtro_donut == 'MacOS': df_filtrado = df_filtrado[df_filtrado['mac'] == True]
            elif filtro_donut == 'Linux': df_filtrado = df_filtrado[df_filtrado['linux'] == True]
        if filtro_barras: df_filtrado = df_filtrado[df_filtrado['nombre'] == filtro_barras]

        if filtro_treemap or filtro_donut or filtro_barras:
            st.success("🖱️ **Filtro cruzado activo.** (Haz doble clic en el gráfico para limpiar la selección)")

        st.markdown("---")

        if not df_filtrado.empty:
            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            kpi1.metric("👥 Jugadores (Totales)", f"{int(df_filtrado['jugadores_actuales'].sum()):,}".replace(',', '.'))
            kpi2.metric("🕹️ Juegos (Unidades)", len(df_filtrado))
            kpi3.metric("💸 Precio Medio (Euros)", f"{df_filtrado[df_filtrado['precio_eur']>0]['precio_eur'].mean():.2f} €" if not df_filtrado[df_filtrado['precio_eur']>0].empty else "0.00 €")
            kpi4.metric("🎁 Juegos Gratuitos (Unidades)", int(df_filtrado['es_gratis'].sum()))

            col_g1, col_g2 = st.columns(2)
            with col_g1:
                df_plot1 = df_filtrado.nlargest(10, 'jugadores_actuales').sort_values('jugadores_actuales')
                fig1 = px.bar(df_plot1, x='jugadores_actuales', y='nombre', orientation='h', title='🏆 Top 10 Juegos', 
                              labels={'jugadores_actuales': 'Jugadores (Unidades)', 'nombre': 'Videojuego'},
                              color_discrete_sequence=[RED_BASE])
                st.plotly_chart(fig1, use_container_width=True, on_select="rerun", selection_mode="points", key="bar_chart")
            
            with col_g2:
                df_gen = df_filtrado.assign(genero=df_filtrado['generos'].str.split(', ')).explode('genero')
                df_g = df_gen.groupby('genero')['jugadores_actuales'].sum().reset_index()
                fig2 = px.treemap(df_g[df_g['jugadores_actuales']>0], path=['genero'], values='jugadores_actuales', title='🎭 Jugadores por Género', 
                                  labels={'jugadores_actuales': 'Jugadores (Unidades)', 'genero': 'Categoría'},
                                  color='jugadores_actuales', color_continuous_scale=RED_SCALE)
                st.plotly_chart(fig2, use_container_width=True, on_select="rerun", selection_mode="points", key="treemap_chart")

            col_g3, col_g4 = st.columns(2)
            with col_g3:
                df_os = pd.DataFrame([('Windows', df_filtrado['windows'].sum()), ('MacOS', df_filtrado['mac'].sum()), ('Linux', df_filtrado['linux'].sum())], columns=['SO', 'Compatibles'])
                fig3 = px.pie(df_os, names='SO', values='Compatibles', hole=0.5, title='🖥️ Compatibilidad de Sistema Operativo', 
                              labels={'SO': 'Sistema Operativo', 'Compatibles': 'Juegos (Unidades)'},
                              color='SO', color_discrete_map=RED_DONUT)
                st.plotly_chart(fig3, use_container_width=True, on_select="rerun", selection_mode="points", key="donut_chart")
            
            with col_g4:
                df_scat = df_filtrado[df_filtrado['metacritic_nota'].notna()]
                if not df_scat.empty:
                    fig4 = px.scatter(df_scat, x='precio_eur', y='metacritic_nota', size='jugadores_actuales', hover_name='nombre', title='💎 Relación Precio y Crítica', 
                                      labels={'precio_eur': 'Precio (Euros)', 'metacritic_nota': 'Nota Crítica (Puntos)', 'nombre': 'Videojuego'},
                                      color='nombre')
                    st.plotly_chart(fig4, use_container_width=True)

# ==========================================
# PESTAÑA 2: BUSCADOR GLOBAL
# ==========================================
with tab2:
    st.header("🔎 Buscador Global de Juegos")
    st.write("¿Quieres consultar un juego que no está en el Top actual? Búscalo aquí.")
    
    df_all_apps = load_all_apps()
    
    if not df_all_apps.empty:
        juego_buscar = st.selectbox("Escribe el nombre del juego:", df_all_apps['name'].unique())
        
        if st.button("Buscar Datos en Vivo"):
            appid_buscar = df_all_apps[df_all_apps['name'] == juego_buscar]['appid'].iloc[0]
            
            col_b1, col_b2 = st.columns(2)
            
            # 1. Buscar Jugadores en Vivo
            url_players = f"https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid={appid_buscar}"
            try:
                res_players = requests.get(url_players).json()
                jugadores_vivo = res_players.get('response', {}).get('player_count', 0)
            except:
                jugadores_vivo = 0
                
            # 2. Buscar Datos de Tienda
            url_store = f"https://store.steampowered.com/api/appdetails?appids={appid_buscar}&cc=es"
            try:
                res_store = requests.get(url_store).json()
                if res_store and str(appid_buscar) in res_store and res_store[str(appid_buscar)].get('success'):
                    data = res_store[str(appid_buscar)]['data']
                    precio = data.get('price_overview', {}).get('final', 0) / 100 if not data.get('is_free', False) else 0.0
                    nota = data.get('metacritic', {}).get('score', "Sin nota")
                    
                    with col_b1:
                        st.image(data.get('header_image', ''), use_container_width=True)
                    with col_b2:
                        st.subheader(data.get('name'))
                        st.metric("👥 Jugadores (Actuales)", f"{jugadores_vivo:,}".replace(',', '.'))
                        st.write(f"💸 **Precio:** {precio} €" if precio > 0 else "💸 **Precio:** Gratis")
                        st.write(f"⭐ **Metacritic:** {nota}")
                        st.write(f"📝 **Descripción:** {data.get('short_description', '')[:200]}...")
            except:
                st.error("No se han podido obtener los datos de la tienda para este juego.")

# ==========================================
# PESTAÑA 3: NOTICIAS (MATPLOTLIB)
# ==========================================
with tab3:
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
                
                with col_m1:
                    st.markdown("**Publicaciones por Categoría**")
                    conteo_cats = df_n_filtro['feedlabel'].value_counts().sort_values(ascending=True)
                    
                    fig_m1, ax_m1 = plt.subplots(figsize=(6, 4))
                    fig_m1.patch.set_alpha(0.0) 
                    ax_m1.patch.set_alpha(0.0)  
                    
                    ax_m1.barh(conteo_cats.index, conteo_cats.values, color=RED_BASE)
                    ax_m1.spines['top'].set_visible(False)
                    ax_m1.spines['right'].set_visible(False)
                    ax_m1.tick_params(colors='gray')
                    
                    ax_m1.set_xlabel('Número de Publicaciones (Unidades)', fontsize=10, color='gray')
                    ax_m1.set_ylabel('Categoría', fontsize=10, color='gray')
                    
                    for spine in ax_m1.spines.values(): spine.set_edgecolor('gray')
                    st.pyplot(fig_m1, transparent=True)
                
                with col_m2:
                    st.markdown("**Evolución de Noticias en el Tiempo**")
                    df_temporal = df_n_filtro.copy()
                    df_temporal['fecha_corta'] = df_temporal['fecha_dt'].dt.date
                    conteo_temporal = df_temporal.groupby('fecha_corta').size()
                    
                    fig_m2, ax_m2 = plt.subplots(figsize=(6, 4))
                    fig_m2.patch.set_alpha(0.0)
                    ax_m2.patch.set_alpha(0.0)
                    
                    ax_m2.plot(conteo_temporal.index, conteo_temporal.values, color=RED_BASE, marker='o', linewidth=2)
                    ax_m2.spines['top'].set_visible(False)
                    ax_m2.spines['right'].set_visible(False)
                    ax_m2.tick_params(colors='gray', rotation=45)
                    
                    ax_m2.set_xlabel('Fecha (Días)', fontsize=10, color='gray')
                    ax_m2.set_ylabel('Número de Publicaciones (Unidades)', fontsize=10, color='gray')
                    
                    for spine in ax_m2.spines.values(): spine.set_edgecolor('gray')
                    st.pyplot(fig_m2, transparent=True)
                
                st.subheader("Últimos Titulares")
                for _, row in df_n_filtro.head(5).iterrows():
                    st.markdown(f"🗓️ **{row['fecha_dt'].strftime('%d/%m/%Y')}** - [{row['title']}]({row['url']})")
            else:
                st.info(f"📭 No hay noticias en el periodo: {filtro_tiempo}.")

# ==========================================
# PESTAÑA 4: PERFIL DE JUGADOR
# ==========================================
with tab4:
    st.header("👤 Análisis de ADN de Jugador")
    st.write("Introduce el SteamID64 de un perfil público (ej: `76561197960435530`).")
    
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

            if not df_juegos.empty and not df_generos_jugador.empty:
                col_j1, col_j2 = st.columns(2)
                
                with col_j1:
                    df_juegos['horas'] = df_juegos['playtime_forever'] / 60
                    top_juegos_jug = df_juegos.nlargest(10, 'horas').sort_values('horas')
                    fig_p1 = px.bar(top_juegos_jug, x='horas', y='name', orientation='h', 
                                    title='🏆 Juegos con Más Horas', 
                                    labels={'horas': 'Tiempo Jugado (Horas)', 'name': 'Videojuego'}, 
                                    color_discrete_sequence=[RED_BASE], template=PLOT_TEMPLATE)
                    st.plotly_chart(fig_p1, use_container_width=True)
                
                with col_j2:
                    radar_data = df_generos_jugador.groupby('genero')['minutos'].sum().reset_index()
                    radar_data['horas'] = radar_data['minutos'] / 60
                    fig_p2 = px.line_polar(radar_data, r='horas', theta='genero', line_close=True,
                                           title='🕸️ ADN de Jugador (Radar de Géneros)',
                                           labels={'horas': 'Tiempo Jugado (Horas)', 'genero': 'Categoría'},
                                           color_discrete_sequence=[RED_BASE], template=PLOT_TEMPLATE)
                    fig_p2.update_traces(fill='toself', fillcolor='rgba(255, 75, 75, 0.4)')
                    st.plotly_chart(fig_p2, use_container_width=True)