#!/bin/bash
# 🚀 SCRIPT COMPLETO DE PROCESAMIENTO PARA SERVIDOR

set -e  # Parar si hay error

echo "🚀 ML WORKSHOP - PROCESAMIENTO COMPLETO"
echo "======================================"

# Verificar Python y virtualenv
if [ ! -d "venv" ]; then
    echo "📦 Creando entorno virtual..."
    python3 -m venv venv
fi

echo "🔧 Activando entorno virtual..."
source venv/bin/activate

# Instalar dependencias si no están
echo "📚 Verificando dependencias..."
pip install --quiet transformers torch pandas plotly spotipy tqdm

echo ""
echo "1️⃣ Filtrando canciones en español..."
if [ ! -f "spanish_songs.pickle" ]; then
    python3 filter_spanish_songs.py
else
    echo "   ✅ spanish_songs.pickle ya existe"
fi

echo ""
echo "2️⃣ Enriqueciendo con Spotify y extrayendo emociones..."
python3 -c "
print('🎵 Iniciando procesamiento con Spotify...')
from spotify_enrichment_optimized import process_spanish_songs_with_spotify_optimized
import sys
import os

# Configurar para procesamiento completo
sample_size = None  # Procesar TODAS las canciones
if '--sample' in sys.argv:
    sample_size = 500  # Para testing

result = process_spanish_songs_with_spotify_optimized(
    input_file='spanish_songs.pickle',
    output_file='spanish_songs_enriched_server.pickle',
    sample_size=sample_size,
    extract_emotions=True
)

if result:
    print('✅ Enriquecimiento completado')
else:
    print('❌ Error en enriquecimiento')
    sys.exit(1)
" $@

echo ""
echo "3️⃣ Limpiando letras con HTML/navegación..."
python3 -c "
print('🧹 Limpiando letras...')
import pickle
import re
import os

input_file = 'spanish_songs_enriched_server.pickle'
output_file = 'spanish_songs_cleaned_server.pickle'

if not os.path.exists(input_file):
    print(f'❌ No se encontró: {input_file}')
    exit(1)

with open(input_file, 'rb') as f:
    data = pickle.load(f)

cleaned_count = 0
total_count = 0

# Patrones para limpiar
html_pattern = re.compile(r'<[^>]+>')
nav_patterns = [
    r'Genius.*?Lyrics',
    r'You might also like',
    r'\[.*?\]',
    r'Embed.*?Cancel',
    r'How to Format Lyrics',
    r'^\s*\d+\s*$'
]

for genre_name, genre_data in data.items():
    for artist_path, artist_songs in genre_data.items():
        if isinstance(artist_songs, dict):
            for song_key, song_data in artist_songs.items():
                if isinstance(song_data, dict) and 'lyrics' in song_data:
                    total_count += 1
                    lyrics = song_data.get('lyrics', '')
                    
                    if lyrics:
                        # Limpiar HTML
                        lyrics = html_pattern.sub('', lyrics)
                        
                        # Limpiar patrones de navegación
                        for pattern in nav_patterns:
                            lyrics = re.sub(pattern, '', lyrics, flags=re.MULTILINE | re.IGNORECASE)
                        
                        # Limpiar espacios extras
                        lyrics = re.sub(r'\n\s*\n', '\n\n', lyrics)
                        lyrics = lyrics.strip()
                        
                        song_data['lyrics'] = lyrics
                        cleaned_count += 1

with open(output_file, 'wb') as f:
    pickle.dump(data, f)

print(f'✅ Letras limpiadas: {cleaned_count}/{total_count}')
print(f'📁 Archivo generado: {output_file}')
"

echo ""
echo "4️⃣ Aplicando corrección de emociones..."
python3 -c "
print('🧠 Corrigiendo extracción de emociones...')
import pickle
import os
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from tqdm import tqdm

class EmotionExtractor:
    def __init__(self):
        self.emotion_classifier = None
        self.initialized = False
        
    def initialize(self):
        if self.initialized:
            return True
        try:
            print('🔄 Inicializando modelo de emociones...')
            model_name = 'j-hartmann/emotion-english-distilroberta-base'
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSequenceClassification.from_pretrained(model_name)
            self.emotion_classifier = pipeline(
                'text-classification',
                model=model,
                tokenizer=tokenizer,
                return_all_scores=False,
                device=-1
            )
            self.initialized = True
            return True
        except Exception as e:
            print(f'❌ Error: {e}')
            return False
    
    def get_emotion(self, text):
        if not self.initialized:
            return 'unknown'
        try:
            text = str(text)[:500]
            result = self.emotion_classifier(text)
            
            if isinstance(result, list) and len(result) > 0:
                # Manejar formato [[{...}]] o [{...}]
                if isinstance(result[0], list) and len(result[0]) > 0:
                    emotion_data = result[0][0]
                else:
                    emotion_data = result[0]
                
                if isinstance(emotion_data, dict):
                    return emotion_data.get('label', 'unknown').lower()
            
            return 'neutral'
        except Exception as e:
            return 'unknown'

input_file = 'spanish_songs_cleaned_server.pickle'
output_file = 'spanish_songs_final_server.pickle'

if not os.path.exists(input_file):
    print(f'❌ No se encontró: {input_file}')
    exit(1)

with open(input_file, 'rb') as f:
    data = pickle.load(f)

extractor = EmotionExtractor()
if not extractor.initialize():
    print('❌ Error inicializando emociones')
    exit(1)

processed = 0
for genre_name, genre_data in data.items():
    for artist_path, artist_songs in genre_data.items():
        if isinstance(artist_songs, dict):
            for song_key, song_data in artist_songs.items():
                if isinstance(song_data, dict) and 'lyrics' in song_data:
                    lyrics = song_data.get('lyrics', '')
                    if lyrics and lyrics.strip():
                        emotion = extractor.get_emotion(lyrics)
                        song_data['emotion'] = emotion
                    else:
                        song_data['emotion'] = 'unknown'
                    processed += 1

with open(output_file, 'wb') as f:
    pickle.dump(data, f)

print(f'✅ Emociones actualizadas: {processed} canciones')
print(f'📁 Archivo final: {output_file}')
"

echo ""
echo "5️⃣ Limpiando canciones vacías y preparando para BD..."
python3 -c "
print('🧹 Limpieza final y preparación para BD...')
import pickle
import json
import pandas as pd
import os
from datetime import datetime

input_file = 'spanish_songs_final_server.pickle'
if not os.path.exists(input_file):
    print(f'❌ No se encontró: {input_file}')
    exit(1)

with open(input_file, 'rb') as f:
    data = pickle.load(f)

songs_for_db = []
empty_songs = 0

for genre_name, genre_data in data.items():
    for artist_path, artist_songs in genre_data.items():
        if isinstance(artist_songs, dict):
            artist_name = artist_path.strip('/').replace('-', ' ').title()
            
            for song_key, song_data in artist_songs.items():
                if isinstance(song_data, dict) and 'lyrics' in song_data:
                    lyrics = song_data.get('lyrics', '').strip()
                    
                    # Solo incluir canciones con letras válidas
                    if (lyrics and 
                        lyrics not in ['N/A', 'No disponible', '', 'null'] and
                        len(lyrics) > 10):
                        
                        song_name = song_key.strip('/').replace('-', ' ').title()
                        
                        db_record = {
                            'id': len(songs_for_db) + 1,
                            'artist': artist_name,
                            'song_title': song_name,
                            'genre': genre_name,
                            'lyrics': lyrics,
                            'lyrics_word_count': len(lyrics.split()),
                            'emotion': song_data.get('emotion', 'unknown'),
                            'spotify_found': song_data.get('spotify_found', False),
                            'popularity': song_data.get('popularity'),
                            'explicit_content': song_data.get('explicit_content', False),
                            'energy': song_data.get('energy'),
                            'danceability': song_data.get('danceability'),
                            'valence': song_data.get('valence'),
                            'tempo': song_data.get('tempo'),
                            'processed_date': datetime.now().isoformat()
                        }
                        
                        songs_for_db.append(db_record)
                    else:
                        empty_songs += 1

# Generar archivos para BD
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

# JSON para MongoDB
json_file = f'songs_server_ready_{timestamp}.json'
with open(json_file, 'w', encoding='utf-8') as f:
    json.dump({
        'metadata': {
            'total_records': len(songs_for_db),
            'export_date': datetime.now().isoformat(),
            'empty_songs_removed': empty_songs
        },
        'songs': songs_for_db
    }, f, indent=2, ensure_ascii=False)

# CSV para análisis
df = pd.DataFrame(songs_for_db)
csv_file = f'songs_server_ready_{timestamp}.csv'
df.to_csv(csv_file, index=False, encoding='utf-8')

print(f'✅ Preparación completada:')
print(f'   🎵 Canciones válidas: {len(songs_for_db)}')
print(f'   🗑️ Canciones vacías eliminadas: {empty_songs}')
print(f'   📄 JSON para BD: {json_file}')
print(f'   📊 CSV para análisis: {csv_file}')
"

echo ""
echo "✅ PROCESAMIENTO COMPLETADO"
echo "=========================="
echo "📁 Archivos generados:"
ls -la songs_server_ready_* spanish_songs_*_server.pickle 2>/dev/null || true

echo ""
echo "🗄️ Archivos listos para base de datos:"
echo "   • songs_server_ready_*.json (para MongoDB)"
echo "   • songs_server_ready_*.csv (para análisis)"
echo ""
echo "🎯 Para cargar en MongoDB:"
echo "   mongoimport --db music_analysis --collection songs --file songs_server_ready_*.json"
echo ""
echo "✨ ¡Proceso completado exitosamente!"
