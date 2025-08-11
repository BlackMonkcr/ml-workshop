"""
Script para filtrar canciones en español basado en artistas latinos/hispanos
"""
import pickle
import re
from typing import Dict, Set, Any

# Lista de artistas/géneros que típicamente cantan en español
SPANISH_SPEAKING_ARTISTS = {
    # Artistas populares latinos/hispanos (ejemplos - se puede expandir)
    'karol-g', 'bad-bunny', 'j-balvin', 'maluma', 'ozuna', 'anuel-aa', 'daddy-yankee',
    'luis-fonsi', 'cnco', 'jesse-joy', 'mau-y-ricky', 'camilo', 'sebastian-yatra',
    'rosalia', 'shakira', 'manu-chao', 'alvaro-soler', 'enrique-iglesias',
    'marc-anthony', 'victor-manuelle', 'gilberto-santa-rosa', 'la-india',
    'romeo-santos', 'prince-royce', 'aventura', 'bachata-heightz',
    'carlos-vives', 'fonseca', 'jesse-uribe', 'silvestre-dangond',
    'grupo-niche', 'la-sonora-ponceña', 'willie-colon', 'ruben-blades',
    'manu-negra', 'orishas', 'bomba-estereo', 'aterciopelados',
    'cafe-tacvba', 'molotov', 'maldita-vecindad', 'los-fabulosos-cadillacs',
    'soda-stereo', 'gustavo-cerati', 'charly-garcia', 'fito-paez',
    'enanitos-verdes', 'los-prisioneros', 'la-ley', 'lucybell',
    'mana', 'caifanes', 'heroes-del-silencio', 'jarabe-de-palo'
}

# Géneros que típicamente son en español
SPANISH_GENRES = {
    'reggaeton', 'salsa', 'bachata', 'merengue', 'cumbia', 'vallenato',
    'ranchera', 'mariachi', 'bolero', 'trova', 'corridos', 'regional',
    'flamenco', 'tango', 'andina', 'folclore', 'tropical', 'balada'
}

# Palabras clave en nombres de artistas que sugieren origen hispano
HISPANIC_KEYWORDS = {
    'los', 'las', 'el', 'la', 'grupo', 'banda', 'orquesta', 'conjunto',
    'son', 'salsa', 'merengue', 'bachata', 'cumbia', 'vallenato'
}

def clean_artist_name(artist_path: str) -> str:
    """Limpia el nombre del artista removiendo las barras y caracteres especiales"""
    return artist_path.strip('/').replace('/', '').replace('-', ' ').lower()

def is_spanish_artist(artist_path: str, genre: str) -> bool:
    """
    Determina si un artista probablemente canta en español
    basado en el nombre del artista y el género
    """
    clean_name = clean_artist_name(artist_path)
    
    # Verificar si está en la lista de artistas conocidos
    if any(known_artist in clean_name for known_artist in SPANISH_SPEAKING_ARTISTS):
        return True
    
    # Verificar si el género es típicamente en español
    if genre.lower() in SPANISH_GENRES:
        return True
    
    # Verificar palabras clave hispanas en el nombre del artista
    if any(keyword in clean_name for keyword in HISPANIC_KEYWORDS):
        return True
    
    # Patrones adicionales que sugieren origen hispano
    hispanic_patterns = [
        r'\b(mc|dj)\s+[a-z]+\b',  # MC o DJ seguido de nombre
        r'\b[a-z]+\s+(jr|junior|hijo)\b',  # Jr, Junior, Hijo
        r'\b(don|doña)\s+[a-z]+\b',  # Don/Doña
    ]
    
    for pattern in hispanic_patterns:
        if re.search(pattern, clean_name):
            return True
    
    return False

def filter_spanish_songs(lyrics_data: Dict, artists_data: Dict) -> Dict:
    """
    Filtra las canciones que probablemente están en español
    """
    spanish_songs = {}
    
    total_songs = 0
    spanish_songs_count = 0
    
    print("Filtrando canciones en español...")
    
    for genre, artists in lyrics_data.items():
        print(f"\nProcesando género: {genre}")
        
        spanish_artists_in_genre = {}
        
        for artist_path, songs in artists.items():
            # Verificar si el artista probablemente canta en español
            if is_spanish_artist(artist_path, genre):
                spanish_artists_in_genre[artist_path] = songs
                spanish_songs_count += len(songs)
                print(f"  ✓ Artista español detectado: {clean_artist_name(artist_path)} ({len(songs)} canciones)")
            
            total_songs += len(songs)
        
        if spanish_artists_in_genre:
            spanish_songs[genre] = spanish_artists_in_genre
            print(f"  Género {genre}: {len(spanish_artists_in_genre)} artistas españoles")
    
    print("\n📊 Resumen del filtrado:")
    print(f"Total de canciones originales: {total_songs}")
    print(f"Canciones en español identificadas: {spanish_songs_count}")
    print(f"Porcentaje filtrado: {(spanish_songs_count/total_songs)*100:.1f}%")
    print(f"Géneros con contenido en español: {len(spanish_songs)}")
    
    return spanish_songs

def save_spanish_songs(spanish_data: Dict, output_file: str = "spanish_songs.pickle"):
    """Guarda las canciones en español en un archivo pickle"""
    with open(output_file, 'wb') as f:
        pickle.dump(spanish_data, f)
    print(f"✅ Datos guardados en {output_file}")

def main():
    """Función principal"""
    print("🎵 Filtrador de Canciones en Español")
    print("=" * 50)
    
    # Cargar datos
    print("Cargando datos...")
    
    try:
        with open('lyrics_by_genre_parallel.pickle', 'rb') as f:
            lyrics_data = pickle.load(f)
        print(f"✅ Letras cargadas: {len(lyrics_data)} géneros")
        
        with open('artists_by_genre.pickle', 'rb') as f:
            artists_data = pickle.load(f)
        print(f"✅ Artistas cargados: {len(artists_data)} géneros")
        
    except FileNotFoundError as e:
        print(f"❌ Error: No se encontró el archivo {e.filename}")
        return
    
    # Filtrar canciones en español
    spanish_songs = filter_spanish_songs(lyrics_data, artists_data)
    
    # Guardar resultado
    save_spanish_songs(spanish_songs, "spanish_songs.pickle")
    
    # Mostrar estadísticas finales
    print("\n🎯 Proceso completado:")
    print("Archivo generado: spanish_songs.pickle")
    print(f"Géneros procesados: {len(spanish_songs)}")
    
    # Mostrar algunos ejemplos
    print("\n📝 Ejemplos de artistas identificados como hispanos:")
    count = 0
    for genre, artists in spanish_songs.items():
        if count >= 10:
            break
        for artist_path in list(artists.keys())[:2]:
            print(f"  {clean_artist_name(artist_path)} ({genre})")
            count += 1
            if count >= 10:
                break

if __name__ == "__main__":
    main()
