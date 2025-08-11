# 🎵 ML Workshop - Análisis de Letras de Canciones

## 🚀 Setup Rápido para Servidor

```bash
# 1. Clonar y setup
git clone https://github.com/BlackMonkcr/ml-workshop.git
cd ml-workshop
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Configurar credenciales Spotify
# Editar spotify_enrichment_optimized.py con tus CLIENT_ID y CLIENT_SECRET

# 3. Procesamiento completo (UN COMANDO)
./process_complete.sh

# 4. Para MongoDB
mongoimport --db music_analysis --collection songs --file songs_server_ready_*.json
```

## 📁 Archivos Principales

- **`process_complete.sh`** - Script completo automatizado
- **`spotify_enrichment_optimized.py`** - Procesamiento principal
- **`SERVER_GUIDE.md`** - Guía completa de comandos
- **`PRODUCTION_READY.md`** - Documentación ejecutiva

## 🎯 Funcionalidades

- ✅ Filtrado de canciones en español
- ✅ Integración con Spotify API
- ✅ Extracción de emociones con IA
- ✅ Limpieza automática de datos
- ✅ Exportación para múltiples BD
- ✅ Dashboard de análisis

## 📊 Resultado Final

Dataset limpio con:
- Letras de canciones en español
- Emociones extraídas (neutral, joy, fear, etc.)
- Metadata de Spotify (popularity, energy, etc.)
- Listo para MongoDB, PostgreSQL, etc.

---
**Creado por**: BlackMonk  
**Fecha**: Agosto 2025
