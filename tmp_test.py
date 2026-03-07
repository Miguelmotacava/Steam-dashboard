import sys
import os
sys.path.append(r"c:\Users\motam\Escritorio\Máster Big Data 2025-2026\2º Cuatrimestre\Visualización\Herramientas\Python\proof\App_streamlit")
from data_api import load_player_profile, load_steam_data, obtener_precio_historico

print("Testing player profile...")
try:
    perfil, df_juegos, df_generos = load_player_profile("76561199435323272")
    print("Profile:", perfil is not None)
    print("Games:", len(df_juegos) if df_juegos is not None else 0)
    print("Genres:", len(df_generos) if df_generos is not None else 0)
except Exception as e:
    import traceback
    traceback.print_exc()

print("\nTesting business model (price hist)...")
try:
    df_super = load_steam_data(10)
    if not df_super.empty:
        game = df_super.iloc[0]
        appid = game['appid']
        name = game['nombre']
        print(f"Testing game: {appid} - {name}")
        hist = obtener_precio_historico(appid, name)
        print("Hist:", hist)
except Exception as e:
    import traceback
    traceback.print_exc()
