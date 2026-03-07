import streamlit as st
import pandas as pd
import requests
import time
import os
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv
from datetime import datetime

# ==========================================
# 1. CONFIGURACIÓN INICIAL Y DISEÑO
# ==========================================
st.set_page_config(page_title="Steam Analytics Dashboard", layout="wide")
load_dotenv()
STEAM_API_KEY = os.getenv("STEAM_API_KEY")

RED_BASE = '#FF4B4B' 
RED_SCALE = 'Reds'
RED_DONUT = {'Windows': '#FF4B4B', 'MacOS': '#FF8080', 'Linux': '#FFB3B3'}
PLOT_TEMPLATE = "plotly_white"

# Sesión HTTP reutilizable (más rápido que crear una nueva conexión por request)
session = requests.Session()

# Inyectamos CSS para forzar que la barra de progreso sea ROJA
st.markdown(
    """
    <style>
    .stProgress > div > div > div > div {
        background-color: #FF4B4B !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==========================================
# 2. FUNCIONES DE EXTRACCIÓN (APIs SEGURAS)
# ==========================================
@st.cache_data(ttl=3600, show_spinner=False)
def load_steam_data(limite):
    url_top = f"https://api.steampowered.com/ISteamChartsService/GetGamesByConcurrentPlayers/v1/?key={STEAM_API_KEY}"
    try:
        res_top = session.get(url_top).json()
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
            res_store = session.get(url_store).json()
            if res_store and str(appid) in res_store and res_store[str(appid)].get('success'):
                data = res_store[str(appid)]['data']
                
                # Extraer descuento actual
                price_ov = data.get('price_overview', {})
                es_gratis = data.get('is_free', False)
                
                datos_tienda.append({
                    'appid': appid, 'nombre': data.get('name', 'Desconocido'),
                    'es_gratis': es_gratis,
                    'precio_inicial': price_ov.get('initial', 0) / 100 if not es_gratis else 0.0,
                    'precio_eur': price_ov.get('final', 0) / 100 if not es_gratis else 0.0,
                    'descuento_pct': price_ov.get('discount_percent', 0),
                    'contenido_adicional_count': len(data.get('dlc', [])),
                    'metacritic_nota': data.get('metacritic', {}).get('score', None),
                    'windows': data.get('platforms', {}).get('windows', False),
                    'mac': data.get('platforms', {}).get('mac', False),
                    'linux': data.get('platforms', {}).get('linux', False),
                    'generos': ", ".join([g['description'] for g in data.get('genres', [])])
                })
        except Exception:
            pass 
        time.sleep(0.5)
        my_bar.progress((i + 1) / len(df_jugadores), text=f"⏳ Descargando datos de {limite} juegos populares...")
    
    my_bar.empty()
    if not datos_tienda: return pd.DataFrame()
    return pd.merge(pd.DataFrame(datos_tienda), df_jugadores, on='appid', how='inner')

@st.cache_data(ttl=600, show_spinner=False)
def load_news_data(appid):
    url_news = f"https://api.steampowered.com/ISteamNews/GetNewsForApp/v0002/?appid={appid}&count=100&format=json"
    try:
        res_news = session.get(url_news).json()
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
        res_sum = session.get(url_sum).json()
        perfil = res_sum.get('response', {}).get('players', [])
        
        url_games = f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={STEAM_API_KEY}&steamid={steamid}&include_appinfo=1&format=json"
        res_games = session.get(url_games).json()
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
    
    for i, appid in enumerate(top_15_jugados['appid']):
        try:
            url_store = f"https://store.steampowered.com/api/appdetails?appids={appid}&cc=es"
            res_store = session.get(url_store).json()
            if res_store and str(appid) in res_store and res_store[str(appid)].get('success'):
                data = res_store[str(appid)]['data']
                for gen in [g['description'] for g in data.get('genres', [])]:
                    generos_jugador.append({'juego': data.get('name'), 'genero': gen, 'minutos': top_15_jugados.iloc[i]['playtime_forever']})
        except Exception:
            pass
        time.sleep(0.5)
    
    return perfil[0], df_juegos, pd.DataFrame(generos_jugador)

@st.cache_data(ttl=86400, show_spinner=False)
def load_all_apps():
    try:
        url = "https://api.steampowered.com/ISteamApps/GetAppList/v2/"
        res = session.get(url).json()
        apps = res.get('applist', {}).get('apps', [])
        df = pd.DataFrame(apps)
        return df[df['name'] != '']
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=3600, show_spinner=False)
def obtener_precio_historico(appid, nombre):
    """Consulta CheapShark para obtener el historial de precios en Steam (USD)."""
    try:
        url_search = f"https://www.cheapshark.com/api/1.0/games?steamAppID={appid}"
        res = session.get(url_search, timeout=5).json()
        if not res or len(res) == 0:
            return None
        
        game_id = res[0].get('gameID')
        if not game_id:
            return None
        
        url_detail = f"https://www.cheapshark.com/api/1.0/games?id={game_id}"
        res_detail = session.get(url_detail, timeout=5).json()
        
        cheapest = res_detail.get('cheapestPriceEver', {})
        precio_min = float(cheapest.get('price', 0))
        fecha_min_ts = cheapest.get('date', 0)
        fecha_min = datetime.fromtimestamp(fecha_min_ts).strftime('%Y-%m-%d') if fecha_min_ts else None
        
        deals = res_detail.get('deals', [])
        steam_deal = next((d for d in deals if d.get('storeID') == '1'), None)
        
        return {
            'precio_min_historico': precio_min,
            'fecha_min_historico': fecha_min,
            'precio_retail_usd': float(steam_deal['retailPrice']) if steam_deal else None,
            'precio_actual_usd': float(steam_deal['price']) if steam_deal else None,
        }
    except Exception:
        return None

def generar_grafico_precio(precio_ini_eur, precio_fin_eur, nombre, datos_historicos=None):
    """Genera un gráfico de evolución de precio.
    Si hay datos de CheapShark, usa precios USD consistentes.
    Si no, usa los precios EUR de Steam como fallback."""
    
    if datos_historicos and datos_historicos.get('fecha_min_historico'):
        # Usar precios USD de CheapShark para consistencia
        precio_retail = datos_historicos.get('precio_retail_usd') or 0
        precio_actual = datos_historicos.get('precio_actual_usd') or 0
        precio_min = datos_historicos['precio_min_historico']
        fecha_min = datos_historicos['fecha_min_historico']
        hoy = pd.Timestamp.today().strftime('%Y-%m-%d')
        
        # Construir puntos del gráfico
        fechas = []
        precios = []
        etiquetas = []
        colores_marker = []
        
        # Punto 1: Precio base (retail) — antes del mínimo histórico
        if precio_retail > 0:
            fecha_base = (pd.to_datetime(fecha_min) - pd.Timedelta(days=30)).strftime('%Y-%m-%d')
            fechas.append(fecha_base)
            precios.append(precio_retail)
            etiquetas.append(f"Precio Base: ${precio_retail:.2f}")
            colores_marker.append(RED_BASE)
        
        # Punto 2: Mínimo histórico
        fechas.append(fecha_min)
        precios.append(precio_min)
        etiquetas.append(f"Mínimo Histórico: ${precio_min:.2f}")
        colores_marker.append('green')
        
        # Punto 3: Precio actual
        fechas.append(hoy)
        precios.append(precio_actual)
        etiquetas.append(f"Hoy: ${precio_actual:.2f}")
        colores_marker.append(RED_BASE)
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=pd.to_datetime(fechas), y=precios,
            mode='lines+markers+text',
            marker=dict(size=12, color=colores_marker),
            line=dict(color=RED_BASE, width=2),
            text=etiquetas,
            textposition='top center',
            textfont=dict(size=10),
            hovertemplate='%{text}<br>Fecha: %{x|%d/%m/%Y}<extra></extra>',
            name='Precio'
        ))
        
        # Línea de referencia del mínimo histórico
        fig.add_hline(
            y=precio_min, line_dash="dash", line_color="green",
            annotation_text=f"Mínimo: ${precio_min:.2f}",
            annotation_position="bottom right"
        )
        
        # Línea de referencia del precio base
        if precio_retail > 0 and precio_retail != precio_actual:
            fig.add_hline(
                y=precio_retail, line_dash="dot", line_color="gray",
                annotation_text=f"Base: ${precio_retail:.2f}",
                annotation_position="top right"
            )
        
        max_precio = max(precios) if precios else 10
        fig.update_layout(
            title=f'📉 Evolución Real del Precio: {nombre}',
            xaxis_title='Fecha',
            yaxis_title='Precio (USD)',
            template=PLOT_TEMPLATE,
            yaxis_range=[0, max_precio + max_precio * 0.3 + 2],
            showlegend=False
        )
        return fig
    else:
        # Fallback: solo precio base y actual EUR (sin datos de CheapShark)
        fechas = pd.date_range(end=pd.Timestamp.today(), periods=2, freq='ME')
        precios_fb = [precio_ini_eur, precio_fin_eur]
        df_hist = pd.DataFrame({'Fecha': fechas, 'Precio (€)': precios_fb})
        fig = px.line(df_hist, x='Fecha', y='Precio (€)', title=f'📈 Precio: {nombre}', 
                      markers=True, color_discrete_sequence=[RED_BASE])
        fig.update_layout(yaxis_range=[0, max(precio_ini_eur, precio_fin_eur)+10], template=PLOT_TEMPLATE)
        return fig

# ==========================================
# INTERFAZ PRINCIPAL
# ==========================================
st.title("Dashboard de Análisis de Steam")
st.markdown("### Configuración de Análisis Global")
num_juegos = st.slider("Selecciona el número de juegos del Top a analizar:", 10, 100, 50, 10)
st.markdown("---")

df_super = load_steam_data(num_juegos)

tab1, tab2, tab3, tab4 = st.tabs(["📈 Tendencias", "🔎 Buscador Global", "📰 Noticias", "👤 Perfil de Jugador"])

# ==========================================
# PESTAÑA 1: TENDENCIAS
# ==========================================
with tab1:
    st.header(f"Tendencias Actuales en el Top {num_juegos}")
    st.info("Mostrando datos en tiempo real. Steam no permite filtrar por horas pasadas en este ranking.")
    
    if df_super.empty:
        st.error("Error al conectar con Steam. Inténtalo de nuevo en unos minutos.")
    else:
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1: juegos_sel = st.multiselect("Filtrar por Videojuego", options=df_super['nombre'].unique())
        with col_f2: plat_sel = st.selectbox("Filtrar por Plataforma", ["Todas", "Windows", "MacOS", "Linux"])
        with col_f3:
            todos_gen = set()
            for gen in df_super['generos'].dropna(): todos_gen.update(gen.split(', '))
            gen_sel = st.selectbox("Filtrar por Género", ["Todos"] + sorted(list(todos_gen)))

        df_filtrado = df_super.copy()
        
        if juegos_sel: df_filtrado = df_filtrado[df_filtrado['nombre'].isin(juegos_sel)]
        if plat_sel != "Todas": df_filtrado = df_filtrado[df_filtrado[plat_sel.lower()] == True]
        if gen_sel != "Todos": df_filtrado = df_filtrado[df_filtrado['generos'].str.contains(gen_sel, na=False)]
        
        st.markdown("---")

        if not df_filtrado.empty:
            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            kpi1.metric("Jugadores (Totales)", f"{int(df_filtrado['jugadores_actuales'].sum()):,}".replace(',', '.'))
            kpi2.metric("Juegos (Unidades)", len(df_filtrado))
            kpi3.metric("Precio Medio (Euros)", f"{df_filtrado[df_filtrado['precio_eur']>0]['precio_eur'].mean():.2f} €" if not df_filtrado[df_filtrado['precio_eur']>0].empty else "0.00 €")
            kpi4.metric("Juegos Gratuitos (Unidades)", int(df_filtrado['es_gratis'].sum()))

            col_g1, col_g2 = st.columns(2)
            with col_g1:
                df_plot1 = df_filtrado.nlargest(10, 'jugadores_actuales').sort_values('jugadores_actuales')
                fig1 = px.bar(df_plot1, x='jugadores_actuales', y='nombre', orientation='h', title='Top 10 Juegos', 
                              labels={'jugadores_actuales': 'Jugadores Concurrentes (Unidades)', 'nombre': 'Videojuego'},
                              color_discrete_sequence=[RED_BASE])
                st.plotly_chart(fig1, use_container_width=True)
            
            with col_g2:
                df_gen = df_filtrado.assign(genero=df_filtrado['generos'].str.split(', ')).explode('genero')
                df_g = df_gen.groupby('genero')['jugadores_actuales'].sum().reset_index()
                fig2 = px.treemap(df_g[df_g['jugadores_actuales']>0], path=['genero'], values='jugadores_actuales', title='Jugadores por Género', 
                                  labels={'jugadores_actuales': 'Jugadores (Unidades)', 'genero': 'Categoría'},
                                  color='jugadores_actuales', color_continuous_scale=RED_SCALE)
                st.plotly_chart(fig2, use_container_width=True)

            col_g3, col_g4 = st.columns(2)
            with col_g3:
                df_os = pd.DataFrame([('Windows', df_filtrado['windows'].sum()), ('MacOS', df_filtrado['mac'].sum()), ('Linux', df_filtrado['linux'].sum())], columns=['SO', 'Compatibles'])
                fig3 = px.pie(df_os, names='SO', values='Compatibles', hole=0.5, title='Compatibilidad de Sistema Operativo', 
                              color='SO', color_discrete_map=RED_DONUT)
                st.plotly_chart(fig3, use_container_width=True)
            
            with col_g4:
                df_scat = df_filtrado[df_filtrado['metacritic_nota'].notna()]
                if not df_scat.empty:
                    fig4 = px.scatter(df_scat, x='precio_eur', y='metacritic_nota', size='jugadores_actuales', hover_name='nombre', title='Relación Precio y Crítica', 
                                      labels={'precio_eur': 'Precio (Euros)', 'metacritic_nota': 'Nota Crítica', 'nombre': 'Videojuego'},
                                      color='nombre')
                    st.plotly_chart(fig4, use_container_width=True)

            # --- CONTENIDO ADICIONAL Y EVOLUCIÓN DE PRECIO ---
            st.markdown("### Análisis de Modelo de Negocio por Juego")
            juego_analisis = st.selectbox("Selecciona un juego para ver su modelo de negocio:", df_filtrado['nombre'].unique(), key="sel_negocio")
            datos_juego = df_filtrado[df_filtrado['nombre'] == juego_analisis].iloc[0]
            
            # Obtener precio histórico de CheapShark
            with st.spinner("Consultando historial de precios en CheapShark..."):
                datos_historicos = obtener_precio_historico(datos_juego['appid'], juego_analisis)
            
            col_d1, col_d2 = st.columns([1, 2])
            with col_d1:
                st.metric("Contenido Adicional", int(datos_juego['contenido_adicional_count']))
                st.write(f"**Precio Base (sin descuento):** {datos_juego['precio_inicial']:.2f} €")
                st.write(f"**Precio Actual:** {datos_juego['precio_eur']:.2f} €")
                if datos_juego['descuento_pct'] > 0:
                    st.success(f"Descuento activo: **-{datos_juego['descuento_pct']}%**")
                if datos_historicos:
                    st.write(f"**Mínimo Histórico:** ${datos_historicos['precio_min_historico']:.2f} USD")
                    if datos_historicos.get('fecha_min_historico'):
                        st.caption(f"Registrado el {datos_historicos['fecha_min_historico']}")
                    if datos_historicos.get('precio_actual_usd') and datos_historicos.get('precio_retail_usd'):
                        ahorro = datos_historicos['precio_retail_usd'] - datos_historicos['precio_min_historico']
                        if ahorro > 0:
                            st.caption(f"Llegó a bajar ${ahorro:.2f} respecto a su precio base")
                else:
                    st.caption("Sin datos históricos disponibles en CheapShark.")
            with col_d2:
                fig_precio = generar_grafico_precio(datos_juego['precio_inicial'], datos_juego['precio_eur'], juego_analisis, datos_historicos)
                st.plotly_chart(fig_precio, use_container_width=True)

# ==========================================
# PESTAÑA 2: BUSCADOR GLOBAL
# ==========================================
with tab2:
    st.header("Explorador del Catálogo")
    st.write("Accede a las métricas en tiempo real de cualquier título fuera del Top 100.")
    
    df_all_apps = load_all_apps()
    
    if not df_all_apps.empty:
        texto_buscar = st.text_input("Escribe el nombre exacto o parte de él (Mínimo 3 letras):")
        
        if len(texto_buscar) >= 3:
            coincidencias = df_all_apps[df_all_apps['name'].str.contains(texto_buscar, case=False, na=False)]
            
            if not coincidencias.empty:
                coincidencias = coincidencias.copy()
                coincidencias['longitud'] = coincidencias['name'].str.len()
                juegos_opciones = coincidencias.sort_values('longitud').head(10)['name'].tolist()
                
                juego_seleccionado = st.selectbox("Resultados encontrados. Selecciona el correcto:", juegos_opciones)
                appid_buscar = int(coincidencias[coincidencias['name'] == juego_seleccionado]['appid'].iloc[0])
                
                st.markdown("---")
                
                col_b1, col_b2, col_b3 = st.columns([1, 1, 1])
                
                url_players = f"https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid={appid_buscar}"
                try:
                    res_players = session.get(url_players).json()
                    jugadores_vivo = res_players.get('response', {}).get('player_count', 0)
                except:
                    jugadores_vivo = 0
                    
                url_store = f"https://store.steampowered.com/api/appdetails?appids={appid_buscar}&cc=es"
                try:
                    res_store = session.get(url_store).json()
                    if res_store and str(appid_buscar) in res_store and res_store[str(appid_buscar)].get('success'):
                        data = res_store[str(appid_buscar)]['data']
                        es_gratis = data.get('is_free', False)
                        price_ov = data.get('price_overview', {})
                        precio_ini = price_ov.get('initial', 0) / 100 if not es_gratis else 0.0
                        precio_fin = price_ov.get('final', 0) / 100 if not es_gratis else 0.0
                        descuento = price_ov.get('discount_percent', 0)
                        contenido_adicional = len(data.get('dlc', []))
                        
                        # Obtener datos históricos de CheapShark
                        datos_hist_buscar = obtener_precio_historico(appid_buscar, data.get('name', ''))
                        
                        with col_b1:
                            st.image(data.get('header_image', ''), use_container_width=True)
                            st.metric("Contenido Adicional", contenido_adicional)
                        
                        with col_b2:
                            st.subheader(data.get('name'))
                            st.metric("Jugadores Actuales", f"{jugadores_vivo:,}".replace(',', '.'))
                            st.metric("Precio Actual", f"{precio_fin:.2f} €" if precio_fin > 0 else "Gratis")
                            if descuento > 0:
                                st.success(f"Descuento activo: **-{descuento}%**")
                            if datos_hist_buscar:
                                st.write(f"**Mínimo Histórico:** ${datos_hist_buscar['precio_min_historico']:.2f} USD")
                                if datos_hist_buscar.get('fecha_min_historico'):
                                    st.caption(f"Registrado el {datos_hist_buscar['fecha_min_historico']}")
                            
                        with col_b3:
                            fig_p_buscar = generar_grafico_precio(precio_ini, precio_fin, data.get('name'), datos_hist_buscar)
                            st.plotly_chart(fig_p_buscar, use_container_width=True)
                except Exception:
                    st.error("No se han podido obtener los datos de la tienda para este juego.")
            else:
                st.warning("No se ha encontrado ningún juego con ese nombre.")

# ==========================================
# PESTAÑA 3: NOTICIAS
# ==========================================
with tab3:
    st.header("Radar de Noticias Oficiales")
    if not df_super.empty:
        col_n1, col_n2, col_n3 = st.columns([2, 1, 1])
        with col_n1:
            juego_elegido = st.selectbox("Selecciona un juego para analizar sus noticias:", df_super['nombre'].unique())
            appid_elegido = df_super[df_super['nombre'] == juego_elegido]['appid'].iloc[0]
        with col_n2:
            filtro_tiempo = st.radio("Rango temporal:", ["Último Día", "Última Semana", "Último Mes", "Todo"], index=2)
        with col_n3:
            tipo_noticia = st.radio("Tipo de Contenido:", ["Todo", "Solo Parches y Actualizaciones", "Anuncios y Novedades"])

        df_news = load_news_data(appid_elegido)
        if not df_news.empty:
            hoy = pd.Timestamp.now()
            if filtro_tiempo == "Último Día": df_n_filtro = df_news[df_news['fecha_dt'] >= (hoy - pd.Timedelta(days=1))]
            elif filtro_tiempo == "Última Semana": df_n_filtro = df_news[df_news['fecha_dt'] >= (hoy - pd.Timedelta(days=7))]
            elif filtro_tiempo == "Último Mes": df_n_filtro = df_news[df_news['fecha_dt'] >= (hoy - pd.Timedelta(days=30))]
            else: df_n_filtro = df_news.copy()

            if tipo_noticia == "Solo Parches y Actualizaciones":
                df_n_filtro = df_n_filtro[df_n_filtro['feed_type'] == 1]
            elif tipo_noticia == "Anuncios y Novedades":
                df_n_filtro = df_n_filtro[df_n_filtro['feed_type'] == 0]

            st.markdown("---")
            if not df_n_filtro.empty:
                st.metric(label=f"Impactos Informativos (Unidades)", value=len(df_n_filtro))
                
                # Titulares primero
                st.subheader("Últimos Titulares")
                for _, row in df_n_filtro.head(5).iterrows():
                    st.markdown(f"**{row['fecha_dt'].strftime('%d/%m/%Y')}** - [{row['title']}]({row['url']})")
                
                # Gráficos al final, más pequeños, con eje X alineado
                st.markdown("---")
                df_temporal = df_n_filtro.copy()
                df_temporal['fecha_corta'] = df_temporal['fecha_dt'].dt.date
                conteo_temporal = df_temporal.groupby('fecha_corta').size()
                conteo_cats = df_n_filtro['feedlabel'].value_counts().sort_values(ascending=True)
                
                col_m1, col_m2 = st.columns(2)
                
                with col_m1:
                    st.caption("Publicaciones por Categoría")
                    fig_m1, ax_m1 = plt.subplots(figsize=(3.5, 1.8))
                    fig_m1.patch.set_alpha(0.0)
                    ax_m1.patch.set_alpha(0.0)
                    ax_m1.barh(conteo_cats.index, conteo_cats.values, color=RED_BASE, height=0.5)
                    ax_m1.spines['top'].set_visible(False)
                    ax_m1.spines['right'].set_visible(False)
                    ax_m1.tick_params(colors='gray', labelsize=7)
                    ax_m1.set_xlabel('Nº Publicaciones', fontsize=8, color='gray')
                    for spine in ax_m1.spines.values(): spine.set_edgecolor('gray')
                    fig_m1.tight_layout()
                    st.pyplot(fig_m1, transparent=True)
                
                with col_m2:
                    st.caption("Evolución Temporal")
                    fig_m2, ax_m2 = plt.subplots(figsize=(3.5, 1.8))
                    fig_m2.patch.set_alpha(0.0)
                    ax_m2.patch.set_alpha(0.0)
                    ax_m2.bar(conteo_temporal.index, conteo_temporal.values, color=RED_BASE, width=0.8)
                    ax_m2.spines['top'].set_visible(False)
                    ax_m2.spines['right'].set_visible(False)
                    ax_m2.tick_params(colors='gray', rotation=30, labelsize=7)
                    ax_m2.set_xlabel('Fecha', fontsize=8, color='gray')
                    ax_m2.set_ylabel('Nº Publicaciones', fontsize=8, color='gray')
                    for spine in ax_m2.spines.values(): spine.set_edgecolor('gray')
                    fig_m2.tight_layout()
                    st.pyplot(fig_m2, transparent=True)
            else:
                st.info(f"No hay noticias en el periodo/tipo seleccionado.")

# ==========================================
# PESTAÑA 4: PERFIL DE JUGADOR
# ==========================================
with tab4:
    st.header("Análisis de ADN de Jugador")
    st.write("Introduce el SteamID64 de un perfil público (ej: `76561197960435530`).")
    
    steam_id_input = st.text_input("SteamID64:", max_chars=17)
    
    if steam_id_input and len(steam_id_input) == 17:
        with st.spinner("Conectando con los servidores de Steam y procesando horas de juego..."):
            perfil, df_juegos, df_generos_jugador = load_player_profile(steam_id_input)
        
        if perfil:
            st.markdown("---")
            col_p1, col_p2 = st.columns([1, 4])
            with col_p1:
                st.image(perfil.get('avatarfull'), width=150)
            with col_p2:
                st.subheader(perfil.get('personaname', 'Desconocido'))
                horas_totales = df_juegos['playtime_forever'].sum() / 60
                st.write(f"**Juegos en Propiedad:** {len(df_juegos)}")
                st.write(f"**Tiempo Jugado Total:** {int(horas_totales):,} Horas".replace(',', '.'))

            if not df_juegos.empty and not df_generos_jugador.empty:
                col_j1, col_j2 = st.columns(2)
                
                with col_j1:
                    df_juegos['horas'] = df_juegos['playtime_forever'] / 60
                    top_juegos_jug = df_juegos.nlargest(10, 'horas').sort_values('horas')
                    fig_p1 = px.bar(top_juegos_jug, x='horas', y='name', orientation='h', 
                                    title='Juegos con Mayor Tiempo de Uso', 
                                    labels={'horas': 'Tiempo Jugado (Horas)', 'name': 'Videojuego'}, 
                                    color_discrete_sequence=[RED_BASE], template=PLOT_TEMPLATE)
                    st.plotly_chart(fig_p1, use_container_width=True)
                
                with col_j2:
                    radar_data = df_generos_jugador.groupby('genero')['minutos'].sum().reset_index()
                    radar_data['horas'] = radar_data['minutos'] / 60
                    fig_p2 = px.line_polar(radar_data, r='horas', theta='genero', line_close=True,
                                           title='Perfil por Categorías',
                                           labels={'horas': 'Tiempo Jugado (Horas)', 'genero': 'Categoría'},
                                           color_discrete_sequence=[RED_BASE], template=PLOT_TEMPLATE)
                    fig_p2.update_traces(fill='toself', fillcolor='rgba(255, 75, 75, 0.4)')
                    st.plotly_chart(fig_p2, use_container_width=True)