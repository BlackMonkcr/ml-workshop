#!/bin/bash
# run_server_json.sh
# Script para ejecutar el procesamiento en servidor y generar JSONs

echo "🖥️ PROCESAMIENTO SERVIDOR → ARCHIVOS JSON"
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

if [ ! -f "complete_spotify_processing_server_json.py" ]; then
    echo "❌ Error: No se encuentra el archivo complete_spotify_processing_server_json.py"
    exit 1
fi

# Mostrar información del sistema
echo "🔧 Información del sistema:"
echo "   CPUs disponibles: $(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 'unknown')"
echo "   Python: $(python3 --version)"

# Mostrar configuración actual
echo ""
echo "⚙️ Configuración del procesamiento:"
echo "   Dataset: $SAMPLE_SIZE canciones"
echo "   Spotify API: $USE_SPOTIFY"
echo "   Workers: $MAX_WORKERS"
echo "   Batch size: $BATCH_SIZE"
echo "   Salida: Archivos JSON"

# Confirmar ejecución
read -p "¿Continuar con el procesamiento? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Procesamiento cancelado"
    exit 1
fi

# Crear directorio de logs si no existe
mkdir -p logs

# Limpiar directorio JSON anterior si existe
if [ -d "json_output" ]; then
    echo "🗑️ Limpiando archivos JSON anteriores..."
    rm -rf json_output
fi

# Ejecutar procesamiento con logging
echo "🚀 Iniciando procesamiento..."
echo "📝 Logs guardados en: server_processing.log"

python3 complete_spotify_processing_server_json.py 2>&1 | tee -a "logs/json_processing_$(date +%Y%m%d_%H%M%S).log"

exit_code=${PIPESTATUS[0]}

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "🎉 ¡PROCESAMIENTO COMPLETADO EXITOSAMENTE!"
    echo "📂 Archivos JSON generados en: json_output/"
    echo ""
    echo "🔄 PRÓXIMOS PASOS:"
    echo "1. Comprimir archivos para transferencia:"
    echo "   tar -czf spanish_songs_json.tar.gz json_output/"
    echo ""
    echo "2. Transferir al PC (ejecutar desde tu PC):"
    echo "   scp usuario@servidor:$(pwd)/spanish_songs_json.tar.gz ./"
    echo "   tar -xzf spanish_songs_json.tar.gz"
    echo ""
    echo "3. Importar a MongoDB (en tu PC):"
    echo "   python3 import_json_to_mongodb.py"
    echo ""
    
    # Crear automáticamente el archivo comprimido
    echo "📦 Comprimiendo archivos..."
    tar -czf spanish_songs_json.tar.gz json_output/
    
    if [ $? -eq 0 ]; then
        echo "✅ Archivo comprimido creado: spanish_songs_json.tar.gz"
        echo "📏 Tamaño: $(du -h spanish_songs_json.tar.gz | cut -f1)"
        
        # Mostrar comando específico para transferencia
        echo ""
        echo "🔄 Comando para copiar desde tu PC:"
        echo "scp $(whoami)@$(hostname):$(pwd)/spanish_songs_json.tar.gz ./"
    fi
    
else
    echo ""
    echo "❌ Error en el procesamiento (código: $exit_code)"
    echo "📝 Revisa los logs para más detalles"
fi

exit $exit_code
