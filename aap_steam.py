##############################################
###     DASHBOARD DE STEAM EN STREAMLIT     ##
##############################################


## IMPORTACIONES

import streamlit as st

# 1. Configuración de la página (debe ser la primera instrucción de Streamlit)
st.set_page_config(page_title="Steam Analytics Dashboard", layout="wide")

# 2. Título principal en la parte superior
st.title("🎮 Dashboard de Análisis de Steam")
st.markdown("---") # Línea separadora visual

# 3. Creación de las tres pestañas (Tabs)
tab1, tab2, tab3 = st.tabs(["📈 Tendencias", "📰 Noticias", "👤 Jugador"])

# 4. Estructura interna de cada pestaña
with tab1:
    st.header("Tendencias Actuales de Steam")
    st.info("Aquí irán las gráficas del Top de juegos, géneros y precios.")
    # Más adelante pegaremos aquí el código de tus gráficas

with tab2:
    st.header("Noticias de Actualidad")
    st.info("Aquí irá el buscador de actualizaciones y parches.")

with tab3:
    st.header("Estadísticas de Perfil de Jugador")
    st.info("Aquí irá el análisis de la biblioteca de un usuario concreto.")