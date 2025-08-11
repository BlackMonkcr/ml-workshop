"""
Script para limpiar las letras de las canciones españolas
Elimina contenido HTML, texto de navegación y ruido del dataset
"""
import pickle
import re
import json
from typing import Dict, Any
import os

def clean_lyrics_text(lyrics: str) -> str:
    """
    Limpia el texto de las letras eliminando:
    - Contenido HTML
    - Texto de navegación/UI
    - Texto en portugués/inglés de la plataforma
    - Espacios y saltos de línea excesivos
    """
    if not lyrics or not isinstance(lyrics, str):
        return ""
    
    # Texto de navegación común que debe eliminarse
    navigation_patterns = [
        r'Iniciar sesión o crear cuenta',
        r'Cuenta',
        r'Envie dúvidas, explicações e curiosidades sobre a letra',
        r'Tire dúvidas sobre idiomas, interaja com outros fãs.*?da música\.',
        r'Confira nosso.*?para deixar comentários\.',
        r'Dúvidas enviadas podem receber respostas de professores e alunos da plataforma\.',
        r'Opções de seleção',
        r'Todavía no recibimos esta contribución.*?enviárnosla\?',
        r'¿Los datos están equivocados\? Avísanos\.',
        r'Compuesta por:.*?Avísanos\.',
        r'<.*?>',  # Tags HTML
        r'class="[^"]*"',  # Atributos de clase
        r'href="[^"]*"',  # Enlaces
        r'target="_blank"',  # Atributos target
        r'font --base --[^"]*',  # Clases de fuente
    ]
    
    cleaned_text = lyrics
    
    # Aplicar patrones de limpieza
    for pattern in navigation_patterns:
        cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE | re.DOTALL)
    
    # Limpiar etiquetas HTML restantes
    cleaned_text = re.sub(r'<[^>]+>', '', cleaned_text)
    
    # Limpiar espacios y saltos de línea excesivos
    cleaned_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned_text)  # Max 2 saltos seguidos
    cleaned_text = re.sub(r'[ \t]+', ' ', cleaned_text)  # Espacios múltiples
    cleaned_text = cleaned_text.strip()
    
    # Si queda muy poco contenido, probablemente era solo navegación
    if len(cleaned_text) < 10:
        return ""
    
    # Verificar si es solo texto de navegación (patrones específicos)
    navigation_only_patterns = [
        r'^[\s\n]*$',  # Solo espacios
        r'^[\s\n]*Iniciar.*?Cuenta[\s\n]*$',  # Solo texto de navegación
    ]
    
    for pattern in navigation_only_patterns:
        if re.match(pattern, cleaned_text, flags=re.DOTALL):
            return ""
    
    return cleaned_text

def is_artist_placeholder_song(song_path: str, artist_path: str, lyrics: str) -> bool:
    """
    Determina si una canción es un placeholder (nombre del artista repetido)
    con letras de navegación
    """
    # Extraer nombre del artista y canción de sus paths
    artist_name = artist_path.strip('/').lower()
    song_name = song_path.strip('/').lower()
    
    # Si el nombre de la canción es igual al del artista
    if artist_name == song_name:
        # Y las letras contienen solo texto de navegación
        cleaned = clean_lyrics_text(lyrics)
        if not cleaned or len(cleaned) < 20:
            return True
    
    return False

def clean_spanish_songs_dataset(input_file: str = "spanish_songs.pickle",
                               output_file: str = "spanish_songs_cleaned.pickle"):
    """
    Limpia el dataset completo de canciones españolas
    """
    print("🧹 Limpiando dataset de canciones españolas")
    print("=" * 50)
    
    # Cargar datos
    try:
        with open(input_file, 'rb') as f:
            spanish_songs = pickle.load(f)
        print(f"✅ Cargado dataset: {len(spanish_songs)} géneros")
    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo {input_file}")
        return
    
    cleaned_songs = {}
    total_songs = 0
    cleaned_songs_count = 0
    removed_songs = 0
    placeholder_songs_removed = 0
    
    # Procesar cada género
    for genre, artists in spanish_songs.items():
        print(f"\n🎼 Procesando género: {genre}")
        cleaned_artists = {}
        
        for artist_path, songs in artists.items():
            cleaned_songs_for_artist = {}
            artist_name = artist_path.strip('/')
            
            for song_path, song_data in songs.items():
                total_songs += 1
                
                # Verificar si es canción placeholder del artista
                if is_artist_placeholder_song(song_path, artist_path, song_data.get('lyrics', '')):
                    placeholder_songs_removed += 1
                    print(f"  🗑️ Eliminada canción placeholder: {song_path}")
                    continue
                
                # Limpiar letras
                original_lyrics = song_data.get('lyrics', '')
                cleaned_lyrics = clean_lyrics_text(original_lyrics)
                
                # Si no quedan letras válidas después de la limpieza, omitir
                if not cleaned_lyrics:
                    removed_songs += 1
                    print(f"  🗑️ Eliminada (sin letras válidas): {song_path}")
                    continue
                
                # Crear entrada limpia
                cleaned_song_data = {
                    **song_data,  # Conservar todos los datos originales
                    'lyrics': cleaned_lyrics,  # Reemplazar letras limpias
                    'lyrics_length': len(cleaned_lyrics),  # Agregar métrica de longitud
                    'lyrics_cleaned': True  # Marcar como limpia
                }
                
                cleaned_songs_for_artist[song_path] = cleaned_song_data
                cleaned_songs_count += 1
                
                # Mostrar progreso cada 100 canciones
                if total_songs % 100 == 0:
                    print(f"  📊 Progreso: {total_songs} procesadas, {cleaned_songs_count} válidas")
            
            # Solo agregar artista si tiene canciones válidas
            if cleaned_songs_for_artist:
                cleaned_artists[artist_path] = cleaned_songs_for_artist
        
        # Solo agregar género si tiene artistas válidos
        if cleaned_artists:
            cleaned_songs[genre] = cleaned_artists
    
    # Guardar dataset limpio
    with open(output_file, 'wb') as f:
        pickle.dump(cleaned_songs, f)
    
    # Crear versión JSON para análisis
    json_file = output_file.replace('.pickle', '.json')
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned_songs, f, ensure_ascii=False, indent=2)
    
    # Mostrar estadísticas finales
    print(f"\n🎯 Limpieza completada!")
    print(f"📊 Estadísticas:")
    print(f"  Total canciones procesadas: {total_songs}")
    print(f"  Canciones válidas conservadas: {cleaned_songs_count}")
    print(f"  Canciones placeholder eliminadas: {placeholder_songs_removed}")
    print(f"  Canciones sin letras válidas eliminadas: {removed_songs}")
    print(f"  Géneros en dataset limpio: {len(cleaned_songs)}")
    print(f"  Tasa de conservación: {(cleaned_songs_count/total_songs)*100:.1f}%")
    print(f"  Archivos generados:")
    print(f"    - {output_file}")
    print(f"    - {json_file}")

def clean_enriched_dataset(input_file: str = "spanish_songs_enriched_final.pickle",
                          output_file: str = "spanish_songs_enriched_cleaned.pickle"):
    """
    Limpia el dataset enriquecido con Spotify
    """
    print("🧹 Limpiando dataset enriquecido con Spotify")
    print("=" * 50)
    
    try:
        with open(input_file, 'rb') as f:
            enriched_songs = pickle.load(f)
        print(f"✅ Cargado dataset enriquecido: {len(enriched_songs)} géneros")
    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo {input_file}")
        return
    
    cleaned_enriched = {}
    total_songs = 0
    cleaned_songs_count = 0
    
    for genre, artists in enriched_songs.items():
        print(f"\n🎼 Procesando género: {genre}")
        cleaned_artists = {}
        
        for artist_path, songs in artists.items():
            cleaned_songs_for_artist = {}
            
            for song_path, song_data in songs.items():
                total_songs += 1
                
                # Limpiar letras si existen
                if 'lyrics' in song_data:
                    cleaned_lyrics = clean_lyrics_text(song_data['lyrics'])
                    
                    # Actualizar datos
                    cleaned_song_data = {
                        **song_data,
                        'lyrics': cleaned_lyrics,
                        'lyrics_length': len(cleaned_lyrics) if cleaned_lyrics else 0,
                        'lyrics_cleaned': True,
                        'has_valid_lyrics': bool(cleaned_lyrics)
                    }
                    
                    cleaned_songs_for_artist[song_path] = cleaned_song_data
                    cleaned_songs_count += 1
                else:
                    # Conservar canción sin letras
                    cleaned_songs_for_artist[song_path] = {
                        **song_data,
                        'has_valid_lyrics': False
                    }
                    cleaned_songs_count += 1
            
            if cleaned_songs_for_artist:
                cleaned_artists[artist_path] = cleaned_songs_for_artist
        
        if cleaned_artists:
            cleaned_enriched[genre] = cleaned_artists
    
    # Guardar dataset enriquecido limpio
    with open(output_file, 'wb') as f:
        pickle.dump(cleaned_enriched, f)
    
    # Crear versión JSON
    json_file = output_file.replace('.pickle', '.json')
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned_enriched, f, ensure_ascii=False, indent=2)
    
    print(f"\n🎯 Limpieza del dataset enriquecido completada!")
    print(f"📊 Estadísticas:")
    print(f"  Total canciones procesadas: {total_songs}")
    print(f"  Canciones conservadas: {cleaned_songs_count}")
    print(f"  Géneros: {len(cleaned_enriched)}")
    print(f"  Archivos generados:")
    print(f"    - {output_file}")
    print(f"    - {json_file}")

def analyze_cleaning_results(cleaned_file: str = "spanish_songs_cleaned.pickle"):
    """
    Analiza los resultados de la limpieza
    """
    print("📊 Analizando resultados de limpieza")
    print("=" * 40)
    
    try:
        with open(cleaned_file, 'rb') as f:
            cleaned_songs = pickle.load(f)
    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo {cleaned_file}")
        return
    
    total_songs = 0
    total_lyrics_length = 0
    songs_with_lyrics = 0
    genres_count = len(cleaned_songs)
    artists_count = 0
    
    for genre, artists in cleaned_songs.items():
        artists_count += len(artists)
        for artist_path, songs in artists.items():
            for song_path, song_data in songs.items():
                total_songs += 1
                lyrics_length = song_data.get('lyrics_length', 0)
                if lyrics_length > 0:
                    songs_with_lyrics += 1
                    total_lyrics_length += lyrics_length
    
    avg_lyrics_length = total_lyrics_length / songs_with_lyrics if songs_with_lyrics > 0 else 0
    
    print(f"🎵 Canciones totales: {total_songs}")
    print(f"🎤 Artistas: {artists_count}")
    print(f"🎼 Géneros: {genres_count}")
    print(f"📝 Canciones con letras válidas: {songs_with_lyrics} ({(songs_with_lyrics/total_songs)*100:.1f}%)")
    print(f"📏 Longitud promedio de letras: {avg_lyrics_length:.0f} caracteres")

def main():
    """Función principal"""
    print("🧹 Sistema de Limpieza de Dataset Musical")
    print("=" * 50)
    print("1. Limpiar dataset original")
    print("2. Limpiar dataset enriquecido")
    print("3. Limpiar ambos")
    print("4. Analizar resultados")
    
    try:
        choice = input("Selecciona una opción (1-4): ").strip()
        
        if choice == '1':
            clean_spanish_songs_dataset()
            analyze_cleaning_results()
        elif choice == '2':
            clean_enriched_dataset()
        elif choice == '3':
            clean_spanish_songs_dataset()
            clean_enriched_dataset()
            analyze_cleaning_results("spanish_songs_cleaned.pickle")
        elif choice == '4':
            analyze_cleaning_results()
        else:
            print("Opción inválida, limpiando dataset original...")
            clean_spanish_songs_dataset()
            analyze_cleaning_results()
            
    except KeyboardInterrupt:
        print("\n❌ Proceso interrumpido por el usuario")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    main()
