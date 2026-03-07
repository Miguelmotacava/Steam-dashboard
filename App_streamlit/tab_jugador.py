import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from data_api import fetch_user_profile, obtener_steam_id_real

RED_BASE = '#FF4B4B'
GRIS_OSCURO = '#2d2d2d'


def aplicar_tema_oscuro_transparente(fig, es_radar=False):
    """
    Modifica el layout de cualquier figura Plotly para tema Dark Mode transparente.
    paper_bgcolor y plot_bgcolor: rgba(0,0,0,0).
    Texto en blanco, grid en rgba(255,255,255,0.1).
    Lógica específica para ejes polares si es_radar=True.
    """
    layout_base = dict(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white', size=12),
        title_font=dict(color='white'),
        margin=dict(l=20, r=20, t=50, b=20),
        showlegend=True,
        legend=dict(font=dict(color='white'), bgcolor='rgba(0,0,0,0)'),
    )

    if es_radar:
        layout_base.update(
            polar=dict(
                bgcolor='rgba(0,0,0,0)',
                radialaxis=dict(
                    gridcolor='rgba(255,255,255,0.1)',
                    tickfont=dict(color='white'),
                    linecolor='rgba(255,255,255,0.1)',
                ),
                angularaxis=dict(
                    gridcolor='rgba(255,255,255,0.1)',
                    tickfont=dict(color='white'),
                    linecolor='rgba(255,255,255,0.1)',
                ),
            )
        )
    else:
        layout_base.update(
            xaxis=dict(
                gridcolor='rgba(255,255,255,0.1)',
                tickfont=dict(color='white'),
                zerolinecolor='rgba(255,255,255,0.1)',
            ),
            yaxis=dict(
                gridcolor='rgba(255,255,255,0.1)',
                tickfont=dict(color='white'),
                zerolinecolor='rgba(255,255,255,0.1)',
            ),
        )

    fig.update_layout(**layout_base)
    return fig


def render_jugador():
    st.header("👤 Análisis de ADN de Jugador")
    st.write("Pega tu SteamID64 o la **URL completa** de tu perfil público.")

    with st.form("jugador_form"):
        col_j_input, col_j_btn = st.columns([4, 1])
        with col_j_input:
            input_perfil = st.text_input(
                "🔍 SteamID o URL (ej: https://steamcommunity.com/profiles/...):"
            )
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
            # --- FILA SUPERIOR: Avatar | Nombre+ID | Métricas [1, 2, 2] ---
            col_avatar, col_info, col_metrics = st.columns([1, 2, 2])
            with col_avatar:
                st.image(perfil.get('avatarfull'), width=150)
            with col_info:
                st.subheader(perfil.get('personaname', 'Desconocido'))
                st.caption(f"ID: {steamid_real}")
            with col_metrics:
                if not df_juegos.empty:
                    horas_totales = int(df_juegos['playtime_forever'].sum() / 60)
                    m1, m2 = st.columns(2)
                    m1.metric("🎮 Juegos Totales", len(df_juegos))
                    m2.metric("⏱️ Horas Totales", f"{horas_totales:,}")
                else:
                    st.metric("🎮 Juegos Totales", "—")

            if df_juegos.empty:
                st.warning(
                    "⚠️ **ATENCIÓN:** Tu perfil general es público, pero tus 'Detalles de los Juegos' "
                    "están configurados como Privados. Ve a tu cuenta de Steam > Modificar Perfil > "
                    "Configuración de Privacidad > Pon 'Detalles de los juegos' en Público."
                )
            else:
                st.markdown("---")

                # --- FILA DE GRÁFICOS 1: Bar horizontal | Radar ---
                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    df_top10 = df_juegos.nlargest(10, 'playtime_forever').copy()
                    df_top10['horas'] = df_top10['playtime_forever'] / 60
                    fig_bar = px.bar(
                        df_top10.sort_values('horas'),
                        x='horas',
                        y='name',
                        orientation='h',
                        title='🏆 Top 10 Juegos por Horas',
                        color_discrete_sequence=[RED_BASE],
                    )
                    st.plotly_chart(
                        aplicar_tema_oscuro_transparente(fig_bar),
                        use_container_width=True,
                    )

                with col_g2:
                    if not df_generos_jugador.empty:
                        radar_data = (
                            df_generos_jugador.groupby('genero')['minutos']
                            .sum()
                            .reset_index()
                        )
                        radar_data['horas'] = radar_data['minutos'] / 60
                        fig_radar = px.line_polar(
                            radar_data,
                            r='horas',
                            theta='genero',
                            line_close=True,
                            title='🕸️ ADN por Géneros',
                            color_discrete_sequence=[RED_BASE],
                        )
                        fig_radar.update_traces(
                            fill='toself',
                            fillcolor='rgba(255, 75, 75, 0.4)',
                        )
                        st.plotly_chart(
                            aplicar_tema_oscuro_transparente(fig_radar, es_radar=True),
                            use_container_width=True,
                        )
                    else:
                        st.info("No hay datos de géneros para el radar.")

                st.markdown("---")

                # --- FILA DE GRÁFICOS 2: Scatter | Donut Backlog ---
                col_g3, col_g4 = st.columns(2)
                with col_g3:
                    df_scatter = df_juegos.copy()
                    df_scatter['horas'] = df_scatter['playtime_forever'] / 60
                    df_scatter_activos = df_scatter[df_scatter['horas'] > 0]
                    if not df_scatter_activos.empty:
                        fig_scatter = px.scatter(
                            df_scatter_activos,
                            x='horas',
                            y='name',
                            size='horas',
                            title='📍 Distribución de Tiempo por Juego',
                            color_discrete_sequence=[RED_BASE],
                        )
                        fig_scatter.update_traces(marker=dict(color=RED_BASE))
                        st.plotly_chart(
                            aplicar_tema_oscuro_transparente(fig_scatter),
                            use_container_width=True,
                        )
                    else:
                        st.info("No hay juegos con horas jugadas para mostrar.")

                with col_g4:
                    juegos_jugados = len(df_juegos[df_juegos['playtime_forever'] > 0])
                    juegos_backlog = len(df_juegos[df_juegos['playtime_forever'] == 0])
                    fig_donut = go.Figure(
                        data=[
                            go.Pie(
                                labels=['Jugados', 'Backlog (0h)'],
                                values=[juegos_jugados, juegos_backlog],
                                hole=0.6,
                                marker_colors=[RED_BASE, GRIS_OSCURO],
                                textinfo='label+percent',
                                textfont=dict(color='white'),
                            )
                        ]
                    )
                    fig_donut.update_layout(title='📦 Estado de la Biblioteca')
                    st.plotly_chart(
                        aplicar_tema_oscuro_transparente(fig_donut),
                        use_container_width=True,
                    )
        else:
            st.error("❌ Perfil no encontrado o no existe.")
