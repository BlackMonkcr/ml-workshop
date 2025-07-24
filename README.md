# ML Workshop - Multi-Genre Latin Music Lyrics Scraper

Este proyecto es un web scraper avanzado que extrae letras de canciones de múltiples géneros musicales latinos del sitio web letras.com para análisis de machine learning.

## Descripción

El programa realiza las siguientes tareas:
- **Multi-género**: Extrae letras de 95+ géneros musicales latinos diferentes
- **Normalización inteligente**: Convierte nombres de géneros a URLs válidas automáticamente
- **Extracción masiva**: Obtiene artistas populares y sus canciones más tocadas por género
- **Almacenamiento estructurado**: Organiza datos por género, artista y canción
- **Análisis integrado**: Incluye herramientas para explorar y analizar el dataset

## Características principales

### 🎸 Múltiples géneros musicales
- Reggaeton, Salsa, Bachata, Cumbia, Rock, Pop, Hip-Hop/Rap
- MPB, Sertanejo, Forró, Tango, Bolero, Vallenato
- Y muchos más géneros latinos (95+ en total)

### 🔧 Funcionalidades técnicas
- **Web Scraping inteligente**: BeautifulSoup + requests con manejo de errores
- **Géneros pre-normalizados**: URLs válidas directamente en `genres.txt`
- **Almacenamiento eficiente**: Datos en pickle y exportación a JSON
- **Recuperación de sesión**: Continúa desde donde se interrumpió
- **Rate limiting**: Pausas entre requests para ser respetuoso
- **Estructura de datos rica**: Letras + compositor + género por canción

### 📊 Herramientas de análisis
- Estadísticas por género y artista
- Búsqueda por género o artista específico
- Exportación a JSON para análisis externos
- Exploración de muestras de letras

## Géneros soportados

El sistema procesa automáticamente estos géneros musicales latinos:

```
Reggaeton, Salsa, Bachata, Cumbia, Vallenato, Merengue, Bolero,
Ranchera, Mariachi, Tango, MPB, Sertanejo, Forró, Axé, Pagode,
Samba, Bossa Nova, Rock, Pop, Hip-Hop/Rap, Trap, R&B, Soul,
Alternative/Indie, Punk Rock, Heavy Metal, Jazz, Blues, Folk,
Flamenco, Trova, Corridos, Regional, Romantic, y muchos más...
```

## Requisitos del sistema

- Python 3.7 o superior
- Conexión a internet estable
- ~2GB de espacio libre (para dataset completo)
- Tiempo estimado: 8-12 horas para dataset completo

## Instalación y configuración

### 1. Clonar o descargar el proyecto

```bash
git clone <repository-url>
cd ml-workshop
```

### 2. Crear un entorno virtual

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En macOS/Linux:
source venv/bin/activate

# En Windows:
# venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

## Uso

### Ejecutar el scraper multi-género

```bash
python app.py
```

El programa:
1. Cargará automáticamente los géneros desde `genres.txt`
2. Para cada género, buscará artistas populares
3. Extraerá letras de las canciones más tocadas
4. Guardará el progreso organizadamente por género
5. Mostrará estadísticas en tiempo real

### Analizar el dataset extraído

```bash
python analyze_dataset.py
```

El analizador permite:
- Ver estadísticas completas del dataset
- Buscar por género específico
- Buscar artistas particulares
- Explorar muestras de letras
- Exportar datos a JSON

### Archivos generados

- `genres.txt`: Lista de géneros musicales a procesar
- `artists_by_genre.pickle`: Artistas organizados por género
- `lyrics_by_genre.pickle`: Dataset completo de letras por género
- `dataset.json`: Exportación en formato JSON (opcional)

### Configuración personalizada

Puedes ajustar los límites en `app.py`:
```python
MAX_ARTISTS_PER_GENRE = 50  # Artistas por género
MAX_SONGS_PER_ARTIST = 10   # Canciones por artista
```

### Interrumpir y reanudar

El programa puede ser interrumpido con `Ctrl+C` y reanudado ejecutando `python app.py` nuevamente. Continuará desde el último género procesado.

## Estructura de datos

El archivo `lyrics_by_genre.pickle` contiene:

```python
{
    'Reggaeton': {
        '/bad-bunny/': {
            '/bad-bunny/cancion-1/': {
                'lyrics': 'letra completa...',
                'composer': 'info del compositor',
                'genre': 'Reggaeton'
            }
        }
    },
    'Salsa': {
        # estructura similar...
    }
}
```

### Estructura de archivos

```
ml-workshop/
├── app.py                      # Scraper principal (secuencial)
├── app_parallel.py             # Scraper paralelo (3-4x más rápido)
├── analyze_dataset.py          # Herramienta de análisis
├── genres.txt                  # Géneros normalizados para URLs
├── genre_display_names.txt     # Mapeo a nombres amigables
├── requirements.txt            # Dependencias Python
├── README.md                   # Esta documentación
│
├── choose_scraper.py           # Recomendador automático
├── benchmark_performance.py    # Comparación de rendimiento
│
├── test_complete.py            # Prueba pipeline completo
├── test_fix.py                 # Prueba extracción de canciones
├── test_lyrics.py              # Prueba extracción de letras
├── debug_scraper.py            # Debug páginas de artistas
├── debug_lyrics.py             # Debug páginas de letras
│
├── artists_by_genre.pickle     # Artistas por género (generado)
├── lyrics_by_genre.pickle      # Dataset secuencial (generado)
├── lyrics_by_genre_parallel.pickle # Dataset paralelo (generado)
└── dataset.json               # Exportación JSON (opcional)
```

### Personalización de géneros

Para agregar o modificar géneros:

1. **Edita `genres.txt`**: Agrega géneros con nombres ya normalizados para URL
   ```
   nuevo-genero
   otro-genero-musical
   ```

2. **Opcionalmente edita `genre_display_names.txt`**: Para nombres amigables
   ```
   nuevo-genero:Nuevo Género
   otro-genero-musical:Otro Género Musical
   ```

3. **Ejecuta el scraper**: Los nuevos géneros se procesarán automáticamente

## Consideraciones éticas y legales

- Este scraper incluye delays entre requests para no sobrecargar el servidor
- Solo extrae contenido públicamente disponible
- Los datos extraídos deben usarse conforme a los términos de servicio del sitio web
- Considere las implicaciones de derechos de autor para uso comercial

## Solución de problemas

### Error de conexión
```bash
# Verificar conexión a internet
ping letras.com
```

### Error de dependencias
```bash
# Reinstalar dependencias
pip install -r requirements.txt --force-reinstall
```

### Memoria insuficiente
El programa procesa solo 200 artistas por defecto. Para procesar menos:
```python
# Modificar línea 132 en app.py
for artist in artists[:50]:  # Cambiar 200 por 50
```

## Análisis de datos avanzado

### Casos de uso para ML

Los datos extraídos son ideales para:

#### 🔍 Análisis de texto
- **Análisis de sentimientos**: Estudiar emociones por género musical
- **Procesamiento de lenguaje natural**: Entrenamiento de modelos en español
- **Análisis semántico**: Identificar temas recurrentes por género

#### 🎵 Clasificación musical
- **Clasificación automática de géneros**: Entrenar modelos para identificar géneros por letra
- **Detección de autor**: Identificar el estilo de escritura de diferentes artistas
- **Evolución temporal**: Analizar cambios en la música latina a través del tiempo

#### 📊 Análisis cultural
- **Diversidad regional**: Comparar vocabulario y temas entre países
- **Influencias culturales**: Identificar elementos comunes entre géneros
- **Tendencias sociales**: Analizar temas sociales reflejados en la música

### Herramientas recomendadas

Para análisis posterior, considera usar:
- **Pandas**: Manipulación de datasets
- **NLTK/spaCy**: Procesamiento de texto en español
- **Scikit-learn**: Machine learning tradicional
- **Transformers**: Modelos de lenguaje modernos
- **Matplotlib/Seaborn**: Visualización de datos

## Consideraciones éticas y legales

⚠️ **Importante**: Este proyecto es para fines educativos y de investigación académica.

### Uso responsable
- ✅ Análisis académico y educativo
- ✅ Investigación sobre música latina
- ✅ Desarrollo de herramientas de NLP
- ❌ Uso comercial sin permisos
- ❌ Redistribución masiva de contenido
- ❌ Violación de derechos de autor

### Aspectos técnicos
- El scraper incluye delays para no sobrecargar servidores
- Solo extrae contenido públicamente disponible
- Respeta robots.txt y términos de servicio
- Implementa manejo de errores robusto

## Solución de problemas

### Error de conexión
```bash
# Verificar conectividad
ping letras.com

# Reintentar con VPN si hay bloqueos regionales
```

### Error: 'NoneType' object has no attribute 'find_all'

Este error indica que la estructura HTML del sitio web ha cambiado. El programa incluye múltiples estrategias de fallback:

1. **Nuevo layout**: Usa selectores `songList-table-row` (estructura actual)
2. **Layout antiguo**: Usa selectores `cnt-list-songs` (estructura legacy)
3. **Método de fallback**: Busca enlaces de canciones por patrón

**Solución automática**: El programa detecta y se adapta automáticamente a cambios en la estructura del sitio.

**Debug manual**: Si persisten errores, usa:
```bash
python debug_scraper.py
```

### Memoria insuficiente
```python
# Reducir límites en app.py
MAX_ARTISTS_PER_GENRE = 20
MAX_SONGS_PER_ARTIST = 5
```

### Géneros no encontrados
El sistema maneja automáticamente géneros que no existen en letras.com y continúa con los siguientes.

### Reiniciar desde género específico
```python
# Modificar la lista de géneros en genres.txt
# Eliminar géneros ya procesados para continuar desde uno específico
```

### Estructura HTML actualizada

El sitio letras.com actualizó su estructura HTML. La nueva versión del scraper es compatible con:

- ✅ **Estructura nueva** (2024+): `songList-table-row`
- ✅ **Estructura antigua** (pre-2024): `cnt-list-songs`
- ✅ **Método de fallback**: Búsqueda por patrones de URL

### Herramientas de debugging incluidas

El proyecto incluye varios scripts de debugging para diagnosticar problemas:

#### 🔧 Scripts de prueba
```bash
# Prueba completa del pipeline
python test_complete.py

# Prueba solo extracción de canciones
python test_fix.py

# Prueba solo extracción de letras
python test_lyrics.py
```

#### 🐛 Scripts de debugging detallado
```bash
# Debug páginas de artistas (lista de canciones)
python debug_scraper.py

# Debug páginas de letras individuales
python debug_lyrics.py
```

#### 📊 Qué verifican las pruebas
- ✅ **Conectividad** con letras.com
- ✅ **Extracción de canciones** por artista
- ✅ **Extracción de letras** por canción
- ✅ **Compatibilidad** con estructura HTML nueva y antigua
- ✅ **Manejo de errores** robusto
- ✅ **Rate limiting** apropiado

## Versión Paralela (Recomendada para datasets grandes)

### 🚀 Scraper Paralelo

Para datasets grandes, usa la versión paralela que es **3-4x más rápida**:

```bash
# Ejecutar versión paralela
python app_parallel.py

# Ver benchmark de rendimiento
python benchmark_performance.py
```

### ⚡ Ventajas de la paralelización

#### **Rendimiento mejorado**
- **4-6 workers** para procesar artistas simultáneamente
- **3-4 workers** para procesar canciones por artista
- **Rate limiting inteligente** para ser respetuoso con el servidor
- **Thread-safe** con locks para evitar conflictos

#### **Tiempo estimado dataset completo**
- **Secuencial**: ~13 horas
- **Paralelo**: ~3-4 horas
- **Mejora**: 70% reducción de tiempo

#### **Configuración optimizada**
```python
MAX_WORKERS_ARTISTS = 4    # Workers para artistas
MAX_WORKERS_SONGS = 3      # Workers para canciones
MAX_ARTISTS_PER_GENRE = 50 # Artistas por género
MAX_SONGS_PER_ARTIST = 10  # Canciones por artista
```

### 🎯 Cuándo usar cada versión

#### **Scraper Secuencial (`app.py`)**
- ✅ **Datasets pequeños** (< 1000 canciones)
- ✅ **Conexión lenta** o inestable
- ✅ **Debugging** y desarrollo
- ✅ **Máxima compatibilidad**

#### **Scraper Paralelo (`app_parallel.py`)**
- ✅ **Datasets grandes** (> 1000 canciones)
- ✅ **Conexión rápida** y estable
- ✅ **Producción** y extracción masiva
- ✅ **Tiempo limitado**
