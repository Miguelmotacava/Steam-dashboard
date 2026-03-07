import streamlit as st
import plotly.express as px
from data_api import fetch_user_profile, obtener_steam_id_real

RED_BASE = '#FF4B4B'

def render_jugador():
    st.header("👤 Análisis de ADN de Jugador")
    st.write("Pega tu SteamID64 o la **URL completa** de tu perfil público.")
    
    with st.form("jugador_form"):
        col_j_input, col_j_btn = st.columns([4, 1])
        with col_j_input: input_perfil = st.text_input("🔍 SteamID o URL (ej: https://steamcommunity.com/profiles/...):")
        with col_j_btn: 
            st.markdown("<br>", unsafe_allow_html=True)
            submit_jugador = st.form_submit_button("Analizar Perfil")
        
    if submit_jugador and input_perfil:
        steamid_real = obtener_steam_id_real(input_perfil)
        if not steamid_real:
            st.error("Formato no válido. Asegúrate de introducir una URL válida o el ID de 17 dígitos.")
            return

        with st.spinner("⏳ Conectando con Steam y extrayendo biblioteca..."):
            try:
                perfil, df_juegos, df_generos_jugador = fetch_user_profile(steamid_real)
            except Exception as e:
                st.error(f"❌ Error al cargar tu perfil: {e}")
                perfil = None
        
        if perfil:
            col_p1, col_p2 = st.columns([1, 4])
            with col_p1: st.image(perfil.get('avatarfull'), width=150)
            with col_p2:
                st.subheader(perfil.get('personaname', 'Desconocido'))
                
                if df_juegos.empty:
                    st.warning("⚠️ **ATENCIÓN:** Tu perfil general es público, pero tus 'Detalles de los Juegos' están configurados como Privados. Ve a tu cuenta de Steam > Modificar Perfil > Configuración de Privacidad > Pon 'Detalles de los juegos' en Público.")
                else:
                    st.write(f"🎮 **Juegos Extraídos:** {len(df_juegos)}")
                    st.write(f"⏱️ **Horas Totales:** {int(df_juegos['playtime_forever'].sum()/60):,}")

                    if not df_generos_jugador.empty:
                        col_j1, col_j2 = st.columns(2)
                        with col_j1:
                            df_mostrar = df_juegos.copy()
                            df_mostrar['horas'] = df_mostrar['playtime_forever'] / 60
                            fig_p1 = px.bar(df_mostrar.nlargest(10, 'horas').sort_values('horas'), x='horas', y='name', orientation='h', title='🏆 Más Jugados', color_discrete_sequence=[RED_BASE])
                            st.plotly_chart(fig_p1, use_container_width=True)
                        with col_j2:
                            radar_data = df_generos_jugador.groupby('genero')['minutos'].sum().reset_index()
                            fig_p2 = px.line_polar(radar_data, r=radar_data['minutos']/60, theta='genero', line_close=True, title='🕸️ ADN por Categorías', color_discrete_sequence=[RED_BASE])
                            fig_p2.update_traces(fill='toself', fillcolor='rgba(255, 75, 75, 0.4)')
                            st.plotly_chart(fig_p2, use_container_width=True)
        else: st.error("❌ Perfil no encontrado o no existe.")