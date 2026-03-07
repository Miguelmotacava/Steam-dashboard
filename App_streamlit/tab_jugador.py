import streamlit as st
import plotly.express as px
from data_api import load_player_profile

RED_BASE = '#FF4B4B'

def render_jugador():
    st.header("👤 Análisis de ADN de Jugador")
    st.write("Introduce un SteamID64 público (ej: `76561197960435530`).")
    
    with st.form("jugador_form"):
        steam_id_input = st.text_input("🔍 SteamID64:")
        buscar_btn = st.form_submit_button("Analizar Perfil")
        
    if buscar_btn and len(steam_id_input) == 17:
        with st.spinner("⏳ Analizando ADN de la biblioteca..."):
            perfil, df_juegos, df_generos_jugador = load_player_profile(steam_id_input)
        
        if perfil:
            col_p1, col_p2 = st.columns([1, 4])
            with col_p1: st.image(perfil.get('avatarfull'), width=150)
            with col_p2:
                st.subheader(perfil.get('personaname', 'Desconocido'))
                st.write(f"🎮 **Juegos:** {len(df_juegos)}")
                st.write(f"⏱️ **Horas Totales:** {int(df_juegos['playtime_forever'].sum()/60):,}")

            if not df_juegos.empty and not df_generos_jugador.empty:
                col_j1, col_j2 = st.columns(2)
                with col_j1:
                    df_juegos['horas'] = df_juegos['playtime_forever'] / 60
                    fig_p1 = px.bar(df_juegos.nlargest(10, 'horas').sort_values('horas'), x='horas', y='name', orientation='h', title='🏆 Más Jugados', color_discrete_sequence=[RED_BASE])
                    st.plotly_chart(fig_p1, use_container_width=True)
                with col_j2:
                    radar_data = df_generos_jugador.groupby('genero')['minutos'].sum().reset_index()
                    fig_p2 = px.line_polar(radar_data, r=radar_data['minutos']/60, theta='genero', line_close=True, title='🕸️ ADN por Categorías', color_discrete_sequence=[RED_BASE])
                    fig_p2.update_traces(fill='toself', fillcolor='rgba(255, 75, 75, 0.4)')
                    st.plotly_chart(fig_p2, use_container_width=True)
        else: st.error("❌ Perfil no encontrado o privado.")