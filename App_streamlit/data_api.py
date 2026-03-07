import streamlit as st
import pandas as pd
import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()
STEAM_API_KEY = os.getenv("STEAM_API_KEY")

@st.cache_data(ttl=3600, show_spinner=False)
def load_steam_data(limite):
    url_top = f"https://api.steampowered.com/ISteamChartsService/GetGamesByConcurrentPlayers/v1/?key={STEAM_API_KEY}"
    try:
        res_top = requests.get(url_top).json()
        top_juegos = res_top.get('response', {}).get('ranks', [])[:limite]
    except:
        return pd.DataFrame()
    
    df_jugadores = pd.DataFrame(top_juegos)
    if df_jugadores.empty: return pd.DataFrame()
    df_jugadores.rename(columns={'concurrent_in_game': 'jugadores_actuales'}, inplace=True)
    
    datos_tienda = []
    my_bar = st.progress(0, text=f"⏳ Descargando datos de {limite} juegos populares...")
    for i, appid in enumerate(df_jugadores['appid']):
        try:
            url_store = f"https://store.steampowered.com/api/appdetails?appids={appid}&cc=es"
            res_store = requests.get(url_store).json()
            if res_store and str(appid) in res_store and res_store[str(appid)].get('success'):
                data = res_store[str(appid)]['data']
                datos_tienda.append({
                    'appid': appid, 'nombre': data.get('name', 'Desconocido'),
                    'es_gratis': data.get('is_free', False),
                    'precio_inicial': data.get('price_overview', {}).get('initial', 0) / 100 if not data.get('is_free', False) else 0.0,
                    'precio_eur': data.get('price_overview', {}).get('final', 0) / 100 if not data.get('is_free', False) else 0.0,
                    'dlc_count': len(data.get('dlc', [])),
                    'metacritic_nota': data.get('metacritic', {}).get('score', None),
                    'windows': data.get('platforms', {}).get('windows', False),
                    'mac': data.get('platforms', {}).get('mac', False),
                    'linux': data.get('platforms', {}).get('linux', False),
                    'generos': ", ".join([g['description'] for g in data.get('genres', [])])
                })
        except: pass 
        time.sleep(1.2)
        my_bar.progress((i + 1) / len(df_jugadores), text=f"⏳ Descargando datos de {limite} juegos populares...")
    my_bar.empty()
    if not datos_tienda: return pd.DataFrame()
    return pd.merge(pd.DataFrame(datos_tienda), df_jugadores, on='appid', how='inner')

@st.cache_data(ttl=600, show_spinner=False)
def load_news_data(appid):
    url_news = f"https://api.steampowered.com/ISteamNews/GetNewsForApp/v0002/?appid={appid}&count=100&format=json"
    try:
        res_news = requests.get(url_news).json()
        noticias = res_news.get('appnews', {}).get('newsitems', [])
        df_noticias = pd.DataFrame(noticias)
        if not df_noticias.empty: df_noticias['fecha_dt'] = pd.to_datetime(df_noticias['date'], unit='s')
        return df_noticias
    except: return pd.DataFrame()

@st.cache_data(ttl=3600, show_spinner=False)
def load_player_profile(steamid):
    try:
        url_sum = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={STEAM_API_KEY}&steamids={steamid}"
        perfil = requests.get(url_sum).json().get('response', {}).get('players', [])
        url_games = f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={STEAM_API_KEY}&steamid={steamid}&include_appinfo=1&format=json"
        juegos = requests.get(url_games).json().get('response', {}).get('games', [])
    except: return None, None, None

    if not perfil or not juegos: return None, None, None
    df_juegos = pd.DataFrame(juegos)
    if 'playtime_forever' not in df_juegos.columns: return perfil[0], pd.DataFrame(), pd.DataFrame()
    
    df_jugados = df_juegos[df_juegos['playtime_forever'] > 0].copy()
    top_15 = df_jugados.nlargest(15, 'playtime_forever')
    generos_jugador = []
    
    for i, appid in enumerate(top_15['appid']):
        try:
            url_store = f"https://store.steampowered.com/api/appdetails?appids={appid}&cc=es"
            res_store = requests.get(url_store).json()
            if res_store and str(appid) in res_store and res_store[str(appid)].get('success'):
                data = res_store[str(appid)]['data']
                for gen in [g['description'] for g in data.get('genres', [])]:
                    generos_jugador.append({'juego': data.get('name'), 'genero': gen, 'minutos': top_15.iloc[i]['playtime_forever']})
        except: pass
        time.sleep(1.2)
    return perfil[0], df_juegos, pd.DataFrame(generos_jugador)

@st.cache_data(ttl=86400, show_spinner=False)
def load_all_apps():
    try:
        url = "https://api.steampowered.com/ISteamApps/GetAppList/v2/"
        res = requests.get(url).json()
        df = pd.DataFrame(res.get('applist', {}).get('apps', []))
        return df[df['name'] != '']
    except: return pd.DataFrame()