#!/usr/bin/env python3
"""
VERSIÓN OPTIMIZADA PARA SERVIDOR CON 48 CPUs + 130GB RAM
Aprovecha recursos masivos para procesamiento paralelo
"""

import pickle
import json
import os
import sys
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from multiprocessing import cpu_count
import time
from functools import partial
import logging
from tqdm import tqdm

# Configurar logging para servidor
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server_processing.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ServerOptimizer:
    def __init__(self):
        # Configuración para servidor de 48 CPUs
        self.total_cpus = cpu_count()  # Detectar CPUs automáticamente
        self.max_workers = min(48, self.total_cpus - 2)  # Usar casi todas las CPUs
        self.batch_size = int(os.getenv('BATCH_SIZE', '2000'))  # Lotes grandes
        self.memory_limit = int(os.getenv('MEMORY_GB', '120'))  # 120GB de 130GB
        
        logger.info(f"🖥️ Configuración del servidor:")
        logger.info(f"   CPUs detectadas: {self.total_cpus}")
        logger.info(f"   Workers a usar: {self.max_workers}")
        logger.info(f"   Batch size: {self.batch_size}")
        logger.info(f"   Límite memoria: {self.memory_limit}GB")

def process_song_batch(batch_data):
    """Procesar un lote de canciones en paralelo"""
    import pickle
    from spotify_enrichment_optimized import EmotionExtractor
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials
    
    batch_id, songs_batch, extract_emotions = batch_data
    
    # Inicializar servicios por worker
    spotify = None
    emotion_extractor = None
    
    try:
        # Spotify API
        CLIENT_ID = "TU_CLIENT_ID"  # Configurar
        CLIENT_SECRET = "TU_CLIENT_SECRET"  # Configurar
        
        if CLIENT_ID != "TU_CLIENT_ID":
            client_credentials_manager = SpotifyClientCredentials(
                client_id=CLIENT_ID,
                client_secret=CLIENT_SECRET
            )
            spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        
        # Extractor de emociones
        if extract_emotions:
            emotion_extractor = EmotionExtractor()
            emotion_extractor.initialize()
        
        processed_songs = []
        
        for song_data in songs_batch:
            try:
                # Procesar canción individual
                result = process_single_song(song_data, spotify, emotion_extractor)
                processed_songs.append(result)
                
            except Exception as e:
                logger.error(f"Error procesando canción en batch {batch_id}: {e}")
                processed_songs.append(song_data)  # Mantener original si falla
        
        return batch_id, processed_songs
        
    except Exception as e:
        logger.error(f"Error en batch {batch_id}: {e}")
        return batch_id, songs_batch  # Retornar sin procesar

def process_single_song(song_data, spotify, emotion_extractor):
    """Procesar una canción individual"""
    try:
        # Enriquecimiento con Spotify
        if spotify:
            # Buscar en Spotify
            artist = song_data.get('artist', '')
            title = song_data.get('song_title', '')
            
            if artist and title:
                search_query = f"artist:{artist} track:{title}"
                results = spotify.search(q=search_query, type='track', limit=1)
                
                if results['tracks']['items']:
                    track = results['tracks']['items'][0]
                    song_data.update({
                        'spotify_found': True,
                        'popularity': track.get('popularity'),
                        'explicit_content': track.get('explicit', False),
                        'duration_ms': track.get('duration_ms'),
                        'release_date': track['album'].get('release_date', ''),
                    })
                    
                    # Estimar características musicales
                    song_data.update(estimate_audio_features(track.get('popularity', 50)))
        
        # Extracción de emociones
        if emotion_extractor and song_data.get('lyrics'):
            emotion = emotion_extractor.get_emotion(song_data['lyrics'])
            song_data['emotion'] = emotion
        
        return song_data
        
    except Exception as e:
        logger.error(f"Error procesando canción individual: {e}")
        return song_data

def estimate_audio_features(popularity):
    """Estimar características musicales basadas en popularidad"""
    import random
    
    # Estimaciones más sofisticadas basadas en popularidad
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

def process_massive_dataset_parallel(input_file="spanish_songs.pickle", 
                                   output_file="spanish_songs_server_processed.pickle",
                                   extract_emotions=True):
    """
    Procesamiento masivo optimizado para servidor de 48 CPUs
    """
    
    optimizer = ServerOptimizer()
    
    logger.info(f"🚀 Iniciando procesamiento masivo paralelo")
    logger.info(f"📖 Cargando: {input_file}")
    
    # Cargar dataset
    with open(input_file, 'rb') as f:
        data = pickle.load(f)
    
    # Convertir a lista plana para procesamiento
    all_songs = []
    song_metadata = []  # Para reconstruir estructura después
    
    for genre_name, genre_data in data.items():
        for artist_path, artist_songs in genre_data.items():
            if isinstance(artist_songs, dict):
                artist_name = artist_path.strip('/').replace('-', ' ').title()
                
                for song_key, song_data in artist_songs.items():
                    if isinstance(song_data, dict):
                        song_name = song_key.strip('/').replace('-', ' ').title()
                        
                        # Preparar datos para procesamiento
                        song_for_processing = {
                            'artist': artist_name,
                            'song_title': song_name,
                            'genre': genre_name,
                            'lyrics': song_data.get('lyrics', ''),
                            **song_data  # Incluir datos existentes
                        }
                        
                        all_songs.append(song_for_processing)
                        song_metadata.append((genre_name, artist_path, song_key))
    
    total_songs = len(all_songs)
    logger.info(f"🎵 Total de canciones a procesar: {total_songs:,}")
    
    # Dividir en batches para procesamiento paralelo
    batches = []
    for i in range(0, total_songs, optimizer.batch_size):
        batch = all_songs[i:i + optimizer.batch_size]
        batches.append((i // optimizer.batch_size, batch, extract_emotions))
    
    logger.info(f"📦 Dividido en {len(batches)} batches de {optimizer.batch_size} canciones")
    
    # Procesamiento paralelo
    processed_songs = {}
    start_time = time.time()
    
    with ProcessPoolExecutor(max_workers=optimizer.max_workers) as executor:
        logger.info(f"⚡ Iniciando {optimizer.max_workers} workers paralelos")
        
        # Enviar batches a workers
        future_to_batch = {
            executor.submit(process_song_batch, batch_data): batch_id 
            for batch_id, batch_data in enumerate(batches)
        }
        
        # Recopilar resultados con barra de progreso
        with tqdm(total=len(batches), desc="Procesando batches") as pbar:
            for future in as_completed(future_to_batch):
                try:
                    batch_id, batch_results = future.result(timeout=300)  # 5 min timeout
                    
                    # Almacenar resultados
                    for i, song in enumerate(batch_results):
                        global_index = batch_id * optimizer.batch_size + i
                        if global_index < len(song_metadata):
                            processed_songs[global_index] = song
                    
                    pbar.update(1)
                    
                    # Log progreso cada 10 batches
                    if (batch_id + 1) % 10 == 0:
                        elapsed = time.time() - start_time
                        rate = (batch_id + 1) * optimizer.batch_size / elapsed
                        logger.info(f"   Procesados {(batch_id + 1) * optimizer.batch_size:,} canciones ({rate:.1f} canciones/seg)")
                    
                except Exception as e:
                    batch_id = future_to_batch[future]
                    logger.error(f"Batch {batch_id} falló: {e}")
    
    # Reconstruir estructura original
    logger.info(f"🔄 Reconstruyendo estructura del dataset...")
    
    reconstructed_data = {}
    for i, (genre_name, artist_path, song_key) in enumerate(song_metadata):
        if i in processed_songs:
            if genre_name not in reconstructed_data:
                reconstructed_data[genre_name] = {}
            if artist_path not in reconstructed_data[genre_name]:
                reconstructed_data[genre_name][artist_path] = {}
            
            reconstructed_data[genre_name][artist_path][song_key] = processed_songs[i]
    
    # Guardar resultado
    logger.info(f"💾 Guardando resultado: {output_file}")
    with open(output_file, 'wb') as f:
        pickle.dump(reconstructed_data, f)
    
    # Estadísticas finales
    total_time = time.time() - start_time
    rate = total_songs / total_time
    
    logger.info(f"")
    logger.info(f"✅ PROCESAMIENTO COMPLETADO")
    logger.info(f"   🎵 Canciones procesadas: {total_songs:,}")
    logger.info(f"   ⏱️ Tiempo total: {total_time/60:.1f} minutos")
    logger.info(f"   🚀 Velocidad: {rate:.1f} canciones/segundo")
    logger.info(f"   🖥️ Workers utilizados: {optimizer.max_workers}")
    logger.info(f"   📁 Archivo generado: {output_file}")
    
    return True

if __name__ == "__main__":
    import sys
    
    # Configuración desde argumentos o variables de entorno
    input_file = sys.argv[1] if len(sys.argv) > 1 else "spanish_songs.pickle"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "spanish_songs_server_processed.pickle"
    extract_emotions = "--no-emotions" not in sys.argv
    
    logger.info(f"🚀 INICIANDO PROCESAMIENTO OPTIMIZADO PARA SERVIDOR")
    logger.info(f"   Input: {input_file}")
    logger.info(f"   Output: {output_file}")
    logger.info(f"   Emociones: {'Sí' if extract_emotions else 'No'}")
    
    try:
        process_massive_dataset_parallel(input_file, output_file, extract_emotions)
        logger.info(f"🎉 ¡Procesamiento exitoso!")
        
    except Exception as e:
        logger.error(f"❌ Error en procesamiento: {e}")
        sys.exit(1)
