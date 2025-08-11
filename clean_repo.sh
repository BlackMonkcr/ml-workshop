#!/bin/bash
# 🧹 SCRIPT DE LIMPIEZA PARA REPOSITORIO DE PRODUCCIÓN

set -e

echo "🧹 LIMPIANDO REPOSITORIO PARA GITHUB"
echo "====================================="

# Crear backup antes de limpiar
echo "💾 Creando backup..."
mkdir -p backup_$(date +%Y%m%d_%H%M%S)
cp *.pickle backup_*/  2>/dev/null || true
cp *.csv backup_*/     2>/dev/null || true
cp *.json backup_*/    2>/dev/null || true

echo "🗑️  Eliminando archivos temporales y de desarrollo..."

# Eliminar archivos pickle de desarrollo/testing
rm -f spanish_songs_enriched_demo.pickle
rm -f spanish_songs_enriched_final.pickle
rm -f spanish_songs_enriched_optimized.pickle
rm -f spanish_songs_enriched_cleaned.pickle
rm -f spanish_songs_emotions_fixed.pickle
rm -f spanish_songs_clean_final.pickle
rm -f artists_by_genre.pickle
rm -f lyrics_by_genre_parallel.pickle

# Eliminar archivos JSON duplicados de desarrollo
rm -f spanish_songs_enriched_demo.json
rm -f spanish_songs_enriched_final.json
rm -f spanish_songs_enriched_optimized.json
rm -f spanish_songs_enriched_cleaned.json

# Eliminar archivos CSV temporales con timestamps
rm -f spanish_songs_dataset_*.csv
rm -f spanish_songs_summary_*.csv
rm -f artists_analysis_*.csv
rm -f emotions_analysis_*.csv

# Eliminar archivos JSON de análisis temporal
rm -f spanish_songs_dataset_*.json

# Eliminar archivos SQL e importación temporal
rm -f songs_database_inserts_*.sql
rm -f songs_for_database_*.csv
rm -f songs_for_database_*.json

# Eliminar scripts de desarrollo/testing
rm -f demo_spotify.py
rm -f spotify_basic.py
rm -f spotify_diagnostic.py
rm -f spotify_enrichment_real.py
rm -f spotify_enrichment_simple.py
rm -f test_emotion_models.py
rm -f analyze_dataset.py
rm -f dataset_analyzer.py
rm -f final_analysis.py
rm -f fix_emotions.py
rm -f export_to_csv.py
rm -f export_advanced.py

# Eliminar dashboards de desarrollo
rm -f dashboard_enriched.py
rm -f dashboard_lyrics.py
rm -f app.py
rm -f app_parallel.py

# Eliminar archivos de ejemplo/respuesta
rm -f spotify_response_sample.json

# Eliminar documentación redundante
rm -f README_SPOTIFY.md
rm -f SPOTIFY_ENRICHMENT_SUMMARY.md

# Limpiar cache y __pycache__
rm -rf __pycache__/
rm -rf .cache/
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

echo "✅ Archivos eliminados"
echo ""
echo "📁 ARCHIVOS ESENCIALES MANTENIDOS:"
echo "=================================="

# Listar archivos que se mantienen
echo ""
echo "🔧 Scripts de procesamiento:"
ls -la *.py | grep -E "(filter_spanish|spotify_enrichment_optimized|clean_lyrics|prepare_for_database)" || true

echo ""
echo "📋 Scripts de automatización:"
ls -la *.sh || true

echo ""
echo "📚 Documentación:"
ls -la *.md || true

echo ""
echo "⚙️  Configuración:"
ls -la requirements.txt .gitignore || true

echo ""
echo "🗂️  Datos base (si existen):"
ls -la *.pickle *.txt 2>/dev/null | grep -E "(spanish_songs\.pickle|genre|requirements)" || echo "  (Ninguno - se generarán en el servidor)"

echo ""
echo "🎯 REPOSITORIO LISTO PARA GITHUB"
echo "================================"
echo ""
echo "Archivos esenciales para el servidor:"
echo "• filter_spanish_songs.py - Filtrar canciones español"
echo "• spotify_enrichment_optimized.py - Enriquecimiento principal"
echo "• clean_lyrics.py - Limpieza de letras"
echo "• prepare_for_database.py - Preparación para BD"
echo "• process_complete.sh - Script completo automatizado"
echo "• dashboard_enhanced.py - Dashboard de análisis"
echo "• requirements.txt - Dependencias"
echo "• SERVER_GUIDE.md - Guía de comandos"
echo "• PRODUCTION_READY.md - Documentación ejecutiva"
echo ""
echo "🚀 Para subir a GitHub:"
echo "git add ."
echo "git commit -m 'Clean repository for production deployment'"
echo "git push origin main"
echo ""
echo "✨ ¡Repositorio optimizado para clonar en servidor!"
