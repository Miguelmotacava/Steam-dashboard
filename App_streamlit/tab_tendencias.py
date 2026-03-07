import streamlit as st
import pandas as pd
import plotly.express as px

RED_BASE, RED_SCALE = '#FF4B4B', 'Reds'
RED_DONUT = {'Windows': '#FF4B4B', 'MacOS': '#FF8080', 'Linux': '#FFB3B3'}

def generar_grafico_precio_real(precio_ini, precio_fin, nombre, fecha_salida):
    """Genera la gráfica conectando el día de lanzamiento real con el día de hoy"""
    hoy = pd.Timestamp.today().strftime('%Y-%m-%d')
    
    # Si la fecha de salida falla, ponemos 'Lanzamiento' como texto genérico
    try:
        inicio = pd.to_datetime(fecha_salida).strftime('%Y-%m-%d')
    except:
        inicio = "Día de Lanzamiento"

    df_hist = pd.DataFrame({
        'Momento': [inicio, hoy],
        'Precio': [precio_ini, precio_fin],
        'Etiqueta': ['Salida', 'Hoy']
    })
    
    fig = px.line(df_hist, x='Momento', y='Precio', title=f'📉 Evolución Real del Precio', 
                  markers=True, text='Etiqueta', labels={'Precio': 'Euros (€)', 'Momento': 'Fechas'}, 
                  color_discrete_sequence=[RED_BASE])
    fig.update_traces(textposition="top center")
    
    max_p = max(precio_ini, precio_fin)
    fig.update_layout(yaxis_range=[0, max_p + (max_p * 0.2) + 5])
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
            fig1 = px.bar(df_filtrado.nlargest(10, 'jugadores_actuales').sort_values('jugadores_actuales'), x='jugadores_actuales', y='nombre', orientation='h', title='🏆 Juegos más populares', color_discrete_sequence=[RED_BASE])
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
                fig4 = px.scatter(df_scat, x='precio_eur', y='metacritic_nota', size='jugadores_actuales', hover_name='nombre', title='💎 Precio vs Calidad (Metacritic)', color='nombre')
                st.plotly_chart(fig4, use_container_width=True)

        st.markdown("### 🛒 Análisis de Modelo de Negocio")
        juego_analisis = st.selectbox("Selecciona un título para analizar precios y DLCs:", df_filtrado['nombre'].unique())
        datos_juego = df_filtrado[df_filtrado['nombre'] == juego_analisis].iloc[0]
        
        col_d1, col_d2 = st.columns([1, 2])
        with col_d1:
            st.markdown("<br>", unsafe_allow_html=True)
            st.metric("🧩 Expansiones y Cosméticos", int(datos_juego['dlc_count']))
            st.write(f"**Precio de Lanzamiento:** {datos_juego['precio_inicial']:.2f} €")
            st.write(f"**Precio Actual (Rebajas):** {datos_juego['precio_eur']:.2f} €")
        with col_d2:
            st.plotly_chart(generar_grafico_precio_real(datos_juego['precio_inicial'], datos_juego['precio_eur'], juego_analisis, datos_juego['fecha_salida']), use_container_width=True)