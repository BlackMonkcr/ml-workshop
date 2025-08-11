#!/bin/bash
# server_config.sh
# Configuración para ejecutar el procesamiento en servidor (MODO JSON)

# Configuración del dataset
export SAMPLE_SIZE=26291  # Procesar dataset completo
export USE_SPOTIFY=true

# Configuración Spotify (definir aquí para seguridad)
export SPOTIFY_CLIENT_ID="cb54f009842e4529b1297a1428da7fc6"
export SPOTIFY_CLIENT_SECRET="d23ed8ab01dd4fcea1b48354189399b6"

# Configuración del servidor
export MAX_WORKERS=48
export BATCH_SIZE=1000

echo "✅ Configuración del servidor establecida (MODO JSON)"
echo "📊 Dataset: $SAMPLE_SIZE canciones"
echo "🎵 Spotify: $USE_SPOTIFY"
echo "🧵 Workers: $MAX_WORKERS"
echo "📦 Batch size: $BATCH_SIZE"
echo "💾 Salida: Archivos JSON para transferir"
