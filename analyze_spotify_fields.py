#!/usr/bin/env python3
"""
VERIFICACIÓN DE CAMPOS DE SPOTIFY EN MONGODB
Analiza qué datos de Spotify están disponibles en la base de datos
"""

from pymongo import MongoClient
from mongodb_config import get_mongodb_uri, get_database_name, get_collection_name
import json

def analyze_spotify_fields():
    """Analizar campos de Spotify disponibles"""
    
    print("🔍 ANÁLISIS DE CAMPOS DE SPOTIFY EN MONGODB")
    print("=" * 50)
    
    client = MongoClient(get_mongodb_uri())
    db = client[get_database_name()]
    collection = db[get_collection_name()]
    
    total_docs = collection.count_documents({})
    print(f"📊 Total documentos: {total_docs:,}")
    
    # Verificar campos específicos de Spotify
    spotify_fields = [
        'popularity', 'explicit_content', 'spotify_found', 'energy', 
        'danceability', 'valence', 'duration_ms', 'release_date',
        'speechiness', 'acousticness', 'instrumentalness', 'liveness',
        'loudness', 'tempo', 'key', 'mode', 'time_signature', 'is_estimated'
    ]
    
    print("\n🎵 ANÁLISIS DE CAMPOS DE SPOTIFY:")
    print("-" * 40)
    
    for field in spotify_fields:
        # Contar documentos que tienen este campo
        with_field = collection.count_documents({field: {"$exists": True, "$ne": None}})
        percentage = (with_field / total_docs * 100) if total_docs > 0 else 0
        
        print(f"   {field:<20}: {with_field:>6,} ({percentage:>5.1f}%)")
        
        # Mostrar valores de ejemplo
        if with_field > 0:
            sample = collection.find_one({field: {"$exists": True, "$ne": None}})
            if sample and field in sample:
                value = sample[field]
                print(f"   {' '*20}   Ejemplo: {value}")
    
    print("\n📋 MUESTRA DE DOCUMENTOS CON CAMPOS SPOTIFY:")
    print("-" * 50)
    
    # Buscar documentos que tengan campos de Spotify
    docs_with_spotify = list(collection.find({
        "$or": [
            {"popularity": {"$exists": True}},
            {"explicit_content": {"$exists": True}},
            {"spotify_found": {"$exists": True}},
            {"energy": {"$exists": True}}
        ]
    }).limit(3))
    
    for i, doc in enumerate(docs_with_spotify, 1):
        print(f"\n{i}. {doc.get('artist', 'N/A')} - {doc.get('song_title', 'N/A')}")
        print(f"   Género: {doc.get('genre', 'N/A')}")
        
        # Mostrar campos de Spotify presentes
        spotify_data = {}
        for field in spotify_fields:
            if field in doc and doc[field] is not None:
                spotify_data[field] = doc[field]
        
        if spotify_data:
            print("   Datos Spotify:")
            for key, value in spotify_data.items():
                print(f"      {key}: {value}")
        else:
            print("   ❌ Sin datos de Spotify")
    
    print("\n🔍 ANÁLISIS DETALLADO DE POPULARITY:")
    print("-" * 40)
    
    # Analizar popularity específicamente
    popularity_stats = list(collection.aggregate([
        {"$match": {"popularity": {"$exists": True, "$ne": None}}},
        {"$group": {
            "_id": None,
            "count": {"$sum": 1},
            "avg": {"$avg": "$popularity"},
            "min": {"$min": "$popularity"},
            "max": {"$max": "$popularity"}
        }}
    ]))
    
    if popularity_stats:
        stats = popularity_stats[0]
        print(f"   Canciones con popularity: {stats['count']:,}")
        print(f"   Promedio: {stats['avg']:.2f}")
        print(f"   Mínimo: {stats['min']}")
        print(f"   Máximo: {stats['max']}")
    else:
        print("   ❌ No se encontraron datos de popularity")
    
    print("\n🔍 ANÁLISIS DETALLADO DE EXPLICIT_CONTENT:")
    print("-" * 45)
    
    # Analizar explicit_content
    explicit_stats = list(collection.aggregate([
        {"$match": {"explicit_content": {"$exists": True, "$ne": None}}},
        {"$group": {
            "_id": "$explicit_content",
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}}
    ]))
    
    if explicit_stats:
        for stat in explicit_stats:
            print(f"   {stat['_id']}: {stat['count']:,} canciones")
    else:
        print("   ❌ No se encontraron datos de explicit_content")
    
    # Buscar el archivo original para verificar
    print("\n🔍 VERIFICANDO ARCHIVO ORIGINAL:")
    print("-" * 35)
    
    try:
        import pickle
        with open('spanish_songs_server_final.pickle', 'rb') as f:
            original_data = pickle.load(f)
        
        # Buscar una canción con datos de Spotify en el archivo original
        found_spotify_example = False
        for genre_data in original_data.values():
            if found_spotify_example:
                break
            for artist_songs in genre_data.values():
                if isinstance(artist_songs, dict):
                    for song_data in artist_songs.values():
                        if isinstance(song_data, dict):
                            if 'popularity' in song_data or 'spotify_found' in song_data:
                                print("   ✅ Ejemplo encontrado en archivo original:")
                                print(f"   Artista: {song_data.get('artist', 'N/A')}")
                                print(f"   Canción: {song_data.get('song_title', 'N/A')}")
                                print(f"   Popularity: {song_data.get('popularity', 'N/A')}")
                                print(f"   Explicit: {song_data.get('explicit_content', 'N/A')}")
                                print(f"   Spotify found: {song_data.get('spotify_found', 'N/A')}")
                                found_spotify_example = True
                                break
        
        if not found_spotify_example:
            print("   ❌ No se encontraron datos de Spotify en archivo original")
            
    except FileNotFoundError:
        print("   ❌ Archivo spanish_songs_server_final.pickle no encontrado")
    except Exception as e:
        print(f"   ❌ Error leyendo archivo: {e}")
    
    client.close()

if __name__ == "__main__":
    analyze_spotify_fields()
