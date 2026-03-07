import streamlit as st
from data_api import load_steam_data

# Importamos las funciones que dibujan cada pestaña
from tab_tendencias import render_tendencias
from tab_buscador import render_buscador
from tab_noticias import render_noticias
from tab_jugador import render_jugador

# 1. Configuración de página y estilos CSS (Barra roja)
st.set_page_config(page_title="Steam Analytics Dashboard", layout="wide")
st.markdown("""<style>.stProgress > div > div > div > div { background-color: #FF4B4B !important; }</style>""", unsafe_allow_html=True)

# 2. Cabecera principal
st.title("🎮 Dashboard de Análisis de Steam")
num_juegos = st.slider("🎯 Selecciona el número de juegos del Top a analizar:", 10, 100, 50, 10)
st.markdown("---")

# 3. Descarga de datos globales
df_super = load_steam_data(num_juegos)

# 4. Creación de pestañas modulares
tab1, tab2, tab3, tab4 = st.tabs(["📈 Tendencias", "🔎 Buscador Global", "📰 Noticias", "👤 Perfil de Jugador"])

if not df_super.empty:
    with tab1: render_tendencias(df_super)
    with tab2: render_buscador()
    with tab3: render_noticias(df_super)
    with tab4: render_jugador()
else:
    st.error("Error crítico: No se ha podido establecer conexión con la base de datos de Steam.")