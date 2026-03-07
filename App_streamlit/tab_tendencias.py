import streamlit as st
import pandas as pd
import plotly.express as px

RED_BASE, RED_SCALE = '#FF4B4B', 'Reds'
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

        st.markdown("### 🛒 Análisis de Modelo de Negocio")
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
        df_tabla['Descuento (%)'] = df_tabla.apply(
            lambda r: round((r['precio_inicial'] - r['precio_eur']) / r['precio_inicial'] * 100, 0)
            if pd.notna(r['precio_inicial']) and r['precio_inicial'] > 0 else 0,
            axis=1
        )
        columnas_tabla = {
            'nombre': 'Nombre',
            'jugadores_actuales': 'Jugadores Actuales',
            'precio_eur': 'Precio (Euros)',
            'Descuento (%)': 'Descuento (%)',
            'dlc_count': 'DLCs',
            'metacritic_nota': 'Nota Metacritic',
            'generos': 'Géneros',
        }
        df_mostrar = df_tabla[list(columnas_tabla.keys())].rename(columns=columnas_tabla)
        st.dataframe(df_mostrar, use_container_width=True, hide_index=True)