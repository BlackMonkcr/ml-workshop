#!/bin/bash
# run_server_processing.sh
# Script para ejecutar el procesamiento completo en servidor

echo "🖥️ INICIANDO PROCESAMIENTO EN SERVIDOR"
echo "========================================"

# Cargar configuración
source ./server_config.sh

# Verificar que el entorno virtual esté activo
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️ Activando entorno virtual..."
    source venv/bin/activate
fi

# Verificar archivos necesarios
if [ ! -f "spanish_songs_server_final.pickle" ]; then
    echo "❌ Error: No se encuentra el archivo spanish_songs_server_final.pickle"
    exit 1
fi

if [ ! -f "complete_spotify_processing_server.py" ]; then
    echo "❌ Error: No se encuentra el archivo complete_spotify_processing_server.py"
    exit 1
fi

# Mostrar información del sistema
echo "🔧 Información del sistema:"
echo "   CPUs disponibles: $(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 'unknown')"
echo "   Memoria RAM: $(free -h 2>/dev/null | awk '/^Mem:/ {print $2}' || echo 'unknown')"
echo "   Python: $(python3 --version)"

# Mostrar configuración actual
echo ""
echo "⚙️ Configuración del procesamiento:"
echo "   Dataset: $SAMPLE_SIZE canciones"
echo "   Spotify API: $USE_SPOTIFY"
echo "   Workers: $MAX_WORKERS"
echo "   Batch size: $BATCH_SIZE"
echo "   MongoDB batch: $MONGODB_BATCH_SIZE"

# Confirmar ejecución
read -p "¿Continuar con el procesamiento? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Procesamiento cancelado"
    exit 1
fi

# Crear directorio de logs si no existe
mkdir -p logs

# Ejecutar procesamiento con logging
echo "🚀 Iniciando procesamiento..."
echo "📝 Logs guardados en: server_processing.log"

python3 complete_spotify_processing_server.py 2>&1 | tee -a "logs/server_run_$(date +%Y%m%d_%H%M%S).log"

exit_code=${PIPESTATUS[0]}

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "🎉 ¡PROCESAMIENTO COMPLETADO EXITOSAMENTE!"
    echo "🌐 Los datos están disponibles en MongoDB Atlas"
    echo "📊 Base de datos: $DATABASE_NAME"
    echo "📊 Colección: $COLLECTION_NAME"
else
    echo ""
    echo "❌ Error en el procesamiento (código: $exit_code)"
    echo "📝 Revisa los logs para más detalles"
fi

exit $exit_code
