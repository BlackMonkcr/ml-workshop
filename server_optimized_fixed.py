#!/usr/bin/env python3
"""
VERSIÓN CORREGIDA - Evita inicialización múltiple del modelo de emociones
Pre-carga una sola vez y usa threading en lugar de multiprocessing
"""

import pickle
import json
import os
import sys
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import logging
from tqdm import tqdm
import threading
from queue import Queue

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

# Global para modelo de emociones (compartido entre threads)
emotion_model = None
emotion_model_lock = threading.Lock()

def initialize_emotion_model():
    """Inicializar modelo de emociones UNA SOLA VEZ"""
    global emotion_model
    
    if emotion_model is not None:
        return True
    
    try:
        logger.info("🧠 Inicializando modelo de emociones (UNA VEZ)...")
        
        from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
        
        model_name = "j-hartmann/emotion-english-distilroberta-base"
        
        # Descargar/cargar modelo
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSequenceClassification.from_pretrained(model_name)
        
        # Crear pipeline
        emotion_model = pipeline(
            "text-classification",
            model=model,
            tokenizer=tokenizer,
            return_all_scores=False,
            device=-1  # CPU
        )
        
        logger.info("✅ Modelo de emociones cargado y listo")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error inicializando modelo: {e}")
        return False

def get_emotion_safe(text):
    """Extraer emoción de forma thread-safe"""
    global emotion_model
    
    if emotion_model is None:
        return "unknown"
    
    try:
        # Thread-safe access al modelo
        with emotion_model_lock:
            text = str(text)[:500]
            result = emotion_model(text)
            
            if isinstance(result, list) and len(result) > 0:
                if isinstance(result[0], list) and len(result[0]) > 0:
                    emotion_data = result[0][0]
                else:
                    emotion_data = result[0]
                
                if isinstance(emotion_data, dict):
                    return emotion_data.get('label', 'unknown').lower()
            
            return "neutral"
            
    except Exception as e:
        logger.error(f"Error extrayendo emoción: {e}")
        return "unknown"

def initialize_spotify():
    """Inicializar Spotify API"""
    try:
        import spotipy
        from spotipy.oauth2 import SpotifyClientCredentials
        
        # CONFIGURAR CON TUS CREDENCIALES
        CLIENT_ID = "TU_CLIENT_ID"  
        CLIENT_SECRET = "TU_CLIENT_SECRET"  
        
        if CLIENT_ID == "TU_CLIENT_ID":
            logger.warning("⚠️ Credenciales de Spotify no configuradas")
            return None
        
        client_credentials_manager = SpotifyClientCredentials(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET
        )
        
        spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        logger.info("✅ Spotify API inicializada")
        return spotify
        
    except Exception as e:
        logger.error(f"Error inicializando Spotify: {e}")
        return None

def estimate_audio_features(popularity):
    """Estimar características musicales"""
    import random
    
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

def process_song_thread(song_data, spotify, extract_emotions, thread_id):
    """Procesar una canción en un thread"""
    try:
        # Spotify enrichment
        if spotify:
            artist = song_data.get('artist', '')
            title = song_data.get('song_title', '')
            
            if artist and title:
                search_query = f"artist:{artist} track:{title}"
                try:
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
                        
                        song_data.update(estimate_audio_features(track.get('popularity', 50)))
                
                except Exception as e:
                    # Spotify API error - continuar sin datos de Spotify
                    song_data['spotify_found'] = False
        
        # Emotion extraction
        if extract_emotions and song_data.get('lyrics'):
            lyrics = song_data['lyrics'].strip()
            if lyrics and len(lyrics) > 10:
                emotion = get_emotion_safe(lyrics)
                song_data['emotion'] = emotion
            else:
                song_data['emotion'] = 'unknown'
        
        return song_data
        
    except Exception as e:
        logger.error(f"Error en thread {thread_id}: {e}")
        return song_data

def process_massive_dataset_threading(input_file="spanish_songs.pickle", 
                                    output_file="spanish_songs_server_processed.pickle",
                                    extract_emotions=True,
                                    max_workers=46):
    """
    Procesamiento optimizado usando ThreadPoolExecutor
    Evita el problema de múltiples inicializaciones del modelo
    """
    
    logger.info(f"🚀 Iniciando procesamiento con {max_workers} threads")
    logger.info(f"📖 Cargando: {input_file}")
    
    # Pre-cargar modelo de emociones UNA VEZ
    if extract_emotions:
        if not initialize_emotion_model():
            logger.error("❌ Error inicializando modelo de emociones")
            extract_emotions = False
    
    # Inicializar Spotify
    spotify = initialize_spotify()
    
    # Cargar dataset
    with open(input_file, 'rb') as f:
        data = pickle.load(f)
    
    # Convertir a lista plana
    all_songs = []
    song_metadata = []
    
    for genre_name, genre_data in data.items():
        for artist_path, artist_songs in genre_data.items():
            if isinstance(artist_songs, dict):
                artist_name = artist_path.strip('/').replace('-', ' ').title()
                
                for song_key, song_data in artist_songs.items():
                    if isinstance(song_data, dict):
                        song_name = song_key.strip('/').replace('-', ' ').title()
                        
                        song_for_processing = {
                            'artist': artist_name,
                            'song_title': song_name,
                            'genre': genre_name,
                            'lyrics': song_data.get('lyrics', ''),
                            **song_data
                        }
                        
                        all_songs.append(song_for_processing)
                        song_metadata.append((genre_name, artist_path, song_key))
    
    total_songs = len(all_songs)
    logger.info(f"🎵 Total canciones a procesar: {total_songs:,}")
    
    # Procesamiento con threads
    processed_songs = {}
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        logger.info(f"⚡ Iniciando {max_workers} threads paralelos")
        
        # Enviar tareas a threads
        future_to_index = {}
        for i, song in enumerate(all_songs):
            future = executor.submit(process_song_thread, song, spotify, extract_emotions, i)
            future_to_index[future] = i
        
        # Recopilar resultados con progreso
        processed_count = 0
        with tqdm(total=total_songs, desc="Procesando canciones") as pbar:
            for future in as_completed(future_to_index):
                try:
                    result = future.result(timeout=30)  # 30 seg timeout por canción
                    index = future_to_index[future]
                    processed_songs[index] = result
                    
                    processed_count += 1
                    pbar.update(1)
                    
                    # Log cada 1000 canciones
                    if processed_count % 1000 == 0:
                        elapsed = time.time() - start_time
                        rate = processed_count / elapsed
                        eta = (total_songs - processed_count) / rate / 60
                        logger.info(f"   Procesadas {processed_count:,}/{total_songs:,} - {rate:.1f}/seg - ETA: {eta:.1f}min")
                
                except Exception as e:
                    index = future_to_index[future]
                    logger.error(f"Canción {index} falló: {e}")
                    processed_songs[index] = all_songs[index]  # Mantener original
    
    # Reconstruir estructura
    logger.info("🔄 Reconstruyendo dataset...")
    reconstructed_data = {}
    
    for i, (genre_name, artist_path, song_key) in enumerate(song_metadata):
        if i in processed_songs:
            if genre_name not in reconstructed_data:
                reconstructed_data[genre_name] = {}
            if artist_path not in reconstructed_data[genre_name]:
                reconstructed_data[genre_name][artist_path] = {}
            
            reconstructed_data[genre_name][artist_path][song_key] = processed_songs[i]
    
    # Guardar
    logger.info(f"💾 Guardando: {output_file}")
    with open(output_file, 'wb') as f:
        pickle.dump(reconstructed_data, f)
    
    # Estadísticas
    total_time = time.time() - start_time
    rate = total_songs / total_time if total_time > 0 else 0
    
    logger.info("")
    logger.info("✅ PROCESAMIENTO COMPLETADO")
    logger.info(f"   🎵 Canciones: {total_songs:,}")
    logger.info(f"   ⏱️ Tiempo: {total_time/60:.1f} minutos")
    logger.info(f"   🚀 Velocidad: {rate:.1f} canciones/segundo")
    logger.info(f"   📁 Archivo: {output_file}")
    
    return True

if __name__ == "__main__":
    # Configuración
    input_file = sys.argv[1] if len(sys.argv) > 1 else "spanish_songs.pickle"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "spanish_songs_server_final.pickle"
    extract_emotions = "--no-emotions" not in sys.argv
    max_workers = int(os.getenv('MAX_WORKERS', '32'))  # Conservador inicialmente
    
    logger.info("🚀 PROCESAMIENTO OPTIMIZADO CON THREADING")
    logger.info(f"   Input: {input_file}")
    logger.info(f"   Output: {output_file}")
    logger.info(f"   Emociones: {'Sí' if extract_emotions else 'No'}")
    logger.info(f"   Max workers: {max_workers}")
    
    try:
        process_massive_dataset_threading(input_file, output_file, extract_emotions, max_workers)
        logger.info("🎉 ¡Procesamiento exitoso!")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        sys.exit(1)
