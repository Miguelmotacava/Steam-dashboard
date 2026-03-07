import streamlit as st
import pandas as pd
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
                    range=[0, 100],
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
                        labels={'horas': 'Tiempo Invertido (Horas)', 'name': 'Videojuego'},
                    )
                    fig_bar.update_traces(hovertemplate='<b>%{y}</b><br>Tiempo Invertido: %{x:.1f} Horas<extra></extra>')
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
                        total_minutos_top15 = radar_data['minutos'].sum()
                        radar_data['porcentaje'] = (
                            (radar_data['minutos'] / total_minutos_top15 * 100)
                            if total_minutos_top15 > 0 else 0
                        )
                        fig_radar = px.line_polar(
                            radar_data,
                            r='porcentaje',
                            theta='genero',
                            line_close=True,
                            title='🕸️ ADN por Géneros',
                            color_discrete_sequence=[RED_BASE],
                            range_r=[0, 100],
                            labels={
                                'porcentaje': 'Porcentaje De Horas (%)',
                                'genero': 'Género',
                            },
                        )
                        fig_radar.update_traces(
                            fill='toself',
                            fillcolor='rgba(255, 75, 75, 0.4)',
                            hovertemplate='<b>%{theta}</b><br>Porcentaje: %{r:.1f} %<extra></extra>',
                        )
                        st.plotly_chart(
                            aplicar_tema_oscuro_transparente(fig_radar, es_radar=True),
                            use_container_width=True,
                        )
                    else:
                        st.info("No hay datos de géneros para el radar.")

                st.markdown("---")

                # --- FILA DE GRÁFICOS 2: Treemap | Donut Backlog ---
                col_g3, col_g4 = st.columns(2)
                with col_g3:
                    df_jugados = df_juegos.copy()
                    df_jugados['horas'] = df_jugados['playtime_forever'] / 60
                    df_treemap = df_jugados[df_jugados['horas'] >= 1]
                    if not df_treemap.empty:
                        fig_treemap = px.treemap(
                            df_treemap,
                            path=[px.Constant("Biblioteca"), 'name'],
                            values='horas',
                            title='📍 Distribución del Tiempo',
                            color_discrete_sequence=[RED_BASE],
                        )
                        fig_treemap.update_traces(
                            marker=dict(cornerradius=4),
                            textinfo='label+value+percent parent',
                            hovertemplate='<b>%{label}</b><br>Tiempo Invertido: %{value:.1f} Horas<br>Porcentaje: %{percentParent:.1%}<extra></extra>',
                        )
                        st.plotly_chart(
                            aplicar_tema_oscuro_transparente(fig_treemap),
                            use_container_width=True,
                        )
                    else:
                        st.info("No hay juegos con más de 1 hora jugada para mostrar.")

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
                                hovertemplate='<b>%{label}</b><br>Juegos: %{value}<br>Porcentaje: %{percent}<extra></extra>',
                            )
                        ]
                    )
                    fig_donut.update_layout(title='📦 Estado de la Biblioteca')
                    st.plotly_chart(
                        aplicar_tema_oscuro_transparente(fig_donut),
                        use_container_width=True,
                    )

                # --- FILA: Historial de Actividad (Juegos Activos por Año) ---
                if 'rtime_last_played' in df_juegos.columns:
                    df_actividad = df_juegos[df_juegos['rtime_last_played'] > 0].copy()
                    if not df_actividad.empty:
                        df_actividad['fecha_ultima'] = pd.to_datetime(
                            df_actividad['rtime_last_played'], unit='s'
                        )
                        df_actividad['año'] = df_actividad['fecha_ultima'].dt.year.astype(int)
                        juegos_por_año = (
                            df_actividad.groupby('año')['name']
                            .apply(lambda x: '<br>'.join(x.astype(str)))
                            .reset_index()
                        )
                        conteo_por_año = (
                            df_actividad.groupby('año').size().reset_index(name='juegos')
                        )
                        df_actividad_plot = conteo_por_año.merge(
                            juegos_por_año.rename(columns={'name': 'juegos_lista'}),
                            on='año',
                        )
                        fig_actividad = px.bar(
                            df_actividad_plot,
                            x='año',
                            y='juegos',
                            title='📅 Historial de Actividad (Juegos Activos por Año)',
                            color_discrete_sequence=[RED_BASE],
                            labels={
                                'año': 'Año De Última Partida (Años)',
                                'juegos': 'Número De Juegos (Unidades)',
                            },
                        )
                        fig_actividad.update_traces(
                            customdata=df_actividad_plot['juegos_lista'],
                            hovertemplate='<b>Año:</b> %{x}<br><b>Juegos Activos:</b> %{y}<br><b>Títulos:</b><br>%{customdata}<extra></extra>',
                        )
                        fig_actividad.update_layout(
                            xaxis=dict(dtick=1, tickformat='d'),
                            yaxis=dict(dtick=1, tickformat='d'),
                        )
                        st.plotly_chart(
                            aplicar_tema_oscuro_transparente(fig_actividad),
                            use_container_width=True,
                        )
                    else:
                        st.info("No hay datos de última partida para mostrar el historial.")
                else:
                    st.caption(
                        "ℹ️ El historial por año no está disponible (rtime_last_played "
                        "solo se devuelve cuando consultas tu propio perfil con tu API key)."
                    )
        else:
            st.error("❌ Perfil no encontrado o no existe.")
