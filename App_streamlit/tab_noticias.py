import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from matplotlib.ticker import MaxNLocator
from data_api import load_news_data, fetch_app_details

RED_BASE = '#FF4B4B'


def aplicar_tema_oscuro_transparente(fig):
    """Aplica tema oscuro transparente a figuras Plotly."""
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white', size=12),
        title_font=dict(color='white'),
        margin=dict(l=20, r=20, t=50, b=20),
        xaxis=dict(
            gridcolor='rgba(255,255,255,0.1)',
            tickfont=dict(color='white'),
        ),
        yaxis=dict(
            gridcolor='rgba(255,255,255,0.1)',
            tickfont=dict(color='white'),
        ),
    )
    return fig


def render_noticias(df_super):
    st.header("📰 Radar de Noticias y Actualizaciones")

    col_n1, col_n2, col_n3 = st.columns([2, 1, 1])
    with col_n1:
        juego_elegido = st.selectbox(
            "🕹️ Selecciona juego:", df_super['nombre'].unique()
        )
    with col_n2:
        filtro_tiempo = st.radio(
            "⏱️ Rango temporal:",
            ["Última Semana", "Mes", "Todo"],
            index=1,
        )
    with col_n3:
        tipo_noticia = st.radio("🛠️ Tipo:", ["Todo", "Parches", "Anuncios"])

    appid_elegido = df_super[df_super['nombre'] == juego_elegido]['appid'].iloc[0]
    df_news = load_news_data(appid_elegido)

    if not df_news.empty:
        if filtro_tiempo == "Última Semana":
            df_news = df_news[
                df_news['fecha_dt'] >= (pd.Timestamp.now() - pd.Timedelta(days=7))
            ]
        elif filtro_tiempo == "Mes":
            df_news = df_news[
                df_news['fecha_dt'] >= (pd.Timestamp.now() - pd.Timedelta(days=30))
            ]
        if tipo_noticia == "Parches":
            df_news = df_news[df_news['feed_type'] == 1]
        elif tipo_noticia == "Anuncios":
            df_news = df_news[df_news['feed_type'] == 0]

        st.markdown("---")
        if not df_news.empty:
            col_met1, col_met2, col_met3 = st.columns(3)
            with col_met1:
                st.metric("📰 Impactos Informativos", len(df_news))
            with col_met2:
                n_parches = len(df_news[df_news['feed_type'] == 1]) if 'feed_type' in df_news.columns else 0
                st.metric("🛠️ Parches", n_parches)
            with col_met3:
                n_anuncios = len(df_news[df_news['feed_type'] == 0]) if 'feed_type' in df_news.columns else 0
                st.metric("📢 Anuncios", n_anuncios)

            # --- Últimos Titulares + Widget Tarjeta [2, 1] ---
            col_titulares, col_tarjeta = st.columns([2, 1])
            with col_titulares:
                st.subheader("Últimos Titulares")
                for _, row in df_news.head(10).iterrows():
                    st.markdown(
                        f"🗓️ **{row['fecha_dt'].strftime('%d/%m/%Y')}** - "
                        f"[{row['title']}]({row['url']})"
                    )

            with col_tarjeta:
                # Obtener header_image y fecha_salida de df_super o API
                if 'header_image' in df_super.columns and 'fecha_salida' in df_super.columns:
                    fila_juego = df_super[df_super['appid'] == appid_elegido].iloc[0]
                    header_image = fila_juego.get('header_image', '')
                    fecha_salida = fila_juego.get('fecha_salida', '')
                else:
                    header_image = ''
                    fecha_salida = ''
                if not header_image or not fecha_salida:
                    detalles = fetch_app_details(appid_elegido)
                    header_image = header_image or detalles['header_image']
                    fecha_salida = fecha_salida or detalles['fecha_salida']

                # Formatear fecha de lanzamiento (unificar con dd/mm/yyyy)
                if not fecha_salida or (isinstance(fecha_salida, str) and 'coming' in fecha_salida.lower()):
                    fecha_lanzamiento_str = "Desconocida"
                else:
                    try:
                        fecha_parseada = pd.to_datetime(fecha_salida, errors='coerce')
                        fecha_lanzamiento_str = fecha_parseada.strftime('%d/%m/%Y') if pd.notna(fecha_parseada) else "Desconocida"
                    except Exception:
                        fecha_lanzamiento_str = "Desconocida"

                ultima_actualizacion = df_news['fecha_dt'].max()

                with st.container():
                    st.markdown("#### 📦 Información del Juego")
                    if header_image:
                        st.image(header_image, use_container_width=True)
                    st.markdown(f"**Fecha De Lanzamiento:** {fecha_lanzamiento_str}")
                    st.markdown(
                        f"**Última Actualización:** {ultima_actualizacion.strftime('%d/%m/%Y')}"
                    )

            st.markdown("---")
            st.markdown("### 📊 Análisis del Volumen Informativo")
            col_m1, col_m2 = st.columns(2)

            # Gráfico Plotly: Publicaciones por Categoría (barras horizontales)
            with col_m1:
                conteo_cats = (
                    df_news['feedlabel']
                    .fillna('Otros')
                    .value_counts()
                    .sort_values(ascending=True)
                    .reset_index()
                )
                conteo_cats.columns = ['categoria', 'cantidad']
                fig_cats = px.bar(
                    conteo_cats,
                    x='cantidad',
                    y='categoria',
                    orientation='h',
                    title='📊 Publicaciones Por Categoría',
                    color_discrete_sequence=[RED_BASE],
                    labels={
                        'cantidad': 'Número De Publicaciones (Unidades)',
                        'categoria': 'Categoría De La Noticia',
                    },
                )
                fig_cats.update_traces(hovertemplate='<b>Categoría</b>: %{y}<br><b>Nº de publicaciones</b>: %{x}<extra></extra>')
                fig_cats = aplicar_tema_oscuro_transparente(fig_cats)
                st.plotly_chart(fig_cats, use_container_width=True)

            # Gráfico Plotly: Porcentaje Parches vs Anuncios
            with col_m2:
                n_parches = len(df_news[df_news['feed_type'] == 1]) if 'feed_type' in df_news.columns else 0
                n_anuncios = len(df_news[df_news['feed_type'] == 0]) if 'feed_type' in df_news.columns else 0
                total = n_parches + n_anuncios
                if total > 0:
                    df_tipo = pd.DataFrame({
                        'tipo': ['Parches', 'Anuncios'],
                        'cantidad': [n_parches, n_anuncios],
                        'porcentaje': [
                            round(n_parches / total * 100, 1),
                            round(n_anuncios / total * 100, 1),
                        ],
                    })
                    fig_tipo = px.pie(
                        df_tipo,
                        names='tipo',
                        values='cantidad',
                        hole=0.5,
                        title='📊 Porcentaje De Noticias: Parches vs Anuncios',
                        color='tipo',
                        color_discrete_map={'Parches': RED_BASE, 'Anuncios': '#FF8080'},
                        labels={'tipo': 'Tipo De Noticia', 'cantidad': 'Cantidad'},
                    )
                    fig_tipo.update_traces(
                        textinfo='percent+label',
                        textposition='outside',
                        hovertemplate='<b>Tipo de noticia</b>: %{label}<br><b>Cantidad</b>: %{value}<br><b>Porcentaje</b>: %{percent}<extra></extra>',
                    )
                    fig_tipo = aplicar_tema_oscuro_transparente(fig_tipo)
                    st.plotly_chart(fig_tipo, use_container_width=True)
                else:
                    st.info("No hay noticias clasificadas por tipo.")

            # Gráfico Matplotlib: Línea temporal histórica (evolución acumulada)
            st.markdown("### 📈 Línea Temporal Histórica de Publicaciones")
            df_temporal = (
                df_news.groupby(df_news['fecha_dt'].dt.to_period('M'))
                .size()
                .sort_index()
                .reset_index()
            )
            df_temporal.columns = ['periodo', 'cantidad']
            df_temporal['periodo'] = df_temporal['periodo'].astype(str)
            if not df_temporal.empty:
                fig_line, ax_line = plt.subplots(figsize=(6, 2.5))
                fig_line.patch.set_alpha(0.0)
                ax_line.patch.set_alpha(0.0)
                ax_line.plot(
                    range(len(df_temporal)),
                    df_temporal['cantidad'].values,
                    color=RED_BASE,
                    marker='o',
                    markersize=4,
                )
                ax_line.set_xticks(range(len(df_temporal)))
                ax_line.set_xticklabels(df_temporal['periodo'], rotation=30, ha='right')
                ax_line.spines['top'].set_visible(False)
                ax_line.spines['right'].set_visible(False)
                ax_line.tick_params(colors='gray', labelsize=8)
                ax_line.set_xlabel('Fecha De Publicación (Tiempo)', color='gray', fontsize=8)
                ax_line.set_ylabel('Número De Noticias (Unidades)', color='gray', fontsize=8)
                ax_line.yaxis.set_major_locator(MaxNLocator(integer=True))
                fig_line.tight_layout(pad=1.2)
                st.pyplot(fig_line, transparent=True)
                plt.close(fig_line)

            # Tabla resumen de noticias (al final)
            st.markdown("---")
            st.markdown("### Tabla Resumen de Noticias")
            df_tabla_news = df_news.copy()
            df_tabla_news['Fecha'] = df_tabla_news['fecha_dt'].dt.strftime('%d/%m/%Y')
            df_tabla_news['Tipo'] = df_tabla_news['feed_type'].map({0: 'Anuncio', 1: 'Parche'}).fillna('Otro')
            df_tabla_news['Categoría'] = df_tabla_news['feedlabel'].fillna('Otros')
            df_mostrar_news = df_tabla_news[['Fecha', 'title', 'url', 'Tipo', 'Categoría']].rename(columns={'title': 'Título', 'url': 'Enlace'})
            st.dataframe(
                df_mostrar_news,
                use_container_width=True,
                hide_index=True,
                column_config={
                    'Enlace': st.column_config.LinkColumn('Enlace', display_text='Ver'),
                },
            )
        else:
            st.info("📭 No hay noticias con los filtros aplicados.")
