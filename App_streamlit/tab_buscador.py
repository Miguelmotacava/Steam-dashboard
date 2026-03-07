import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
from data_api import load_all_apps

RED_BASE = '#FF4B4B'

def generar_grafico_precio(precio_ini, precio_fin, nombre):
    fechas = pd.date_range(end=pd.Timestamp.today(), periods=6, freq='ME')
    precios = [precio_ini, precio_ini, precio_ini, precio_fin, precio_fin, precio_fin]
    fig = px.line(pd.DataFrame({'Fecha': fechas, 'Precio': precios}), x='Fecha', y='Precio', title=f'📈 Evolución del Precio', markers=True, color_discrete_sequence=[RED_BASE])
    fig.update_layout(yaxis_range=[0, max(precio_ini, precio_fin)+10])
    return fig

def render_buscador():
    st.header("🌌 Explorador del Catálogo Global")
    df_all_apps = load_all_apps()
    
    if not df_all_apps.empty:
        # Usamos un form para que no recargue hasta darle al botón
        with st.form("buscador_form"):
            texto_buscar = st.text_input("✍️ Escribe el nombre del juego (Mínimo 3 letras):")
            submit_search = st.form_submit_button("Buscar Juego")
            
        if submit_search and len(texto_buscar) >= 3:
            coincidencias = df_all_apps[df_all_apps['name'].str.contains(texto_buscar, case=False, na=False)].copy()
            if not coincidencias.empty:
                coincidencias['longitud'] = coincidencias['name'].str.len()
                appid_buscar = coincidencias.sort_values('longitud').iloc[0]['appid']
                nombre_real = coincidencias.sort_values('longitud').iloc[0]['name']
                
                st.success(f"✅ Mostrando resultados para: **{nombre_real}**")
                col_b1, col_b2, col_b3 = st.columns([1, 1, 1])
                
                try:
                    jugadores_vivo = requests.get(f"https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid={appid_buscar}").json().get('response', {}).get('player_count', 0)
                    data = requests.get(f"https://store.steampowered.com/api/appdetails?appids={appid_buscar}&cc=es").json()[str(appid_buscar)]['data']
                    precio_ini = data.get('price_overview', {}).get('initial', 0) / 100 if not data.get('is_free', False) else 0.0
                    precio_fin = data.get('price_overview', {}).get('final', 0) / 100 if not data.get('is_free', False) else 0.0
                    
                    with col_b1:
                        st.image(data.get('header_image', ''), use_container_width=True)
                        st.metric("🧩 DLCs y Cosméticos", len(data.get('dlc', [])))
                    with col_b2:
                        st.metric("👥 Jugadores Actuales", f"{jugadores_vivo:,}".replace(',', '.'))
                        st.metric("💸 Precio Actual", f"{precio_fin} €" if precio_fin > 0 else "Gratis")
                    with col_b3:
                        st.plotly_chart(generar_grafico_precio(precio_ini, precio_fin, data.get('name')), use_container_width=True)
                except: st.error("No hay datos comerciales detallados de este juego.")
            else: st.warning("No se encontró ningún juego.")