#!/usr/bin/env python3
"""
SCRIPT COMPLETO: LIMPIEZA + SPOTIFY + MONGODB
Procesa el dataset, enriquece con Spotify API y exporta a MongoDB Atlas
"""

import pickle
import json
import re
import requests
import base64
import time
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import BulkWriteError
import logging
import sys
from tqdm import tqdm
import random
import os

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('complete_processing.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuración MongoDB
MONGODB_URI = "mongodb+srv://admin:Wwc8mSrm7WhfHbu1@notez.lwzox.mongodb.net/?retryWrites=true&w=majority&appName=Notez"
DATABASE_NAME = "ml-workshop"
COLLECTION_NAME = "songs"

# Configuración Spotify
SPOTIFY_CLIENT_ID = "cb54f009842e4529b1297a1428da7fc6"
SPOTIFY_CLIENT_SECRET = "d23ed8ab01dd4fcea1b48354189399b6"

class SpotifyAPI:
    """Cliente simplificado para Spotify API"""

    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_expires_at = 0

    def get_access_token(self):
        """Obtener token de acceso"""
        if self.access_token and time.time() < self.token_expires_at:
            return self.access_token

        auth_url = "https://accounts.spotify.com/api/token"
        auth_header = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()

        headers = {"Authorization": f"Basic {auth_header}"}
        data = {"grant_type": "client_credentials"}

        try:
            response = requests.post(auth_url, headers=headers, data=data, timeout=10)
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data["access_token"]
                self.token_expires_at = time.time() + token_data["expires_in"] - 60  # 1 min buffer
                return self.access_token
        except Exception as e:
            logger.warning(f"Error obteniendo token: {e}")

        return None

    def search_track(self, artist, song_title, max_retries=3):
        """Buscar canción en Spotify"""
        token = self.get_access_token()
        if not token:
            return None

        # Limpiar nombres para búsqueda
        clean_artist = re.sub(r'[^\w\s]', '', artist)[:50]
        clean_song = re.sub(r'[^\w\s]', '', song_title)[:50]
        query = f"artist:{clean_artist} track:{clean_song}"

        search_url = "https://api.spotify.com/v1/search"
        headers = {"Authorization": f"Bearer {token}"}
        params = {"q": query, "type": "track", "limit": 1}

        for attempt in range(max_retries):
            try:
                response = requests.get(search_url, headers=headers, params=params, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    tracks = data.get("tracks", {}).get("items", [])

                    if tracks:
                        track = tracks[0]
                        return {
                            "spotify_found": True,
                            "popularity": track.get("popularity", 0),
                            "explicit_content": track.get("explicit", False),
                            "duration_ms": track.get("duration_ms", 0),
                            "release_date": track.get("album", {}).get("release_date", ""),
                            "spotify_id": track.get("id", "")
                        }

                elif response.status_code == 429:  # Rate limit
                    retry_after = int(response.headers.get('Retry-After', 1))
                    logger.info(f"Rate limit, esperando {retry_after}s...")
                    time.sleep(retry_after)
                    continue

                elif response.status_code == 401:  # Token expired
                    self.access_token = None
                    token = self.get_access_token()
                    if token:
                        headers = {"Authorization": f"Bearer {token}"}
                        continue

                break

            except Exception as e:
                logger.warning(f"Error búsqueda Spotify (intento {attempt + 1}): {e}")
                time.sleep(1)

        return {"spotify_found": False}

def clean_lyrics_text(lyrics: str) -> str:
    """Limpiar letras de contenido HTML y navegación"""
    if not lyrics or not isinstance(lyrics, str):
        return ""

    navigation_patterns = [
        r'Iniciar sesión o crear cuenta\s*\n*\s*Cuenta',
        r'<p class="[^"]*">.*?</p>',
        r'Envie dúvidas, explicações e curiosidades sobre a letra',
        r'Tire dúvidas sobre idiomas.*?da música\.',
        r'Confira nosso.*?para deixar comentários\.',
        r'Dúvidas enviadas podem receber respostas.*?plataforma\.',
        r'Opções de seleção',
        r'Todavía no recibimos esta contribución.*?enviárnosla\?',
        r'¿Los datos están equivocados\? Avísanos\.',
        r'Compuesta por:.*?Avísanos\.',
        r'<[^>]+>',  # Tags HTML
    ]

    cleaned_text = lyrics
    for pattern in navigation_patterns:
        cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE | re.DOTALL)

    # Limpiar espacios excesivos
    cleaned_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned_text)
    cleaned_text = re.sub(r'[ \t]+', ' ', cleaned_text)

    return cleaned_text.strip()

def is_valid_song(song_key: str, artist_path: str, lyrics: str) -> bool:
    """Validar si la canción debe incluirse"""
    # Limpiar letras
    cleaned_lyrics = clean_lyrics_text(lyrics)

    if len(cleaned_lyrics) < 15:
        return False

    # Verificar si es placeholder (artista = canción)
    artist_name = artist_path.strip('/').lower().replace('-', '').replace(' ', '')
    song_name = song_key.strip('/').lower().replace('-', '').replace(' ', '')

    if artist_name == song_name and len(cleaned_lyrics) < 50:
        return False

    return True

def estimate_audio_features(popularity: int) -> dict:
    """Estimar características musicales basadas en popularidad"""
    base_energy = 0.4 + (popularity / 100) * 0.4
    base_danceability = 0.3 + (popularity / 100) * 0.5

    return {
        'energy': round(base_energy + random.uniform(-0.1, 0.1), 4),
        'danceability': round(base_danceability + random.uniform(-0.1, 0.1), 4),
        'valence': round(0.3 + (popularity / 100) * 0.4 + random.uniform(-0.1, 0.1), 4),
        'speechiness': round(random.uniform(0.02, 0.15), 4),
        'acousticness': round(random.uniform(0.1, 0.8), 4),
        'instrumentalness': round(random.uniform(0.0, 0.1), 4),
        'liveness': round(random.uniform(0.05, 0.25), 4),
        'loudness': round(random.uniform(-15, -5), 4),
        'tempo': round(random.uniform(80, 140), 2),
        'key': random.randint(0, 11),
        'mode': random.randint(0, 1),
        'time_signature': random.choice([3, 4, 5]),
        'is_estimated': True
    }

def process_complete_dataset(input_file: str = "spanish_songs_server_final.pickle",
                           sample_size: int = 1000, use_spotify: bool = True):
    """Procesar dataset completo con limpieza, Spotify y exportación"""

    logger.info(f"🚀 PROCESAMIENTO COMPLETO: {input_file}")
    logger.info(f"   Muestra: {sample_size} canciones")
    logger.info(f"   Spotify API: {'Sí' if use_spotify else 'No'}")

    # Cargar datos
    try:
        with open(input_file, 'rb') as f:
            data = pickle.load(f)
        logger.info(f"✅ Dataset cargado: {len(data)} géneros")
    except Exception as e:
        logger.error(f"❌ Error cargando: {e}")
        return None

    # Inicializar Spotify API
    spotify = None
    if use_spotify:
        spotify = SpotifyAPI(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
        if spotify.get_access_token():
            logger.info("✅ Spotify API inicializada")
        else:
            logger.warning("⚠️ Spotify API no disponible, usando estimaciones")
            spotify = None

    # Recopilar todas las canciones válidas
    all_songs = []
    stats = {'total': 0, 'valid': 0, 'invalid': 0}

    logger.info("🔄 Recopilando canciones válidas...")
    for genre_name, genre_data in tqdm(data.items(), desc="Géneros"):
        if not isinstance(genre_data, dict):
            continue

        for artist_path, artist_songs in genre_data.items():
            if not isinstance(artist_songs, dict):
                continue

            artist_name = artist_path.strip('/').replace('-', ' ').title()

            for song_key, song_data in artist_songs.items():
                if not isinstance(song_data, dict):
                    continue

                stats['total'] += 1
                lyrics = song_data.get('lyrics', '')

                if is_valid_song(song_key, artist_path, lyrics):
                    song_title = song_key.strip('/').replace('-', ' ').title()

                    song_info = {
                        'artist': artist_name,
                        'song_title': song_title,
                        'genre': genre_name,
                        'lyrics': clean_lyrics_text(lyrics),
                        'composer': clean_lyrics_text(song_data.get('composer', '')),
                        'emotion': song_data.get('emotion', 'unknown')
                    }

                    all_songs.append(song_info)
                    stats['valid'] += 1
                else:
                    stats['invalid'] += 1

    logger.info(f"📊 Canciones recopiladas:")
    logger.info(f"   Total: {stats['total']:,}")
    logger.info(f"   Válidas: {stats['valid']:,}")
    logger.info(f"   Inválidas: {stats['invalid']:,}")

    # Limitar muestra si es necesario
    if sample_size and len(all_songs) > sample_size:
        all_songs = random.sample(all_songs, sample_size)
        logger.info(f"📋 Muestra limitada a: {len(all_songs):,} canciones")

    # Procesar con Spotify
    processed_documents = []
    spotify_stats = {'found': 0, 'not_found': 0, 'errors': 0}

    logger.info("🎵 Enriqueciendo con Spotify...")
    for i, song in enumerate(tqdm(all_songs, desc="Spotify API")):

        doc = song.copy()

        if spotify:
            # Buscar en Spotify
            spotify_data = spotify.search_track(song['artist'], song['song_title'])

            if spotify_data:
                doc.update(spotify_data)

                if spotify_data.get('spotify_found'):
                    spotify_stats['found'] += 1
                    # Estimar características adicionales
                    audio_features = estimate_audio_features(spotify_data.get('popularity', 50))
                    doc.update(audio_features)
                else:
                    spotify_stats['not_found'] += 1
                    # Estimar todo
                    estimated_data = {
                        'spotify_found': False,
                        'popularity': random.randint(20, 70),
                        'explicit_content': False,
                        'duration_ms': random.randint(120000, 300000)
                    }
                    doc.update(estimated_data)
                    doc.update(estimate_audio_features(estimated_data['popularity']))
            else:
                spotify_stats['errors'] += 1
        else:
            # Solo estimaciones
            estimated_data = {
                'spotify_found': False,
                'popularity': random.randint(20, 70),
                'explicit_content': False,
                'duration_ms': random.randint(120000, 300000)
            }
            doc.update(estimated_data)
            doc.update(estimate_audio_features(estimated_data['popularity']))

        # Metadata adicional
        doc.update({
            'lyrics_word_count': len(doc['lyrics'].split()),
            'processed_date': datetime.now().isoformat(),
            'source': 'complete_processing_with_spotify',
            'dataset_version': 'v3.0'
        })

        # ID único
        clean_artist = ''.join(c for c in doc['artist'].lower() if c.isalnum())[:20]
        clean_song = ''.join(c for c in doc['song_title'].lower() if c.isalnum())[:20]
        clean_genre = ''.join(c for c in doc['genre'].lower() if c.isalnum())[:15]
        doc['unique_id'] = f"{clean_artist}_{clean_song}_{clean_genre}"

        processed_documents.append(doc)

        # Rate limiting
        if spotify and i % 50 == 0:
            time.sleep(1)

    logger.info(f"📊 Estadísticas Spotify:")
    logger.info(f"   Encontradas: {spotify_stats['found']:,}")
    logger.info(f"   No encontradas: {spotify_stats['not_found']:,}")
    logger.info(f"   Errores: {spotify_stats['errors']:,}")

    return processed_documents

def export_to_mongodb(documents: list):
    """Exportar a MongoDB Atlas"""
    if not documents:
        return False

    logger.info("🗄️ EXPORTANDO A MONGODB")

    try:
        client = MongoClient(MONGODB_URI)
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]

        client.admin.command('ismaster')
        logger.info("✅ Conectado a MongoDB")

        # Limpiar colección
        collection.drop()

        # Insertar
        result = collection.insert_many(documents)

        # Crear índices
        collection.create_index([("genre", 1)])
        collection.create_index([("artist", 1)])
        collection.create_index([("popularity", 1)])
        collection.create_index([("explicit_content", 1)])

        logger.info(f"✅ Exportación exitosa: {len(result.inserted_ids):,} documentos")

        client.close()
        return True

    except Exception as e:
        logger.error(f"❌ Error MongoDB: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 PROCESAMIENTO COMPLETO CON SPOTIFY")
    logger.info("=" * 60)

    # Configuración
    SAMPLE_SIZE = int(os.getenv('SAMPLE_SIZE', '5000'))  # Muestra de 5000 para prueba
    USE_SPOTIFY = os.getenv('USE_SPOTIFY', 'true').lower() == 'true'

    logger.info(f"Configuración:")
    logger.info(f"  Muestra: {SAMPLE_SIZE}")
    logger.info(f"  Spotify: {USE_SPOTIFY}")

    # Procesar
    documents = process_complete_dataset(
        sample_size=SAMPLE_SIZE,
        use_spotify=USE_SPOTIFY
    )

    if not documents:
        logger.error("❌ No se procesaron documentos")
        sys.exit(1)

    # Exportar
    success = export_to_mongodb(documents)

    if success:
        logger.info("🎉 ¡PROCESO COMPLETADO!")
        logger.info("🌐 Dataset con Spotify disponible en MongoDB")
    else:
        logger.error("❌ Error en exportación")
        sys.exit(1)
