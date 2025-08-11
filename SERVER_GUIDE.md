# 🚀 GUÍA DE PROCESAMIENTO EN SERVIDOR - ML WORKSHOP

## 📋 Comandos para ejecutar (en orden)

### 1. Preparación del entorno
```bash
# Clonar repositorio y setup
git clone https://github.com/BlackMonkcr/ml-workshop.git
cd ml-workshop
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Instalar dependencias adicionales para servidor
pip install transformers torch pandas plotly spotipy
```

### 2. Configurar credenciales Spotify
```bash
# Editar archivo con tus credenciales
nano spotify_enrichment_optimized.py
# Cambiar CLIENT_ID y CLIENT_SECRET
```

### 3. Procesamiento completo (todos los comandos)
```bash
# Filtrar canciones en español (desde dataset completo)
python3 filter_spanish_songs.py

# Enriquecer con Spotify y extraer emociones (TODAS las canciones)
python3 -c "
from spotify_enrichment_optimized import process_spanish_songs_with_spotify_optimized
process_spanish_songs_with_spotify_optimized(
    input_file='spanish_songs.pickle',
    output_file='spanish_songs_enriched_complete.pickle',
    sample_size=None,  # Procesar TODAS
    extract_emotions=True
)
"

# Limpiar letras con HTML/navegación
python3 clean_lyrics.py

# Corregir emociones con parser actualizado
python3 fix_emotions.py

# Limpiar canciones vacías y preparar para BD
python3 prepare_for_database.py
```

### 4. Análisis y exportación final
```bash
# Generar análisis completo
python3 final_analysis.py

# Exportar todos los formatos
python3 export_to_csv.py
python3 export_advanced.py
```

## 🗄️ RECOMENDACIONES PARA BASE DE DATOS

### Para SERVIDOR DE PRODUCCIÓN:

**1. MongoDB (NoSQL) - RECOMENDADO**
- ✅ Maneja JSON nativo
- ✅ Escalable para millones de canciones
- ✅ Flexible para cambios de schema
```bash
# Usar archivo: songs_for_database_YYYYMMDD_HHMMSS.json
mongoimport --db music_analysis --collection songs --file songs_for_database_*.json
```

**2. PostgreSQL (SQL) - ALTERNATIVA**
- ✅ JSONB para lyrics y metadata
- ✅ Índices eficientes
- ✅ Análisis estadísticos avanzados
```bash
# Usar archivo: songs_database_inserts_*.sql
psql -d music_db -f songs_database_inserts_*.sql
```

**3. ❌ NO usar CSV en producción**
- Lento para queries complejas
- No maneja well UTF-8 con lyrics
- Limitado para análisis

## ⚡ OPTIMIZACIONES PARA SERVIDOR

### Variables de entorno
```bash
export BATCH_SIZE=1000          # Procesar en lotes
export MAX_WORKERS=4            # Hilos paralelos
export SPOTIFY_RATE_LIMIT=100   # Requests por minuto
export LOG_LEVEL=INFO           # Logging detallado
```

### Comando optimizado para servidor
```bash
# Procesamiento en background con logs
nohup python3 -c "
import os
os.environ['BATCH_SIZE'] = '1000'
os.environ['MAX_WORKERS'] = '4'
from spotify_enrichment_optimized import process_spanish_songs_with_spotify_optimized
process_spanish_songs_with_spotify_optimized(
    input_file='spanish_songs.pickle',
    output_file='spanish_songs_server_processed.pickle',
    sample_size=None,
    extract_emotions=True
)
" > processing.log 2>&1 &

# Monitorear progreso
tail -f processing.log
```

## 📊 ESTRUCTURA FINAL DE ARCHIVOS

```
Archivos de entrada:
- spanish_songs.pickle (dataset filtrado español)

Archivos de procesamiento:
- spanish_songs_enriched_complete.pickle (con Spotify + emociones)
- spanish_songs_emotions_fixed.pickle (emociones corregidas)
- spanish_songs_clean_final.pickle (sin canciones vacías)

Archivos para BD:
- songs_for_database_*.json (MongoDB)
- songs_for_database_*.csv (import temporal)
- songs_database_inserts_*.sql (PostgreSQL)

Archivos de análisis:
- spanish_songs_dataset_*.csv (análisis)
- emotions_analysis_*.csv (estadísticas emociones)
- artists_analysis_*.csv (estadísticas artistas)
```

## 🎯 COMANDO ÚNICO PARA TODO EL PROCESO

```bash
#!/bin/bash
# Script completo de procesamiento

set -e  # Parar si hay error

echo "🚀 Iniciando procesamiento completo..."

# Setup
source venv/bin/activate

# Procesamiento principal
python3 filter_spanish_songs.py
python3 -c "
from spotify_enrichment_optimized import process_spanish_songs_with_spotify_optimized
process_spanish_songs_with_spotify_optimized('spanish_songs.pickle', 'spanish_songs_complete.pickle', None, True)
"
python3 clean_lyrics.py
python3 fix_emotions.py
python3 prepare_for_database.py

# Análisis y exportación
python3 final_analysis.py
python3 export_advanced.py

echo "✅ Procesamiento completado. Archivos listos para BD."
```

## 🔍 MONITOREO Y LOGS

```bash
# Ver progreso en tiempo real
watch -n 5 "ls -la *.pickle *.json *.csv | wc -l"

# Verificar memoria y CPU
htop

# Logs de errores
tail -f processing.log | grep "ERROR\|❌"
```
