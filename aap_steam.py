##############################################
###     DASHBOARD DE STEAM EN STREAMLIT     ##
##############################################


## IMPORTACIONES

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

# 2. Función de Extracción con Caché (¡Vital para Streamlit!)
@st.cache_data(ttl=3600) # Guarda los datos 1 hora en memoria
def load_steam_data():
    url_top = f"https://api.steampowered.com/ISteamChartsService/GetGamesByConcurrentPlayers/v1/?key={STEAM_API_KEY}"
    res_top = requests.get(url_top).json()
    top_juegos = res_top.get('response', {}).get('ranks', [])[:50]
    
    df_jugadores = pd.DataFrame(top_juegos)
    df_jugadores.rename(columns={'concurrent_in_game': 'jugadores_actuales'}, inplace=True)
    
    datos_tienda = []
    
    # Barra de progreso visual en Streamlit mientras carga
    progress_text = "Descargando datos en vivo de Steam. Por favor, espera..."
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
        time.sleep(1.2)
        my_bar.progress((i + 1) / len(df_jugadores), text=progress_text)
        
    my_bar.empty() # Borra la barra al terminar
    df_tienda = pd.DataFrame(datos_tienda)
    return pd.merge(df_tienda, df_jugadores, on='appid', how='inner')

# 3. Interfaz de Usuario
st.title("🎮 Dashboard de Análisis de Steam")
st.markdown("---")

# Cargamos los datos
df_super = load_steam_data()

# Creamos las pestañas
tab1, tab2, tab3 = st.tabs(["📈 Tendencias", "📰 Noticias", "👤 Jugador"])

with tab1:
    st.header("Tendencias Actuales en el Top 50")
    
    # FILTROS EN COLUMNAS
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Filtro de Videojuego (Multiselect)
        juegos_seleccionados = st.multiselect("Filtrar por Videojuego", options=df_super['nombre'].unique())
        
    with col2:
        # Filtro de Plataforma (Selectbox)
        plataforma = st.selectbox("Filtrar por Plataforma", ["Todas", "Windows", "MacOS", "Linux"])
        
    with col3:
        # Filtro de Categoría/Género (buscamos géneros únicos)
        todos_generos = set()
        for gen in df_super['generos'].dropna():
            todos_generos.update(gen.split(', '))
        genero_seleccionado = st.selectbox("Filtrar por Género", ["Todos"] + sorted(list(todos_generos)))

    # APLICAR LOS FILTROS AL DATAFRAME
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
        # Comprobamos si el string del género seleccionado está dentro de la columna 'generos'
        df_filtrado = df_filtrado[df_filtrado['generos'].str.contains(genero_seleccionado, na=False)]

    st.markdown("---")
    
    # REPRESENTACIONES PLOTLY (usando df_filtrado)
    if not df_filtrado.empty:
        col_graf1, col_graf2 = st.columns(2)
        
        with col_graf1:
            # Gráfica 1: Top Jugadores
            fig1 = px.bar(
                df_filtrado.nlargest(15, 'jugadores_actuales').sort_values('jugadores_actuales'), 
                x='jugadores_actuales', y='nombre', orientation='h',
                title='Top Juegos por Jugadores Concurrentes',
                color='jugadores_actuales', color_continuous_scale='Viridis'
            )
            st.plotly_chart(fig1, use_container_width=True)
            
        with col_graf2:
            # Gráfica 2: Precio vs Popularidad
            df_precio = df_filtrado[df_filtrado['metacritic_nota'].notna()]
            if not df_precio.empty:
                fig2 = px.scatter(
                    df_precio, x='precio_eur', y='jugadores_actuales', 
                    size='metacritic_nota', hover_name='nombre',
                    title='Precio vs Jugadores (Burbuja = Nota Crítica)',
                    color='es_gratis'
                )
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("No hay suficientes datos de Metacritic para esta selección.")
    else:
        st.warning("No hay juegos que cumplan con los filtros seleccionados.")

with tab2:
    st.header("Noticias de Actualidad")
    st.info("Próximamente...")

with tab3:
    st.header("Estadísticas de Perfil de Jugador")
    st.info("Próximamente...")