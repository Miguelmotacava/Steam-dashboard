# Histórico Steam Streamlit

Carpeta que contiene el **recolector** de datos del Top 100 de Steam y el CSV de historial generado automáticamente.

---

## Contenido

| Archivo | Descripción |
|---------|-------------|
| `recolector.py` | Script que consulta la API `GetGamesByConcurrentPlayers` y añade registros al CSV. |
| `historial_top100.csv` | Datos históricos acumulados. Generado y actualizado por el workflow de GitHub Actions. |

---

## Formato del CSV

El archivo `historial_top100.csv` tiene las siguientes columnas:

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `Fecha` | datetime | Momento del registro (timestamp de la ejecución). |
| `appid` | int | Identificador del juego en Steam. |
| `jugadores_historicos` | int | Número de jugadores concurrentes en ese instante. |

Cada ejecución del recolector añade hasta 100 filas (una por juego del Top 100). El CSV crece con el tiempo y permite construir gráficos de evolución y animaciones de carrera en la pestaña **Tendencias**.

---

## Ejecución Automática (GitHub Actions)

El workflow `.github/workflows/recolector.yml` ejecuta el recolector cada 10 minutos (en los minutos 7, 17, 27, 37, 47 y 57 de cada hora) para evitar coincidir con el minuto :00 en horas punta.

**Requisitos:**
- El repositorio debe tener el secret `STEAM_API_KEY` configurado en GitHub (Settings → Secrets and variables → Actions).
- El workflow solo corre en la rama por defecto (`main`).

**Limitación:** Si el repositorio no tiene actividad durante 60 días, GitHub desactiva los workflows programados. Para reactivar: **Actions** → *Recolector Steam Top 100* → *Run workflow*.

---

## Ejecución Local

Para ejecutar el recolector manualmente (por ejemplo, para pruebas):

```bash
# Desde la raíz del proyecto
export STEAM_API_KEY="tu_api_key"
python historico_steam_streamlit/recolector.py
```

En Windows (PowerShell):

```powershell
$env:STEAM_API_KEY = "tu_api_key"
python historico_steam_streamlit/recolector.py
```

**Dependencias:** `requests`, `pandas` (incluidas en `App_streamlit/requirements.txt` o instalables con `pip install requests pandas`).

---

## Uso en el Dashboard

El dashboard (`tab_tendencias.py`) lee el CSV y lo cruza con los metadatos de los juegos del Top actual (`df_super`) para:

- Mostrar líneas de evolución de jugadores concurrentes en el tiempo.
- Mostrar áreas apiladas por género.
- Generar animaciones de carrera (juegos y géneros) con ranking dinámico por frame.

Si el CSV no existe o está vacío, la sección "Evolución Histórica de Jugadores" no se muestra.
