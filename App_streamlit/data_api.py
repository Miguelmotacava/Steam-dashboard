import streamlit as st
import pandas as pd
import requests
import time
import os
import re
from dotenv import load_dotenv

# Cargar .env desde distintas rutas posibles
load_dotenv(".env")
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

STEAM_API_KEY = os.getenv("STEAM_API_KEY")

# Si no está en las variables de entorno, buscar en Streamlit Secrets (Cloud)
if not STEAM_API_KEY:
    try:
        STEAM_API_KEY = st.secrets.get("STEAM_API_KEY")
    except Exception:
        pass

def obtener_steam_id_real(input_usuario):
    """Extrae el SteamID64 numérico de una URL o texto plano."""
    match = re.search(r'7656119\d{10}', input_usuario)
    if match: return match.group(0)
    
    vanity = input_usuario.rstrip('/').split('/')[-1]
    url_vanity = f"https://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/?key={STEAM_API_KEY}&vanityurl={vanity}"
    try:
        res = requests.get(url_vanity).json()
        if res.get('response', {}).get('success') == 1: return res['response']['steamid']
    except: pass
    return None

@st.cache_data(ttl=3600, show_spinner=False)
def load_steam_data(limite):
    url_top = f"https://api.steampowered.com/ISteamChartsService/GetGamesByConcurrentPlayers/v1/?key={STEAM_API_KEY}"
    try:
        top_juegos = requests.get(url_top).json().get('response', {}).get('ranks', [])[:limite]
    except: return pd.DataFrame()
    
    df_jugadores = pd.DataFrame(top_juegos)
    if df_jugadores.empty: return pd.DataFrame()
    df_jugadores.rename(columns={'concurrent_in_game': 'jugadores_actuales'}, inplace=True)
    
    datos_tienda = []
    my_bar = st.progress(0, text=f"⏳ Descargando datos ultrarrápidos de {limite} juegos...")
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
                    'fecha_salida': data.get('release_date', {}).get('date', ''), # NUEVO: Fecha real
                    'dlc_count': len(data.get('dlc', [])),
                    'metacritic_nota': data.get('metacritic', {}).get('score', None),
                    'windows': data.get('platforms', {}).get('windows', False),
                    'mac': data.get('platforms', {}).get('mac', False),
                    'linux': data.get('platforms', {}).get('linux', False),
                    'generos': ", ".join([g['description'] for g in data.get('genres', [])])
                })
        except: pass 
        time.sleep(1.2)
        my_bar.progress((i + 1) / len(df_jugadores), text=f"⏳ Analizando mercado...")
    my_bar.empty()
    return pd.merge(pd.DataFrame(datos_tienda), df_jugadores, on='appid', how='inner')

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_precio_historico(appid, nombre):
    """Consulta CheapShark para obtener el precio más bajo histórico en Steam."""
    try:
        url_search = f"https://www.cheapshark.com/api/1.0/games?steamAppID={appid}"
        res = requests.get(url_search, timeout=5).json()
        if not res or len(res) == 0: return None
        
        game_id = res[0].get('gameID')
        if not game_id: return None
        
        url_detail = f"https://www.cheapshark.com/api/1.0/games?id={game_id}"
        res_detail = requests.get(url_detail, timeout=5).json()
        
        from datetime import datetime
        cheapest = res_detail.get('cheapestPriceEver', {})
        precio_min = float(cheapest.get('price', 0))
        fecha_min_ts = cheapest.get('date', 0)
        fecha_min = datetime.fromtimestamp(fecha_min_ts).strftime('%Y-%m-%d') if fecha_min_ts else None
        
        deals = res_detail.get('deals', [])
        steam_deal = next((d for d in deals if d.get('storeID') == '1'), None)
        
        return {
            'precio_min_historico': precio_min,
            'fecha_min_historico': fecha_min,
            'precio_retail': float(steam_deal['retailPrice']) if steam_deal else None,
            'precio_actual_cs': float(steam_deal['price']) if steam_deal else None,
        }
    except Exception as e:
        # Raise instead of return None so Streamlit doesn't cache the error
        raise RuntimeError(f"Error en CheapShark API: {e}")

@st.cache_data(ttl=600, show_spinner=False)
def load_news_data(appid):
    url_news = f"https://api.steampowered.com/ISteamNews/GetNewsForApp/v0002/?appid={appid}&count=100&format=json"
    try:
        noticias = requests.get(url_news).json().get('appnews', {}).get('newsitems', [])
        df_noticias = pd.DataFrame(noticias)
        if not df_noticias.empty: df_noticias['fecha_dt'] = pd.to_datetime(df_noticias['date'], unit='s')
        return df_noticias
    except: return pd.DataFrame()

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_player_profile(steamid):
    if not STEAM_API_KEY:
        raise ValueError("STEAM_API_KEY no detectado (revisa el archivo .env o secrets)")
    try:
        url_sum = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={STEAM_API_KEY}&steamids={steamid}"
        perfil = requests.get(url_sum).json().get('response', {}).get('players', [])
        
        url_games = f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={STEAM_API_KEY}&steamid={steamid}&include_appinfo=1&format=json"
        juegos = requests.get(url_games).json().get('response', {}).get('games', [])
    except Exception as e:
        raise RuntimeError(f"Error conectando a Steam API: {e}")

    if not perfil: raise ValueError("El perfil devuelto está vacío")
    df_juegos = pd.DataFrame(juegos)
    
    if 'playtime_forever' not in df_juegos.columns or df_juegos.empty: 
        return perfil[0], pd.DataFrame(), pd.DataFrame()
        
    df_jugados = df_juegos.copy() # Eliminado el filtro '> 0' para que usuarios con "0 horas" no rompan la app
    top_15 = df_jugados.nlargest(15, 'playtime_forever')
    generos_jugador = []
    
    my_bar = st.progress(0, text="⏳ Extrayendo géneros de tu biblioteca...")
    for i, appid in enumerate(top_15['appid']):
        try:
            url_store = f"https://store.steampowered.com/api/appdetails?appids={appid}&cc=es"
            data = requests.get(url_store).json().get(str(appid), {}).get('data', {})
            for gen in [g['description'] for g in data.get('genres', [])]:
                generos_jugador.append({'juego': data.get('name'), 'genero': gen, 'minutos': top_15.iloc[i]['playtime_forever']})
        except: pass
        time.sleep(1.2)
        my_bar.progress((i + 1) / len(top_15), text="⏳ Extrayendo géneros de tu biblioteca...")
    my_bar.empty()
    return perfil[0], df_juegos, pd.DataFrame(generos_jugador)