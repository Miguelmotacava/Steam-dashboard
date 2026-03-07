#!/usr/bin/env python3
"""
Recolector de datos del Top 100 de Steam (GetGamesByConcurrentPlayers).
Añade registros a historial_top100.csv con columnas: Fecha, appid, jugadores_historicos.
"""
import os
import pandas as pd
import requests

STEAM_API_KEY = os.environ.get("STEAM_API_KEY")
if not STEAM_API_KEY:
    raise SystemExit("STEAM_API_KEY no definido en el entorno.")

URL_API = "https://api.steampowered.com/ISteamChartsService/GetGamesByConcurrentPlayers/v1/"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(SCRIPT_DIR, "historial_top100.csv")


def main():
    res = requests.get(f"{URL_API}?key={STEAM_API_KEY}", timeout=30)
    res.raise_for_status()
    ranks = res.json().get("response", {}).get("ranks", [])[:100]

    if not ranks:
        raise SystemExit("No se obtuvieron datos de la API.")

    fecha = pd.Timestamp.now()
    df_nuevo = pd.DataFrame([
        {
            "Fecha": fecha,
            "appid": r["appid"],
            "jugadores_historicos": r["concurrent_in_game"],
        }
        for r in ranks
    ])

    if os.path.exists(CSV_PATH):
        df_existente = pd.read_csv(CSV_PATH)
        df_existente["Fecha"] = pd.to_datetime(df_existente["Fecha"])
        df_completo = pd.concat([df_existente, df_nuevo], ignore_index=True)
    else:
        df_completo = df_nuevo

    df_completo.to_csv(CSV_PATH, index=False)
    print(f"Registros añadidos: {len(df_nuevo)}. Total en CSV: {len(df_completo)}")


if __name__ == "__main__":
    main()
