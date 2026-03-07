import sys
import os
import streamlit as st
from dotenv import dotenv_values

sys.path.append(r"c:\Users\motam\Escritorio\Máster Big Data 2025-2026\2º Cuatrimestre\Visualización\Herramientas\Python\proof\App_streamlit")
from data_api import get_api_key

print("st.secrets:", end=" ")
try:
    print(st.secrets)
except Exception as e:
    print("Error:", e)
    
print("os.getenv('STEAM_API_KEY'):", repr(os.getenv('STEAM_API_KEY')))

rutas_env = [
    ".env",
    os.path.join(r"c:\Users\motam\Escritorio\Máster Big Data 2025-2026\2º Cuatrimestre\Visualización\Herramientas\Python\proof\App_streamlit", '.env'),
    os.path.join(r"c:\Users\motam\Escritorio\Máster Big Data 2025-2026\2º Cuatrimestre\Visualización\Herramientas\Python\proof\App_streamlit", '..', '.env')
]

for ruta in rutas_env:
    print(f"Path {ruta} exists? {os.path.exists(ruta)}")
    if os.path.exists(ruta):
        try:
            val = dotenv_values(ruta)
            print("dotenv_values returns:", val.get('STEAM_API_KEY'))
        except Exception as e:
            print("Exception:", e)

res = get_api_key("STEAM_API_KEY")
print("get_api_key RESULT:", repr(res))
