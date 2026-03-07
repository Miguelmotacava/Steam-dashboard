import streamlit as st
import pandas as pd
import requests
import time
import os
import re
from dotenv import dotenv_values

def get_api_key(key_name="STEAM_API_KEY"):
    """
    Obtiene la API key de forma infalible buscando en Secrets de Streamlit o archivos .env 
    directamente sin depender de la caché de os.environ.
    """
    # 1. Prioridad a Streamlit Secrets (para el despliegue en la nube)
    try:
        if key_name in st.secrets:
            return st.secrets[key_name]
    except Exception:
        pass

    # 2. Buscar en las variables de entorno ya cargadas
    val = os.getenv(key_name)
    if val: return val

    # 3. Leer directamente los archivos .env locales (saltando bloqueos de SO)
    rutas_env = [
        ".env",
        os.path.join(os.path.dirname(__file__), '.env'),
        os.path.join(os.path.dirname(__file__), '..', '.env')
    ]
    for ruta in rutas_env:
        if os.path.exists(ruta):
            diccionario_env = dotenv_values(ruta)
            if key_name in diccionario_env and diccionario_env[key_name]:
                return diccionario_env[key_name]
                
    return None

def obtener_steam_id_real(input_usuario):
    """Extrae el SteamID64 numérico de una URL o texto plano."""
    match = re.search(r'7656119\d{10}', input_usuario)
    if match: return match.group(0)
    
    steam_api_key = get_api_key()
    if not steam_api_key: return None
    
    vanity = input_usuario.rstrip('/').split('/')[-1]
    url_vanity = f"https://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/?key={steam_api_key}&vanityurl={vanity}"
    try:
        res = requests.get(url_vanity).json()
        if res.get('response', {}).get('success') == 1: return res['response']['steamid']
    except: pass
    return None

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_global_steam_data(limite):
    steam_api_key = get_api_key()
    if not steam_api_key: 
        raise RuntimeError("STEAM_API_KEY no detectado (API global). Configure el archivo .env o st.secrets.")
    
    url_top = f"https://api.steampowered.com/ISteamChartsService/GetGamesByConcurrentPlayers/v1/?key={steam_api_key}"
    try:
        res = requests.get(url_top)
        res.raise_for_status()
        top_juegos = res.json().get('response', {}).get('ranks', [])[:limite]
    except Exception as e:
        raise RuntimeError(f"Error HTTP Steam API Global: {e}")
    
    df_jugadores = pd.DataFrame(top_juegos)
    if df_jugadores.empty: return pd.DataFrame()
    df_jugadores.rename(columns={'concurrent_in_game': 'jugadores_actuales'}, inplace=True)
    df_jugadores['ranking'] = range(1, len(df_jugadores) + 1)
    
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
                    'fecha_salida': data.get('release_date', {}).get('date', ''),
                    'header_image': data.get('header_image', ''),
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
def fetch_history_price(appid, nombre):
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

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_app_details(appid):
    """Obtiene header_image y fecha_salida de la Steam Store API."""
    try:
        url = f"https://store.steampowered.com/api/appdetails?appids={appid}&cc=es"
        res = requests.get(url, timeout=5).json()
        if res and str(appid) in res and res[str(appid)].get('success'):
            data = res[str(appid)]['data']
            return {
                'header_image': data.get('header_image', ''),
                'fecha_salida': data.get('release_date', {}).get('date', ''),
            }
    except Exception:
        pass
    return {'header_image': '', 'fecha_salida': ''}


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_dlc_list(appid):
    """Obtiene lista de DLCs/expansiones/cosméticos con nombre, fecha de salida y precio."""
    try:
        url = f"https://store.steampowered.com/api/appdetails?appids={appid}&cc=es"
        res = requests.get(url, timeout=5).json()
        if not res or str(appid) not in res or not res[str(appid)].get('success'):
            return []
        data = res[str(appid)]['data']
        dlc_appids = data.get('dlc', [])
        if not dlc_appids:
            return []
        def _infer_tipo_dlc(nombre):
            n = (nombre or '').lower()
            if 'soundtrack' in n or ' ost' in n or 'banda sonora' in n:
                return 'Banda Sonora'
            if 'cosmetic' in n or 'skin' in n or 'cosmético' in n:
                return 'Cosmético'
            if 'expansion' in n or 'expansión' in n:
                return 'Expansión'
            return 'DLC'

        resultados = []
        for dlc_id in dlc_appids:
            try:
                url_dlc = f"https://store.steampowered.com/api/appdetails?appids={dlc_id}&cc=es"
                r = requests.get(url_dlc, timeout=5).json()
                time.sleep(0.5)
                if r and str(dlc_id) in r and r[str(dlc_id)].get('success'):
                    d = r[str(dlc_id)]['data']
                    po = d.get('price_overview', {})
                    if d.get('is_free', False) or not po:
                        precio = 0.0
                    else:
                        precio = po.get('final', 0) / 100
                    fecha = d.get('release_date', {}).get('date', '')
                    nombre_dlc = d.get('name', 'Desconocido')
                    resultados.append({
                        'nombre': nombre_dlc,
                        'fecha_salida': fecha,
                        'precio_eur': precio,
                        'tipo': _infer_tipo_dlc(nombre_dlc),
                    })
            except Exception:
                pass
        return resultados
    except Exception:
        return []

@st.cache_data(ttl=600, show_spinner=False)
def load_news_data(appid):
    url_news = f"https://api.steampowered.com/ISteamNews/GetNewsForApp/v0002/?appid={appid}&count=2000&format=json"
    try:
        noticias = requests.get(url_news).json().get('appnews', {}).get('newsitems', [])
        df_noticias = pd.DataFrame(noticias)
        if not df_noticias.empty: df_noticias['fecha_dt'] = pd.to_datetime(df_noticias['date'], unit='s')
        return df_noticias
    except: return pd.DataFrame()

def _fetch_player_badges(steamid, steam_api_key):
    """Obtiene player_level del endpoint GetBadges."""
    try:
        url = f"https://api.steampowered.com/IPlayerService/GetBadges/v1/?key={steam_api_key}&steamid={steamid}"
        res = requests.get(url, timeout=10).json()
        return res.get('response', {}).get('player_level', 0)
    except Exception:
        return 0

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_user_profile(steamid):
    steam_api_key = get_api_key()
    if not steam_api_key:
        raise ValueError("STEAM_API_KEY no detectado (Asegúrate de configurar los Secrets en Streamlit Cloud o tener el archivo .env)")
    try:
        url_sum = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={steam_api_key}&steamids={steamid}"
        perfil = requests.get(url_sum).json().get('response', {}).get('players', [])
        
        url_games = f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={steam_api_key}&steamid={steamid}&include_appinfo=1&format=json"
        juegos = requests.get(url_games).json().get('response', {}).get('games', [])
    except Exception as e:
        raise RuntimeError(f"Error conectando a Steam API: {e}")

    if not perfil: raise ValueError("El perfil devuelto está vacío")
    p = perfil[0]
    p['loccountrycode'] = p.get('loccountrycode') or ''
    p['timecreated'] = p.get('timecreated') or 0
    p['player_level'] = _fetch_player_badges(steamid, steam_api_key)
    perfil[0] = p
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


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_player_achievements(steamid, appid):
    """
    Obtiene logros del jugador para un juego y sus rarezas globales.
    Retorna lista de dicts: name, description, unlocktime, rarity (%), achieved.
    """
    steam_api_key = get_api_key()
    if not steam_api_key:
        return []
    try:
        url_ach = f"https://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v1/?key={steam_api_key}&steamid={steamid}&appid={appid}&l=spanish"
        res_ach = requests.get(url_ach, timeout=10).json()
        player_ach = res_ach.get('playerstats', {}).get('achievements', [])
        if not player_ach:
            return []

        url_global = f"https://api.steampowered.com/ISteamUserStats/GetGlobalAchievementPercentagesForApp/v0002/?gameid={appid}"
        res_global = requests.get(url_global, timeout=10).json()
        global_pct = {}
        for a in res_global.get('achievementpercentages', {}).get('achievements', []):
            global_pct[a.get('name', '')] = float(a.get('percent', 50))

        resultados = []
        for i, a in enumerate(player_ach):
            apiname = a.get('apiname', '')
            achieved = a.get('achieved', 0) == 1
            rarity = global_pct.get(apiname, 50.0)
            unlocktime = a.get('unlocktime', 0) if achieved else None
            resultados.append({
                'name': a.get('name', f'Logro {i+1}'),
                'description': a.get('description', ''),
                'unlocktime': unlocktime,
                'rarity': rarity,
                'achieved': achieved,
                'orden': i + 1,
            })
        return resultados
    except Exception:
        return []