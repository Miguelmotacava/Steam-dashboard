import streamlit as st
from data_api import load_steam_data

from tab_tendencias import render_tendencias
from tab_noticias import render_noticias
from tab_jugador import render_jugador

st.set_page_config(page_title="Steam Analytics Dashboard", layout="wide")
st.markdown("""<style>.stProgress > div > div > div > div { background-color: #FF4B4B !important; }</style>""", unsafe_allow_html=True)

st.title("🎮 Dashboard de Análisis de Steam")
num_juegos = st.slider("🎯 Límite de juegos del Top actual a analizar:", 10, 100, 50, 10)
st.markdown("---")

df_super = load_steam_data(num_juegos)

# El buscador global ha sido eliminado para máxima velocidad
tab1, tab2, tab3 = st.tabs(["📈 Tendencias", "📰 Noticias", "👤 Perfil de Jugador"])

if not df_super.empty:
    with tab1: render_tendencias(df_super)
    with tab2: render_noticias(df_super)
    with tab3: render_jugador()
else:
    st.error("Error crítico: No se ha podido establecer conexión con la base de datos de Steam.")