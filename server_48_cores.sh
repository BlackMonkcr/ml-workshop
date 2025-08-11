#!/bin/bash
# 🚀 SCRIPT OPTIMIZADO PARA SERVIDOR CON 48 CPUs + 130GB RAM

set -e

echo "🖥️ CONFIGURACIÓN PARA SERVIDOR DE ALTO RENDIMIENTO"
echo "=================================================="
echo "Recursos detectados:"
echo "• CPUs disponibles: $(nproc)"
echo "• Memoria total: $(free -h | awk '/^Mem:/ {print $2}')"
echo "• Espacio en disco: $(df -h . | awk 'NR==2 {print $4}')"

# Configurar variables de entorno para máximo rendimiento
export BATCH_SIZE=2000              # Lotes grandes para aprovechar RAM
export MAX_WORKERS=46               # 48 CPUs - 2 para sistema
export MEMORY_GB=120                # 120GB de 130GB disponibles  
export SPOTIFY_RATE_LIMIT=500       # Rate limit alto para paralelización
export OMP_NUM_THREADS=48           # OpenMP para transformers
export MKL_NUM_THREADS=48           # Intel MKL para NumPy
export NUMBA_NUM_THREADS=48         # Numba para cálculos numéricos

# Configurar Python para alto rendimiento
export PYTHONHASHSEED=0
export PYTHONIOENCODING=utf-8
export PYTHONUNBUFFERED=1

echo ""
echo "⚙️ CONFIGURACIÓN APLICADA:"
echo "• Batch size: $BATCH_SIZE canciones por lote"
echo "• Workers paralelos: $MAX_WORKERS"
echo "• Límite memoria: ${MEMORY_GB}GB"
echo "• Rate limit Spotify: $SPOTIFY_RATE_LIMIT req/min"

# Verificar Python y dependencias
echo ""
echo "🔧 Verificando entorno..."
python3 --version
pip --version

# Crear entorno si no existe
if [ ! -d "venv" ]; then
    echo "📦 Creando entorno virtual optimizado..."
    python3 -m venv venv --clear
fi

echo "🔌 Activando entorno virtual..."
source venv/bin/activate

echo "📚 Instalando dependencias optimizadas..."
pip install --upgrade pip setuptools wheel

# Instalar con optimizaciones para CPU
pip install torch --index-url https://download.pytorch.org/whl/cpu  # CPU-only para mejor rendimiento
pip install transformers accelerate optimum[onnxruntime]  # Optimizaciones para CPU
pip install pandas numpy scipy scikit-learn
pip install spotipy requests beautifulsoup4 lxml
pip install tqdm psutil memory-profiler

echo ""
echo "🎵 PROCESAMIENTO MASIVO OPTIMIZADO"
echo "=================================="

# Verificar archivo de entrada
if [ ! -f "spanish_songs.pickle" ]; then
    echo "❌ No se encontró spanish_songs.pickle"
    echo "   Ejecuta primero el filtrado de canciones"
    exit 1
fi

echo "📊 Analizando dataset..."
python3 -c "
import pickle
with open('spanish_songs.pickle', 'rb') as f:
    data = pickle.load(f)

total = 0
for genre_data in data.values():
    for artist_songs in genre_data.values():
        if isinstance(artist_songs, dict):
            total += len([s for s in artist_songs.values() if isinstance(s, dict)])

print(f'🎵 Total canciones a procesar: {total:,}')
print(f'⏱️ Tiempo estimado con 46 workers: {total/(46*10):.1f} minutos')
print(f'💾 Memoria estimada necesaria: {total*0.5/1000:.1f}MB por worker')
"

echo ""
echo "🚀 Iniciando procesamiento paralelo masivo..."
echo "   (Logs detallados en: server_processing.log)"

# Ejecutar procesamiento optimizado
time python3 server_optimized.py spanish_songs.pickle spanish_songs_server_final.pickle

# Verificar resultado
if [ -f "spanish_songs_server_final.pickle" ]; then
    echo ""
    echo "✅ PROCESAMIENTO COMPLETADO EXITOSAMENTE"
    echo "========================================"
    
    # Estadísticas finales
    python3 -c "
import pickle
import os
from datetime import datetime

with open('spanish_songs_server_final.pickle', 'rb') as f:
    data = pickle.load(f)

total = 0
with_emotions = 0
with_spotify = 0

for genre_data in data.values():
    for artist_songs in genre_data.values():
        if isinstance(artist_songs, dict):
            for song in artist_songs.values():
                if isinstance(song, dict):
                    total += 1
                    if song.get('emotion', 'unknown') != 'unknown':
                        with_emotions += 1
                    if song.get('spotify_found', False):
                        with_spotify += 1

size_mb = os.path.getsize('spanish_songs_server_final.pickle') / (1024*1024)

print(f'📊 ESTADÍSTICAS FINALES:')
print(f'  🎵 Total canciones: {total:,}')
print(f'  🧠 Con emociones: {with_emotions:,} ({with_emotions/total*100:.1f}%)')
print(f'  🎯 Encontradas en Spotify: {with_spotify:,} ({with_spotify/total*100:.1f}%)')
print(f'  📁 Tamaño archivo: {size_mb:.1f}MB')
print(f'  📅 Procesado: {datetime.now().strftime(\"%Y-%m-%d %H:%M:%S\")}')
print(f'')
print(f'🗄️ LISTO PARA BASE DE DATOS:')
print(f'  MongoDB: python3 prepare_for_database.py')
print(f'  Dashboard: streamlit run dashboard_enhanced.py')
"

    echo ""
    echo "🎯 PRÓXIMOS PASOS:"
    echo "• Preparar para BD: python3 prepare_for_database.py"
    echo "• Ver dashboard: streamlit run dashboard_enhanced.py"
    echo "• Backup: cp spanish_songs_server_final.pickle backup/"
    
else
    echo "❌ Error en el procesamiento"
    echo "   Revisar logs: tail -f server_processing.log"
    exit 1
fi

echo ""
echo "🎉 ¡APROVECHAMIENTO MÁXIMO DE TUS 48 CPUs COMPLETADO!"
