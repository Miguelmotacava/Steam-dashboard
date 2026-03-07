# Steam Analytics Dashboard

Dashboard interactivo de análisis del ecosistema Steam desarrollado con **Streamlit** y **Python**, desplegado en Streamlit Cloud.

**App en vivo:** [steam-dashboard-app-icai.streamlit.app](https://steam-dashboard-app-icai.streamlit.app/)

---

## Descripción

Herramienta de visualización en tiempo real que extrae y analiza datos directamente desde las APIs oficiales de Steam y CheapShark para ofrecer insights sobre el mercado de videojuegos.

## Funcionalidades

### Tendencias (Pestaña 1)
- Top N juegos por jugadores concurrentes (configurable 10-100)
- KPIs: jugadores totales, precio medio, juegos gratuitos
- Gráficos interactivos: barras (Top 10), treemap (géneros), donut (SO), scatter (precio vs Metacritic)
- Filtros por videojuego, plataforma y género
- Modelo de Negocio: precio mínimo histórico (vía CheapShark), descuentos activos, contenido adicional

### Buscador Global (Pestaña 2)
- Búsqueda entre todos los títulos del catálogo de Steam (~200.000+)
- Datos en tiempo real: jugadores actuales, precio, descuentos, contenido adicional
- Gráfico de evolución de precio con mínimo histórico

### Noticias (Pestaña 3)
- Noticias oficiales por juego con filtros temporales (día/semana/mes/todo)
- Clasificación por tipo: parches vs anuncios
- Titulares destacados y visualización de frecuencia temporal

### Perfil de Jugador (Pestaña 4)
- Análisis de biblioteca personal por SteamID64
- Top 10 juegos más jugados
- Diagrama radar de preferencias por género

---

## Tecnologías

| Componente | Tecnología |
|------------|-----------|
| Frontend | Streamlit |
| Visualización | Plotly, Matplotlib |
| Datos | Pandas |
| APIs | Steam Web API, Steam Store API, CheapShark API |
| Deploy | Streamlit Cloud |

## APIs Utilizadas

| API | Uso | Autenticación |
|-----|-----|---------------|
| [Steam Web API](https://developer.valvesoftware.com/wiki/Steam_Web_API) | Rankings, noticias, perfiles de jugador | API Key |
| [Steam Store API](https://store.steampowered.com/api/appdetails) | Precios, géneros, plataformas, contenido adicional | Sin key |
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
pip install -r requirements.txt
```

### 4. Configurar variables de entorno
Crear archivo `.env` en la raíz del proyecto:
```env
STEAM_API_KEY=tu_api_key_aqui
```
Puedes obtener tu API Key en [steamcommunity.com/dev/apikey](https://steamcommunity.com/dev/apikey)

### 5. Ejecutar
```bash
streamlit run app_steam.py
```

---

## Estructura del Proyecto

```
Steam-dashboard/
├── app_steam.py          # Aplicación principal (desplegada)
├── requirements.txt      # Dependencias Python
├── .env                  # Variables de entorno (no incluido en repo)
├── .gitignore
├── README.md
├── App_streamlit/        # Versión modular (referencia)
│   ├── app_steam.py
│   ├── data_api.py
│   ├── tab_tendencias.py
│   ├── tab_noticias.py
│   ├── tab_jugador.py
│   └── config.toml
└── Graphs_dashboard/     # Notebooks de exploración
    ├── graphs.ipynb
    └── proof.ipynb
```

---

## Licencia

Proyecto académico — Master Big Data ICAI (2025-2026), asignatura de Visualización.

## Autor

**Miguel Mota Cava** — [GitHub](https://github.com/Miguelmotacava)
