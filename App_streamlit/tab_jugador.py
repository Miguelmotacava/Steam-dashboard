import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data_api import fetch_user_profile, obtener_steam_id_real, fetch_player_achievements

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

    perfil, df_juegos, df_generos_jugador = None, None, None
    if submit_jugador and input_perfil:
        steamid_real = obtener_steam_id_real(input_perfil)
        if not steamid_real:
            st.error("Formato no válido. Asegúrate de introducir una URL válida o el ID de 17 dígitos.")
            return

        with st.spinner("⏳ Conectando con Steam y extrayendo biblioteca..."):
            try:
                perfil, df_juegos, df_generos_jugador = fetch_user_profile(steamid_real)
                st.session_state['jugador_perfil'] = perfil
                st.session_state['jugador_df_juegos'] = df_juegos if df_juegos is not None else pd.DataFrame()
                st.session_state['jugador_df_generos'] = df_generos_jugador if df_generos_jugador is not None else pd.DataFrame()
                st.session_state['jugador_steamid'] = steamid_real
            except Exception as e:
                st.error(f"❌ Error al cargar tu perfil: {e}")
                perfil = None
    else:
        if 'jugador_perfil' in st.session_state:
            perfil = st.session_state['jugador_perfil']
            _df = st.session_state.get('jugador_df_juegos')
            df_juegos = pd.DataFrame() if _df is None else _df
            _dg = st.session_state.get('jugador_df_generos')
            df_generos_jugador = pd.DataFrame() if _dg is None else _dg
            steamid_real = st.session_state.get('jugador_steamid', '')

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

            # --- SECCIÓN: Análisis Detallado por Título (Selector + Métricas + 3 Gráficos) ---
            if df_juegos is not None and not df_juegos.empty:
                st.markdown("---")
                st.markdown("### 🔍 Análisis Detallado por Título")

                from datetime import datetime
                steamid_actual = st.session_state.get('jugador_steamid', '')
                df_ordenado = df_juegos.sort_values('playtime_forever', ascending=False).reset_index(drop=True)
                opciones = df_ordenado['name'].astype(str).tolist()
                juego_seleccionado = st.selectbox(
                    "🔍 Análisis Detallado por Título",
                    options=opciones,
                    key='selector_juego',
                )

                df_filtrado = df_juegos[df_juegos['name'].astype(str) == juego_seleccionado]
                if df_filtrado.empty:
                    st.info("No hay datos para el juego seleccionado.")
                else:
                    juego_actual = df_filtrado.iloc[0]
                    appid_actual = juego_actual.get('appid')
                    horas_juego = (juego_actual.get('playtime_forever') or 0) / 60.0

                    # Ingesta: al seleccionar el juego se llama a la API de logros para ese appid
                    logros_raw = []
                    if steamid_actual and appid_actual:
                        try:
                            logros_raw = fetch_player_achievements(steamid_actual, appid_actual)
                        except Exception:
                            pass

                    # DataFrame: Nombre, Fecha de obtención, Rareza (%), Descripcion — solo desbloqueados
                    desbloqueados = [l for l in logros_raw if l.get('achieved')]
                    df_logros = pd.DataFrame()
                    if desbloqueados:
                        filas = []
                        for l in desbloqueados:
                            ut = l.get('unlocktime')
                            if ut is None or (isinstance(ut, (int, float)) and ut <= 0):
                                continue
                            try:
                                fecha = datetime.utcfromtimestamp(int(ut))
                            except (TypeError, ValueError, OSError):
                                continue
                            try:
                                rareza = float(l.get('rarity', 50))
                            except (TypeError, ValueError):
                                rareza = 50.0
                            filas.append({
                                'Nombre': str(l.get('name', '')),
                                'Fecha': fecha,
                                'Rareza': rareza,
                                'Descripcion': (str(l.get('description') or '')[:200]),
                            })
                        if filas:
                            df_logros = pd.DataFrame(filas)
                            df_logros['Fecha'] = pd.to_datetime(df_logros['Fecha'], utc=False)
                            df_logros = df_logros.sort_values('Fecha').reset_index(drop=True)
                            df_logros['Conteo Acumulado'] = list(range(1, len(df_logros) + 1))

                    if df_logros.empty:
                        st.info(
                            "No hay logros desbloqueados para este título, o el perfil de logros es privado. "
                            "Activa la visibilidad de logros en Steam para ver la cronología y el mapa de rareza."
                        )
                    else:
                        try:
                            # Métricas sobre los gráficos
                                total_logros = len(df_logros)
                            dificultad_media = round(df_logros['Rareza'].mean(), 1)
                            ultima_fecha = df_logros['Fecha'].max()
                            ultima_str = ultima_fecha.strftime('%d/%m/%Y') if hasattr(ultima_fecha, 'strftime') else str(ultima_fecha)

                            col_m1, col_m2, col_m3 = st.columns(3)
                            with col_m1:
                                st.metric("🏆 Logros Ganados", total_logros, help="Total de logros desbloqueados")
                            with col_m2:
                                st.metric("📊 Dificultad Media", f"{dificultad_media} %", help="Rareza media de tus logros (menor % = más difícil)")
                            with col_m3:
                                st.metric("📅 Último Desafío", ultima_str, help="Fecha del logro más reciente")

                            # Fila 1: Línea de vida (acumulativa) + Donut plataformas
                            col_timeline, col_pie = st.columns([2, 1])

                            with col_timeline:
                                df_timeline = df_logros[['Fecha', 'Conteo Acumulado', 'Rareza']].copy()
                                df_timeline['Rareza'] = df_timeline['Rareza'].astype(float)
                                df_timeline['Conteo Acumulado'] = df_timeline['Conteo Acumulado'].astype(int)
                                try:
                                    fig_line = px.line(
                                        df_timeline,
                                        x='Fecha',
                                        y='Conteo Acumulado',
                                        markers=True,
                                        color='Rareza',
                                        color_continuous_scale='Plasma',
                                        title='📈 Cronología De Progresión (Hitos de Juego)',
                                        labels={
                                            'Fecha': 'Fecha de obtención',
                                            'Conteo Acumulado': 'Logros acumulados',
                                            'Rareza': 'Rareza (%)',
                                        },
                                    )
                                except (TypeError, ValueError):
                                    fig_line = px.line(
                                        df_timeline,
                                        x='Fecha',
                                        y='Conteo Acumulado',
                                        markers=True,
                                        title='📈 Cronología De Progresión (Hitos de Juego)',
                                        labels={'Fecha': 'Fecha de obtención', 'Conteo Acumulado': 'Logros acumulados'},
                                    )
                                    fig_line.update_traces(line_color=RED_BASE)
                                fig_line.update_traces(
                                    line=dict(width=2),
                                    marker=dict(size=8),
                                )
                                fig_line.update_layout(
                                    xaxis_title='Fecha de obtención',
                                    yaxis_title='Logros acumulados',
                                )
                                st.plotly_chart(aplicar_tema_oscuro_transparente(fig_line), use_container_width=True)

                            with col_pie:
                                win, mac, linux_val = False, False, False
                                if df_super is not None and not df_super.empty and 'appid' in df_super.columns:
                                    match = df_super[df_super['appid'] == appid_actual]
                                    if not match.empty:
                                        win = bool(match.iloc[0].get('windows', False))
                                        mac = bool(match.iloc[0].get('mac', False))
                                        linux_val = bool(match.iloc[0].get('linux', False))
                                if not (win or mac or linux_val):
                                    win = True
                                total_h = max(horas_juego, 0.1)
                                plat_data = []
                                n_plat = sum([win, mac, linux_val])
                                if n_plat == 1:
                                    if win:
                                        plat_data = [{'Sistema': '🪟 Windows', 'Horas': total_h}]
                                    elif mac:
                                        plat_data = [{'Sistema': '🍎 Mac', 'Horas': total_h}]
                                    else:
                                        plat_data = [{'Sistema': '🐧 Linux / Steam Deck', 'Horas': total_h}]
                                else:
                                    h_w = (total_h * 0.7) if win else 0
                                    h_m = (total_h * 0.2) if mac else 0
                                    h_l = (total_h * 0.1) if linux_val else 0
                                    if win:
                                        plat_data.append({'Sistema': '🪟 Windows', 'Horas': max(h_w, 0.1)})
                                    if mac:
                                        plat_data.append({'Sistema': '🍎 Mac', 'Horas': max(h_m, 0.1)})
                                    if linux_val:
                                        plat_data.append({'Sistema': '🐧 Linux / Steam Deck', 'Horas': max(h_l, 0.1)})
                                df_plat = pd.DataFrame(plat_data)
                                fig_pie = px.pie(
                                    df_plat,
                                    values='Horas',
                                    names='Sistema',
                                    hole=0.6,
                                    title='💻 Plataforma De Uso',
                                    color_discrete_sequence=[RED_BASE, '#FF8080', '#FFB3B3'],
                                    labels={'Horas': 'Horas', 'Sistema': 'Sistema'},
                                )
                                fig_pie.update_traces(
                                    hovertemplate='<b>%{label}</b><br>Horas: %{value:.1f}<extra></extra>',
                                )
                                st.plotly_chart(aplicar_tema_oscuro_transparente(fig_pie), use_container_width=True)

                            # Fila 2: Bubble chart rareza (ancho completo)
                            df_bubble = df_logros.copy()
                            df_bubble['Tamaño'] = (100 - df_bubble['Rareza']) + 10
                            fig_bubble = px.scatter(
                                df_bubble,
                                x='Fecha',
                                y='Rareza',
                                size='Tamaño',
                                color='Rareza',
                                color_continuous_scale='Plasma',
                                hover_data={'Nombre': True, 'Descripcion': True, 'Fecha': '|%d/%m/%Y', 'Rareza': ':.1f', 'Tamaño': False},
                                title='🔮 Mapa De Rareza Y Mérito De Logros',
                                labels={'Fecha': 'Fecha de obtención', 'Rareza': 'Rareza (%)'},
                            )
                            fig_bubble.update_layout(
                                xaxis_title='Fecha de obtención',
                                yaxis_title='Rareza (%)',
                                showlegend=True,
                                coloraxis_showscale=True,
                            )
                            st.plotly_chart(aplicar_tema_oscuro_transparente(fig_bubble), use_container_width=True)
                        except Exception:
                            st.warning(
                                "No se pudieron generar los gráficos de logros para este título. "
                                "El juego puede no tener logros o los datos no están disponibles."
                            )
    elif submit_jugador and input_perfil:
        st.error("❌ Perfil no encontrado o no existe.")
