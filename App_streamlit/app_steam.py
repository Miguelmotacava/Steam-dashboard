import streamlit as st
import pandas as pd
from data_api import fetch_global_steam_data

from tab_tendencias import render_tendencias
from tab_noticias import render_noticias
from tab_jugador import render_jugador

st.set_page_config(page_title="Steam Analytics Dashboard", layout="wide")
st.markdown("""<style>.stProgress > div > div > div > div { background-color: #FF4B4B !important; }</style>""", unsafe_allow_html=True)

st.title("🎮 Dashboard de Análisis de Steam")

# El buscador global ha sido eliminado para máxima velocidad
tab1, tab2, tab3 = st.tabs(["📈 Tendencias", "📰 Noticias", "👤 Perfil de Jugador"])

num_juegos = st.slider("🎯 Límite de juegos del Top actual a analizar:", min_value=10, max_value=100, value=100, step=10)

df_super = pd.DataFrame()
try:
    df_super = fetch_global_steam_data(num_juegos)
except Exception as e:
    st.error(f"Error al analizar el mercado global: {e}")

st.markdown("---")

if not df_super.empty:
    with tab1: render_tendencias(df_super)
    with tab2: render_noticias(df_super)
    with tab3: render_jugador(df_super)
else:
    st.warning("⚠️ No se pudo cargar el mercado global. **En Streamlit Cloud:** ve a *Manage app* → *Settings* → *Secrets* y añade: `STEAM_API_KEY = \"tu_clave\"`")
    st.info("💡 Mientras tanto, puedes usar la pestaña **Perfil de Jugador** para analizar tu biblioteca de Steam.")
    with tab3: render_jugador(pd.DataFrame())