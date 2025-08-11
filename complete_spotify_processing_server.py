#!/usr/bin/env python3
"""
SCRIPT OPTIMIZADO PARA SERVIDOR: LIMPIEZA + SPOTIFY + MONGODB
Versión optimizada con threading para servidor de 48 CPUs
Procesa el dataset completo con enriquecimiento Spotify y exporta a MongoDB Atlas
"""

import pickle
import json
import re
import requests
import base64
import time
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from pymongo import MongoClient
from pymongo.errors import BulkWriteError
import logging
import sys
from tqdm import tqdm
import random
import os
import queue
from collections import defaultdict
import gc

# Configuración de logging optimizada
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(threadName)s - %(message)s',
    handlers=[
        logging.FileHandler('server_processing.log', mode='w'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuración desde variables de entorno
MONGODB_URI = os.getenv('MONGODB_URI', "mongodb://localhost:27017/")
DATABASE_NAME = os.getenv('DATABASE_NAME', "ml-workshop")
COLLECTION_NAME = os.getenv('COLLECTION_NAME', "songs")

# Configuración Spotify desde variables de entorno
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

# Configuración para servidor
MAX_WORKERS = min(int(os.getenv('MAX_WORKERS', '48')), os.cpu_count())
BATCH_SIZE = int(os.getenv('BATCH_SIZE', '1000'))  # Procesar en lotes
MONGODB_BATCH_SIZE = int(os.getenv('MONGODB_BATCH_SIZE', '500'))  # Inserción en lotes más pequeños
RATE_LIMIT_DELAY = float(os.getenv('RATE_LIMIT_DELAY', '0.1'))  # Delay entre requests Spotify

class ThreadSafeSpotifyAPI:
    """Cliente Spotify thread-safe con pool de tokens"""

    def __init__(self, client_id, client_secret, pool_size=10):
        self.client_id = client_id
        self.client_secret = client_secret
        self.pool_size = pool_size
        self.token_pool = queue.Queue()
        self.lock = threading.Lock()
        self._initialize_token_pool()

    def _initialize_token_pool(self):
        """Inicializar pool de tokens"""
        logger.info(f"🔑 Inicializando pool de {self.pool_size} tokens...")
        
        for _ in range(self.pool_size):
            token_data = self._get_new_token()
            if token_data:
                self.token_pool.put(token_data)
            else:
                break
                
        logger.info(f"✅ Pool inicializado con {self.token_pool.qsize()} tokens")

    def _get_new_token(self):
        """Obtener nuevo token de acceso"""
        auth_url = "https://accounts.spotify.com/api/token"
        auth_header = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()

        headers = {"Authorization": f"Basic {auth_header}"}
        data = {"grant_type": "client_credentials"}

        try:
            response = requests.post(auth_url, headers=headers, data=data, timeout=10)
            if response.status_code == 200:
                token_data = response.json()
                return {
                    'access_token': token_data["access_token"],
                    'expires_at': time.time() + token_data["expires_in"] - 60
                }
        except Exception as e:
            logger.warning(f"Error obteniendo token: {e}")

        return None

    def get_token(self):
        """Obtener token del pool"""
        try:
            # Intentar obtener token válido
            while not self.token_pool.empty():
                token_data = self.token_pool.get_nowait()
                if time.time() < token_data['expires_at']:
                    return token_data['access_token']
            
            # Si no hay tokens válidos, crear uno nuevo
            with self.lock:
                new_token = self._get_new_token()
                if new_token:
                    return new_token['access_token']
                    
        except queue.Empty:
            pass
            
        return None

    def return_token(self, token_data):
        """Devolver token al pool (si aún es válido)"""
        if token_data and time.time() < token_data.get('expires_at', 0):
            try:
                self.token_pool.put_nowait(token_data)
            except queue.Full:
                pass

    def search_track(self, artist, song_title, max_retries=2):
        """Buscar canción en Spotify (thread-safe)"""
        token = self.get_token()
        if not token:
            return {"spotify_found": False, "error": "no_token"}

        # Limpiar nombres para búsqueda
        clean_artist = re.sub(r'[^\w\s]', '', artist)[:30]
        clean_song = re.sub(r'[^\w\s]', '', song_title)[:30]
        query = f"artist:{clean_artist} track:{clean_song}"

        search_url = "https://api.spotify.com/v1/search"
        headers = {"Authorization": f"Bearer {token}"}
        params = {"q": query, "type": "track", "limit": 1}

        for attempt in range(max_retries):
            try:
                time.sleep(RATE_LIMIT_DELAY)  # Rate limiting
                response = requests.get(search_url, headers=headers, params=params, timeout=5)

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
                    retry_after = min(int(response.headers.get('Retry-After', 1)), 10)
                    time.sleep(retry_after)
                    continue

                break

            except Exception as e:
                if attempt == max_retries - 1:
                    logger.warning(f"Error búsqueda Spotify: {e}")
                time.sleep(0.5)

        return {"spotify_found": False}

def clean_lyrics_text(lyrics: str) -> str:
    """Limpiar letras de contenido HTML y navegación (optimizado)"""
    if not lyrics or not isinstance(lyrics, str):
        return ""

    # Patrones compilados para mejor rendimiento
    navigation_patterns = [
        re.compile(r'Iniciar sesión o crear cuenta\s*\n*\s*Cuenta', re.IGNORECASE),
        re.compile(r'<p class="[^"]*">.*?</p>', re.IGNORECASE | re.DOTALL),
        re.compile(r'Envie dúvidas, explicações e curiosidades sobre a letra', re.IGNORECASE),
        re.compile(r'Tire dúvidas sobre idiomas.*?da música\.', re.IGNORECASE | re.DOTALL),
        re.compile(r'Confira nosso.*?para deixar comentários\.', re.IGNORECASE | re.DOTALL),
        re.compile(r'Dúvidas enviadas podem receber respostas.*?plataforma\.', re.IGNORECASE | re.DOTALL),
        re.compile(r'Opções de seleção', re.IGNORECASE),
        re.compile(r'Todavía no recibimos esta contribución.*?enviárnosla\?', re.IGNORECASE | re.DOTALL),
        re.compile(r'¿Los datos están equivocados\? Avísanos\.', re.IGNORECASE),
        re.compile(r'Compuesta por:.*?Avísanos\.', re.IGNORECASE | re.DOTALL),
        re.compile(r'<[^>]+>'),  # Tags HTML
    ]

    cleaned_text = lyrics
    for pattern in navigation_patterns:
        cleaned_text = pattern.sub('', cleaned_text)

    # Limpiar espacios excesivos
    cleaned_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned_text)
    cleaned_text = re.sub(r'[ \t]+', ' ', cleaned_text)

    return cleaned_text.strip()

def is_valid_song(song_key: str, artist_path: str, lyrics: str) -> bool:
    """Validar si la canción debe incluirse (optimizado)"""
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

def process_song_batch(songs_batch, spotify_api, batch_id):
    """Procesar lote de canciones con Spotify"""
    processed_songs = []
    stats = {'found': 0, 'not_found': 0, 'errors': 0}
    
    for song in songs_batch:
        try:
            doc = song.copy()
            
            if spotify_api:
                spotify_data = spotify_api.search_track(song['artist'], song['song_title'])
                
                if spotify_data:
                    doc.update(spotify_data)
                    
                    if spotify_data.get('spotify_found'):
                        stats['found'] += 1
                        audio_features = estimate_audio_features(spotify_data.get('popularity', 50))
                        doc.update(audio_features)
                    else:
                        stats['not_found'] += 1
                        estimated_data = {
                            'spotify_found': False,
                            'popularity': random.randint(20, 70),
                            'explicit_content': False,
                            'duration_ms': random.randint(120000, 300000)
                        }
                        doc.update(estimated_data)
                        doc.update(estimate_audio_features(estimated_data['popularity']))
                else:
                    stats['errors'] += 1
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
                'source': 'server_processing_optimized',
                'dataset_version': 'v4.0'
            })

            # ID único
            clean_artist = ''.join(c for c in doc['artist'].lower() if c.isalnum())[:20]
            clean_song = ''.join(c for c in doc['song_title'].lower() if c.isalnum())[:20]
            clean_genre = ''.join(c for c in doc['genre'].lower() if c.isalnum())[:15]
            doc['unique_id'] = f"{clean_artist}_{clean_song}_{clean_genre}"

            processed_songs.append(doc)
            
        except Exception as e:
            logger.error(f"Error procesando canción en lote {batch_id}: {e}")
            stats['errors'] += 1

    return processed_songs, stats

def collect_valid_songs(data, sample_size=None):
    """Recopilar todas las canciones válidas (optimizado)"""
    logger.info("🔄 Recopilando canciones válidas...")
    
    all_songs = []
    stats = {'total': 0, 'valid': 0, 'invalid': 0}

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

    return all_songs

def process_with_threading(all_songs, spotify_api, max_workers=MAX_WORKERS):
    """Procesar canciones usando threading"""
    logger.info(f"🧵 Procesando con {max_workers} threads...")
    
    # Dividir en lotes
    batches = [all_songs[i:i + BATCH_SIZE] for i in range(0, len(all_songs), BATCH_SIZE)]
    logger.info(f"📦 Dividido en {len(batches)} lotes de ~{BATCH_SIZE} canciones")

    processed_documents = []
    total_stats = {'found': 0, 'not_found': 0, 'errors': 0}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Enviar lotes a procesar
        futures = {
            executor.submit(process_song_batch, batch, spotify_api, i): i 
            for i, batch in enumerate(batches)
        }

        # Procesar resultados
        with tqdm(total=len(batches), desc="Lotes procesados") as pbar:
            for future in as_completed(futures):
                batch_id = futures[future]
                try:
                    batch_results, batch_stats = future.result()
                    processed_documents.extend(batch_results)
                    
                    # Actualizar estadísticas
                    for key in total_stats:
                        total_stats[key] += batch_stats[key]
                        
                    pbar.set_postfix({
                        'Encontradas': total_stats['found'],
                        'No encontradas': total_stats['not_found'],
                        'Errores': total_stats['errors']
                    })
                    
                except Exception as e:
                    logger.error(f"Error en lote {batch_id}: {e}")
                    total_stats['errors'] += BATCH_SIZE
                    
                pbar.update(1)
                
                # Liberación de memoria periódica
                if pbar.n % 10 == 0:
                    gc.collect()

    logger.info(f"📊 Estadísticas finales Spotify:")
    logger.info(f"   Encontradas: {total_stats['found']:,}")
    logger.info(f"   No encontradas: {total_stats['not_found']:,}")
    logger.info(f"   Errores: {total_stats['errors']:,}")

    return processed_documents

def export_to_mongodb_batched(documents):
    """Exportar a MongoDB en lotes (optimizado para servidor)"""
    if not documents:
        return False

    logger.info(f"🗄️ EXPORTANDO {len(documents):,} DOCUMENTOS A MONGODB")

    try:
        client = MongoClient(MONGODB_URI, maxPoolSize=50)
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]

        client.admin.command('ismaster')
        logger.info("✅ Conectado a MongoDB")

        # Limpiar colección
        collection.drop()
        logger.info("🗑️ Colección limpiada")

        # Insertar en lotes
        batches = [documents[i:i + MONGODB_BATCH_SIZE] for i in range(0, len(documents), MONGODB_BATCH_SIZE)]
        
        inserted_count = 0
        for i, batch in enumerate(tqdm(batches, desc="Insertando lotes")):
            try:
                result = collection.insert_many(batch, ordered=False)
                inserted_count += len(result.inserted_ids)
            except BulkWriteError as e:
                logger.warning(f"Errores en lote {i}: {len(e.details.get('writeErrors', []))}")
                inserted_count += len(batch) - len(e.details.get('writeErrors', []))

        # Crear índices
        logger.info("📇 Creando índices...")
        collection.create_index([("genre", 1)])
        collection.create_index([("artist", 1)])
        collection.create_index([("popularity", 1)])
        collection.create_index([("explicit_content", 1)])
        collection.create_index([("energy", 1)])
        collection.create_index([("danceability", 1)])
        collection.create_index([("valence", 1)])

        logger.info(f"✅ Exportación exitosa: {inserted_count:,} documentos")
        logger.info(f"📊 Base de datos: {DATABASE_NAME}")
        logger.info(f"📊 Colección: {COLLECTION_NAME}")

        client.close()
        return True

    except Exception as e:
        logger.error(f"❌ Error MongoDB: {e}")
        return False

def process_complete_dataset_optimized(input_file: str = "spanish_songs_server_final.pickle",
                                     sample_size: int = None, use_spotify: bool = True):
    """Procesar dataset completo optimizado para servidor"""

    logger.info(f"🚀 PROCESAMIENTO OPTIMIZADO PARA SERVIDOR")
    logger.info(f"   Archivo: {input_file}")
    logger.info(f"   Muestra: {sample_size if sample_size else 'COMPLETA'} canciones")
    logger.info(f"   Spotify API: {'Sí' if use_spotify else 'No'}")
    logger.info(f"   CPUs disponibles: {os.cpu_count()}")
    logger.info(f"   Threads configurados: {MAX_WORKERS}")
    logger.info("=" * 80)

    # Cargar datos
    try:
        logger.info("📂 Cargando dataset...")
        with open(input_file, 'rb') as f:
            data = pickle.load(f)
        logger.info(f"✅ Dataset cargado: {len(data)} géneros")
    except Exception as e:
        logger.error(f"❌ Error cargando: {e}")
        return None

    # Inicializar Spotify API
    spotify = None
    if use_spotify:
        if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
            logger.warning("⚠️ Credenciales Spotify no configuradas, usando solo estimaciones")
        else:
            logger.info("🎵 Inicializando Spotify API...")
            spotify = ThreadSafeSpotifyAPI(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, pool_size=10)

    # Recopilar canciones válidas
    all_songs = collect_valid_songs(data, sample_size)
    
    if not all_songs:
        logger.error("❌ No se encontraron canciones válidas")
        return None

    # Liberar memoria del dataset original
    del data
    gc.collect()
    
    logger.info(f"🚀 Iniciando procesamiento de {len(all_songs):,} canciones...")

    # Procesar con threading
    processed_documents = process_with_threading(all_songs, spotify, MAX_WORKERS)
    
    if not processed_documents:
        logger.error("❌ No se procesaron documentos")
        return None

    logger.info(f"✅ Procesamiento completado: {len(processed_documents):,} documentos")
    
    return processed_documents

if __name__ == "__main__":
    logger.info("🖥️ PROCESAMIENTO OPTIMIZADO PARA SERVIDOR")
    logger.info("=" * 80)
    
    start_time = time.time()

    # Configuración desde variables de entorno
    SAMPLE_SIZE = int(os.getenv('SAMPLE_SIZE', '0'))  # 0 = procesar todo
    USE_SPOTIFY = os.getenv('USE_SPOTIFY', 'true').lower() == 'true'

    if SAMPLE_SIZE == 0:
        SAMPLE_SIZE = None  # Procesar todo
        
    logger.info(f"⚙️ Configuración:")
    logger.info(f"  Muestra: {'COMPLETA' if SAMPLE_SIZE is None else f'{SAMPLE_SIZE:,}'}")
    logger.info(f"  Spotify: {USE_SPOTIFY}")
    logger.info(f"  CPUs: {MAX_WORKERS}")
    logger.info(f"  Lote: {BATCH_SIZE}")

    # Procesar
    documents = process_complete_dataset_optimized(
        sample_size=SAMPLE_SIZE,
        use_spotify=USE_SPOTIFY
    )

    if not documents:
        logger.error("❌ No se procesaron documentos")
        sys.exit(1)

    # Exportar a MongoDB
    success = export_to_mongodb_batched(documents)

    elapsed_time = time.time() - start_time
    
    if success:
        logger.info("🎉 ¡PROCESO COMPLETADO EXITOSAMENTE!")
        logger.info(f"⏱️ Tiempo total: {elapsed_time/60:.1f} minutos")
        logger.info(f"🌐 Dataset completo disponible en MongoDB Atlas")
        logger.info(f"📊 Total documentos: {len(documents):,}")
    else:
        logger.error("❌ Error en exportación a MongoDB")
        sys.exit(1)
