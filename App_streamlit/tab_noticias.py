import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from matplotlib.ticker import MaxNLocator
from data_api import load_news_data, fetch_app_details

RED_BASE = '#FF4B4B'


def aplicar_tema_plotly(fig):
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
                for _, row in df_news.head(5).iterrows():
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

                ultima_actualizacion = df_news['fecha_dt'].max()

                with st.container():
                    st.markdown("#### 📦 Información del Juego")
                    if header_image:
                        st.image(header_image, use_container_width=True)
                    st.markdown(f"**Fecha De Lanzamiento:** {fecha_salida or 'N/D'}")
                    st.markdown(
                        f"**Última Actualización:** {ultima_actualizacion.strftime('%d/%m/%Y')}"
                    )

            st.markdown("---")
            st.markdown("### 📊 Análisis del Volumen Informativo")
            col_m1, col_m2 = st.columns(2)

            # Gráfico Matplotlib: Publicaciones por Categoría
            with col_m1:
                st.markdown("**Publicaciones Por Categoría**")
                conteo_cats = (
                    df_news['feedlabel']
                    .fillna('Otros')
                    .value_counts()
                    .sort_values(ascending=True)
                )
                fig_m1, ax_m1 = plt.subplots(figsize=(3, 2))
                fig_m1.patch.set_alpha(0.0)
                ax_m1.patch.set_alpha(0.0)
                ax_m1.barh(
                    conteo_cats.index.astype(str),
                    conteo_cats.values,
                    color=RED_BASE,
                )
                ax_m1.spines['top'].set_visible(False)
                ax_m1.spines['right'].set_visible(False)
                ax_m1.tick_params(colors='gray', labelsize=7)
                ax_m1.set_xlabel(
                    'Número De Publicaciones (Unidades)',
                    color='gray',
                    fontsize=7,
                )
                ax_m1.set_ylabel('Categoría', color='gray', fontsize=7)
                ax_m1.xaxis.set_major_locator(MaxNLocator(integer=True))
                fig_m1.tight_layout(pad=1.2)
                st.pyplot(fig_m1, transparent=True)
                plt.close(fig_m1)

            # Gráfico Plotly: Evolución Temporal de Noticias
            with col_m2:
                conteo_temp = (
                    df_news.groupby(df_news['fecha_dt'].dt.date)
                    .size()
                    .reset_index(name='publicaciones')
                )
                conteo_temp.columns = ['fecha', 'publicaciones']
                fig_evol = px.bar(
                    conteo_temp,
                    x='fecha',
                    y='publicaciones',
                    title='📈 Evolución Temporal De Noticias',
                    color_discrete_sequence=[RED_BASE],
                    labels={
                        'fecha': 'Fecha',
                        'publicaciones': 'Número De Publicaciones (Unidades)',
                    },
                )
                fig_evol.update_layout(
                    yaxis=dict(tickformat='d', dtick=1),
                )
                fig_evol = aplicar_tema_plotly(fig_evol)
                st.plotly_chart(fig_evol, use_container_width=True)
        else:
            st.info("📭 No hay noticias con los filtros aplicados.")
