#!/usr/bin/env python3
"""
Script para limpiar canciones vacías y preparar dataset final para BD
"""

import pickle
import os
import json
from datetime import datetime

def clean_empty_songs(input_file: str = "spanish_songs_emotions_fixed.pickle"):
    """
    Eliminar canciones sin letras válidas del dataset
    """
    
    print(f"📖 Cargando dataset: {input_file}")
    
    if not os.path.exists(input_file):
        print(f"❌ No se encontró: {input_file}")
        return False
    
    with open(input_file, 'rb') as f:
        data = pickle.load(f)
    
    # Estadísticas iniciales
    total_initial = 0
    empty_songs = 0
    cleaned_data = {}
    
    print("🧹 Limpiando canciones vacías...")
    
    for genre_name, genre_data in data.items():
        cleaned_genre = {}
        
        for artist_path, artist_songs in genre_data.items():
            if isinstance(artist_songs, dict):
                cleaned_artist = {}
                
                for song_key, song_data in artist_songs.items():
                    if isinstance(song_data, dict) and 'lyrics' in song_data:
                        total_initial += 1
                        lyrics = song_data.get('lyrics', '').strip()
                        
                        # Verificar si tiene letras válidas
                        if (lyrics and 
                            lyrics not in ['N/A', 'No disponible', '', 'null', 'undefined'] and
                            len(lyrics) > 10):  # Mínimo 10 caracteres para considerar válido
                            
                            cleaned_artist[song_key] = song_data
                        else:
                            empty_songs += 1
                
                # Solo incluir artista si tiene canciones válidas
                if cleaned_artist:
                    cleaned_genre[artist_path] = cleaned_artist
        
        # Solo incluir género si tiene artistas válidos
        if cleaned_genre:
            cleaned_data[genre_name] = cleaned_genre
    
    # Contar canciones finales
    total_final = 0
    for genre_data in cleaned_data.values():
        for artist_songs in genre_data.values():
            total_final += len([s for s in artist_songs.values() if isinstance(s, dict)])
    
    # Guardar dataset limpio
    output_file = "spanish_songs_clean_final.pickle"
    with open(output_file, 'wb') as f:
        pickle.dump(cleaned_data, f)
    
    print(f"\n📊 Limpieza completada:")
    print(f"  ➖ Canciones iniciales: {total_initial}")
    print(f"  🗑️  Canciones eliminadas: {empty_songs}")
    print(f"  ✅ Canciones válidas: {total_final}")
    print(f"  📁 Dataset limpio: {output_file}")
    
    return output_file, total_final

def export_for_database(input_file: str):
    """
    Exportar dataset en formato óptimo para base de datos
    """
    
    with open(input_file, 'rb') as f:
        data = pickle.load(f)
    
    # Estructura plana para BD
    songs_for_db = []
    
    for genre_name, genre_data in data.items():
        for artist_path, artist_songs in genre_data.items():
            if isinstance(artist_songs, dict):
                artist_name = artist_path.strip('/').replace('-', ' ').title()
                
                for song_key, song_data in artist_songs.items():
                    if isinstance(song_data, dict) and 'lyrics' in song_data:
                        song_name = song_key.strip('/').replace('-', ' ').title()
                        
                        # Estructura optimizada para BD
                        db_record = {
                            # Identificadores
                            "id": len(songs_for_db) + 1,
                            "artist": artist_name,
                            "song_title": song_name,
                            "genre": genre_name,
                            
                            # Contenido
                            "lyrics": song_data.get('lyrics', ''),
                            "lyrics_word_count": len(song_data.get('lyrics', '').split()),
                            
                            # Análisis emocional
                            "emotion": song_data.get('emotion', 'unknown'),
                            
                            # Metadata Spotify
                            "spotify_found": song_data.get('spotify_found', False),
                            "popularity": song_data.get('popularity'),
                            "explicit_content": song_data.get('explicit_content', False),
                            "release_date": song_data.get('release_date', ''),
                            "duration_ms": song_data.get('duration_ms'),
                            
                            # Características musicales
                            "energy": song_data.get('energy'),
                            "danceability": song_data.get('danceability'),
                            "valence": song_data.get('valence'),
                            "speechiness": song_data.get('speechiness'),
                            "acousticness": song_data.get('acousticness'),
                            "instrumentalness": song_data.get('instrumentalness'),
                            "liveness": song_data.get('liveness'),
                            "loudness": song_data.get('loudness'),
                            "tempo": song_data.get('tempo'),
                            "key_signature": song_data.get('key'),
                            "mode": song_data.get('mode'),
                            "time_signature": song_data.get('time_signature'),
                            
                            # Metadata del procesamiento
                            "is_estimated": song_data.get('is_estimated', True),
                            "processed_date": datetime.now().isoformat()
                        }
                        
                        songs_for_db.append(db_record)
    
    # Exportar en múltiples formatos para BD
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. JSON para NoSQL (MongoDB, etc.)
    json_file = f"songs_for_database_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            "metadata": {
                "total_records": len(songs_for_db),
                "export_date": datetime.now().isoformat(),
                "schema_version": "1.0"
            },
            "songs": songs_for_db
        }, f, indent=2, ensure_ascii=False)
    
    # 2. CSV para importación SQL
    import pandas as pd
    df = pd.DataFrame(songs_for_db)
    csv_file = f"songs_for_database_{timestamp}.csv"
    df.to_csv(csv_file, index=False, encoding='utf-8')
    
    # 3. SQL INSERT statements
    sql_file = f"songs_database_inserts_{timestamp}.sql"
    with open(sql_file, 'w', encoding='utf-8') as f:
        f.write("-- Tabla de canciones para ML Workshop\n")
        f.write("CREATE TABLE IF NOT EXISTS songs (\n")
        f.write("    id INTEGER PRIMARY KEY,\n")
        f.write("    artist VARCHAR(255) NOT NULL,\n")
        f.write("    song_title VARCHAR(255) NOT NULL,\n")
        f.write("    genre VARCHAR(100),\n")
        f.write("    lyrics TEXT,\n")
        f.write("    lyrics_word_count INTEGER,\n")
        f.write("    emotion VARCHAR(50),\n")
        f.write("    spotify_found BOOLEAN,\n")
        f.write("    popularity INTEGER,\n")
        f.write("    explicit_content BOOLEAN,\n")
        f.write("    release_date VARCHAR(20),\n")
        f.write("    duration_ms INTEGER,\n")
        f.write("    energy DECIMAL(5,4),\n")
        f.write("    danceability DECIMAL(5,4),\n")
        f.write("    valence DECIMAL(5,4),\n")
        f.write("    speechiness DECIMAL(5,4),\n")
        f.write("    acousticness DECIMAL(5,4),\n")
        f.write("    instrumentalness DECIMAL(5,4),\n")
        f.write("    liveness DECIMAL(5,4),\n")
        f.write("    loudness DECIMAL(8,4),\n")
        f.write("    tempo DECIMAL(8,4),\n")
        f.write("    key_signature INTEGER,\n")
        f.write("    mode INTEGER,\n")
        f.write("    time_signature INTEGER,\n")
        f.write("    is_estimated BOOLEAN,\n")
        f.write("    processed_date TIMESTAMP\n")
        f.write(");\n\n")
        
        # INSERTs
        for song in songs_for_db:
            values = []
            for key in ['id', 'artist', 'song_title', 'genre', 'lyrics', 'lyrics_word_count',
                       'emotion', 'spotify_found', 'popularity', 'explicit_content', 'release_date',
                       'duration_ms', 'energy', 'danceability', 'valence', 'speechiness',
                       'acousticness', 'instrumentalness', 'liveness', 'loudness', 'tempo',
                       'key_signature', 'mode', 'time_signature', 'is_estimated', 'processed_date']:
                value = song.get(key)
                if value is None:
                    values.append('NULL')
                elif isinstance(value, str):
                    # Escapar comillas para SQL
                    escaped = value.replace("'", "''")
                    values.append(f"'{escaped}'")
                elif isinstance(value, bool):
                    values.append('TRUE' if value else 'FALSE')
                else:
                    values.append(str(value))
            
            f.write(f"INSERT INTO songs VALUES ({', '.join(values)});\n")
    
    print(f"\n🗄️ Archivos para base de datos generados:")
    print(f"  📄 JSON (NoSQL): {json_file}")
    print(f"  📊 CSV (Import): {csv_file}")
    print(f"  🗃️ SQL Scripts: {sql_file}")
    print(f"  🎵 Total registros: {len(songs_for_db)}")
    
    return json_file, csv_file, sql_file

if __name__ == "__main__":
    print("🧹 LIMPIEZA Y PREPARACIÓN PARA BASE DE DATOS")
    print("=" * 60)
    
    # Paso 1: Limpiar canciones vacías
    clean_file, total_songs = clean_empty_songs()
    
    if clean_file and total_songs > 0:
        print(f"\n📦 Preparando archivos para base de datos...")
        export_for_database(clean_file)
        
        print(f"\n✅ Proceso completado exitosamente!")
        print(f"   🎵 {total_songs} canciones válidas listas para BD")
    else:
        print("❌ Error en el proceso de limpieza")
