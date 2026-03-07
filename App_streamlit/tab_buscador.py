import streamlit as st
import pandas as pd
import requests
from data_api import load_all_apps
from tab_tendencias import generar_grafico_precio

def render_buscador():
    st.header("🌌 Explorador del Catálogo Global")
    st.write("Busca cualquier título entre los 150.000 juegos de Steam.")
    
    df_all_apps = load_all_apps()
    if df_all_apps.empty:
        st.error("No se ha podido cargar el catálogo global en este momento.")
        return

    with st.form("buscador_form"):
        col_b_input, col_b_btn = st.columns([4, 1])
        with col_b_input: texto_buscar = st.text_input("✍️ Escribe el nombre (Ej: Cyberpunk, Portal 2):")
        with col_b_btn: 
            st.markdown("<br>", unsafe_allow_html=True)
            submit_buscar = st.form_submit_button("🔍 Buscar en Steam")
            
    if submit_buscar and len(texto_buscar) >= 3:
        coincidencias = df_all_apps[df_all_apps['name'].str.contains(texto_buscar, case=False, na=False)].copy()
        if not coincidencias.empty:
            coincidencias['longitud'] = coincidencias['name'].str.len()
            mejor_match = coincidencias.sort_values('longitud').iloc[0]
            appid_buscar = mejor_match['appid']
            
            st.success(f"✅ Extrayendo información comercial para: **{mejor_match['name']}**")
            col_b1, col_b2, col_b3 = st.columns([1, 1, 1])
            
            try:
                jugadores_vivo = requests.get(f"https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid={appid_buscar}").json().get('response', {}).get('player_count', 0)
                res_store = requests.get(f"https://store.steampowered.com/api/appdetails?appids={appid_buscar}&cc=es").json()
                
                if res_store and str(appid_buscar) in res_store and res_store[str(appid_buscar)].get('success'):
                    data = res_store[str(appid_buscar)]['data']
                    precio_ini = data.get('price_overview', {}).get('initial', 0) / 100 if not data.get('is_free', False) else 0.0
                    precio_fin = data.get('price_overview', {}).get('final', 0) / 100 if not data.get('is_free', False) else 0.0
                    dlcs_totales = len(data.get('dlc', []))
                    
                    with col_b1:
                        st.image(data.get('header_image', ''), use_container_width=True)
                        st.metric("🧩 DLCs y Contenido Extra", dlcs_totales)
                    with col_b2:
                        st.metric("👥 Jugadores Ahora Mismo", f"{jugadores_vivo:,}".replace(',', '.'))
                        st.metric("💸 Precio Actual", f"{precio_fin} €" if precio_fin > 0 else "Gratis")
                    with col_b3:
                        st.plotly_chart(generar_grafico_precio(precio_ini, precio_fin, data.get('name')), use_container_width=True)
                else: st.error("Steam no devuelve información pública de la tienda para este título.")
            except: st.error("Ocurrió un error al contactar con la API de Steam.")
        else: st.warning("No se ha encontrado ningún juego con ese nombre.")
    elif submit_buscar: st.warning("Escribe al menos 3 letras.")