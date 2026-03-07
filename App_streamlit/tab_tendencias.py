import os
import streamlit as st
import pandas as pd
import plotly.express as px

RED_BASE, RED_SCALE = '#FF4B4B', 'Reds'
PALETA_ROJA = [RED_BASE, '#FF6666', '#FF8080', '#FF9999', '#FFB3B3', '#E74C3C', '#C0392B', '#FF6B6B', '#FF8B8B', '#FF5555']


def _ruta_historial():
    """Ruta al CSV de historial (historico_steam_streamlit)."""
    return os.path.join(os.path.dirname(__file__), '..', 'historico_steam_streamlit', 'historial_top100.csv')


def _aplicar_tema_plotly(fig):
    """Fondos transparentes y estética #FF4B4B."""
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white', size=12),
        title_font=dict(color='white'),
        margin=dict(l=20, r=20, t=50, b=20),
        xaxis=dict(gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='white')),
        yaxis=dict(gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='white')),
    )
    return fig


def _extraer_seleccion(event):
    """Extrae el valor seleccionado de un evento Plotly (nombre o género)."""
    try:
        if not event or not hasattr(event, 'selection'):
            return None
        sel = event.selection
        pts = getattr(sel, 'points', None) or (sel.get('points') if hasattr(sel, 'get') else None)
        if not pts:
            return None
        pt = pts[0] if isinstance(pts, list) else pts
        if hasattr(pt, 'get'):
            return pt.get('label') or pt.get('y') or pt.get('hovertext') or pt.get('legendgroup') or pt.get('id')
        return getattr(pt, 'label', None) or getattr(pt, 'y', None)
    except (IndexError, KeyError, TypeError, AttributeError):
        return None


def _aplicar_filtro_cross(df, valor):
    """Aplica filtro cruzado por nombre o género."""
    if not valor or not isinstance(valor, str) or df.empty:
        return df
    df_nombre = df[df['nombre'] == valor]
    if not df_nombre.empty:
        return df_nombre
    return df[df['generos'].str.contains(valor, na=False)]


RED_DONUT = {'Windows': '#FF4B4B', 'MacOS': '#FF8080', 'Linux': '#FFB3B3'}
import plotly.graph_objects as go
from data_api import fetch_history_price, fetch_dlc_list

def generar_grafico_precio_real(precio_ini, precio_fin, nombre, fecha_salida, datos_historicos=None):
    """Genera la gráfica conectando el día de lanzamiento real, el mínimo histórico y el día de hoy"""
    hoy = pd.Timestamp.today().strftime('%Y-%m-%d')
    try: inicio = pd.to_datetime(fecha_salida).strftime('%Y-%m-%d')
    except: inicio = (pd.Timestamp.today() - pd.Timedelta(days=365)).strftime('%Y-%m-%d')

    fechas = [hoy]
    precios = [precio_fin]
    etiquetas = [f"Hoy: {precio_fin:.2f}€"]

    if datos_historicos and datos_historicos.get('fecha_min_historico'):
        fecha_min = datos_historicos['fecha_min_historico']
        precio_min = datos_historicos['precio_min_historico']
        
        # Para evitar problemas de X asimétricas si inicio > fecha_min
        if pd.to_datetime(inicio) > pd.to_datetime(fecha_min):
            inicio = (pd.to_datetime(fecha_min) - pd.Timedelta(days=1)).strftime('%Y-%m-%d')

        fechas.insert(0, fecha_min)
        precios.insert(0, precio_min)
        etiquetas.insert(0, f"Mínimo Histórico: {precio_min:.2f}€")

    if datos_historicos and datos_historicos.get('precio_retail') and abs(precio_ini) < 0.01 and precio_fin > 0.01:
        precio_ini = datos_historicos['precio_retail']

    # Mantenemos inicial como punto de partida si difiere del primer punto (o si solo tenemos 1 punto)
    if len(fechas) < 2 or (precio_ini > 0 and abs(precio_ini - precios[0]) > 0.01):
        fechas.insert(0, inicio)
        precios.insert(0, precio_ini)
        etiquetas.insert(0, f"Precio Base: {precio_ini:.2f}€")

    df_hist = pd.DataFrame({
        'Momento': pd.to_datetime(fechas),
        'Precio': precios,
        'Etiqueta': etiquetas
    })
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df_hist['Momento'], y=df_hist['Precio'],
        mode='lines+markers+text',
        marker=dict(size=12, color=RED_BASE),
        line=dict(color=RED_BASE, width=3),
        text=etiquetas,
        textposition='top center',
        name='Precio',
        hovertemplate='Fecha: %{x|%d/%m/%Y}<br>Precio: %{y:.2f} €<extra></extra>',
    ))

    # Línea base para el mínimo si existe
    if datos_historicos:
        p_min = datos_historicos['precio_min_historico']
        fig.add_hline(y=p_min, line_dash="dash", line_color="green", annotation_text=f"Mínimo histórico: {p_min:.2f}€", annotation_position="bottom right")
    
    max_p = max(precios) if precios else max(precio_ini, precio_fin)
    fig.update_layout(
        title=f'📉 Evolución Real del Precio',
        yaxis_range=[0, max_p + (max_p * 0.3) + 2],
        xaxis_title='Fecha (Tiempo)',
        yaxis_title='Precio (Euros)',
        showlegend=False
    )
    return fig

def render_tendencias(df_super):
    st.header("📈 Tendencias Actuales")

    # Cargar historial si existe
    df_historial = None
    ruta_csv = _ruta_historial()
    if os.path.exists(ruta_csv):
        try:
            df_historial = pd.read_csv(ruta_csv)
            df_historial['Fecha'] = pd.to_datetime(df_historial['Fecha'])
        except Exception:
            df_historial = None
    
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1: juegos_sel = st.multiselect("🎮 Filtrar por Videojuego", options=df_super['nombre'].unique())
    with col_f2: plat_sel = st.selectbox("💻 Filtrar por Plataforma", ["Todas", "Windows", "MacOS", "Linux"])
    with col_f3:
        todos_gen = set()
        for gen in df_super['generos'].dropna(): todos_gen.update(gen.split(', '))
        gen_sel = st.selectbox("🎭 Filtrar por Género", ["Todos"] + sorted(list(todos_gen)))

    df_filtrado = df_super.copy()
    if juegos_sel: df_filtrado = df_filtrado[df_filtrado['nombre'].isin(juegos_sel)]
    if plat_sel != "Todas": df_filtrado = df_filtrado[df_filtrado[plat_sel.lower()] == True]
    if gen_sel != "Todos": df_filtrado = df_filtrado[df_filtrado['generos'].str.contains(gen_sel, na=False)]
    

    if not df_filtrado.empty:
        # --- KPIs justo debajo de los filtros ---
        st.markdown("---")
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("👥 Jugadores Concurrentes", f"{int(df_filtrado['jugadores_actuales'].sum()):,}".replace(',', '.'))
        kpi2.metric("🕹️ Títulos Mostrados", len(df_filtrado))
        kpi3.metric("💸 Precio Medio", f"{df_filtrado[df_filtrado['precio_eur']>0]['precio_eur'].mean():.2f} €" if not df_filtrado[df_filtrado['precio_eur']>0].empty else "0.00 €")
        kpi4.metric("🎁 Free-to-Play", int(df_filtrado['es_gratis'].sum()))
        

        # --- Gráficos con cross-filtering (selección aplica filtro al resto) ---
        col_g1, col_g2 = st.columns(2)
        sel_bar, sel_treemap, sel_scatter = None, None, None
        with col_g1:
            fig1 = px.bar(
                df_filtrado.nlargest(10, 'jugadores_actuales').sort_values('jugadores_actuales'),
                x='jugadores_actuales', y='nombre', orientation='h',
                title='🏆 Juegos más populares', color_discrete_sequence=[RED_BASE],
                labels={'jugadores_actuales': 'Jugadores Concurrentes (Unidades)', 'nombre': 'Videojuego'},
            )
            fig1.update_traces(hovertemplate='<b>%{y}</b><br>Jugadores: %{x:,.0f}<extra></extra>')
            evt1 = st.plotly_chart(fig1, use_container_width=True, on_select='rerun', key='bar_top10', selection_mode='points')
            sel_bar = _extraer_seleccion(evt1)
        with col_g2:
            df_gen = df_filtrado.assign(genero=df_filtrado['generos'].str.split(', ')).explode('genero')
            fig2 = px.treemap(df_gen.groupby('genero')['jugadores_actuales'].sum().reset_index(), path=['genero'], values='jugadores_actuales', title='🎭 Distribución por Géneros', color='jugadores_actuales', color_continuous_scale=RED_SCALE)
            fig2.update_traces(textinfo='label+value+percent parent', hovertemplate='<b>%{label}</b><br>Jugadores: %{value:,.0f}<br>Porcentaje: %{percentParent:.1%}<extra></extra>')
            evt2 = st.plotly_chart(fig2, use_container_width=True, on_select='rerun', key='treemap_gen', selection_mode='points')
            sel_treemap = _extraer_seleccion(evt2)

        col_g3, col_g4 = st.columns(2)
        with col_g3:
            df_os = pd.DataFrame([('Windows', df_filtrado['windows'].sum()), ('MacOS', df_filtrado['mac'].sum()), ('Linux', df_filtrado['linux'].sum())], columns=['SO', 'Compatibles'])
            fig3 = px.pie(df_os, names='SO', values='Compatibles', hole=0.5, title='🖥️ Compatibilidad de Sistemas', color='SO', color_discrete_map=RED_DONUT)
            fig3.update_traces(hovertemplate='<b>%{label}</b><br>Compatibles: %{value}<extra></extra>')
            st.plotly_chart(fig3, use_container_width=True)
        with col_g4:
            df_scat = df_filtrado[df_filtrado['metacritic_nota'].notna()]
            if not df_scat.empty:
                fig4 = px.scatter(
                    df_scat, x='precio_eur', y='metacritic_nota',
                    size='jugadores_actuales', hover_name='nombre',
                    title='💎 Precio vs Calidad (Metacritic)', color='nombre',
                    labels={'precio_eur': 'Precio (Euros)', 'metacritic_nota': 'Nota Metacritic'},
                )
                fig4.update_traces(
                    customdata=df_scat['jugadores_actuales'],
                    hovertemplate='<b>%{hovertext}</b><br>Precio: %{x:.2f} €<br>Nota Metacritic: %{y}<br>Jugadores: %{customdata:,.0f}<extra></extra>',
                )
                evt4 = st.plotly_chart(fig4, use_container_width=True, on_select='rerun', key='scatter_metacritic', selection_mode='points')
                sel_scatter = _extraer_seleccion(evt4)
            else:
                st.info("No hay juegos con nota Metacritic para mostrar.")

        filtro_cross = sel_scatter or sel_bar or sel_treemap
        if filtro_cross:
            df_filtrado = _aplicar_filtro_cross(df_filtrado, filtro_cross)
            if not df_filtrado.empty:
                st.caption(f"🔍 Filtro activo: **{filtro_cross}** (clic en un gráfico para deseleccionar)")

        # --- Gráficas Históricas (si existe historial) ---
        if df_historial is not None and not df_historial.empty:
            df_hist_merge = pd.merge(
                df_historial,
                df_filtrado[['appid', 'nombre', 'generos']].drop_duplicates('appid'),
                on='appid',
                how='inner',
            )
            if not df_hist_merge.empty:
                df_hist_merge['Hora_Frame'] = pd.to_datetime(df_hist_merge['Fecha']).dt.strftime('%d/%m %H:%M')
                st.markdown("---")
                st.markdown("### 📊 Evolución Histórica de Jugadores")

                col_h1, col_h2 = st.columns(2)
                with col_h1:
                    top_10_appids = df_filtrado.nlargest(10, 'jugadores_actuales')['appid'].tolist()
                    df_line_top10 = df_hist_merge[df_hist_merge['appid'].isin(top_10_appids)]
                    if not df_line_top10.empty:
                        fig_line = px.line(
                            df_line_top10,
                            x='Fecha',
                            y='jugadores_historicos',
                            color='nombre',
                            title='📈 Evolución Por Número de Jugadores Concurrentes En El Tiempo',
                            color_discrete_sequence=px.colors.qualitative.Vivid,
                            labels={
                                'Fecha': 'Fecha De Registro (Tiempo)',
                                'jugadores_historicos': 'Jugadores Concurrentes (Unidades)',
                                'nombre': 'Videojuego',
                            },
                        )
                        fig_line.update_traces(
                            hovertemplate='<b>%{fullData.name}</b><br>Fecha: %{x|%d/%m/%Y}<br>Jugadores: %{y:,.0f}<extra></extra>',
                        )
                        fig_line = _aplicar_tema_plotly(fig_line)
                        st.plotly_chart(fig_line, use_container_width=True)

                        # Animación 1: Carrera de Juegos
                        df_anim_top10 = df_line_top10.sort_values('Fecha').copy()
                        df_anim_top10['Hora_Frame'] = pd.to_datetime(df_anim_top10['Fecha']).dt.strftime('%d/%m %H:%M')
                        max_jugadores = df_anim_top10['jugadores_historicos'].max()
                        fig_anim1 = px.bar(
                            df_anim_top10,
                            x='jugadores_historicos',
                            y='nombre',
                            orientation='h',
                            color='nombre',
                            animation_frame='Hora_Frame',
                            title='🏃 Carrera De Jugadores Concurrentes (Animación En Vivo)',
                            color_discrete_sequence=px.colors.qualitative.Vivid,
                            labels={
                                'jugadores_historicos': 'Jugadores Concurrentes (Unidades)',
                                'nombre': 'Videojuego',
                                'Hora_Frame': 'Fecha De Registro (Tiempo)',
                            },
                        )
                        fig_anim1 = _aplicar_tema_plotly(fig_anim1)
                        fig_anim1.update_layout(
                            xaxis_range=[0, max_jugadores * 1.1],
                            margin=dict(b=120),
                        )
                        fig_anim1.update_xaxes(title_standoff=30)
                        if fig_anim1.layout.updatemenus:
                            fig_anim1.layout.updatemenus[0].y = -0.25
                        if fig_anim1.layout.sliders:
                            fig_anim1.layout.sliders[0].y = -0.25
                        st.plotly_chart(fig_anim1, use_container_width=True)
                    else:
                        st.info("No hay datos históricos para el Top 10 actual.")

                with col_h2:
                    df_gen_hist = (
                        df_hist_merge.assign(genero=df_hist_merge['generos'].str.split(', '))
                        .explode('genero')
                        .groupby(['Fecha', 'genero'])['jugadores_historicos']
                        .sum()
                        .reset_index()
                    )
                    if not df_gen_hist.empty:
                        fig_area = px.area(
                            df_gen_hist,
                            x='Fecha',
                            y='jugadores_historicos',
                            color='genero',
                            title='📊 Evolución Por Género En El Tiempo',
                            color_discrete_sequence=px.colors.qualitative.Vivid,
                            labels={
                                'Fecha': 'Fecha De Registro (Tiempo)',
                                'jugadores_historicos': 'Jugadores Concurrentes (Unidades)',
                                'genero': 'Género',
                            },
                        )
                        st.write("")
                        fig_area.update_traces(
                            hovertemplate='<b>%{fullData.name}</b><br>Fecha: %{x|%d/%m/%Y}<br>Jugadores: %{y:,.0f}<extra></extra>',
                        )
                        fig_area = _aplicar_tema_plotly(fig_area)
                        st.plotly_chart(fig_area, use_container_width=True)

                        # Animación 2: Evolución de Categorías
                        df_anim_gen = df_gen_hist.sort_values('Fecha').copy()
                        df_anim_gen['Hora_Frame'] = pd.to_datetime(df_anim_gen['Fecha']).dt.strftime('%d/%m %H:%M')
                        max_jugadores_categoria = df_anim_gen['jugadores_historicos'].max()
                        fig_anim2 = px.bar(
                            df_anim_gen,
                            x='genero',
                            y='jugadores_historicos',
                            color='genero',
                            animation_frame='Hora_Frame',
                            title='📊 Evolución De Jugadores Por Categoría (Animación En Vivo)',
                            color_discrete_sequence=px.colors.qualitative.Vivid,
                            labels={
                                'genero': 'Género',
                                'jugadores_historicos': 'Jugadores Concurrentes (Unidades)',
                                'Hora_Frame': 'Fecha De Registro (Tiempo)',
                            },
                        )
                        fig_anim2 = _aplicar_tema_plotly(fig_anim2)
                        fig_anim2.update_layout(
                            yaxis_range=[0, max_jugadores_categoria * 1.1],
                            margin=dict(b=120),
                        )
                        fig_anim2.update_xaxes(title_standoff=30)
                        if fig_anim2.layout.updatemenus:
                            fig_anim2.layout.updatemenus[0].y = -0.25
                        if fig_anim2.layout.sliders:
                            fig_anim2.layout.sliders[0].y = -0.25
                        st.plotly_chart(fig_anim2, use_container_width=True)
                    else:
                        st.info("No hay datos históricos por género.")
        st.markdown("---")
        st.markdown("### 🛒 Análisis de Precio Histórico")
        juego_analisis = st.selectbox("Selecciona un título para analizar precios y DLCs:", df_filtrado['nombre'].unique())
        try:
            datos_juego = df_filtrado[df_filtrado['nombre'] == juego_analisis].iloc[0]

            with st.spinner("🔍 Consultando historial de precios reales..."):
                try:
                    datos_historicos = fetch_history_price(datos_juego['appid'], juego_analisis)
                except Exception:
                    datos_historicos = None

            dlcs = None
            ultima_act = "Desconocida"
            if datos_juego['dlc_count'] > 0:
                with st.spinner("Cargando DLCs..."):
                    dlcs = fetch_dlc_list(datos_juego['appid'])
                if dlcs:
                    df_dlc_temp = pd.DataFrame(dlcs)
                    df_dlc_temp['fecha_dt'] = pd.to_datetime(df_dlc_temp['fecha_salida'], errors='coerce')
                    df_dlc_temp = df_dlc_temp.dropna(subset=['fecha_dt'])
                    if not df_dlc_temp.empty:
                        ultima_act = df_dlc_temp['fecha_dt'].max().strftime('%d/%m/%Y')

            # --- TAREA 1: Ficha del Juego Base (Widgets y Gráfica) ---
            col_info, col_graf = st.columns([1, 2])
            with col_info:
                st.markdown("#### 🎮 Ficha del Juego Base")
                precio_actual = float(datos_juego.get('precio_eur', 0) or 0)
                precio_original = float(datos_juego.get('precio_inicial', 0) or 0)
                precio_min = None
                if datos_historicos and datos_historicos.get('precio_min_historico') is not None:
                    precio_min = float(datos_historicos['precio_min_historico'])
                try:
                    fecha_lanz = pd.to_datetime(datos_juego.get('fecha_salida', ''), errors='coerce')
                    fecha_lanz_str = fecha_lanz.strftime('%d/%m/%Y') if pd.notna(fecha_lanz) else "Desconocida"
                except Exception:
                    fecha_lanz_str = "Desconocida"

                c1, c2 = st.columns(2)
                with c1:
                    st.metric("Precio Actual", f"{precio_actual:.2f} €")
                    st.metric("Lanzamiento", fecha_lanz_str)
                with c2:
                    st.metric("Precio Mínimo", f"{precio_min:.2f} €" if precio_min is not None else "N/D")
                    st.metric("Última Act.", ultima_act)

            with col_graf:
                try:
                    st.plotly_chart(
                        generar_grafico_precio_real(
                            precio_original, precio_actual, juego_analisis,
                            datos_juego.get('fecha_salida', ''),
                            datos_historicos
                        ),
                        use_container_width=True,
                    )
                except Exception:
                    import traceback
                    st.error(f"Error generando gráfico: {traceback.format_exc()}")

            # --- TAREA 2: Ecosistema de DLCs ---
            if datos_juego['dlc_count'] <= 0:
                st.info("Este juego no tiene DLCs o contenido adicional registrado.")
            elif not dlcs:
                st.info("No se pudieron cargar los detalles de los DLCs.")
            else:
                df_dlc = pd.DataFrame(dlcs)
                df_dlc['fecha_dt'] = pd.to_datetime(df_dlc['fecha_salida'], errors='coerce')
                df_dlc['fecha_dt'] = df_dlc['fecha_dt'].fillna(pd.Timestamp.today())
                df_dlc['precio_eur'] = df_dlc['precio_eur'].fillna(0)

                def _categoria_dlc(row):
                    n = (row.get('nombre', '') or '').lower()
                    p = float(row.get('precio_eur', 0) or 0)
                    if 'soundtrack' in n or 'ost' in n:
                        return "🎵 Banda Sonora"
                    if 'season pass' in n or 'pase' in n:
                        return "🎟️ Pase de Temporada"
                    if p >= 15:
                        return "🗺️ Expansión Mayor"
                    if p < 5 or 'pack' in n or 'skin' in n:
                        return "👗 Cosmético / Menor"
                    return "🧩 DLC Estándar"

                df_dlc['Categoria_DLC'] = df_dlc.apply(_categoria_dlc, axis=1)
                df_dlc_con_fecha = df_dlc.sort_values('fecha_dt')

                col_dlc_info, col_dlc_graf = st.columns([1, 2])
                with col_dlc_info:
                    st.markdown("#### 🧩 Ecosistema de Expansiones (DLCs)")
                    total_dlcs = len(df_dlc)
                    precio_medio = df_dlc['precio_eur'].mean()
                    fecha_primera = df_dlc_con_fecha['fecha_dt'].min()
                    fecha_ultima = df_dlc_con_fecha['fecha_dt'].max()

                    dc1, dc2 = st.columns(2)
                    with dc1:
                        st.metric("Total Expansiones", total_dlcs)
                        st.metric("Primer DLC", fecha_primera.strftime('%d/%m/%Y'))
                    with dc2:
                        st.metric("Precio Medio", f"{precio_medio:.2f} €")
                        st.metric("Último DLC", fecha_ultima.strftime('%d/%m/%Y'))

                with col_dlc_graf:
                    fig_dlc = px.scatter(
                        df_dlc_con_fecha,
                        x='fecha_dt',
                        y='precio_eur',
                        hover_name='nombre',
                        color='Categoria_DLC',
                        symbol='Categoria_DLC',
                        title='📅 Distribución De Lanzamientos (DLCs)',
                        size_max=12,
                        color_discrete_map={
                            '🎵 Banda Sonora': RED_BASE,
                            '🎟️ Pase de Temporada': '#FF6666',
                            '🗺️ Expansión Mayor': '#FF8080',
                            '👗 Cosmético / Menor': '#FF9999',
                            '🧩 DLC Estándar': '#FFB3B3',
                        },
                        labels={
                            'fecha_dt': 'Fecha De Lanzamiento (Tiempo)',
                            'precio_eur': 'Precio Actual (Euros)',
                            'nombre': 'Contenido',
                            'Categoria_DLC': 'Categoría (Tipo)',
                        },
                    )
                    fig_dlc.update_traces(
                        marker=dict(size=12),
                        hovertemplate='<b>%{hovertext}</b><br>Fecha: %{x|%d/%m/%Y}<br>Precio: %{y:.2f} €<extra></extra>',
                    )
                    fig_dlc = _aplicar_tema_plotly(fig_dlc)
                    max_precio = df_dlc_con_fecha['precio_eur'].max()
                    fig_dlc.update_layout(
                        yaxis=dict(rangemode='tozero', range=[0, max(max_precio * 1.1, 1)]),
                    )
                    st.plotly_chart(fig_dlc, use_container_width=True)

                with st.expander("Ver listado completo de contenido adicional"):
                    df_listado = df_dlc_con_fecha.copy()
                    df_listado['Fecha'] = df_listado['fecha_dt'].dt.strftime('%d/%m/%Y')
                    df_listado['Precio'] = df_listado['precio_eur'].apply(
                        lambda x: "Gratis" if pd.isna(x) or x == 0 else f"{x:.2f} €"
                    )
                    st.dataframe(
                        df_listado[['nombre', 'Fecha', 'Precio', 'Categoria_DLC']].rename(
                            columns={'nombre': 'Contenido', 'Categoria_DLC': 'Categoría'}
                        ),
                        use_container_width=True,
                        hide_index=True,
                    )
        except Exception as e:
            import traceback
            st.error(f"Error procesando análisis de negocio: {traceback.format_exc()}")

        st.markdown("---")
        st.markdown("### 📋 Tabla Resumen de Juegos")
        df_tabla = df_filtrado.copy()
        df_tabla['Descuento'] = df_tabla.apply(
            lambda r: round((r['precio_inicial'] - r['precio_eur']) / r['precio_inicial'] * 100, 0)
            if pd.notna(r['precio_inicial']) and r['precio_inicial'] > 0 else 0,
            axis=1
        )
        df_mostrar = pd.DataFrame({
            'Imagen': df_tabla['header_image'].fillna(''),
            'Ranking': df_tabla['ranking'].astype(int),
            'Nombre': df_tabla['nombre'],
            'Jugadores Actuales': df_tabla['jugadores_actuales'].apply(lambda x: f"{int(x):,}".replace(',', '.')),
            'Precio Actual': df_tabla['precio_eur'].apply(lambda x: "Gratis" if pd.isna(x) or x == 0 else f"{x:.2f} €"),
            'Descuento': df_tabla['Descuento'].astype(int).astype(str) + ' %',
            'Contenido Adicional': df_tabla['dlc_count'].astype(int),
            'Géneros': df_tabla['generos'].fillna(''),
        })
        st.dataframe(
            df_mostrar,
            use_container_width=True,
            hide_index=True,
            column_config={
                'Imagen': st.column_config.ImageColumn('Imagen', width='small'),
            },
        )