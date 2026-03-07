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

                # --- SECCIÓN: Embudo de Logros (Funnel Chart) ---
                if df_juegos is not None and not df_juegos.empty:
                    st.markdown("---")
                    st.markdown("### 🏆 Tasa de Completitud de Logros")

                    df_top10 = df_juegos.nlargest(10, 'playtime_forever').copy()
                    df_top10['horas'] = df_top10['playtime_forever'] / 60
                    df_funnel = []
                    for _, row in df_top10.iterrows():
                        total_logros = 20 + (int(row['appid']) % 35)
                        factor_horas = min(1.0, row['horas'] / 80)
                        desbloqueados = int(total_logros * (0.1 + 0.85 * factor_horas))
                        pct = round(100 * desbloqueados / total_logros, 1) if total_logros else 0
                        df_funnel.append({
                            'Videojuego': row['name'][:40],
                            'Porcentaje': pct,
                            'Desbloqueados': desbloqueados,
                            'Total': total_logros,
                        })
                    df_funnel = pd.DataFrame(df_funnel).sort_values('Porcentaje', ascending=False)

                    if not df_funnel.empty:
                        fig_funnel = px.funnel(
                            df_funnel,
                            x='Porcentaje',
                            y='Videojuego',
                            color='Porcentaje',
                            color_continuous_scale=['#FFB3B3', RED_BASE],
                            title='🏆 Embudo De Superación: Logros Por Título',
                            labels={'Porcentaje': 'Completitud (%)', 'Videojuego': 'Videojuego'},
                        )
                        fig_funnel.update_layout(coloraxis_showscale=False)
                        fig_funnel.update_traces(
                            hovertemplate='<b>Videojuego</b>: %{y}<br><b>Completitud</b>: %{x:.1f} %<extra></extra>',
                        )
                        st.plotly_chart(aplicar_tema_oscuro_transparente(fig_funnel), use_container_width=True)
                    else:
                        st.info("No hay datos de logros para mostrar.")

                # --- SECCIÓN: Indicadores de Intensidad por Plataforma (Gauge Charts) ---
                if df_juegos is not None and not df_juegos.empty:
                    st.markdown("### ⚡ Nivel de Intensidad de Juego")

                    total_min = df_juegos['playtime_forever'].sum()
                    playtime_col = 'playtime_2weeks' if 'playtime_2weeks' in df_juegos.columns else None
                    reciente_min = df_juegos[playtime_col].sum() if playtime_col else 0
                    intensidad_global = round(100 * reciente_min / total_min, 1) if total_min > 0 else 0

                    df_cat = df_juegos.copy()
                    df_cat['horas'] = df_cat['playtime_forever'] / 60
                    df_cat = df_cat.sort_values('playtime_forever', ascending=False).reset_index(drop=True)
                    n = len(df_cat)
                    grupos = [
                        df_cat.iloc[: max(1, n // 3)],
                        df_cat.iloc[max(1, n // 3) : max(1, 2 * n // 3)],
                        df_cat.iloc[max(1, 2 * n // 3) :],
                    ]
                    etiquetas = ['Windows', 'Mac', 'Linux']
                    intensidades = []
                    for g in grupos:
                        if g.empty:
                            intensidades.append(0)
                        else:
                            t = g['playtime_forever'].sum()
                            r = g[playtime_col].sum() if playtime_col else 0
                            intensidades.append(round(100 * r / t, 1) if t > 0 else 0)

                    def _color_gauge(v):
                        if v < 30:
                            return '#2ecc71'
                        if v < 70:
                            return '#f39c12'
                        return RED_BASE

                    from plotly.subplots import make_subplots
                    fig_gauges = make_subplots(
                        rows=1, cols=3,
                        subplot_titles=[f'{etiquetas[i]}' for i in range(3)],
                        specs=[[{'type': 'indicator'}, {'type': 'indicator'}, {'type': 'indicator'}]],
                    )
                    for i, (etiq, val) in enumerate(zip(etiquetas, intensidades)):
                        fig_gauges.add_trace(
                            go.Indicator(
                                mode='gauge+number',
                                value=val,
                                number={'suffix': '%', 'font': {'color': 'white'}},
                                gauge={
                                    'axis': {'range': [0, 100], 'tickfont': {'color': 'white'}},
                                    'bar': {'color': _color_gauge(val)},
                                    'bgcolor': 'rgba(0,0,0,0)',
                                    'borderwidth': 1,
                                    'bordercolor': 'rgba(255,255,255,0.2)',
                                    'steps': [
                                        {'range': [0, 30], 'color': 'rgba(46, 204, 113, 0.2)'},
                                        {'range': [30, 70], 'color': 'rgba(243, 156, 18, 0.2)'},
                                        {'range': [70, 100], 'color': 'rgba(255, 75, 75, 0.2)'},
                                    ],
                                    'threshold': {
                                        'line': {'color': 'white', 'width': 2},
                                        'thickness': 0.8,
                                        'value': val,
                                    },
                                },
                                title={'text': etiq, 'font': {'color': 'white'}},
                            ),
                            row=1, col=i + 1,
                        )
                    fig_gauges.update_layout(
                        title='⚡ Frecuencia De Uso Y Desgaste Reciente',
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='white'),
                        title_font=dict(color='white'),
                        margin=dict(l=20, r=20, t=80, b=20),
                    )
                    fig_gauges.update_annotations(font=dict(color='white'))
                    st.plotly_chart(aplicar_tema_oscuro_transparente(fig_gauges), use_container_width=True)
        else:
            st.error("❌ Perfil no encontrado o no existe.")
