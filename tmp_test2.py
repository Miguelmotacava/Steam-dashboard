import sys
import traceback
sys.path.append(r"c:\Users\motam\Escritorio\Máster Big Data 2025-2026\2º Cuatrimestre\Visualización\Herramientas\Python\proof\App_streamlit")
from data_api import load_player_profile, obtener_precio_historico

with open("debug_log.txt", "w", encoding="utf-8") as f:
    f.write("--- PLAYER PROFILE TEST ---\n")
    try:
        perfil, df_juegos, df_generos = load_player_profile("76561199435323272")
        f.write(f"Profile: {perfil['personaname']}\n")
        f.write(f"Games: {len(df_juegos)}\n")
        f.write(f"Genres: {len(df_generos)}\n")
    except Exception as e:
        f.write("ERROR in Player Profile:\n")
        f.write(traceback.format_exc() + "\n")

    f.write("\n--- CHEAPSHARK TEST ---\n")
    try:
        hist = obtener_precio_historico(252490, "Rust")
        f.write(f"Hist for Rust: {hist}\n")
    except Exception as e:
        f.write("ERROR in CheapShark:\n")
        f.write(traceback.format_exc() + "\n")
