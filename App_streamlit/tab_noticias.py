import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from data_api import load_news_data

RED_BASE = '#FF4B4B'


def render_noticias(df_super):
    st.header("📰 Radar de Noticias y Actualizaciones")

    col_n1, col_n2, col_n3 = st.columns([2, 1, 1])
    with col_n1:
        juego_elegido = st.selectbox("🕹️ Selecciona juego:", df_super['nombre'].unique())
    with col_n2:
        filtro_tiempo = st.radio("⏱️ Rango temporal:", ["Mes", "Todo"], index=1)
    with col_n3:
        tipo_noticia = st.radio("🛠️ Tipo:", ["Todo", "Parches", "Anuncios"])

    appid_elegido = df_super[df_super['nombre'] == juego_elegido]['appid'].iloc[0]
    df_news = load_news_data(appid_elegido)

    if not df_news.empty:
        if filtro_tiempo == "Mes":
            df_news = df_news[
                df_news['fecha_dt'] >= (pd.Timestamp.now() - pd.Timedelta(days=30))
            ]
        if tipo_noticia == "Parches":
            df_news = df_news[df_news['feed_type'] == 1]
        elif tipo_noticia == "Anuncios":
            df_news = df_news[df_news['feed_type'] == 0]

        st.markdown("---")
        if not df_news.empty:
            st.metric("Impactos Informativos", len(df_news))
            st.subheader("Últimos Titulares")
            for _, row in df_news.head(5).iterrows():
                st.markdown(
                    f"🗓️ **{row['fecha_dt'].strftime('%d/%m/%Y')}** - [{row['title']}]({row['url']})"
                )

            st.markdown("---")
            st.markdown("### 📊 Análisis del Volumen Informativo")
            col_m1, col_m2 = st.columns(2)

            with col_m1:
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
                    conteo_cats.index.astype(str), conteo_cats.values, color=RED_BASE
                )
                ax_m1.spines['top'].set_visible(False)
                ax_m1.spines['right'].set_visible(False)
                ax_m1.tick_params(colors='gray', labelsize=7)
                ax_m1.set_xlabel(
                    'Número De Publicaciones (Unidades)', color='gray', fontsize=7
                )
                ax_m1.set_ylabel('Categoría', color='gray', fontsize=7)
                ax_m1.xaxis.set_major_locator(MaxNLocator(integer=True))
                fig_m1.tight_layout(pad=1.2)
                st.pyplot(fig_m1, transparent=True)
                plt.close(fig_m1)

            with col_m2:
                conteo_temp = (
                    df_news.groupby(df_news['fecha_dt'].dt.date).size().sort_index()
                )
                fig_m2, ax_m2 = plt.subplots(figsize=(3, 2))
                fig_m2.patch.set_alpha(0.0)
                ax_m2.patch.set_alpha(0.0)
                x_labels = [str(d) for d in conteo_temp.index]
                ax_m2.plot(
                    range(len(conteo_temp)),
                    conteo_temp.values,
                    color=RED_BASE,
                    marker='o',
                    markersize=4,
                )
                ax_m2.set_xticks(range(len(conteo_temp)))
                ax_m2.set_xticklabels(x_labels, rotation=30, ha='right', fontsize=6)
                ax_m2.yaxis.set_major_locator(MaxNLocator(integer=True))
                max_val = conteo_temp.max() if not conteo_temp.empty else 10
                ax_m2.set_ylim(0, max_val + (max_val * 0.2))
                ax_m2.spines['top'].set_visible(False)
                ax_m2.spines['right'].set_visible(False)
                ax_m2.tick_params(colors='gray', labelsize=7)
                ax_m2.set_xlabel('Fecha', color='gray', fontsize=7)
                ax_m2.set_ylabel(
                    'Número De Publicaciones (Unidades)', color='gray', fontsize=7
                )
                fig_m2.tight_layout(pad=1.2)
                st.pyplot(fig_m2, transparent=True)
                plt.close(fig_m2)
        else:
            st.info("📭 No hay noticias con los filtros aplicados.")
