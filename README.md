# Steam Analytics Dashboard

Dashboard interactivo de análisis del ecosistema Steam: tendencias de mercado, noticias por juego y perfil de jugador con análisis de logros y rareza.

**Aplicación en vivo:** [steam-dashboard-app-icai.streamlit.app](https://steam-dashboard-app-icai.streamlit.app/)

---

## Resumen Ejecutivo

El **Steam Analytics Dashboard** es una herramienta de visualización que permite a usuarios y analistas explorar el mercado de videojuegos en Steam desde tres perspectivas:

1. **Tendencias** — Top de jugadores concurrentes, evolución histórica, análisis de precios y DLCs.
2. **Noticias** — Radar de actualizaciones y parches oficiales por título.
3. **Perfil de Jugador** — Análisis de biblioteca, preferencias por género y análisis detallado de logros por título (cronología, rareza, mérito).

Los datos se obtienen en tiempo real desde las APIs oficiales de Steam y CheapShark. La evolución histórica de jugadores se alimenta de un CSV generado por un workflow de GitHub Actions que se ejecuta cada 10 minutos.

---

## Capturas de Pantalla

<!-- Placeholder: añadir capturas de pantalla de las tres pestañas -->
| Tendencias | Noticias | Perfil de Jugador |
|------------|----------|-------------------|
| *[Screenshot Tendencias]* | *[Screenshot Noticias]* | *[Screenshot Perfil]* |

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
proof/
├── App_streamlit/
│   ├── app_steam.py          # Aplicación principal
│   ├── data_api.py           # Llamadas a APIs (Steam, CheapShark)
│   ├── tab_tendencias.py     # Pestaña Tendencias
│   ├── tab_noticias.py       # Pestaña Noticias
│   ├── tab_jugador.py        # Pestaña Perfil de Jugador
│   ├── requirements.txt
│   └── .streamlit/
├── historico_steam_streamlit/
│   ├── recolector.py         # Script de recolección Top 100
│   └── historial_top100.csv  # Datos históricos (generado por workflow)
├── .github/workflows/
│   └── recolector.yml        # Ejecución cada 10 min
├── DICCIONARIO_TECNICO.md    # Memoria técnica (traducción código → negocio)
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
