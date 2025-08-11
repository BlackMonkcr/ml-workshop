#!/usr/bin/env python3
"""
Prueba final con filtrado inteligente de canciones
Solo procesar canciones que tengan nombres válidos
"""

import pickle
import re

def analyze_song_names():
    """Analizar tipos de nombres de canciones para filtrar mejor"""
    
    print("🔍 ANALIZANDO NOMBRES DE CANCIONES")
    print("=" * 50)
    
    # Cargar datos
    with open("spanish_songs_server_final.pickle", 'rb') as f:
        data = pickle.load(f)
    
    song_patterns = {
        'numeric_only': [],
        'has_numbers': [],
        'normal_names': [],
        'very_long': [],
        'duplicated_artist': []
    }
    
    total_analyzed = 0
    
    for genre_name, genre_data in data.items():
        if total_analyzed >= 1000:  # Analizar muestra
            break
            
        for artist_path, artist_songs in genre_data.items():
            if not isinstance(artist_songs, dict):
                continue
                
            artist_name = artist_path.strip('/').replace('-', ' ').title()
            
            for song_key, song_data in artist_songs.items():
                if total_analyzed >= 1000:
                    break
                    
                song_title = song_key.strip('/').replace('-', ' ').title()
                total_analyzed += 1
                
                # Clasificar canciones
                if song_title.isdigit():
                    song_patterns['numeric_only'].append((artist_name, song_title))
                elif re.search(r'\d{6,}', song_title):  # 6+ dígitos consecutivos
                    song_patterns['numeric_only'].append((artist_name, song_title))
                elif any(char.isdigit() for char in song_title):
                    song_patterns['has_numbers'].append((artist_name, song_title))
                elif len(song_title) > 80:
                    song_patterns['very_long'].append((artist_name, song_title))
                elif artist_name.lower() in song_title.lower():
                    song_patterns['duplicated_artist'].append((artist_name, song_title))
                else:
                    song_patterns['normal_names'].append((artist_name, song_title))
    
    print("📊 ANÁLISIS DE NOMBRES:")
    for pattern, songs in song_patterns.items():
        percentage = (len(songs) / total_analyzed) * 100
        print(f"   {pattern}: {len(songs)} ({percentage:.1f}%)")
        
        if len(songs) > 0:
            print("   Ejemplos:")
            for i, (artist, song) in enumerate(songs[:3]):
                print(f"      • {artist} - {song}")
            print()
    
    return song_patterns

def is_valid_spotify_song(artist_name, song_title):
    """Determinar si una canción tiene potencial de encontrarse en Spotify"""
    
    # Filtros básicos
    if len(song_title) < 2:
        return False
    
    # Rechazar canciones que son solo números
    if song_title.isdigit():
        return False
    
    # Rechazar IDs o códigos largos
    if re.search(r'\d{6,}', song_title):
        return False
    
    # Rechazar títulos demasiado largos (probablemente mal formateados)
    if len(song_title) > 100:
        return False
    
    # Rechazar si el artista está duplicado en el título de forma obvia
    artist_clean = re.sub(r'[^\w]', '', artist_name.lower())
    song_clean = re.sub(r'[^\w]', '', song_title.lower())
    
    if artist_clean and artist_clean == song_clean:
        return False
    
    # Rechazar patrones obviamente problemáticos
    problematic_patterns = [
        r'^track\s*\d+$',  # Track 1, Track 2, etc.
        r'^\d+\s*-\s*\d+$',  # Rangos numéricos
        r'^untitled',  # Canciones sin título
        r'^instrumental\s*\d*$'  # Instrumentales genéricos
    ]
    
    for pattern in problematic_patterns:
        if re.match(pattern, song_title.lower()):
            return False
    
    return True

def create_filtered_sample():
    """Crear muestra filtrada de canciones con alto potencial Spotify"""
    
    print("🎯 CREANDO MUESTRA FILTRADA PARA SPOTIFY")
    print("=" * 50)
    
    # Cargar datos
    with open("spanish_songs_server_final.pickle", 'rb') as f:
        data = pickle.load(f)
    
    valid_songs = []
    rejected_songs = []
    
    for genre_name, genre_data in data.items():
        if len(valid_songs) >= 50:  # Muestra pequeña para prueba
            break
            
        for artist_path, artist_songs in genre_data.items():
            if not isinstance(artist_songs, dict):
                continue
                
            artist_name = artist_path.strip('/').replace('-', ' ').title()
            
            for song_key, song_data in artist_songs.items():
                song_title = song_key.strip('/').replace('-', ' ').title()
                
                if is_valid_spotify_song(artist_name, song_title):
                    valid_songs.append({
                        'artist': artist_name,
                        'song_title': song_title,
                        'genre': genre_name,
                        'lyrics': song_data.get('lyrics', ''),
                        'emotion': song_data.get('emotion', 'unknown')
                    })
                else:
                    rejected_songs.append((artist_name, song_title))
                
                if len(valid_songs) >= 50:
                    break
    
    print(f"✅ Canciones válidas para Spotify: {len(valid_songs)}")
    print(f"❌ Canciones rechazadas: {len(rejected_songs)}")
    
    print("\n🎵 MUESTRA DE CANCIONES VÁLIDAS:")
    for i, song in enumerate(valid_songs[:10]):
        print(f"   {i+1}. {song['artist']} - {song['song_title']}")
    
    print("\n🚫 MUESTRA DE CANCIONES RECHAZADAS:")
    for i, (artist, song) in enumerate(rejected_songs[:10]):
        print(f"   {i+1}. {artist} - {song}")
    
    return valid_songs

if __name__ == "__main__":
    patterns = analyze_song_names()
    print("\n" + "="*50 + "\n")
    filtered_songs = create_filtered_sample()
