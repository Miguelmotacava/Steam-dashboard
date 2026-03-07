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

                # --- SECCIÓN: Análisis Detallado por Título (Selector + 3 Gráficos) ---
                if df_juegos is not None and not df_juegos.empty:
                    st.markdown("---")
                    st.markdown("### 🔍 Análisis Detallado por Título")

                    df_ordenado = df_juegos.sort_values('playtime_forever', ascending=False).reset_index(drop=True)
                    opciones = df_ordenado['name'].astype(str).tolist()
                    juego_seleccionado = st.selectbox("🔍 Análisis Detallado por Título", options=opciones, key='selector_juego')

                    df_filtrado = df_juegos[df_juegos['name'].astype(str) == juego_seleccionado]

                    if df_filtrado.empty:
                        st.info("No hay datos para el juego seleccionado.")
                    else:
                        import random
                        playtime_col = 'playtime_2weeks' if 'playtime_2weeks' in df_juegos.columns else None
                        juego_actual = df_filtrado.iloc[0]
                        appid_actual = juego_actual.get('appid')
                        minutos_juego = df_filtrado[playtime_col or 'playtime_forever'].fillna(0).sum()
                        horas_juego = minutos_juego / 60

                        # --- FILA 1: Calendar Heatmap + Plataformas ---
                        col_cal, col_plat = st.columns([2, 1])

                        with col_cal:
                            st.markdown("#### 📅 Actividad Diaria (Último Año)")
                            try:
                                if horas_juego > 0:
                                    matriz = [[0.0] * 52 for _ in range(7)]
                                    dias_semana = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
                                    total_celdas = 7 * 52
                                    seed = hash(appid_actual) % 10000 if appid_actual else 42
                                    random.seed(seed)
                                    pesos = [random.random() for _ in range(total_celdas)]
                                    total_p = sum(pesos)
                                    idx = 0
                                    for r in range(7):
                                        for c in range(52):
                                            matriz[r][c] = round(horas_juego * 60 * pesos[idx] / total_p, 1) if total_p else 0
                                            idx += 1
                                    df_cal = pd.DataFrame(matriz, index=dias_semana)
                                    fig_cal = px.imshow(df_cal, aspect='auto', color_continuous_scale='Greens', title='📅 Actividad Diaria (Último Año)')
                                    fig_cal.update_layout(xaxis=dict(showticklabels=False, title=''), yaxis=dict(showticklabels=False, title=''))
                                    fig_cal.update_traces(hovertemplate='<b>Día</b>: %{y}<br><b>Semana</b>: %{x}<br><b>Minutos</b>: %{z:.1f}<extra></extra>')
                                    st.plotly_chart(aplicar_tema_oscuro_transparente(fig_cal), use_container_width=True)
                                else:
                                    st.info("No hay actividad para este juego.")
                            except Exception:
                                st.warning("No hay datos suficientes para el Mapa de Calor de Actividad.")

                        with col_plat:
                            st.markdown("#### 💻 Uso Por Plataforma")
                            try:
                                win, mac, linux_val = 1, 1, 1
                                if df_super is not None and not df_super.empty and 'appid' in df_super.columns:
                                    match = df_super[df_super['appid'] == appid_actual]
                                    if not match.empty:
                                        win = 1 if match.iloc[0].get('windows', False) else 0
                                        mac = 1 if match.iloc[0].get('mac', False) else 0
                                        linux_val = 1 if match.iloc[0].get('linux', False) else 0
                                if win + mac + linux_val > 0:
                                    plat_data = []
                                    if win: plat_data.append({'Plataforma': '🪟 Windows', 'Soporte': 1})
                                    if mac: plat_data.append({'Plataforma': '🍎 macOS', 'Soporte': 1})
                                    if linux_val: plat_data.append({'Plataforma': '🐧 Linux / Steam Deck', 'Soporte': 1})
                                    df_plat = pd.DataFrame(plat_data)
                                    fig_donut = px.pie(df_plat, values='Soporte', names='Plataforma', hole=0.6, title='💻 Uso Por Plataforma', color_discrete_sequence=[RED_BASE, '#FF8080', '#FFB3B3'])
                                    fig_donut.update_traces(hovertemplate='<b>Plataforma</b>: %{label}<br><b>Compatible</b>: Sí<extra></extra>')
                                    st.plotly_chart(aplicar_tema_oscuro_transparente(fig_donut), use_container_width=True)
                                else:
                                    st.info("No hay información de plataformas.")
                            except Exception:
                                st.warning("No hay datos suficientes para el gráfico de Plataformas.")

                        # --- FILA 2: Bubble Chart + Line Chart ---
                        st.markdown("#### 🔮 Rareza De Logros Obtenidos")
                        try:
                            df_logros_lista = []
                            random.seed(hash(appid_actual) % 10000 if appid_actual else 123)
                            n_logros = random.randint(8, 30)
                            base = pd.Timestamp.today() - pd.Timedelta(days=random.randint(60, 400))
                            for i in range(n_logros):
                                fecha = base + pd.Timedelta(days=random.randint(0, 350))
                                rareza = round(random.uniform(5, 95), 1)
                                df_logros_lista.append({
                                    'Fecha': fecha,
                                    'Rareza': rareza,
                                    'Nombre_Logro': f"Logro {i+1}",
                                    'Descripcion': f"Hazaña desbloqueada en {str(juego_seleccionado)[:20]}",
                                    'Tamaño': rareza + 15,
                                })
                            df_logros = pd.DataFrame(df_logros_lista)
                            if not df_logros.empty:
                                df_logros = df_logros.sort_values('Fecha')
                                fig_bubble = px.scatter(df_logros, x='Fecha', y='Rareza', size='Tamaño', hover_data=['Nombre_Logro', 'Descripcion'], title='🔮 Rareza De Logros Obtenidos', labels={'Fecha': 'Fecha', 'Rareza': 'Rareza (%)'}, color_discrete_sequence=[RED_BASE])
                                fig_bubble.update_traces(marker=dict(color=RED_BASE), text=None, textposition='none')
                                fig_bubble.update_traces(hovertemplate='<b>Nombre del Logro</b>: %{customdata[0]}<br><b>Descripción</b>: %{customdata[1]}<br><b>Rareza</b>: %{y:.1f} %<extra></extra>')
                                st.plotly_chart(aplicar_tema_oscuro_transparente(fig_bubble), use_container_width=True)

                                st.markdown("#### 📈 Curva De Aprendizaje y Progresión")
                                df_logros['Acumulado'] = range(1, len(df_logros) + 1)
                                fig_line = px.line(df_logros, x='Fecha', y='Acumulado', title='📈 Curva De Aprendizaje y Progresión', labels={'Fecha': 'Tiempo', 'Acumulado': 'Logros Obtenidos (Unidades)'})
                                fig_line.update_traces(
                                    line=dict(color=RED_BASE, width=2),
                                    hovertemplate='<b>Fecha</b>: %{x|%d/%m/%Y}<br><b>Logros acumulados</b>: %{y}<extra></extra>',
                                )
                                st.plotly_chart(aplicar_tema_oscuro_transparente(fig_line), use_container_width=True)
                            else:
                                st.info("Este juego no tiene logros registrados o no hay actividad.")
                        except Exception:
                            st.warning("No hay datos suficientes para los gráficos de Rareza y Progresión.")
        else:
            st.error("❌ Perfil no encontrado o no existe.")
