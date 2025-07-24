#!/usr/bin/env python3
"""
Analizador de datos de letras musicales multi-género
Este script proporciona herramientas para explorar y analizar
los datos extraídos por el scraper multi-género.
"""

import pickle
import os
from collections import defaultdict, Counter
import json


def load_lyrics_data(filepath):
    """Carga los datos de letras desde el archivo pickle"""
    if not os.path.exists(filepath):
        print(f"❌ Error: No se encontró el archivo {filepath}")
        return None

    with open(filepath, "rb") as f:
        return pickle.load(f)


def load_genre_display_names(path="genre_display_names.txt"):
    """Carga el mapeo de nombres normalizados a nombres amigables"""
    display_names = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and ':' in line:
                    normalized, display = line.split(':', 1)
                    display_names[normalized] = display
    except FileNotFoundError:
        print(f"⚠️  Archivo {path} no encontrado, usando nombres normalizados")
    return display_names


def analyze_dataset(lyrics_by_genre):
    """Analiza el dataset completo y muestra estadísticas"""
    print("🔍 ANÁLISIS DEL DATASET MULTI-GÉNERO")
    print("=" * 50)

    total_genres = len(lyrics_by_genre)
    total_artists = 0
    total_songs = 0
    genre_stats = {}

    for genre, artists in lyrics_by_genre.items():
        artist_count = len(artists)
        song_count = sum(len(songs) for songs in artists.values())

        genre_stats[genre] = {
            'artists': artist_count,
            'songs': song_count
        }

        total_artists += artist_count
        total_songs += song_count

    print("📊 Resumen general:")
    print(f"   🎸 Total de géneros: {total_genres}")
    print(f"   👥 Total de artistas: {total_artists}")
    print(f"   🎵 Total de canciones: {total_songs}")
    print(f"   📈 Promedio canciones por artista: {total_songs/total_artists:.1f}")

    print("\n📋 Estadísticas por género:")
    # Ordenar géneros por número de canciones
    sorted_genres = sorted(genre_stats.items(),
                          key=lambda x: x[1]['songs'],
                          reverse=True)

    for genre, stats in sorted_genres:
        print(f"   🎶 {genre}:")
        print(f"      👥 Artistas: {stats['artists']}")
        print(f"      🎵 Canciones: {stats['songs']}")
        print(f"      📊 Canciones/Artista: {stats['songs']/stats['artists']:.1f}")

    return genre_stats


def export_to_json(lyrics_by_genre, output_file):
    """Exporta los datos a formato JSON para análisis externo"""
    print(f"\n💾 Exportando datos a {output_file}...")

    # Crear estructura simplificada para JSON
    json_data = {}

    for genre, artists in lyrics_by_genre.items():
        json_data[genre] = {}

        for artist, songs in artists.items():
            json_data[genre][artist] = {}

            for song_url, song_data in songs.items():
                if isinstance(song_data, dict):
                    # Nueva estructura
                    song_name = song_url.split('/')[-1]
                    json_data[genre][artist][song_name] = {
                        'url': song_url,
                        'lyrics': song_data.get('lyrics', ''),
                        'composer': song_data.get('composer', ''),
                        'genre': song_data.get('genre', genre)
                    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    print(f"✅ Datos exportados exitosamente a {output_file}")


def search_by_genre(lyrics_by_genre, genre_name):
    """Busca y muestra información de un género específico"""
    if genre_name not in lyrics_by_genre:
        print(f"❌ Género '{genre_name}' no encontrado")
        available_genres = list(lyrics_by_genre.keys())
        print(f"📋 Géneros disponibles: {', '.join(available_genres)}")
        return

    artists = lyrics_by_genre[genre_name]
    print(f"\n🎸 GÉNERO: {genre_name}")
    print("-" * 40)
    print(f"👥 Artistas encontrados: {len(artists)}")

    for artist, songs in artists.items():
        song_count = len(songs)
        print(f"  🎤 {artist}: {song_count} canciones")


def search_by_artist(lyrics_by_genre, artist_name):
    """Busca un artista específico en todos los géneros"""
    found = False

    for genre, artists in lyrics_by_genre.items():
        for artist, songs in artists.items():
            if artist_name.lower() in artist.lower():
                if not found:
                    print(f"\n🔍 RESULTADOS PARA: '{artist_name}'")
                    print("-" * 40)
                    found = True

                print(f"🎸 Género: {genre}")
                print(f"🎤 Artista: {artist}")
                print(f"🎵 Canciones: {len(songs)}")

                # Mostrar algunas canciones
                song_list = list(songs.keys())[:5]  # Primeras 5 canciones
                for song in song_list:
                    song_name = song.split('/')[-1] if isinstance(song, str) else song
                    print(f"   • {song_name}")

                if len(songs) > 5:
                    print(f"   ... y {len(songs) - 5} más")
                print()

    if not found:
        print(f"❌ No se encontró ningún artista que contenga '{artist_name}'")


def get_lyrics_sample(lyrics_by_genre, genre=None, artist=None, limit=3):
    """Muestra una muestra de letras (solo primeras líneas por copyright)"""
    count = 0

    for g, artists in lyrics_by_genre.items():
        if genre and g != genre:
            continue

        for a, songs in artists.items():
            if artist and artist.lower() not in a.lower():
                continue

            for song_url, song_data in songs.items():
                if count >= limit:
                    return

                song_name = song_url.split('/')[-1] if isinstance(song_url, str) else song_url

                # Extraer letra según estructura de datos
                if isinstance(song_data, dict):
                    lyrics = song_data.get('lyrics', '')
                    composer = song_data.get('composer', 'N/A')
                else:
                    lyrics = str(song_data)
                    composer = 'N/A'

                print(f"\n🎵 {song_name}")
                print(f"🎤 Artista: {a}")
                print(f"🎸 Género: {g}")
                print(f"✍️  Compositor: {composer}")
                print("📝 Muestra de letra:")

                # Mostrar solo las primeras 2 líneas por copyright
                lines = lyrics.split('\n')[:2]
                for line in lines:
                    if line.strip():
                        print(f"   {line.strip()}")

                if len(lyrics.split('\n')) > 2:
                    print("   [... contenido adicional ...]")

                count += 1


def main():
    """Función principal del analizador"""
    lyrics_file = "lyrics_by_genre.pickle"

    # Cargar datos
    lyrics_data = load_lyrics_data(lyrics_file)
    if not lyrics_data:
        return

    # Cargar nombres amigables de géneros
    genre_display_names = load_genre_display_names()

    def get_display_name(genre):
        """Obtiene el nombre amigable de un género"""
        return genre_display_names.get(genre, genre.title())

    # Cargar nombres amigables de géneros
    genre_display_names = load_genre_display_names()

    while True:
        print("\n🎵 ANALIZADOR DE LETRAS MULTI-GÉNERO")
        print("=" * 40)
        print("1. 📊 Análisis completo del dataset")
        print("2. 🎸 Buscar por género")
        print("3. 🎤 Buscar por artista")
        print("4. 📝 Muestra de letras")
        print("5. 💾 Exportar a JSON")
        print("6. 🚪 Salir")

        choice = input("\n🔍 Selecciona una opción: ").strip()

        if choice == "1":
            analyze_dataset(lyrics_data)

        elif choice == "2":
            genre = input("🎸 Ingresa el nombre del género: ").strip()
            search_by_genre(lyrics_data, genre)

        elif choice == "3":
            artist = input("🎤 Ingresa el nombre del artista: ").strip()
            search_by_artist(lyrics_data, artist)

        elif choice == "4":
            genre = input("🎸 Género (opcional, presiona Enter para todos): ").strip()
            artist = input("🎤 Artista (opcional, presiona Enter para todos): ").strip()

            genre = genre if genre else None
            artist = artist if artist else None

            get_lyrics_sample(lyrics_data, genre, artist)

        elif choice == "5":
            output_file = input("💾 Nombre del archivo JSON (default: dataset.json): ").strip()
            if not output_file:
                output_file = "dataset.json"
            export_to_json(lyrics_data, output_file)

        elif choice == "6":
            print("👋 ¡Hasta luego!")
            break

        else:
            print("❌ Opción no válida")

        input("\n⏎ Presiona Enter para continuar...")


if __name__ == "__main__":
    main()
