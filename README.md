# Steam Analytics Dashboard

Dashboard interactivo de análisis del ecosistema Steam desarrollado con Streamlit y Python. La aplicación consume datos en tiempo real desde las APIs oficiales de Steam y CheapShark, y se despliega en Streamlit Cloud.

**Aplicación en vivo:** [steam-dashboard-app-icai.streamlit.app](https://steam-dashboard-app-icai.streamlit.app/)

---

## Descripción

Herramienta de visualización que permite analizar el mercado de videojuegos en Steam desde tres perspectivas: tendencias globales, noticias y actualizaciones por juego, y perfil de jugador. Los datos se obtienen directamente de las APIs públicas, sin almacenamiento intermedio salvo el historial de jugadores concurrentes, generado por un workflow automatizado.

---

## Funcionalidades

### Tendencias

Análisis del mercado en tiempo real basado en el Top de jugadores concurrentes de Steam.

- **KPIs:** jugadores concurrentes totales, número de títulos mostrados, precio medio y juegos gratuitos.
- **Filtros:** por videojuego, plataforma (Windows, MacOS, Linux) y género.
- **Cross-filtering:** selección de un juego o género en cualquier gráfico para filtrar el resto de visualizaciones.
- **Gráficos:** barras (Top 10 por jugadores), treemap (distribución por géneros), donut (compatibilidad de sistemas operativos), scatter (precio vs Metacritic).
- **Evolución histórica:** líneas de jugadores concurrentes en el tiempo y áreas por género (requiere el CSV generado por el recolector).
- **Análisis de precio histórico:** evolución del precio base, mínimo histórico (CheapShark) y gráfico de dispersión de expansiones y cosméticos por fecha y precio.
- **Tabla resumen:** imagen, ranking, jugadores, precio, descuento, contenido adicional y géneros de cada juego.

### Noticias

Radar de noticias y actualizaciones oficiales por juego.

- **Filtros:** rango temporal (última semana, mes, todo) y tipo (parches, anuncios o todo).
- **Métricas:** impactos informativos, parches y anuncios.
- **Últimos titulares:** enlaces a las 10 noticias más recientes.
- **Widget informativo:** imagen del juego, fecha de lanzamiento y última actualización.
- **Gráficos:** publicaciones por categoría en barras horizontales y porcentaje parches vs anuncios en donut.
- **Línea temporal:** evolución mensual de publicaciones (Matplotlib).
- **Tabla resumen:** fecha, título, enlace, tipo y categoría de cada noticia.

### Perfil de Jugador

Análisis de la biblioteca Steam a partir del SteamID64 o la URL del perfil público.

- **Métricas:** total de juegos y horas jugadas.
- **Top 10:** juegos con más horas invertidas.
- **Radar:** preferencias por género (porcentaje normalizado 0–100%).
- **Treemap:** distribución del tiempo entre juegos.
- **Donut:** estado del backlog (jugados vs sin abrir).
- **Curva de Pareto:** concentración de horas por juego (porcentaje acumulado).
- **Actividad reciente:** horas jugadas en los últimos 14 días por juego (si la API lo proporciona).

---

## Tecnologías

| Componente | Tecnología |
|------------|------------|
| Frontend | Streamlit |
| Visualización | Plotly, Matplotlib |
| Datos | Pandas |
| APIs | Steam Web API, Steam Store API, CheapShark API |
| Recolección | GitHub Actions (cron cada 10 min) |
| Deploy | Streamlit Cloud |

## APIs Utilizadas

| API | Uso | Autenticación |
|-----|-----|---------------|
| [Steam Web API](https://developer.valvesoftware.com/wiki/Steam_Web_API) | Rankings, noticias, perfiles de jugador | API Key |
| [Steam Store API](https://store.steampowered.com/api/appdetails) | Precios, géneros, plataformas, DLCs | Sin key |
| [CheapShark API](https://www.cheapshark.com/api) | Precio mínimo histórico con fecha | Sin key |

---

## Instalación Local

### 1. Clonar el repositorio

```bash
git clone https://github.com/Miguelmotacava/Steam-dashboard.git
cd Steam-dashboard
```

### 2. Crear entorno virtual

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
cd App_streamlit
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Crear el archivo `.env` en `App_streamlit/` con:

```env
STEAM_API_KEY=tu_api_key_aqui
```

La API Key se obtiene en [steamcommunity.com/dev/apikey](https://steamcommunity.com/dev/apikey).

### 5. Ejecutar

```bash
cd App_streamlit
streamlit run app_steam.py
```

Desde la raíz del proyecto en Windows: `.\run_app.ps1`

---

## Estructura del Proyecto

```
proof/
├── App_streamlit/
│   ├── app_steam.py          # Aplicación principal
│   ├── data_api.py           # Llamadas a APIs (Steam, CheapShark)
│   ├── tab_tendencias.py     # Pestaña Tendencias
│   ├── tab_noticias.py       # Pestaña Noticias
│   ├── tab_jugador.py        # Pestaña Perfil de Jugador
│   ├── config.toml           # Tema Streamlit
│   ├── requirements.txt
│   └── .streamlit/
│       └── secrets.toml.example
├── historico_steam_streamlit/
│   ├── recolector.py         # Script de recolección Top 100
│   └── historial_top100.csv  # Datos históricos (generado por workflow)
├── .github/workflows/
│   └── recolector.yml        # Ejecución cada 10 min
├── run_app.ps1               # Script de ejecución (Windows)
└── README.md
```

---

## Licencia

Proyecto académico — Máster Big Data ICAI (2025-2026), asignatura de Visualización.

## Autor

**Miguel Mota Cava** — [GitHub](https://github.com/Miguelmotacava)
