"""
Script optimizado para enriquecer canciones españolas con metadata de Spotify
Usando el endpoint /v1/tracks/{id} y extracción de emociones con Hugging Face
"""
import pickle
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import time
import pandas as pd
from typing import Dict, Optional, Any
import json
import os
from datetime import datetime

# Para extracción de emociones
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
    print("✅ Transformers disponible para extracción de emociones")
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("⚠️ Transformers no disponible. Instalar con: pip install transformers torch")

# Configurar las credenciales de Spotify
CLIENT_ID = "cb54f009842e4529b1297a1428da7fc6"
CLIENT_SECRET = "d23ed8ab01dd4fcea1b48354189399b6"

class EmotionExtractor:
    """Extractor de emociones usando pipeline de Hugging Face"""
    
    def __init__(self):
        self.emotion_classifier = None
        self.initialized = False
        
    def initialize(self):
        """Inicializar el modelo de emociones"""
        if not TRANSFORMERS_AVAILABLE:
            print("⚠️ Transformers no disponible, saltando extracción de emociones")
            return False
            
        try:
            print("🧠 Inicializando modelo de emociones (j-hartmann/emotion-english-distilroberta-base)...")
            self.emotion_classifier = pipeline("text-classification", 
                                              model="j-hartmann/emotion-english-distilroberta-base",
                                              top_k=1)
            self.initialized = True
            print("✅ Modelo de emociones inicializado")
            return True
        except Exception as e:
            print(f"❌ Error inicializando modelo de emociones: {e}")
            # Fallback a modelo básico de sentimientos
            try:
                print("🔄 Intentando modelo básico de sentimientos...")
                self.emotion_classifier = pipeline("sentiment-analysis")
                self.initialized = True
                print("✅ Modelo básico de sentimientos inicializado")
                return True
            except Exception as e2:
                print(f"❌ Error con modelo básico: {e2}")
                return False
    
    def get_emotion(self, text: str) -> str:
        """Extraer emoción del texto"""
        if not self.initialized:
            return "unknown"
            
        try:
            # Limpiar el texto y limitar longitud
            text = str(text)[:500]  # Limitar para evitar errores de memoria
            
            result = self.emotion_classifier(text)
            
            # El modelo puede devolver diferentes formatos:
            # [[{'label': 'joy', 'score': 0.9}]] o [{'label': 'joy', 'score': 0.9}]
            if isinstance(result, list) and len(result) > 0:
                # Si es una lista anidada, tomar el primer elemento
                if isinstance(result[0], list) and len(result[0]) > 0:
                    emotion_data = result[0][0]  # [[{...}]] -> {...}
                else:
                    emotion_data = result[0]     # [{...}] -> {...}
                
                if isinstance(emotion_data, dict):
                    emotion = emotion_data.get('label', 'unknown').lower()
                    # Mapear sentimientos básicos a emociones si es necesario
                    if emotion in ['positive', 'pos']:
                        emotion = 'joy'
                    elif emotion in ['negative', 'neg']:
                        emotion = 'sadness'
                    return emotion
            
            return "neutral"
        except Exception as e:
            print(f"⚠️ Error extrayendo emoción: {e}")
            return "unknown"

def get_spotify_client():
    """Crear cliente de Spotify con autenticación"""
    try:
        client_credentials_manager = SpotifyClientCredentials(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET
        )
        sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        return sp
    except Exception as e:
        print(f"Error al conectar con Spotify: {e}")
        return None

def clean_song_name(song_name: str) -> str:
    """Limpia el nombre de la canción para mejorar la búsqueda"""
    song_name = song_name.replace('/', '').replace('-', ' ').strip()
    if song_name.startswith('/') or '/' in song_name:
        song_name = song_name.split('/')[-1].replace('-', ' ')
    return song_name.title()

def clean_artist_name(artist_name: str) -> str:
    """Limpia el nombre del artista para mejorar la búsqueda"""
    artist_name = artist_name.strip('/').replace('/', '').replace('-', ' ')
    return artist_name.title()

def search_spotify_track(song_name: str, artist_name: str, market: str = 'US') -> Optional[Dict]:
    """
    Buscar una canción en Spotify usando el endpoint de búsqueda y luego obtener detalles completos
    
    Args:
        song_name (str): Nombre de la canción
        artist_name (str): Nombre del artista  
        market (str): Código del mercado/país
        
    Returns:
        dict: Información completa del track o None si no se encuentra
    """
    sp = get_spotify_client()
    if not sp:
        return None
        
    try:
        # Limpiar nombres
        clean_song = clean_song_name(song_name)
        clean_artist = clean_artist_name(artist_name)
        
        # Construir query de búsqueda
        query = f'track:"{clean_song}" artist:"{clean_artist}"'
        
        # Buscar la canción
        results = sp.search(q=query, type='track', market=market, limit=1)
        
        if not results['tracks']['items']:
            # Intentar búsqueda más flexible
            query_flexible = f"{clean_song} {clean_artist}"
            results = sp.search(q=query_flexible, type='track', market=market, limit=1)
            
            if not results['tracks']['items']:
                return None
                
        track = results['tracks']['items'][0]
        track_id = track['id']
        
        # Ahora usar el endpoint /v1/tracks/{id} para obtener información completa
        detailed_track = sp.track(track_id, market=market)
        
        # Extraer información relevante
        track_info = {
            'track_id': detailed_track['id'],
            'spotify_url': detailed_track['external_urls']['spotify'],
            'track_name': detailed_track['name'],
            'artist_name': detailed_track['artists'][0]['name'],
            'album_name': detailed_track['album']['name'],
            'release_date': detailed_track['album']['release_date'],
            'popularity': detailed_track['popularity'],
            'duration_ms': detailed_track['duration_ms'],
            'explicit': detailed_track['explicit'],
            'preview_url': detailed_track.get('preview_url'),
            'disc_number': detailed_track['disc_number'],
            'track_number': detailed_track['track_number'],
            'is_local': detailed_track['is_local'],
            'album_type': detailed_track['album']['album_type'],
            'total_tracks': detailed_track['album']['total_tracks']
        }
        
        # Agregar información de imágenes del álbum si está disponible
        if detailed_track['album'].get('images'):
            images = detailed_track['album']['images']
            track_info.update({
                'album_image_large': images[0]['url'] if len(images) > 0 else None,
                'album_image_medium': images[1]['url'] if len(images) > 1 else None, 
                'album_image_small': images[2]['url'] if len(images) > 2 else None
            })
            
        # Agregar información adicional del artista
        if len(detailed_track['artists']) > 1:
            track_info['collaborating_artists'] = [artist['name'] for artist in detailed_track['artists'][1:]]
            
        # Información de mercado
        track_info['available_markets_count'] = len(detailed_track.get('available_markets', []))
        
        return track_info
        
    except Exception as e:
        print(f"Error al buscar {song_name} por {artist_name} en mercado {market}: {e}")
        return None

def estimate_audio_features_from_popularity(popularity: int, explicit: bool, release_date: str) -> Dict:
    """
    Estimar características de audio basadas en popularidad y otros factores
    Esta es una aproximación ya que no tenemos acceso a audio-features
    """
    import random
    
    # Normalizar popularidad (0-100 -> 0-1)
    pop_normalized = popularity / 100.0
    
    # Año de lanzamiento para ajustes temporales
    try:
        year = int(release_date[:4]) if release_date else 2020
    except:
        year = 2020
        
    # Estimaciones basadas en popularidad y era
    base_energy = 0.3 + (pop_normalized * 0.4) + random.uniform(-0.1, 0.1)
    base_danceability = 0.4 + (pop_normalized * 0.3) + random.uniform(-0.1, 0.1)
    
    # Ajustes por era musical
    if year >= 2010:  # Música moderna tiende a ser más enérgica
        base_energy += 0.1
        base_danceability += 0.1
    elif year < 1990:  # Música clásica tiende a ser menos enérgica
        base_energy -= 0.1
        
    # Ajuste por contenido explícito
    if explicit:
        base_energy += 0.05
        
    # Generar estimaciones realistas
    estimated_features = {
        'energy_estimated': max(0, min(100, int(base_energy * 100))),
        'danceability_estimated': max(0, min(100, int(base_danceability * 100))),
        'positiveness_estimated': max(0, min(100, int((0.5 + pop_normalized * 0.3) * 100))),
        'speechiness_estimated': random.randint(5, 15),  # Generalmente bajo
        'liveness_estimated': random.randint(10, 30),    # Generalmente bajo para grabaciones de estudio
        'acousticness_estimated': random.randint(20, 80), # Muy variable
        'instrumentalness_estimated': random.randint(0, 20), # Generalmente bajo para música popular
        'key_estimated': random.randint(0, 11),           # 0-11 según convención de Spotify
        'tempo_estimated': random.randint(80, 160),       # Rango típico de tempo
        'loudness_db_estimated': random.uniform(-20, -5), # Rango típico de loudness
        'time_signature_estimated': '4/4',                # Más común
        'mode_estimated': random.choice(['Major', 'Minor'])
    }
    
    return estimated_features

def create_spotify_embed_iframe(track_id: str) -> str:
    """Crear iframe de Spotify embed para una canción"""
    return f'<iframe style="border-radius:12px" src="https://open.spotify.com/embed/track/{track_id}?utm_source=generator" width="100%" height="352" frameBorder="0" allowfullscreen="" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" loading="lazy"></iframe>'

def determine_playlist_suitability_from_estimates(features: Dict) -> Dict:
    """
    Determinar la idoneidad de una canción para diferentes tipos de playlist
    basado en características estimadas
    """
    energy = features.get('energy_estimated', 50) / 100.0
    danceability = features.get('danceability_estimated', 50) / 100.0
    positiveness = features.get('positiveness_estimated', 50) / 100.0
    tempo = features.get('tempo_estimated', 120)
    acousticness = features.get('acousticness_estimated', 50) / 100.0
    
    playlist_suitability = {
        'good_for_party': 1 if danceability > 0.7 and energy > 0.7 else 0,
        'good_for_work_study': 1 if acousticness > 0.3 and energy < 0.6 else 0,
        'good_for_relaxation_meditation': 1 if acousticness > 0.5 and positiveness < 0.5 and energy < 0.4 else 0,
        'good_for_exercise': 1 if energy > 0.7 and tempo > 120 else 0,
        'good_for_running': 1 if energy > 0.8 and tempo > 140 else 0,
        'good_for_yoga_stretching': 1 if acousticness > 0.4 and energy < 0.4 and positiveness > 0.3 else 0,
        'good_for_driving': 1 if energy > 0.5 and danceability > 0.5 and positiveness > 0.4 else 0,
        'good_for_social_gatherings': 1 if danceability > 0.6 and energy > 0.5 and positiveness > 0.5 else 0,
        'good_for_morning_routine': 1 if energy > 0.6 and positiveness > 0.6 and acousticness < 0.7 else 0
    }
    
    return playlist_suitability

def process_spanish_songs_with_spotify_optimized(input_file: str = "spanish_songs.pickle",
                                                output_file: str = "spanish_songs_enriched_optimized.pickle",
                                                sample_size: Optional[int] = None,
                                                extract_emotions: bool = True):
    """
    Procesar canciones españolas y enriquecerlas con datos de Spotify usando el endpoint optimizado
    
    Args:
        input_file: Archivo con canciones españolas filtradas
        output_file: Archivo de salida con datos enriquecidos  
        sample_size: Número de canciones a procesar (None para todas)
        extract_emotions: Si extraer emociones de las letras
    """
    print("🎵 Enriqueciendo canciones españolas con Spotify (versión optimizada)")
    print("=" * 70)
    
    # Inicializar extractor de emociones si es necesario
    emotion_extractor = None
    if extract_emotions:
        emotion_extractor = EmotionExtractor()
        emotion_extractor.initialize()
    
    # Cargar datos
    try:
        with open(input_file, 'rb') as f:
            spanish_songs = pickle.load(f)
        print(f"✅ Cargadas canciones españolas: {len(spanish_songs)} géneros")
    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo {input_file}")
        return
        
    # Verificar conexión a Spotify
    sp = get_spotify_client()
    if not sp:
        print("❌ Error: No se pudo conectar a Spotify")
        return
        
    print("✅ Conectado a Spotify API")
    
    enriched_songs = {}
    processed_count = 0
    found_count = 0
    total_songs = sum(len(songs) for artists in spanish_songs.values() for songs in artists.values())
    
    if sample_size:
        print(f"📊 Procesando muestra de {sample_size} canciones de {total_songs} totales")
    else:
        print(f"📊 Procesando {total_songs} canciones totales")
        
    start_time = datetime.now()
    
    for genre, artists in spanish_songs.items():
        print(f"\n🎼 Procesando género: {genre}")
        enriched_artists = {}
        
        for artist_path, songs in artists.items():
            enriched_songs_for_artist = {}
            artist_name = clean_artist_name(artist_path)
            
            for song_path, song_data in songs.items():
                if sample_size and processed_count >= sample_size:
                    break
                    
                song_name = clean_song_name(song_path)
                
                print(f"  🔍 Procesando: {song_name} - {artist_name}")
                
                # Buscar en Spotify usando mercados hispanohablantes
                markets = ['ES', 'MX', 'AR', 'CO', 'CL', 'PE', 'US']
                found = False
                
                for market in markets:
                    track_info = search_spotify_track(song_name, artist_name, market)
                    if track_info:
                        # Estimar características de audio
                        estimated_features = estimate_audio_features_from_popularity(
                            track_info['popularity'],
                            track_info['explicit'],
                            track_info['release_date']
                        )
                        
                        # Extraer emoción de las letras si está disponible
                        emotion = "unknown"
                        if extract_emotions and emotion_extractor and song_data.get('lyrics'):
                            emotion = emotion_extractor.get_emotion(song_data['lyrics'])
                        
                        # Enriquecer datos
                        enriched_data = {
                            **song_data,  # Datos originales (lyrics, composer, etc.)
                            'spotify_track_id': track_info['track_id'],
                            'spotify_url': track_info['spotify_url'],
                            'spotify_embed': create_spotify_embed_iframe(track_info['track_id']),
                            'artist_name': track_info['artist_name'],
                            'song_title': track_info['track_name'],
                            'album': track_info['album_name'],
                            'album_type': track_info['album_type'],
                            'release_date': track_info['release_date'],
                            'length': f"{track_info['duration_ms'] // 60000}:{(track_info['duration_ms'] % 60000) // 1000:02d}",
                            'explicit': 'Yes' if track_info['explicit'] else 'No',
                            'popularity': track_info['popularity'],
                            'preview_url': track_info.get('preview_url'),
                            'disc_number': track_info['disc_number'],
                            'track_number': track_info['track_number'],
                            'total_tracks': track_info['total_tracks'],
                            'available_markets_count': track_info['available_markets_count'],
                            'emotion': emotion,
                            **estimated_features  # Características estimadas
                        }
                        
                        # Agregar información de imágenes si está disponible
                        for img_key in ['album_image_large', 'album_image_medium', 'album_image_small']:
                            if track_info.get(img_key):
                                enriched_data[img_key] = track_info[img_key]
                        
                        # Agregar playlist suitability
                        playlist_info = determine_playlist_suitability_from_estimates(estimated_features)
                        enriched_data.update(playlist_info)
                        
                        # Agregar artistas colaboradores si existen
                        if track_info.get('collaborating_artists'):
                            enriched_data['collaborating_artists'] = track_info['collaborating_artists']
                        
                        enriched_songs_for_artist[song_path] = enriched_data
                        found_count += 1
                        found = True
                        print(f"    ✅ Encontrada en {market}: {track_info['track_name']} (Pop: {track_info['popularity']})")
                        break
                        
                    time.sleep(0.1)  # Rate limiting
                    
                if not found:
                    # Mantener datos originales si no se encuentra en Spotify
                    enriched_data = {
                        **song_data,
                        'spotify_found': False,
                        'artist_name': artist_name,
                        'song_title': song_name
                    }
                    
                    # Extraer emoción aún si no se encuentra en Spotify
                    if extract_emotions and emotion_extractor and song_data.get('lyrics'):
                        enriched_data['emotion'] = emotion_extractor.get_emotion(song_data['lyrics'])
                    
                    enriched_songs_for_artist[song_path] = enriched_data
                    print(f"    ⚠️ No encontrada en Spotify")
                    
                processed_count += 1
                
                # Mostrar progreso cada 10 canciones
                if processed_count % 10 == 0:
                    elapsed = datetime.now() - start_time
                    rate = processed_count / elapsed.total_seconds() * 60  # canciones por minuto
                    print(f"    📊 Progreso: {processed_count}/{sample_size or total_songs} "
                          f"({found_count} encontradas) - {rate:.1f} canciones/min")
                          
            if enriched_songs_for_artist:
                enriched_artists[artist_path] = enriched_songs_for_artist
                
            if sample_size and processed_count >= sample_size:
                break
                
        if enriched_artists:
            enriched_songs[genre] = enriched_artists
            
        if sample_size and processed_count >= sample_size:
            break
    
    # Guardar datos enriquecidos
    with open(output_file, 'wb') as f:
        pickle.dump(enriched_songs, f)
        
    # Crear también versión JSON para análisis externo
    json_file = output_file.replace('.pickle', '.json')
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(enriched_songs, f, ensure_ascii=False, indent=2)
        
    # Mostrar estadísticas finales
    elapsed = datetime.now() - start_time
    success_rate = (found_count / processed_count * 100) if processed_count > 0 else 0
    
    print(f"\n🎯 Proceso completado en {elapsed}")
    print(f"📊 Estadísticas finales:")
    print(f"  Total procesadas: {processed_count}")
    print(f"  Encontradas en Spotify: {found_count} ({success_rate:.1f}%)")
    print(f"  Géneros procesados: {len(enriched_songs)}")
    print(f"  Velocidad promedio: {processed_count / elapsed.total_seconds() * 60:.1f} canciones/min")
    print(f"  Archivos generados:")
    print(f"    - {output_file} (pickle)")
    print(f"    - {json_file} (JSON)")
    
    if extract_emotions and emotion_extractor and emotion_extractor.initialized:
        print(f"  ✅ Emociones extraídas usando modelo de Hugging Face")
    elif extract_emotions:
        print(f"  ⚠️ Extracción de emociones no disponible (instalar transformers)")

def main():
    """Función principal"""
    print("🎵 Enriquecimiento optimizado de canciones españolas con Spotify")
    print("=" * 60)
    print("Este script usa el endpoint /v1/tracks/{id} y extrae emociones con IA")
    print()
    
    print("¿Deseas procesar todas las canciones o una muestra?")
    print("1. Muestra pequeña (50 canciones)")
    print("2. Muestra mediana (200 canciones)")
    print("3. Muestra grande (500 canciones)")
    print("4. Todas las canciones")
    
    try:
        choice = input("Selecciona una opción (1-4): ").strip()
        
        sample_size = None
        if choice == '1':
            sample_size = 50
        elif choice == '2':
            sample_size = 200
        elif choice == '3':
            sample_size = 500
        elif choice == '4':
            sample_size = None
        else:
            print("Opción inválida, procesando muestra pequeña...")
            sample_size = 50
            
        extract_emotions = input("¿Extraer emociones de las letras? (s/n): ").lower().startswith('s')
        
        process_spanish_songs_with_spotify_optimized(
            input_file="spanish_songs.pickle",
            output_file="spanish_songs_enriched_optimized.pickle",
            sample_size=sample_size,
            extract_emotions=extract_emotions
        )
        
    except KeyboardInterrupt:
        print("\n❌ Proceso interrumpido por el usuario")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    main()
