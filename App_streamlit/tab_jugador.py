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


PAISES = {
    'ES': 'España', 'US': 'Estados Unidos', 'GB': 'Reino Unido', 'DE': 'Alemania', 'FR': 'Francia',
    'IT': 'Italia', 'RU': 'Rusia', 'BR': 'Brasil', 'AR': 'Argentina', 'MX': 'México', 'CL': 'Chile',
    'CO': 'Colombia', 'PE': 'Perú', 'PT': 'Portugal', 'NL': 'Países Bajos', 'PL': 'Polonia',
    'JP': 'Japón', 'KR': 'Corea del Sur', 'CN': 'China', 'AU': 'Australia', 'CA': 'Canadá',
}

def render_jugador(df_super=None):
    if df_super is None:
        df_super = pd.DataFrame()
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
            # --- TARJETA DE IDENTIDAD VIP ---
            nombre_jugador = perfil.get('personaname', 'Desconocido')
            avatar_url = perfil.get('avatarfull') or ''
            loc = perfil.get('loccountrycode') or ''
            pais = PAISES.get(loc.upper(), loc) if loc else "Privado"
            nivel = perfil.get('player_level', 0) or 0
            ts = perfil.get('timecreated') or 0
            from datetime import datetime
            anios = max(0, 2026 - datetime.fromtimestamp(ts).year) if ts and ts > 0 else 0

            if avatar_url:
                col_avatar, col_identidad = st.columns([1, 4])
                with col_avatar:
                    st.image(avatar_url, width=120)
                with col_identidad:
                    st.header(f"🎮 {nombre_jugador}")
                    st.caption(f"ID: {steamid_real}")
                    st.markdown(f"**🌍 {pais}** | **⭐ Nivel {nivel}** | **🎂 Antigüedad: {anios} Años**")
            else:
                st.header(f"🎮 {nombre_jugador}")
                st.caption(f"ID: {steamid_real}")
                st.markdown(f"**🌍 {pais}** | **⭐ Nivel {nivel}** | **🎂 Antigüedad: {anios} Años**")

            # --- FILA DE KPIs (Métricas Principales) ---
            st.markdown("---")
            col1, col2, col3, col4 = st.columns(4)

            juegos_totales = len(df_juegos) if df_juegos is not None and not df_juegos.empty else 0
            horas_totales = int(df_juegos['playtime_forever'].sum() / 60) if df_juegos is not None and not df_juegos.empty else 0
            valor_estimado = 0.0
            if df_juegos is not None and not df_juegos.empty and df_super is not None and not df_super.empty:
                merge_precio = df_juegos[['appid']].merge(
                    df_super[['appid', 'precio_eur']], on='appid', how='left'
                )
                valor_estimado = float(merge_precio['precio_eur'].fillna(0).sum())
            sin_tocar = (df_juegos['playtime_forever'] == 0).sum() if df_juegos is not None and not df_juegos.empty else 0
            total_juegos = juegos_totales
            pct_pozo = round(sin_tocar / total_juegos * 100, 0) if total_juegos and total_juegos > 0 else 0

            def _fmt_miles(n):
                return f"{int(n):,}".replace(",", ".") if n is not None else "—"

            def _fmt_euros(v):
                if v is None or (isinstance(v, float) and pd.isna(v)):
                    return "—"
                return f"{float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"

            with col1:
                st.metric("🕹️ Juegos Totales", _fmt_miles(juegos_totales))
            with col2:
                st.metric("⏱️ Horas Totales", _fmt_miles(horas_totales))
            with col3:
                valor_str = _fmt_euros(valor_estimado) if (juegos_totales and df_super is not None and not df_super.empty) else "—"
                st.metric("💸 Valor Estimado", valor_str)
            with col4:
                pozo_str = f"{_fmt_miles(sin_tocar)} ({int(pct_pozo)}%)" if total_juegos else "—"
                st.metric("🪦 Pozo de la Vergüenza", pozo_str)

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
                    fig_bar.update_traces(hovertemplate='<b>Videojuego</b>: %{y}<br><b>Tiempo invertido</b>: %{x:.1f} h<extra></extra>')
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
                        max_minutos = radar_data['minutos'].max()
                        radar_data['afinidad_relativa'] = (
                            (radar_data['minutos'] / max_minutos * 100)
                            if max_minutos > 0 else 0
                        )
                        fig_radar = px.line_polar(
                            radar_data,
                            r='afinidad_relativa',
                            theta='genero',
                            line_close=True,
                            title='🕸️ ADN por Géneros',
                            color_discrete_sequence=[RED_BASE],
                            range_r=[0, 100],
                            labels={
                                'afinidad_relativa': 'Afinidad Relativa (%)',
                                'genero': 'Género',
                            },
                        )
                        fig_radar.update_traces(
                            fill='toself',
                            fillcolor='rgba(255, 75, 75, 0.4)',
                            hovertemplate='<b>Género</b>: %{theta}<br><b>Afinidad relativa</b>: %{r:.1f} %<extra></extra>',
                        )
                        st.plotly_chart(
                            aplicar_tema_oscuro_transparente(fig_radar, es_radar=True),
                            use_container_width=True,
                        )
                    else:
                        st.info("No hay datos de géneros para el radar.")

                st.markdown("---")

                # --- FILA DE GRÁFICOS 2: Sunburst | Donut Backlog ---
                col_g3, col_g4 = st.columns(2)
                with col_g3:
                    df_sunburst = df_juegos[df_juegos['playtime_forever'] > 0].copy()
                    df_sunburst['horas'] = df_sunburst['playtime_forever'] / 60
                    df_sunburst = df_sunburst.sort_values('playtime_forever', ascending=False).reset_index(drop=True)
                    if not df_sunburst.empty:
                        df_sunburst['categoria_anillo'] = [
                            'Top 5 Favoritos' if i < 5 else 'Resto Del Catálogo'
                            for i in range(len(df_sunburst))
                        ]
                        fig_sunburst = px.sunburst(
                            df_sunburst,
                            path=['categoria_anillo', 'name'],
                            values='horas',
                            title='☀️ Distribución Del Tiempo De Vida',
                            color='categoria_anillo',
                            color_discrete_map={
                                'Top 5 Favoritos': RED_BASE,
                                'Resto Del Catálogo': GRIS_OSCURO,
                            },
                            labels={
                                'horas': 'Tiempo Invertido (Horas)',
                                'name': 'Videojuego',
                                'categoria_anillo': 'Categoría',
                            },
                        )
                        fig_sunburst.update_traces(
                            hovertemplate='<b>Elemento</b>: %{label}<br><b>Tiempo invertido</b>: %{value:.1f} h<br><b>Porcentaje del total</b>: %{percentParent:.1%}<extra></extra>',
                        )
                        st.plotly_chart(
                            aplicar_tema_oscuro_transparente(fig_sunburst),
                            use_container_width=True,
                        )
                    else:
                        st.info("No hay juegos con tiempo jugado para mostrar.")

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
                                hovertemplate='<b>Estado</b>: %{label}<br><b>Nº de juegos</b>: %{value}<br><b>Porcentaje</b>: %{percent}<extra></extra>',
                            )
                        ]
                    )
                    fig_donut.update_layout(title='📦 Estado de la Biblioteca')
                    st.plotly_chart(
                        aplicar_tema_oscuro_transparente(fig_donut),
                        use_container_width=True,
                    )

                # --- FILA: Treemap Distribución del Tiempo ---
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
                        hovertemplate='<b>Videojuego</b>: %{label}<br><b>Tiempo invertido</b>: %{value:.1f} h<br><b>Porcentaje del total</b>: %{percentParent:.1%}<extra></extra>',
                    )
                    st.plotly_chart(
                        aplicar_tema_oscuro_transparente(fig_treemap),
                        use_container_width=True,
                    )
                else:
                    st.info("No hay juegos con más de 1 hora jugada para mostrar.")

                # --- SECCIÓN: Slope Chart - Eficiencia de Compra ---
                if not df_generos_jugador.empty:
                    st.markdown("---")
                    st.markdown("### 📉 Relación: Cantidad vs Dedicación Real")

                    df_slope = df_generos_jugador.groupby('genero').agg(
                        cantidad=('juego', 'count'),
                        dedicacion_minutos=('minutos', 'sum'),
                    ).reset_index()
                    df_slope['dedicacion_horas'] = df_slope['dedicacion_minutos'] / 60
                    df_slope['rank_biblioteca'] = df_slope['cantidad'].rank(ascending=False, method='min').astype(int)
                    df_slope['rank_juego'] = df_slope['dedicacion_horas'].rank(ascending=False, method='min').astype(int)

                    long_slope = pd.concat([
                        df_slope[['genero', 'rank_biblioteca']].assign(Eje='En Biblioteca').rename(columns={'rank_biblioteca': 'Posicion'}),
                        df_slope[['genero', 'rank_juego']].assign(Eje='En Juego').rename(columns={'rank_juego': 'Posicion'}),
                    ], ignore_index=True)

                    fig_slope = px.line(
                        long_slope,
                        x='Eje',
                        y='Posicion',
                        color='genero',
                        markers=True,
                        title='📊 Comparativa De Relevancia Por Género',
                        labels={'Eje': '', 'Posicion': 'Posición (Ranking)', 'genero': 'Género'},
                        color_discrete_sequence=px.colors.qualitative.Vivid,
                    )
                    fig_slope.update_yaxes(autorange='reversed', title_text='Posición (Ranking)')
                    fig_slope.update_traces(
                        hovertemplate='<b>Género</b>: %{fullData.name}<br><b>Eje</b>: %{x}<br><b>Posición</b>: %{y}<extra></extra>',
                    )
                    st.plotly_chart(aplicar_tema_oscuro_transparente(fig_slope), use_container_width=True)

                # --- SECCIÓN: Burbujas de Actividad Reciente (Punch Card) ---
                if df_juegos is not None and not df_juegos.empty:
                    playtime_col = 'playtime_2weeks' if 'playtime_2weeks' in df_juegos.columns else None
                    if playtime_col:
                        df_reciente = df_juegos[df_juegos[playtime_col] > 0].copy()
                        if not df_reciente.empty:
                            st.markdown("### 🕒 Intensidad de Sesiones Recientes")
                            df_reciente['horas_recientes'] = df_reciente[playtime_col] / 60
                            df_reciente['eje_fijo'] = 1

                            fig_burb = px.scatter(
                                df_reciente,
                                x='name',
                                y='eje_fijo',
                                size='horas_recientes',
                                color='horas_recientes',
                                color_continuous_scale=['#FFB3B3', RED_BASE],
                                title='🔥 Intensidad De Juego (Últimas 2 Semanas)',
                                labels={'name': 'Videojuego', 'horas_recientes': 'Horas (Últimas 2 Semanas)', 'eje_fijo': ''},
                            )
                            fig_burb.update_layout(showlegend=False)
                            fig_burb.update_yaxes(showticklabels=False, title_text='')
                            fig_burb.update_traces(
                                customdata=df_reciente['horas_recientes'],
                                hovertemplate='<b>Videojuego</b>: %{x}<br><b>Horas jugadas</b>: %{customdata:.1f} h<extra></extra>',
                            )
                            st.plotly_chart(aplicar_tema_oscuro_transparente(fig_burb), use_container_width=True)
                        else:
                            st.markdown("### 🕒 Intensidad de Sesiones Recientes")
                            st.info("No hay actividad en las últimas 2 semanas.")
                    else:
                        st.markdown("### 🕒 Intensidad de Sesiones Recientes")
                        st.info("Los datos de actividad reciente no están disponibles para este perfil.")
        else:
            st.error("❌ Perfil no encontrado o no existe.")
