# Steam Analytics Dashboard

Dashboard interactivo de análisis del ecosistema Steam: tendencias de mercado, noticias por juego y perfil de jugador con análisis de logros y rareza.

**Aplicación en vivo:** [steam-dashboard-app-icai.streamlit.app](https://steam-dashboard-app-icai.streamlit.app/)

---

## Resumen Ejecutivo

El **Steam Analytics Dashboard** es una herramienta de visualización que permite a usuarios y analistas explorar el mercado de videojuegos en Steam desde tres perspectivas:

1. **Tendencias** — Top de jugadores concurrentes, evolución histórica, animaciones de carrera, análisis de precios y DLCs.
2. **Noticias** — Radar de actualizaciones y parches oficiales por título.
3. **Perfil de Jugador** — Análisis de biblioteca, preferencias por género, análisis detallado de logros por título y tabla completa de la biblioteca.

Los datos se obtienen en tiempo real desde las APIs oficiales de Steam y CheapShark. La evolución histórica de jugadores se alimenta de un CSV generado por un workflow de GitHub Actions que se ejecuta cada 10 minutos.

---

## Capturas de Pantalla

<!-- Placeholder: añadir capturas de pantalla de las tres pestañas -->
| Tendencias | Noticias | Perfil de Jugador |
|------------|----------|-------------------|
| *[Screenshot Tendencias]* | *[Screenshot Noticias]* | *[Screenshot Perfil]* |

---

## Funcionalidades por Pestaña

### 📈 Tendencias

- **KPIs:** jugadores concurrentes totales, títulos mostrados, precio medio, juegos gratuitos.
- **Filtros:** por videojuego, plataforma (Windows, MacOS, Linux) y género.
- **Cross-filtering:** selección en un gráfico filtra el resto.
- **Gráficos:** barras Top 10, treemap por géneros, donut de compatibilidad, scatter precio vs Metacritic.
- **Evolución histórica:** líneas de jugadores en el tiempo, áreas por género, animaciones de carrera (juegos y géneros) con ranking dinámico.
- **Análisis de precio:** evolución real, mínimo histórico (CheapShark), dispersión de DLCs por fecha y precio.
- **Tabla resumen:** imagen, ranking, jugadores, precio, descuento, DLCs, géneros.

### 📰 Noticias

- **Filtros:** rango temporal (semana, mes, todo) y tipo (parches, anuncios, todo).
- **Métricas:** impactos informativos, parches, anuncios.
- **Últimos titulares:** enlaces a las 10 noticias más recientes.
- **Gráficos:** barras por categoría, donut parches vs anuncios.
- **Línea temporal:** evolución mensual de publicaciones (Matplotlib).
- **Tabla resumen:** fecha, título, enlace, tipo, categoría.

### 👤 Perfil de Jugador

- **Entrada:** SteamID64 o URL de perfil público.
- **Métricas:** juegos totales, horas jugadas, valor estimado, pozo de la vergüenza (sin abrir).
- **Gráficos:** Top 10 por horas, radar por géneros, sunburst de distribución, donut backlog, treemap.
- **Análisis por título:** selector de juego → cronología de logros, dificultad media, último desafío, donut de plataformas, mapa de rareza (bubble chart).
- **Biblioteca completa:** tabla con todos los juegos, horas jugadas y logros (desbloqueados/total para los 25 con más horas).

---

## Stack Tecnológico

| Capa | Tecnología |
|------|------------|
| **Framework** | Python 3.11+ |
| **UI** | Streamlit |
| **Visualización** | Plotly, Matplotlib |
| **Datos** | Pandas |
| **APIs** | Steam Web API, Steam Store API, CheapShark API |
| **Despliegue** | Streamlit Cloud |

---

## Guía de Uso

### Cómo introducir el SteamID

1. Ve a la pestaña **Perfil de Jugador**.
2. Pega tu **SteamID64** (17 dígitos) o la **URL completa** de tu perfil público, por ejemplo:
   ```
   https://steamcommunity.com/profiles/76561198012345678
   ```
3. Pulsa **Analizar Perfil**.

### Qué insights obtienes

| Sección | Insight |
|---------|---------|
| **Métricas principales** | Juegos totales, horas jugadas, valor estimado de la biblioteca, pozo de la vergüenza (juegos sin abrir). |
| **Top 10 y radar** | Tus juegos favoritos por horas y tu ADN por géneros. |
| **Análisis por título** | Al seleccionar un juego: cronología de logros, dificultad media, último desafío, distribución estimada por plataforma (Windows/Mac/Linux) y mapa de rareza (qué logros son más difíciles de conseguir). |
| **Biblioteca completa** | Tabla con todos los juegos ordenados por horas, incluyendo logros para los 25 con más tiempo jugado. |

**Requisitos:** El perfil debe ser público y los "Detalles de los juegos" visibles. Para el análisis de logros, la visibilidad de logros debe estar activada en Steam.

---

## Instalación Local

```bash
git clone https://github.com/Miguelmotacava/Steam-dashboard.git
cd Steam-dashboard
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

cd App_streamlit
pip install -r requirements.txt
```

Crear `.env` en `App_streamlit/` con:

```env
STEAM_API_KEY=tu_api_key_aqui
```

Obtener la API Key en [steamcommunity.com/dev/apikey](https://steamcommunity.com/dev/apikey).

```bash
streamlit run app_steam.py
```

Desde la raíz en Windows: `.\run_app.ps1`

---

## Estructura del Proyecto

```
Steam-dashboard/
├── App_streamlit/
│   ├── app_steam.py          # Aplicación principal (tabs)
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
│   ├── historial_top100.csv  # Datos históricos (generado por workflow)
│   └── README.md
├── .github/workflows/
│   └── recolector.yml        # Ejecución cada 10 min
├── DICCIONARIO_TECNICO.md    # Memoria técnica (traducción código → negocio)
├── run_app.ps1               # Script de ejecución (Windows)
└── README.md
```

---

## ⚠️ Advertencia: Recolector y GitHub Actions

La **evolución histórica de jugadores** (gráficos en el tiempo y animaciones de carrera) depende del archivo `historico_steam_streamlit/historial_top100.csv`, actualizado por la GitHub Action `.github/workflows/recolector.yml` cada 10 minutos.

**Importante:** el recolector puede **dejar de actualizarse** si:

- El repositorio no tiene actividad durante **60 días** — GitHub desactiva los workflows programados.
- En horas punta, GitHub puede retrasar u omitir ejecuciones del cron.

Para reactivar: **Actions** → *Recolector Steam Top 100* → *Run workflow*.

---

## Documentación Técnica

Ver **[DICCIONARIO_TECNICO.md](DICCIONARIO_TECNICO.md)** para el mapeo de APIs, traducción de variables y lógica de gráficos (Línea de Vida, Bubble Chart, heurística de DLCs).

---

## Licencia

Proyecto académico — Máster Big Data ICAI (2025-2026), asignatura de Visualización.

**Autor:** Miguel Mota Cava — [GitHub](https://github.com/Miguelmotacava)
