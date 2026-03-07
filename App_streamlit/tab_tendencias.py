import os
import streamlit as st
import pandas as pd
import plotly.express as px

RED_BASE, RED_SCALE = '#FF4B4B', 'Reds'
PALETA_ROJA = [RED_BASE, '#FF6666', '#FF8080', '#FF9999', '#FFB3B3', '#E74C3C', '#C0392B', '#FF6B6B', '#FF8B8B', '#FF5555']


def _ruta_historial():
    """Ruta al CSV de historial (repo root)."""
    return os.path.join(os.path.dirname(__file__), '..', 'historial_top100.csv')


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


RED_DONUT = {'Windows': '#FF4B4B', 'MacOS': '#FF8080', 'Linux': '#FFB3B3'}
import plotly.graph_objects as go
from data_api import fetch_history_price

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
        name='Precio'
    ))

    # Línea base para el mínimo si existe
    if datos_historicos:
        p_min = datos_historicos['precio_min_historico']
        fig.add_hline(y=p_min, line_dash="dash", line_color="green", annotation_text=f"Mínimo histórico: {p_min:.2f}€", annotation_position="bottom right")
    
    max_p = max(precios) if precios else max(precio_ini, precio_fin)
    fig.update_layout(
        title=f'📉 Evolución Real del Precio',
        yaxis_range=[0, max_p + (max_p * 0.3) + 2],
        xaxis_title='Fecha',
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
    st.markdown("---")

    if not df_filtrado.empty:
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("👥 Jugadores Concurrentes", f"{int(df_filtrado['jugadores_actuales'].sum()):,}".replace(',', '.'))
        kpi2.metric("🕹️ Títulos Mostrados", len(df_filtrado))
        kpi3.metric("💸 Precio Medio", f"{df_filtrado[df_filtrado['precio_eur']>0]['precio_eur'].mean():.2f} €" if not df_filtrado[df_filtrado['precio_eur']>0].empty else "0.00 €")
        kpi4.metric("🎁 Free-to-Play", int(df_filtrado['es_gratis'].sum()))

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            fig1 = px.bar(
                df_filtrado.nlargest(10, 'jugadores_actuales').sort_values('jugadores_actuales'),
                x='jugadores_actuales', y='nombre', orientation='h',
                title='🏆 Juegos más populares', color_discrete_sequence=[RED_BASE],
                labels={'jugadores_actuales': 'Jugadores Actuales (Unidades)', 'nombre': 'Videojuego'},
            )
            st.plotly_chart(fig1, use_container_width=True)
        with col_g2:
            df_gen = df_filtrado.assign(genero=df_filtrado['generos'].str.split(', ')).explode('genero')
            fig2 = px.treemap(df_gen.groupby('genero')['jugadores_actuales'].sum().reset_index(), path=['genero'], values='jugadores_actuales', title='🎭 Distribución por Géneros', color='jugadores_actuales', color_continuous_scale=RED_SCALE)
            st.plotly_chart(fig2, use_container_width=True)

        col_g3, col_g4 = st.columns(2)
        with col_g3:
            df_os = pd.DataFrame([('Windows', df_filtrado['windows'].sum()), ('MacOS', df_filtrado['mac'].sum()), ('Linux', df_filtrado['linux'].sum())], columns=['SO', 'Compatibles'])
            fig3 = px.pie(df_os, names='SO', values='Compatibles', hole=0.5, title='🖥️ Compatibilidad de Sistemas', color='SO', color_discrete_map=RED_DONUT)
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
                st.plotly_chart(fig4, use_container_width=True)

        # --- Gráficas Históricas (si existe historial) ---
        if df_historial is not None and not df_historial.empty:
            df_hist_merge = pd.merge(
                df_historial,
                df_filtrado[['appid', 'nombre', 'generos']].drop_duplicates('appid'),
                on='appid',
                how='inner',
            )
            if not df_hist_merge.empty:
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
                            title='📈 Top 10 Actual - Evolución En El Tiempo',
                            color_discrete_sequence=PALETA_ROJA,
                            labels={
                                'Fecha': 'Fecha De Registro (Tiempo)',
                                'jugadores_historicos': 'Jugadores Concurrentes (Unidades)',
                                'nombre': 'Videojuego',
                            },
                        )
                        fig_line = _aplicar_tema_plotly(fig_line)
                        st.plotly_chart(fig_line, use_container_width=True)
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
                            color_discrete_sequence=PALETA_ROJA,
                            labels={
                                'Fecha': 'Fecha De Registro (Tiempo)',
                                'jugadores_historicos': 'Jugadores Concurrentes (Unidades)',
                                'genero': 'Género',
                            },
                        )
                        fig_area = _aplicar_tema_plotly(fig_area)
                        st.plotly_chart(fig_area, use_container_width=True)
                    else:
                        st.info("No hay datos históricos por género.")

        st.markdown("### 🛒 Análisis de Precio Histórico")
        juego_analisis = st.selectbox("Selecciona un título para analizar precios y DLCs:", df_filtrado['nombre'].unique())
        try:
            datos_juego = df_filtrado[df_filtrado['nombre'] == juego_analisis].iloc[0]
            
            with st.spinner("🔍 Consultando historial de precios reales..."):
                try:
                    datos_historicos = fetch_history_price(datos_juego['appid'], juego_analisis)
                except Exception as e:
                    import traceback
                    st.error(f"Error consultando historial: {e}")
                    datos_historicos = None

            col_d1, col_d2 = st.columns([1, 2])
            with col_d1:
                st.markdown("<br>", unsafe_allow_html=True)
                st.metric("🧩 Expansiones y Cosméticos", int(datos_juego['dlc_count']))
                st.write(f"**Precio de Lanzamiento:** {datos_juego['precio_inicial']:.2f} €")
                st.write(f"**Precio Actual (Rebajas):** {datos_juego['precio_eur']:.2f} €")
                if datos_historicos:
                    st.write(f"**💰 Mínimo Histórico:** {datos_historicos['precio_min_historico']:.2f} €")
            with col_d2:
                try:
                    st.plotly_chart(generar_grafico_precio_real(datos_juego['precio_inicial'], datos_juego['precio_eur'], juego_analisis, datos_juego['fecha_salida'], datos_historicos), use_container_width=True)
                except Exception as e:
                    import traceback
                    st.error(f"Error generando gráfico: {traceback.format_exc()}")
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
            'Nombre': df_tabla['nombre'],
            'Jugadores Actuales': df_tabla['jugadores_actuales'].apply(lambda x: f"{int(x):,}".replace(',', '.')),
            'Precio Actual': df_tabla['precio_eur'].apply(lambda x: "Gratis" if pd.isna(x) or x == 0 else f"{x:.2f} €"),
            'Descuento': df_tabla['Descuento'].astype(int).astype(str) + ' %',
            'Contenido Adicional': df_tabla['dlc_count'].astype(int),
            'Géneros': df_tabla['generos'].fillna(''),
        })
        st.dataframe(df_mostrar, use_container_width=True, hide_index=True)