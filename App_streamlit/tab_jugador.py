import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from data_api import fetch_user_profile, obtener_steam_id_real

RED_BASE = '#FF4B4B'

def aplicar_estilo_transparente(fig):
    """Elimina fondos y ajusta colores para que coincidan con el tema oscuro de Streamlit"""
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color="white",
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
        yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
    )
    return fig

def render_jugador():
    st.header("👤 Análisis de ADN de Jugador")
    st.write("Visualiza tu biblioteca y estadísticas personales de Steam.")
    
    # Formulario de búsqueda mejorado
    with st.container():
        col_j_input, col_j_btn = st.columns([4, 1])
        with col_j_input: 
            input_perfil = st.text_input("🔍 SteamID o URL:", placeholder="https://steamcommunity.com/profiles/76561199435323272")
        with col_j_btn: 
            st.markdown("<br>", unsafe_allow_html=True)
            submit_jugador = st.button("🚀 Analizar Perfil")
        
    if (submit_jugador or st.session_state.get('last_id') == input_perfil) and input_perfil:
        steamid_real = obtener_steam_id_real(input_perfil)
        if not steamid_real:
            st.error("❌ Formato no válido. Introduce una URL o ID de 17 dígitos.")
            return

        with st.spinner("📊 Procesando metadatos de biblioteca..."):
            try:
                perfil, df_juegos, df_generos_jugador = fetch_user_profile(steamid_real)
            except Exception as e:
                st.error(f"❌ Error de conexión: {e}")
                perfil = None
        
        if perfil:
            # --- CABECERA DE PERFIL ---
            col_avatar, col_info, col_metrics = st.columns([1, 2, 2])
            with col_avatar: 
                st.image(perfil.get('avatarfull'), width=150)
            with col_info:
                st.markdown(f"### {perfil.get('personaname')}")
                st.caption(f"ID: {steamid_real}")
                if perfil.get('loccountrycode'):
                    st.write(f"📍 Región: {perfil.get('loccountrycode')}")
            
            # --- WIDGETS DE MÉTRICAS ---
            if not df_juegos.empty:
                horas_totales = int(df_juegos['playtime_forever'].sum()/60)
                with col_metrics:
                    m1, m2 = st.columns(2)
                    m1.metric("Total Juegos", len(df_juegos))
                    m2.metric("Horas de Vida", f"{horas_totales:,}")
                    
                st.markdown("---")

                # --- FILA 1: GRÁFICOS PRINCIPALES ---
                col_g1, col_g2 = st.columns(2)
                
                with col_g1:
                    df_mostrar = df_juegos.nlargest(10, 'playtime_forever').copy()
                    df_mostrar['horas'] = (df_mostrar['playtime_forever'] / 60).round(1)
                    fig_p1 = px.bar(
                        df_mostrar.sort_values('horas'), 
                        x='horas', y='name', 
                        orientation='h', 
                        title='🏆 Top 10 Juegos (Horas)',
                        color='horas',
                        color_continuous_scale=['#444', RED_BASE]
                    )
                    st.plotly_chart(aplicar_estilo_transparente(fig_p1), use_container_width=True)
                
                with col_g2:
                    if not df_generos_jugador.empty:
                        radar_data = df_generos_jugador.groupby('genero')['minutos'].sum().reset_index()
                        radar_data['horas'] = radar_data['minutos'] / 60
                        fig_p2 = px.line_polar(
                            radar_data, r='horas', theta='genero', 
                            line_close=True, title='🕸️ ADN por Categorías',
                            color_discrete_sequence=[RED_BASE]
                        )
                        fig_p2.update_traces(fill='toself', fillcolor='rgba(255, 75, 75, 0.3)')
                        st.plotly_chart(aplicar_estilo_transparente(fig_p2), use_container_width=True)

                # --- FILA 2: NUEVAS GRÁFICAS RECOMENDADAS ---
                st.markdown("### 🔍 Análisis de Inversión de Tiempo")
                col_g3, col_g4 = st.columns([2, 1])
                
                with col_g3:
                    # Gráfico de dispersión: Horas vs Juegos (para detectar outliers o juegos abandonados)
                    df_juegos['horas'] = df_juegos['playtime_forever'] / 60
                    fig_scatter = px.scatter(
                        df_juegos[df_juegos['horas'] > 0], 
                        x='horas', y='name',
                        size='horas', 
                        color='horas',
                        title="📍 Distribución de Tiempo por Título",
                        color_continuous_scale=['#FF8080', RED_BASE]
                    )
                    st.plotly_chart(aplicar_estilo_transparente(fig_scatter), use_container_width=True)
                
                with col_g4:
                    # Widget de "Estado de la Biblioteca"
                    juegos_jugados = len(df_juegos[df_juegos['playtime_forever'] > 0])
                    juegos_virgenes = len(df_juegos[df_juegos['playtime_forever'] == 0])
                    
                    fig_pie = go.Figure(data=[go.Pie(
                        labels=['Jugados', 'Sin Abrir'],
                        values=[juegos_jugados, juegos_virgenes],
                        hole=.6,
                        marker_colors=[RED_BASE, '#333']
                    )])
                    fig_pie.update_layout(title="📦 Salud de la Biblioteca", showlegend=False)
                    st.plotly_chart(aplicar_estilo_transparente(fig_pie), use_container_width=True)
                    st.caption(f"Tienes {juegos_virgenes} juegos en el 'Backlog' (sin jugar).")

            else:
                st.warning("⚠️ **Perfil Privado:** Steam impide leer tus juegos. Ve a 'Configuración de Privacidad' en Steam y pon 'Detalles de los juegos' en **Público**.")
        else: 
            st.error("❌ No se pudo recuperar el perfil. Verifica que el ID sea correcto.")