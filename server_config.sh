#!/bin/bash
# server_config.sh
# Configuración para ejecutar el procesamiento en servidor

# Configuración del dataset
export SAMPLE_SIZE=26291  # Procesar dataset completo
export USE_SPOTIFY=true

# Configuración MongoDB (definir aquí para seguridad)
export MONGODB_URI="mongodb+srv://admin:Wwc8mSrm7WhfHbu1@notez.lwzox.mongodb.net/?retryWrites=true&w=majority&appName=Notez"
export DATABASE_NAME="ml-workshop"
export COLLECTION_NAME="songs"

# Configuración Spotify (definir aquí para seguridad)
export SPOTIFY_CLIENT_ID="cb54f009842e4529b1297a1428da7fc6"
export SPOTIFY_CLIENT_SECRET="d23ed8ab01dd4fcea1b48354189399b6"

# Configuración del servidor
export MAX_WORKERS=48
export BATCH_SIZE=1000
export MONGODB_BATCH_SIZE=500

echo "✅ Configuración del servidor establecida"
echo "📊 Dataset: $SAMPLE_SIZE canciones"
echo "🎵 Spotify: $USE_SPOTIFY"
echo "🧵 Workers: $MAX_WORKERS"
echo "📦 Batch size: $BATCH_SIZE"
