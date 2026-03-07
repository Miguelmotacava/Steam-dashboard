import streamlit as st
import pandas as pd
import requests
import time
import os
import plotly.express as px
from dotenv import load_dotenv

# 1. Configuración inicial
st.set_page_config(page_title="Steam Analytics Dashboard", layout="wide")
load_dotenv()
STEAM_API_KEY = os.getenv("STEAM_API_KEY")

# 2. Función de Extracción con Caché parametrizada
# Le pasamos show_spinner=False para que no se superponga con nuestra barra de progreso
@st.cache_data(ttl=3600, show_spinner=False) 
def load_steam_data(limite):
    url_top = f"https://api.steampowered.com/ISteamChartsService/GetGamesByConcurrentPlayers/v1/?key={STEAM_API_KEY}"
    res_top = requests.get(url_top).json()
    
    # Usamos el límite que ha elegido el usuario en lugar de 50
    top_juegos = res_top.get('response', {}).get('ranks', [])[:limite]
    
    df_jugadores = pd.DataFrame(top_juegos)
    df_jugadores.rename(columns={'concurrent_in_game': 'jugadores_actuales'}, inplace=True)
    
    datos_tienda = []
    
    # Barra de progreso visual en la parte superior
    progress_text = f"⏳ Descargando datos en vivo de los {limite} juegos más populares. Por favor, espera..."
    my_bar = st.progress(0, text=progress_text)
    
    for i, appid in enumerate(df_jugadores['appid']):
        url_store = f"https://store.steampowered.com/api/appdetails?appids={appid}&cc=es"
        res_store = requests.get(url_store).json()
        
        if res_store and str(appid) in res_store and res_store[str(appid)].get('success'):
            data = res_store[str(appid)]['data']
            datos_tienda.append({
                'appid': appid,
                'nombre': data.get('name', 'Desconocido'),
                'es_gratis': data.get('is_free', False),
                'precio_eur': data.get('price_overview', {}).get('final', 0) / 100 if not data.get('is_free', False) else 0.0,
                'metacritic_nota': data.get('metacritic', {}).get('score', None),
                'windows': data.get('platforms', {}).get('windows', False),
                'mac': data.get('platforms', {}).get('mac', False),
                'linux': data.get('platforms', {}).get('linux', False),
                'generos': ", ".join([g['description'] for g in data.get('genres', [])])
            })
        time.sleep(1.2) # Pausa para no saturar la API
        my_bar.progress((i + 1) / len(df_jugadores), text=progress_text)
        
    my_bar.empty() # Borra la barra al terminar
    df_tienda = pd.DataFrame(datos_tienda)
    return pd.merge(df_tienda, df_jugadores, on='appid', how='inner')

# 3. Interfaz de Usuario (Cabecera)
st.title("🎮 Dashboard de Análisis de Steam")

# El usuario decide el límite ANTES de cargar los datos
st.markdown("### Configuración de Análisis")
num_juegos = st.slider("🎯 Selecciona el número de juegos del Top a analizar:", min_value=10, max_value=100, value=50, step=10)
st.markdown("---")

# Cargamos los datos (la barra de progreso aparecerá justo aquí, arriba de las pestañas)
df_super = load_steam_data(num_juegos)

# 4. Creamos las pestañas
tab1, tab2, tab3 = st.tabs(["📈 Tendencias", "📰 Noticias", "👤 Jugador"])

with tab1:
    st.header(f"📈 Tendencias Actuales en el Top {num_juegos}")
    
    # --- PALETA DE COLORES STEAM ---
    STEAM_COLORS = ['#66c0f4', '#2a475e', '#c7d5e0', '#1b2838', '#171a21']
    PLOT_TEMPLATE = "plotly_white" 
    
    # --- FILTROS ---
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        juegos_seleccionados = st.multiselect("🎮 Filtrar por Videojuego", options=df_super['nombre'].unique())
    with col_f2:
        plataforma = st.selectbox("💻 Filtrar por Plataforma", ["Todas", "Windows", "MacOS", "Linux"])
    with col_f3:
        todos_generos = set()
        for gen in df_super['generos'].dropna():
            todos_generos.update(gen.split(', '))
        genero_seleccionado = st.selectbox("🎭 Filtrar por Género", ["Todos"] + sorted(list(todos_generos)))

    # --- LÓGICA DE FILTRADO ---
    df_filtrado = df_super.copy()
    
    if juegos_seleccionados:
        df_filtrado = df_filtrado[df_filtrado['nombre'].isin(juegos_seleccionados)]
    if plataforma == "Windows":
        df_filtrado = df_filtrado[df_filtrado['windows'] == True]
    elif plataforma == "MacOS":
        df_filtrado = df_filtrado[df_filtrado['mac'] == True]
    elif plataforma == "Linux":
        df_filtrado = df_filtrado[df_filtrado['linux'] == True]
    if genero_seleccionado != "Todos":
        df_filtrado = df_filtrado[df_filtrado['generos'].str.contains(genero_seleccionado, na=False)]

    st.markdown("---")

    # Si hay datos después de filtrar, mostramos el Dashboard
    if not df_filtrado.empty:
        
        # --- WIDGETS DE MÉTRICAS (KPIs) ---
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        total_jugadores = int(df_filtrado['jugadores_actuales'].sum())
        precio_medio = df_filtrado[df_filtrado['precio_eur'] > 0]['precio_eur'].mean()
        juegos_gratis = df_filtrado['es_gratis'].sum()
        
        kpi1.metric(label="👥 Jugadores Totales", value=f"{total_jugadores:,}".replace(',', '.'))
        kpi2.metric(label="🕹️ Juegos en Pantalla", value=len(df_filtrado))
        kpi3.metric(label="💸 Precio Medio (De Pago)", value=f"{precio_medio:.2f} €" if pd.notna(precio_medio) else "0.00 €")
        kpi4.metric(label="🎁 Juegos Gratuitos", value=int(juegos_gratis))
        
        st.markdown("<br>", unsafe_allow_html=True)

        # --- FILA 1 DE GRÁFICAS ---
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            # 1. Top Juegos 
            df_plot1 = df_filtrado.nlargest(10, 'jugadores_actuales').sort_values('jugadores_actuales')
            fig1 = px.bar(
                df_plot1, x='jugadores_actuales', y='nombre', orientation='h',
                title='🏆 Top 10 Juegos por Jugadores',
                labels={'jugadores_actuales': 'Jugadores', 'nombre': ''},
                color_discrete_sequence=[STEAM_COLORS[0]], template=PLOT_TEMPLATE
            )
            st.plotly_chart(fig1, use_container_width=True)

        with col_g2:
            # 2. Comparación de Categorías/Géneros
            df_gen = df_filtrado.assign(genero_indv=df_filtrado['generos'].str.split(', ')).explode('genero_indv')
            df_gen_agrupado = df_gen.groupby('genero_indv')['jugadores_actuales'].sum().reset_index()
            df_gen_agrupado = df_gen_agrupado[df_gen_agrupado['jugadores_actuales'] > 0]
            
            fig2 = px.treemap(
                df_gen_agrupado, path=['genero_indv'], values='jugadores_actuales',
                title='🎭 Distribución de Jugadores por Género',
                color='jugadores_actuales', color_continuous_scale='Blues',
                template=PLOT_TEMPLATE
            )
            st.plotly_chart(fig2, use_container_width=True)

        # --- FILA 2 DE GRÁFICAS ---
        col_g3, col_g4 = st.columns(2)
        
        with col_g3:
            # 3. Soporte por Sistema Operativo
            os_counts = {
                'Windows': df_filtrado['windows'].sum(),
                'MacOS': df_filtrado['mac'].sum(),
                'Linux': df_filtrado['linux'].sum()
            }
            df_os = pd.DataFrame(list(os_counts.items()), columns=['SO', 'Compatibles'])
            
            fig3 = px.pie(
                df_os, names='SO', values='Compatibles', hole=0.5,
                title='🖥️ Compatibilidad de SO en esta selección',
                color='SO', color_discrete_map={'Windows': STEAM_COLORS[0], 'MacOS': STEAM_COLORS[2], 'Linux': STEAM_COLORS[1]},
                template=PLOT_TEMPLATE
            )
            st.plotly_chart(fig3, use_container_width=True)

        with col_g4:
            # 4. Precio vs Metacritic vs Jugadores
            df_scatter = df_filtrado[df_filtrado['metacritic_nota'].notna()]
            if not df_scatter.empty:
                fig4 = px.scatter(
                    df_scatter, x='precio_eur', y='metacritic_nota', 
                    size='jugadores_actuales', hover_name='nombre',
                    title='💎 Precio vs Crítica (Tamaño = Jugadores)',
                    labels={'precio_eur': 'Precio (€)', 'metacritic_nota': 'Nota Metacritic'},
                    color_discrete_sequence=[STEAM_COLORS[1]], template=PLOT_TEMPLATE
                )
                st.plotly_chart(fig4, use_container_width=True)
            else:
                st.info("No hay suficientes datos de Metacritic para dibujar esta gráfica.")

    else:
        st.warning("⚠️ No hay juegos que cumplan con los filtros seleccionados.")

with tab2:
    st.header("Noticias de Actualidad")
    st.info("Próximamente...")

with tab3:
    st.header("Estadísticas de Perfil de Jugador")
    st.info("Próximamente...")