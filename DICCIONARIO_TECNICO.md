# Diccionario Técnico — Steam Analytics Dashboard

**Memoria Técnica de Entrega** — Traducción del código a conceptos de negocio y lógica de datos.

---

## 1. Mapeo de APIs

### GetOwnedGames → Biblioteca del Jugador

| API (Steam Web API) | Concepto de Negocio | Lógica de Datos |
|---------------------|---------------------|-----------------|
| `GetOwnedGames` | **Biblioteca del jugador** | Lista de juegos poseídos con `appid`, `name`, `playtime_forever` (minutos), `playtime_2weeks` (opcional). Permite calcular horas totales, backlog (juegos con 0h) y distribución del tiempo. |
| `playtime_forever` | Tiempo total invertido | Minutos jugados desde la compra. Se divide entre 60 para mostrar horas. |
| `playtime_linux_forever` | Uso en Steam Deck / Linux | Minutos jugados en Linux. En el dashboard se traduce a la categoría "Linux / Steam Deck" en el donut de plataformas. Steam no distingue Steam Deck de Linux; se agrupan bajo la misma métrica. |

### GetPlayerAchievements + GetGlobalAchievementPercentagesForApp → Dificultad de Reto

| API | Concepto de Negocio | Lógica de Datos |
|-----|---------------------|-----------------|
| `GetPlayerAchievements` | Logros desbloqueados por el jugador | Devuelve `apiname`, `name`, `description`, `achieved` (0/1), `unlocktime` (timestamp Unix). Solo los logros con `achieved=1` tienen `unlocktime` válido. |
| `GetGlobalAchievementPercentagesForApp` | Rareza global de cada logro | Porcentaje de jugadores que han desbloqueado cada logro (0–100%). Menor % = logro más difícil. |
| **Cruze de ambos** | **Dificultad de Reto** | Se cruza por `apiname`: cada logro del jugador recibe su `rarity` global. Así se calcula la "Dificultad Media" (promedio de rareza de los logros desbloqueados) y el "Mapa de Rareza y Mérito" (burbujas donde tamaño ∝ dificultad). |

### GetGamesByConcurrentPlayers + Store API → Tendencias de Mercado

| API | Concepto de Negocio | Lógica de Datos |
|-----|---------------------|-----------------|
| `GetGamesByConcurrentPlayers` | Top de juegos por jugadores en juego | `appid`, `concurrent_in_game`. Base para el ranking y las animaciones de carrera. |
| Steam Store API (`appdetails`) | Metadatos de cada juego | Nombre, precio, géneros, plataformas (windows, mac, linux), DLCs, fecha de lanzamiento, Metacritic. |
| CheapShark API | Precio mínimo histórico | Fecha y precio del mínimo histórico para el gráfico de evolución de precios. |

### GetNewsForApp → Noticias por Juego

| API | Concepto de Negocio | Lógica de Datos |
|-----|---------------------|-----------------|
| `GetNewsForApp` | Noticias y parches oficiales | `date` (timestamp), `title`, `url`, `feedname`. Se clasifican en parches vs anuncios por heurística de `feedname`. |

---

## 2. Traducción de Variables

| Variable Técnica | Traducción a Negocio |
|------------------|----------------------|
| `playtime_linux_forever` | Uso en **Steam Deck / Linux**. Steam no expone una métrica específica para Steam Deck; se agrupa con Linux. |
| `unlocktime` | **Hito histórico**: timestamp Unix de cuándo el jugador desbloqueó el logro. Se convierte a `datetime` para el eje X de la Línea de Vida y del Bubble Chart. |
| `rarity` | **Rareza global** (%). Indica qué porcentaje de jugadores ha conseguido ese logro. Menor valor = logro más difícil = mayor mérito individual. |
| `playtime_forever` | **Horas totales** invertidas en el juego. Base para el donut de plataformas (reparto estimado Windows/Mac/Linux). |
| `windows`, `mac`, `linux` (Store API) | **Compatibilidad por plataforma**. Se usa para estimar la distribución de horas cuando no hay datos reales por SO (heurística 70/20/10). |
| `concurrent_in_game` | **Jugadores concurrentes** en un juego en un instante. Base para el ranking y las animaciones de carrera. |
| `jugadores_historicos` (CSV) | Registro histórico de jugadores concurrentes por `appid` y `Fecha`. Alimenta las líneas de evolución y las animaciones. |

---

## 3. Lógica de Gráficos — Traducción Visual

### Línea de Vida (Cronología de Progresión)

| Técnico | Negocio |
|---------|---------|
| Eje X: `Fecha` (datetime de `unlocktime`) | **Historial de actividad**: cuándo el jugador fue desbloqueando logros. |
| Eje Y: `Conteo Acumulado` (1, 2, 3, …) | **Hitos de juego**: progresión acumulada. Cada punto = un logro más desbloqueado. |
| Color: `Rareza` | Dificultad del logro en ese momento. Permite ver si los logros recientes son más o menos difíciles. |

**Traducción:** Los logros acumulados se convierten en un **historial de actividad** que muestra el ritmo y la dificultad del progreso del jugador en el título.

### Bubble Chart (Mapa de Rareza y Mérito)

| Técnico | Negocio |
|---------|---------|
| Eje X: `Fecha` | Momento en que se obtuvo el logro. |
| Eje Y: `Rareza` (%) | Dificultad global del logro. |
| Tamaño: `(100 - Rareza) + 10` | **Mérito individual**: logros más difíciles (menor %) = burbuja más grande. |
| Hover: `Nombre`, `Descripcion` | Detalle del logro sin saturar el gráfico. |

**Traducción:** La **rareza global** se traduce en **mérito individual**: cuánto destaca el jugador al conseguir logros que pocos tienen.

### Donut de Plataformas (Uso por Sistema)

| Técnico | Negocio |
|---------|---------|
| Valores: `Horas` por Windows / Mac / Linux | **Distribución estimada** de horas según compatibilidad del juego. |
| Heurística: 70% Windows, 20% Mac, 10% Linux | Reparto cuando no hay datos reales por plataforma (Steam no los expone por juego). |

**Traducción:** Muestra dónde el jugador probablemente invierte más tiempo (Windows, Mac o Linux/Steam Deck) según las horas totales y la compatibilidad del título.

### Animaciones de Carrera (Tendencias)

| Técnico | Negocio |
|---------|---------|
| `go.Figure` + frames por `Hora_Frame` | Cada instante de tiempo = un frame. |
| `yaxis_categoryarray` por frame | **Ranking dinámico**: en cada instante, el orden del eje Y refleja quién lidera (más jugadores = más arriba). |
| Barras horizontales ordenadas por `jugadores_historicos` desc | Cuando un juego supera a otro, intercambian posición visualmente. |

**Traducción:** La evolución histórica se traduce en una **carrera visual** donde juegos y géneros suben o bajan según su posición en el ranking en cada momento.

---

## 4. Heurística de DLCs — Traducción de Precio/Nombre a Categorías

| Regla | Categoría de Negocio | Lógica |
|-------|----------------------|--------|
| `soundtrack` / `ost` / `banda sonora` en nombre | 🎵 Banda Sonora | Contenido musical. |
| `season pass` / `pase` en nombre | 🎟️ Pase de Temporada | Acceso a contenido futuro. |
| `precio >= 15 €` | 🗺️ Expansión Mayor | Contenido sustancial por precio alto. |
| `precio < 5 €` o `pack` / `skin` en nombre | 👗 Cosmético / Menor | Contenido menor o cosmético. |
| Resto | 🧩 DLC Estándar | Contenido adicional típico. |

**Traducción:** El **precio** y el **nombre** del DLC se usan para clasificar el contenido en categorías de negocio (Expansión vs. Cosmético vs. Banda Sonora, etc.) sin datos estructurados de Steam.

---

## 5. Tabla Biblioteca Completa (Perfil de Jugador)

| Columna | Origen | Traducción |
|---------|--------|------------|
| `#` | Posición por `playtime_forever` desc | Ranking del jugador por dedicación. |
| `Nombre` | `name` (GetOwnedGames) | Nombre del juego. |
| `Horas` | `playtime_forever` / 60 | Tiempo total jugado. |
| `Logros` | `fetch_player_achievements` (top 25) | Desbloqueados/Total. "—" para el resto (límite de API). |

---

## 6. Resumen de Flujos de Datos

```
GetOwnedGames ──► Biblioteca (juegos, horas)
       │
       └──► Selector "Análisis Detallado por Título" ──► appid
       │                                                      │
       └──► Tabla Biblioteca Completa ◄──────────────────────┘
                    │
GetPlayerAchievements ◄── appid (top 25)
       │
       └──► GetGlobalAchievementPercentagesForApp
                    │
                    ▼
              df_logros (Nombre, Fecha, Rareza, Descripcion)
                    │
                    ├──► Línea de Vida (Fecha × Conteo Acumulado)
                    ├──► Donut Plataformas (heurística Windows/Mac/Linux)
                    └──► Bubble Chart (Fecha × Rareza, tamaño = mérito)

GetGamesByConcurrentPlayers + historial_top100.csv
       │
       └──► Animaciones de carrera (juegos, géneros)
```

---

*Documento generado para la entrega final del proyecto — Máster Big Data ICAI (2025-2026).*
