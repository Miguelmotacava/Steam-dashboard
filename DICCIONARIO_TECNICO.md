# Diccionario Técnico y Variables de Entorno (Steam Dashboard)

Este diccionario documenta de manera técnica cómo se obtiene, procesa y visualiza la información en la aplicación *Steam Dashboard*. Explica en detalle los orígenes de datos (APIs), las variables manejadas en el sistema (su significado) y cómo estas estructuran y componen el ecosistema visual (Gráficos) de la herramienta.

---

## 1. Orígenes de Datos (APIs Utilizadas)

El sistema utiliza tres servicios web externos principales para nutrirse de información en tiempo real y datos históricos:

### Steam API (Backend Core WebAPI)
Es la fuente principal de datos a nivel de cuentas y métricas en vivo. URL Base referenciada: `https://api.steampowered.com/`

*   **`ISteamUser/ResolveVanityURL`**: Obtiene el identificador numérico interno (`steamid`) a partir del alias público que compone la URL (URL de vanidad).
*   **`ISteamChartsService/GetGamesByConcurrentPlayers`**: Retorna el volumen actual y global de la comunidad (usuarios conectados jugando al mismo tiempo por videojuego).
*   **`ISteamNews/GetNewsForApp`**: Obtiene un vector de comunicados, agrupando parches (soporte) y anuncios (marketing) sobre un juego.
*   **`IPlayerService/GetBadges`**: Recoge el "Nivel de Steam" (player level) calculado en función de la obtención y crafteo de insignias.
*   **`ISteamUser/GetPlayerSummaries`**: Recupera los metadatos de configuración y públicos del usuario (Avatar, nombre de perfil, fecha de alta, país de residencia).
*   **`IPlayerService/GetOwnedGames`**: Lista la totalidad del inventario de títulos que la cuenta tiene comprados junto con el tiempo histórico que el usuario les ha dedicado.
*   **`ISteamUserStats/GetPlayerAchievements`**: Revisa si el usuario ha desbloqueado los logros disponibles para un juego y la fecha (timestamp) de dicho desbloqueo.
*   **`ISteamUserStats/GetGlobalAchievementPercentagesForApp`**: Identifica qué tan frecuente o complejo (rareza comparada) es un logro analizando el porcentaje de toda la comunidad que lo ha conseguido.

### Steam Storefront API (StoreData)
Da contexto comercial y catalográfico (Ficha de la tienda del videojuego). URL Base referenciada: `https://store.steampowered.com/api/appdetails`

*   **`appdetails`**: Recupera todos los datos comerciales estructurados de una aplicación por su `appid`, como: Su precio base y actual, fecha de lanzamiento, motor gráfico (compatibilidad SO), puntuación en **Metacritic**, etiquetas semánticas (Géneros), DLCs y carátula principal (`header_image`).

### CheapShark API (Ofertas e Histórico)
Complementa la visión comercial con métricas temporales de precio procedentes de trackers externos. URL Base referenciada: `https://www.cheapshark.com/api/1.0/games`

*   **`games`**: Analiza un título para extraer el **Precio Mínimo Histórico**, determinando cuándo y por cuánto fue la rebaja más fuerte en Steam, aportando contexto sobre cómo se ha depreciado el título a lo largo del tiempo.

---

## 2. Variables Maestras y Definiciones Técnicas

### Identificadores y Metadatos de Juego/Perfil
*   **`steamid` / `steamid64`**: (String/Integer). Identificador único global y numérico (17 dígitos) que asigna Steam a cualquier cuenta de usuario.
*   **`appid`**: (Integer). Identificador numérico universal y estático del producto en sí (el videojuego, aplicación de software o DLC).
*   **`personaname` / `nombre`**: (String). Etiqueta de texto; puede ser el seudónimo del jugador o el "Nombre Técnico" del título que publica la distribuidora.
*   **`avatarfull`**: (String - URL). Enlace que aloja el avatar (foto de perfil) del usuario en máxima resolución.
*   **`loccountrycode`**: (String). Código de dos letras (Ej: 'ES', 'US') indicando la geolocalización o el país configurado de manera pública por un usuario.
*   **`timecreated`**: (Integer - Timestamp de Unix). Marca temporal del momento biológico en el que se generó y validó la cuenta del jugador (se usa para derivar la **Antigüedad de la cuenta**).
*   **`player_level`**: (Integer). Cifra bruta que representa el "Nivel" calculable sobre el propio jugador.

### Métricas de Juego y Desempeño
*   **`playtime_forever`**: (Integer). Sumatorio total en minutos jugados registrados por Steam para un `appid` específico. En el dashboard frecuentemente se transforma en horas (`horas = minutos / 60`).
*   **`concurrent_in_game` / `jugadores_actuales`**: (Integer). Métrica instantánea de cuántas instancias del juego estaban abiertas a nivel mundial en el milisegundo en que se ejecutó la consulta.
*   **`unlocktime`**: (Integer - Timestamp). Momento exacto en el ciclo de vida del usuario en el que superó un desafío (logro), validado por los servidores contra trampas de Steam.
*   **`achieved`**: (Boolean / Integer). Determina de manera binaria (1 o True) que un jugador posee efectivamente un logro.
*   **`rarity` / `rareza`**: (Float). Porcentaje de jugadores del título en cuestión que han sacado el logro. Cuanto inferior, mayor rareza.

### Métricas Económicas, Soporte y Calidad
*   **`precio_eur` / `precio_inicial` / `precio_retail`**: (Float). Métrica monetaria actual o precio base sin descuentos en euros.
*   **`precio_min_historico`**: (Float). El extremo inferior del registro histórico de caídas de precio, extraído a través de *CheapShark*.
*   **`es_gratis`**: (Boolean). Indica si un juego tiene el identificativo nativo de modelo de negocio *Free-to-Play* activo.
*   **`dlc_count`**: (Integer). Volumetría de elementos extra de pago o gratuito (expansiones) derivados del juego.
*   **`windows` / `mac` / `linux`**: (Boolean). Indicativos de soporte y compatibilidad exportados de cada título (incluyendo soporte adaptado para Steam Deck bajo linux).
*   **`generos` / `genero` / `Categoria_DLC`**: (String). Taxonomía. El tipo de mecánica principal en juegos (Ej. "Acción", "RPG"). En el caso de los DLCs especifica si es Cosmético, Banda Sonora, Season Pass o Expansión basándose en palabras clave y coste relativo a modo de inferencia.
*   **`metacritic_nota`**: (Integer). Valoración estandarizada global (del 1 al 100) sobre consenso crítico de prensa profesional en Metacritic.
*   **`feed_type` / `feedlabel`**: (Integer/String). Bandera sobre noticias: Identifica si el texto de la base notificada es un "Anuncio Comunitario" (`0`) o una "Actualización de Contenido/Parche de sistema" (`1`), y qué portal ha publicado la noticia.

---

## 3. Arquitectura de Visualizaciones (Gráficas)

El Dashboard presenta la información de manera estratificada en tres pestañas temáticas (Jugador, Noticias, y Tendencias), usando bibliotecas de trazado interactivo y dinámico (*Plotly / Matplotlib*). 

### Pestaña Jugador (`tab_jugador.py`)

*   **Bar Chart -> Top 10 Juegos por Horas**:
    *   **Eje X**: `horas` (Tiempo en horas jugadas derivado de `playtime_forever`).
    *   **Eje Y**: `name` (Nombre del videojuego).
    *   *Representación*: Revela qué software de la biblioteca domina directamente el interés lúdico histórico del usuario filtrado en su top de diez favoritos.
*   **Radar Chart Polar -> Radar por Géneros**:
    *   **Radio (R)**: `afinidad_relativa` (Porcentaje precalculado, el 100% repesenta el género en el que el jugador ha invertido el pico de tiempo máximo).
    *   **Ángulo (Theta)**: `genero` (Acción, Estrategia, Indie, etc.).
    *   *Representación*: Genera una huella visual del gusto en los géneros dominantes del jugador, analizando afinidad por volumen de minutos.
*   **Sunburst Chart -> Distribución Del Tiempo De Favoritos y Resto de Catálogo**:
    *   **Jerarquía (Path)**: `categoria_anillo` ("Top 5 Favoritos" vs "Resto Del Catálogo") -> `name`.
    *   **Peso (Values)**: `horas`.
    *   *Representación*: Establece el balance respecto a si el usuario juega a gran escala a títulos diferentes o polariza casi todo su ocio global en muy contados juegos (2 a 5 máximo).
*   **Donut Chart -> Estado de la Biblioteca**:
    *   **Segmentos (Labels)**: 'Jugados' vs 'Sin Jugar (0h)'.
    *   *Representación*: Agrega una métrica informal del "Pozo de la Vergüenza/Backlog", visualizando el gap de todos los productos conseguidos y los que jamás corrieron.
*   **Treemap Jerárquico -> Distribución del Tiempo de Todos los Juegos**:
    *   **Jerarquía (Path)**: Raíz "Biblioteca" -> `name`.
    *   **Peso (Values)**: `horas` (Para juegos mayor a 1h).
    *   *Representación*: Mapa calórico con rectángulos del total de la dispersión de tiempo invertido dentro del alcance del usuario.
*   **Line Chart -> Cronología De Progresión (Hitos de Juego)**:
    *   **Eje X**: `Fecha` de logro.
    *   **Eje Y**: `Conteo Acumulado` (Línea acumulativa sumando logros uno a uno a través del tiempo).
    *   **Filtro/Color**: `Rareza` como gradiente en la marca.
    *   *Representación*: Ritmo individual al que el usuario interactúa y progresa sacando los trofeos in-game contra una escala cronométrica real de vida.
*   **Pie Chart -> Plataforma De Uso**:
    *   **Segmentos (Names)**: `Sistema` compatible.
    *   **Peso (Values)**: `Horas` (Estimación).
    *   *Representación*: Una aproximación estadística y calculada del tiempo derivado dedicado a PC, MAC o Linux partiendo del soporte.
*   **Scatter Bubble Chart -> Mapa De Rareza Y Mérito De Logros**:
    *   **Eje X**: `Fecha` (Obtención).
    *   **Eje Y**: `Rareza` (Escalar global inverso).
    *   **Tamaño/Color**: `Tamaño` calibrado según cuán extraño y exclusivo sea el reto; un color derivado de esto mismo.
    *   *Representación*: Relata visualmente a lo largo de los días qué "hitos de enorme éxito/dificultad" frente a "logros típicos de tutorial" fueron desbloqueados.

### Pestaña Noticias (`tab_noticias.py`)

*   **Bar Chart Horizontal -> Cobertura Por Medios**:
    *   **Eje X**: `cantidad` (Número de envíos informativos rastreados).
    *   **Eje Y**: `categoria` o agente de la comunicación (`feedlabel`).
    *   *Representación*: Expresa claramente los foros de comunicación, revistas o blogs adyacentes a la comunidad de un juego.
*   **Pie Chart Modificado -> Balance: Soporte vs Marketing**:
    *   **Segmentos (Names)**: Tipo ('Parches' o 'Anuncios' de acuerdo a `feed_type`).
    *   *Representación*: Muestra el equilibrio de qué prioriza comunicar la desarrolladora que se encuentra en curso; si inyectar mantenimiento y soporte estructural o publicidad pura relacional.
*   **Line Chart (Matplotlib) -> Línea Temporal Histórica de Publicaciones**:
    *   **Eje X**: `periodo` (Temporalidad mensual formateada).
    *   **Eje Y**: `cantidad` generalizada de artículos.
    *   *Representación*: Relato cronológico que subraya qué épocas concretas concentraron toda la cobertura editorial (ej. épocas de lanzamiento inicial vs relanzamientos DLCs vs abandono/valles).

### Pestaña Tendencias (`tab_tendencias.py`)

*   **Bar Chart -> Juegos más populares**:
    *   **Eje X**: `jugadores_actuales` (Instantánea viva de concurrencia).
    *   **Eje Y**: `nombre`.
    *   *Representación*: Top bruto a tiempo real en el minuto evaluado, qué retiene fundamentalmente a la mayor proporción poblacional en las redes de la plataforma.
*   **Categorical Treemap -> Distribución por Géneros**:
    *   **Categorías (Path)**: `genero` extrapolado.
    *   **Peso (Values)**: Sumatoria de `jugadores_actuales` adheridas.
    *   *Representación*: Agrupa la masa de usuarios concentrada ahora mismo en modas subyacentes mecánicas. Si explota un tipo de juego sobre el resto.
*   **Pie Chart -> Compatibilidad de Sistemas**:
    *   **Segmentos**: `SO` (Win/Mac/Linux).
    *   *Representación*: Proporción de compatibilidad dentro del conjunto superior evaluado y si influye el multi-espectro de plataformas.
*   **Scatter -> Precio vs Calidad (Metacritic)**:
    *   **Eje X**: `precio_eur`.
    *   **Eje Y**: `metacritic_nota`.
    *   **Tamaño**: Inferencia generada por `jugadores_actuales` logrando dar peso como factor.
    *   *Representación*: Mapeo del espectro rentabilidad-producto. Ubica a colosos free/poca nota frente a obras de calidad suprema en coste y nichos, creando clústers.
*   **Line Chart -> Evolución Por Número de Jugadores Concurrentes**:
    *   **Eje X**: Timestamp de guardado `Fecha`.
    *   **Eje Y**: `jugadores_historicos` agrupado histórico.
    *   *Representación*: Seguimiento a un número acotado del Top actual para trazar varianzas y picos recientes (demostrando si una moda pierde retención o alza en ciertos días).
*   **Area Chart Apilado -> Evolución Por Género En El Tiempo**:
    *   **Eje X**: Timestamp de guardado `Fecha`.
    *   **Eje Y**: `jugadores_historicos` condensado en la variable analítica superior `genero`.
    *   *Representación*: Traslada a histórico la visión base del Treemap; las cuotas de subidas o decaídas de todo un nicho lúdico a lo largo del tiempo.
*   **Animaciones Racing Bar Chart -> Carrera De Jugadores / Géneros**:
    *   Gráficas avanzadas animadas usando iteración de layout según `Hora_Frame`. Una barra de reproducción secuencial actualiza frame a frame ordenando las barras según los `jugadores_historicos` dominantes o géneros por ese punto cronológico, fomentando una lectura viva y por lapsos temporales.
*   **Hybrid (Line+Marker) -> Evolución del Precio**:
    *   **Eje X**: Eventos cronológicos especiales ("Día de Salida", "Día precio Mínimo", "Día de Hoy").
    *   **Eje Y**: Salto evaluativo por variable € (`precio_inicial`, `precio_min_historico`, `precio_eur` actual).
    *   *Representación*: Fotografía del modelo de rebajas a nivel comercial, revelando políticas de depreciación agresivas vs precio estanco en base a hitos de rebajas cruzando datos de Steam y trackers económicos baratos.
*   **Scatter Temático -> Distribución De Lanzamientos (DLCs)**:
    *   **Eje X**: Instante en el mercado `fecha_dt` de salida de los extras.
    *   **Eje Y**: `precio_eur` por adición.
    *   **Simbología/Color**: Agrupamiento derivado pre-filtrado sobre nombres categorizándolo de banda sonora hasta pase completo (`Categoria_DLC`).
    *   *Representación*: Da sentido visual al volumen de contenido de un juego. Analiza, mediante la agrupación visual de colores, si es un juego de constante emisión o micro-extras frente a uno que estira grandes expansiones masivas y el coste base subyacente de cada ciclo o periodo.
