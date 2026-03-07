# Histórico Steam Streamlit

Carpeta que contiene el **recolector** de datos del Top 100 de Steam y el CSV generado.

- **recolector.py**: Script que consulta la API GetGamesByConcurrentPlayers cada 10 minutos (vía GitHub Actions).
- **historial_top100.csv**: Datos históricos (Fecha, appid, jugadores_historicos). Generado automáticamente por el workflow.
