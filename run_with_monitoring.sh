#!/bin/bash
# run_with_monitoring.sh
# Script para ejecutar el procesamiento con monitoreo automático

echo "🖥️ PROCESAMIENTO CON MONITOREO AUTOMÁTICO"
echo "========================================="

# Cargar configuración
source ./server_config.sh

# Verificar entorno virtual
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️ Activando entorno virtual..."
    source venv/bin/activate
fi

# Crear directorio de logs
mkdir -p logs

echo "🚀 Iniciando procesamiento principal..."

# Ejecutar procesamiento en background
python3 complete_spotify_processing_server.py > "logs/processing_$(date +%Y%m%d_%H%M%S).log" 2>&1 &
MAIN_PID=$!

echo "📊 PID del proceso principal: $MAIN_PID"

# Esperar un momento para que inicie
sleep 5

echo "🔍 Iniciando monitor..."

# Ejecutar monitor en foreground
python3 simple_monitor.py 20

# Verificar si el proceso principal sigue corriendo
if ps -p $MAIN_PID > /dev/null; then
    echo "⏰ Esperando que termine el procesamiento principal..."
    wait $MAIN_PID
    exit_code=$?
else
    echo "❌ El proceso principal ya terminó"
    exit_code=1
fi

if [ $exit_code -eq 0 ]; then
    echo "🎉 ¡PROCESAMIENTO COMPLETADO!"
else
    echo "❌ Error en procesamiento (código: $exit_code)"
fi

exit $exit_code
