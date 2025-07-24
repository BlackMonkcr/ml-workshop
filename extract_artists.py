#!/usr/bin/env python3
"""
Extractor de artistas por género (solo artistas, sin letras)
Este script extrae rápidamente todos los artistas de todos los géneros
para luego usar en el scraper paralelo de letras.
"""

import requests
from bs4 import BeautifulSoup
import pickle
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Importar funciones necesarias
from app import normalize_genre_name, load_genres, save_pickle, read_pickle

# Lock para escritura thread-safe
write_lock = threading.Lock()

def get_artists_for_genre(args):
    """
    Extrae artistas de un género específico (para paralelización)

    Args:
        args: tuple (genre, base_url)

    Returns:
        dict: {'genre': genre, 'artists': list, 'success': bool}
    """
    genre, base_url = args

    try:
        # Normalizar género y construir URL
        normalized_genre = normalize_genre_name(genre)
        url = f"{base_url}/mais-acessadas/{normalized_genre}/"

        print(f"🔍 Buscando artistas de {genre}...")

        result = requests.get(url, timeout=10)
        result.raise_for_status()

        soup = BeautifulSoup(result.content, "lxml")
        links = soup.find("ol", class_="top-list_art")

        if not links:
            print(f"⚠️  No se encontraron artistas para {genre}")
            return {
                'genre': genre,
                'artists': [],
                'success': False,
                'message': 'No se encontró contenedor de artistas'
            }

        artists = []
        for link in links.find_all("li"):
            artist_link = link.find("a")
            if artist_link and "href" in artist_link.attrs:
                url_artist = artist_link.attrs["href"]
                artists.append(url_artist)

        print(f"✅ {genre}: {len(artists)} artistas encontrados")
        return {
            'genre': genre,
            'artists': artists,
            'success': True,
            'message': f'{len(artists)} artistas'
        }

    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión para {genre}: {e}")
        return {
            'genre': genre,
            'artists': [],
            'success': False,
            'message': f'Error de conexión: {e}'
        }
    except Exception as e:
        print(f"❌ Error inesperado para {genre}: {e}")
        return {
            'genre': genre,
            'artists': [],
            'success': False,
            'message': f'Error: {e}'
        }


def main():
    """Función principal para extraer artistas"""
    print("👥 EXTRACTOR DE ARTISTAS POR GÉNERO")
    print("=" * 45)

    # Configuración
    base_url = "https://www.letras.com"
    genres_path = "genres.txt"
    artists_path = "artists_by_genre.pickle"
    max_workers = 8  # Más workers ya que solo extraemos artistas (más rápido)

    print("⚙️  Configuración:")
    print(f"   🔧 Workers paralelos: {max_workers}")
    print(f"   📁 Archivo de salida: {artists_path}")

    # Cargar géneros
    if not os.path.exists(genres_path):
        print(f"❌ Error: No se encontró el archivo {genres_path}")
        return

    genres = load_genres(genres_path)
    print(f"📂 Se cargaron {len(genres)} géneros musicales")

    # Verificar si ya existen datos
    if os.path.exists(artists_path):
        print("📁 Archivo de artistas existente encontrado")
        response = input("¿Quieres sobreescribir los datos existentes? (y/N): ")
        if response.lower() != 'y':
            print("❌ Operación cancelada")
            return

    start_time = time.time()
    artists_by_genre = {}

    # Preparar argumentos para procesamiento paralelo
    genre_args = [(genre, base_url) for genre in genres]

    print("\n🚀 Iniciando extracción paralela de artistas...")
    print("-" * 50)

    successful_genres = 0
    total_artists = 0

    # Procesar géneros en paralelo
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Enviar todas las tareas
        future_to_genre = {
            executor.submit(get_artists_for_genre, args): args[0]
            for args in genre_args
        }

        # Procesar resultados conforme van completándose
        for i, future in enumerate(as_completed(future_to_genre), 1):
            genre = future_to_genre[future]

            try:
                result = future.result()

                if result['success']:
                    artists_by_genre[result['genre']] = result['artists']
                    successful_genres += 1
                    total_artists += len(result['artists'])

                    progress = (i / len(genres)) * 100
                    print(f"✅ [{i:2d}/{len(genres)}] ({progress:4.1f}%) {result['genre']}: {result['message']}")
                else:
                    print(f"❌ [{i:2d}/{len(genres)}] {result['genre']}: {result['message']}")

                # Guardar progreso cada 10 géneros
                if i % 10 == 0:
                    with write_lock:
                        save_pickle(artists_path, artists_by_genre)
                        print(f"💾 Progreso guardado ({i}/{len(genres)} géneros)")

            except Exception as e:
                print(f"❌ [{i:2d}/{len(genres)}] {genre}: Error procesando resultado: {e}")

    # Guardar resultados finales
    save_pickle(artists_path, artists_by_genre)

    # Estadísticas finales
    end_time = time.time()
    elapsed_time = end_time - start_time

    print(f"\n🎉 ¡Extracción de artistas completada!")
    print("=" * 45)
    print("📊 Estadísticas finales:")
    print(f"   ⏱️  Tiempo total: {elapsed_time:.1f} segundos")
    print(f"   🎸 Géneros exitosos: {successful_genres}/{len(genres)}")
    print(f"   👥 Total artistas: {total_artists:,}")
    print(f"   📈 Promedio artistas/género: {total_artists/successful_genres:.1f}")
    print(f"   🚀 Velocidad: {total_artists/elapsed_time:.1f} artistas/segundo")
    print(f"   💾 Datos guardados en: {artists_path}")

    if successful_genres > 0:
        print(f"\n✅ ¡Listo! Ahora puedes ejecutar:")
        print(f"   python app_parallel.py  # Para extraer letras en paralelo")
        print(f"   python app.py           # Para extraer letras secuencialmente")
    else:
        print(f"\n❌ No se pudieron extraer artistas. Verificar conectividad.")


if __name__ == "__main__":
    main()
