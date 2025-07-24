#!/usr/bin/env python3
"""
Versión paralelizada del scraper multi-género
Utiliza ThreadPoolExecutor para procesar múltiples artistas y canciones en paralelo
"""

import requests
from bs4 import BeautifulSoup
import pickle
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from functools import wraps


# Importar funciones del módulo principal
from app import (
    normalize_genre_name, load_genres, save_pickle, read_pickle,
    get_artists, extract_songs_from_new_layout, extract_songs_from_old_layout,
    extract_songs_fallback, extract_lyrics_new_layout, extract_lyrics_old_layout,
    extract_lyrics_fallback
)

# Lock para escritura thread-safe
write_lock = threading.Lock()
request_lock = threading.Lock()

# Contador de requests para rate limiting
request_count = 0
last_request_time = 0


def rate_limited_request(url, delay=0.5):
    """Realiza requests con rate limiting thread-safe"""
    global request_count, last_request_time

    with request_lock:
        current_time = time.time()
        time_since_last = current_time - last_request_time

        if time_since_last < delay:
            time.sleep(delay - time_since_last)

        request_count += 1
        last_request_time = time.time()

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"      ❌ Error de conexión en {url}: {e}")
            return None


def get_song_names_parallel(url):
    """Versión thread-safe de get_song_names"""
    try:
        result = rate_limited_request(url)
        if not result:
            return []

        soup = BeautifulSoup(result.content, "lxml")

        # Intentar nuevo layout primero
        songs = extract_songs_from_new_layout(soup)
        if songs:
            return songs

        # Intentar layout antiguo
        songs = extract_songs_from_old_layout(soup)
        if songs:
            return songs

        # Método de fallback
        songs = extract_songs_fallback(soup, url)
        unique_songs = list(dict.fromkeys(songs))
        return unique_songs

    except Exception as e:
        print(f"      ❌ Error en get_song_names_parallel: {e}")
        return []


def get_lyrics_parallel(url):
    """Versión thread-safe de get_lyrics"""
    try:
        result = rate_limited_request(url)
        if not result:
            return "", ""

        soup = BeautifulSoup(result.content, "lxml")

        # Intentar nuevo layout primero
        lyrics, composer = extract_lyrics_new_layout(soup)
        if lyrics:
            return lyrics, composer

        # Intentar layout antiguo
        lyrics, composer = extract_lyrics_old_layout(soup)
        if lyrics:
            return lyrics, composer

        # Método de fallback
        lyrics, composer = extract_lyrics_fallback(soup)
        return lyrics, composer

    except Exception as e:
        print(f"      ❌ Error en get_lyrics_parallel: {e}")
        return "", ""


def process_song(args):
    """Procesa una canción individual (para paralelización)"""
    song_url, artist, genre, base_url = args

    song_name = song_url.split('/')[-2] if song_url.endswith('/') else song_url.split('/')[-1]
    full_url = base_url + song_url

    lyrics, composer = get_lyrics_parallel(full_url)

    result = {
        'song_url': song_url,
        'song_name': song_name,
        'artist': artist,
        'genre': genre,
        'lyrics': lyrics,
        'composer': composer,
        'success': len(lyrics) > 0
    }

    return result


def process_artist(args):
    """Procesa un artista individual (para paralelización)"""
    artist, genre, base_url, end_url, max_songs = args

    try:
        # Obtener canciones del artista
        songs_url = base_url + artist + end_url
        songs = get_song_names_parallel(songs_url)

        if not songs:
            return {
                'artist': artist,
                'genre': genre,
                'songs': {},
                'success': False,
                'message': 'No se encontraron canciones'
            }

        # Limitar número de canciones
        songs_to_process = songs[:max_songs]

        # Procesar canciones en paralelo (con menos workers para no sobrecargar)
        song_args = [(song, artist, genre, base_url) for song in songs_to_process]
        artist_songs = {}

        with ThreadPoolExecutor(max_workers=3) as song_executor:
            song_futures = {song_executor.submit(process_song, args): args for args in song_args}

            for future in as_completed(song_futures):
                try:
                    result = future.result()
                    if result['success']:
                        artist_songs[result['song_url']] = {
                            'lyrics': result['lyrics'],
                            'composer': result['composer'],
                            'genre': result['genre']
                        }
                except Exception as e:
                    print(f"      ❌ Error procesando canción: {e}")

        return {
            'artist': artist,
            'genre': genre,
            'songs': artist_songs,
            'success': len(artist_songs) > 0,
            'message': f'Procesadas {len(artist_songs)} canciones'
        }

    except Exception as e:
        return {
            'artist': artist,
            'genre': genre,
            'songs': {},
            'success': False,
            'message': f'Error: {e}'
        }


def main():
    """Función principal del scraper paralelo"""
    print("🚀 SCRAPER MULTI-GÉNERO PARALELIZADO")
    print("=" * 50)

    # Configuración
    base_url = "https://www.letras.com"
    end_url = "mais-tocadas.html"
    genres_path = "genres.txt"
    artists_path = "artists_by_genre.pickle"
    lyrics_path = "lyrics_by_genre_parallel.pickle"

    # Configuración de paralelización OPTIMIZADA
    MAX_ARTISTS_PER_GENRE = 100  # Número muy alto = efectivamente todos
    MAX_SONGS_PER_ARTIST = 10      # 10 canciones por artista como solicitaste
    MAX_WORKERS_ARTISTS = 8        # Más workers para artistas (aprovecha CPU)
    MAX_WORKERS_SONGS = 6          # Más workers para canciones (balance CPU/red)

    print("⚙️  Configuración paralela:")
    print(f"   👥 Workers para artistas: {MAX_WORKERS_ARTISTS}")
    print(f"   🎵 Workers para canciones: {MAX_WORKERS_SONGS}")
    print(f"   🎯 Máx artistas por género: {'TODOS' if MAX_ARTISTS_PER_GENRE >= 1000 else MAX_ARTISTS_PER_GENRE}")
    print(f"   🎶 Máx canciones por artista: {MAX_SONGS_PER_ARTIST}")
    print("   🚀 Modo: EXTRACCIÓN MÁXIMA")

    # Cargar géneros
    if not os.path.exists(genres_path):
        print(f"❌ Error: No se encontró el archivo {genres_path}")
        return

    genres = load_genres(genres_path)
    print(f"📂 Se cargaron {len(genres)} géneros musicales")

    # Cargar artistas
    if os.path.exists(artists_path):
        artists_by_genre = read_pickle(artists_path)
        print("📁 Cargada lista existente de artistas por género")
    else:
        print("❌ Necesitas ejecutar el scraper normal primero para obtener artistas")
        return

    # Inicializar estructura de letras
    if os.path.exists(lyrics_path):
        lyrics_by_genre = read_pickle(lyrics_path)
        print("📁 Cargada base de datos existente de letras paralelas")
    else:
        lyrics_by_genre = {}
        print("🆕 Creando nueva base de datos de letras paralelas")

    start_time = time.time()

    # Procesar géneros (TODOS los géneros)
    for i, genre in enumerate(genres, 1):  # Procesar TODOS los géneros
        if genre not in artists_by_genre:
            print(f"⚠️  Saltando {genre}: no hay artistas")
            continue

        print(f"\n🎸 Procesando género {i}/{len(genres)}: {genre}")
        print("-" * 40)

        artists = artists_by_genre[genre]

        # Tomar todos los artistas disponibles (limitado por MAX_ARTISTS_PER_GENRE)
        artists_to_process = artists[:MAX_ARTISTS_PER_GENRE]

        # Mensaje informativo
        if len(artists_to_process) == len(artists):
            artists_count_msg = f"TODOS ({len(artists)})"
        else:
            artists_count_msg = f"{len(artists_to_process)} de {len(artists)}"

        print(f"👥 Procesando {artists_count_msg} artistas en paralelo...")

        # Preparar argumentos para procesamiento paralelo
        artist_args = [
            (artist, genre, base_url, end_url, MAX_SONGS_PER_ARTIST)
            for artist in artists
        ]

        # Procesar artistas en paralelo
        genre_results = {}
        completed_artists = 0

        with ThreadPoolExecutor(max_workers=MAX_WORKERS_ARTISTS) as executor:
            future_to_artist = {
                executor.submit(process_artist, args): args[0]
                for args in artist_args
            }

            for future in as_completed(future_to_artist):
                artist = future_to_artist[future]
                completed_artists += 1

                try:
                    result = future.result()

                    if result['success']:
                        genre_results[result['artist']] = result['songs']
                        print(f"  ✅ {completed_artists}/{len(artists)}: {result['artist']} - {result['message']}")
                    else:
                        print(f"  ❌ {completed_artists}/{len(artists)}: {result['artist']} - {result['message']}")

                except Exception as e:
                    print(f"  ❌ {completed_artists}/{len(artists)}: {artist} - Error: {e}")

        # Guardar resultados del género
        if genre_results:
            lyrics_by_genre[genre] = genre_results

            # Guardar progreso thread-safe
            with write_lock:
                save_pickle(lyrics_path, lyrics_by_genre)

            total_songs = sum(len(songs) for songs in genre_results.values())
            print(f"✅ {genre}: {len(genre_results)} artistas, {total_songs} canciones")
        else:
            print(f"❌ {genre}: No se procesó ningún artista exitosamente")

    # Estadísticas finales
    end_time = time.time()
    elapsed_time = end_time - start_time

    total_genres = len(lyrics_by_genre)
    total_artists = sum(len(artists) for artists in lyrics_by_genre.values())
    total_songs = sum(
        len(songs)
        for genre_data in lyrics_by_genre.values()
        for songs in genre_data.values()
    )

    print("\n🎉 ¡Extracción paralela completada!")
    print("=" * 50)
    print("📊 Estadísticas finales:")
    print(f"   ⏱️  Tiempo total: {elapsed_time:.1f} segundos")
    print(f"   🎸 Géneros procesados: {total_genres}")
    print(f"   👥 Artistas procesados: {total_artists}")
    print(f"   🎵 Canciones extraídas: {total_songs}")
    print(f"   🌐 Requests realizados: {request_count}")
    print(f"   📈 Velocidad: {total_songs/elapsed_time:.1f} canciones/segundo")
    print(f"   💾 Datos guardados en: {lyrics_path}")


if __name__ == "__main__":
    main()
