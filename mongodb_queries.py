#!/usr/bin/env python3
"""
CONSULTAS Y VERIFICACIÓN DE MONGODB ATLAS
"""

from pymongo import MongoClient
from mongodb_config import get_mongodb_uri, get_database_name, get_collection_name
import json
from datetime import datetime

def connect_and_query():
    """Conectar y hacer consultas de ejemplo"""
    
    print("🔌 Conectando a MongoDB Atlas...")
    client = MongoClient(get_mongodb_uri())
    db = client[get_database_name()]
    collection = db[get_collection_name()]
    
    print("✅ Conexión exitosa!")
    print(f"📚 Base de datos: {get_database_name()}")
    print(f"📦 Colección: {get_collection_name()}")
    print()
    
    # Estadísticas generales
    total_docs = collection.count_documents({})
    print(f"📊 Total documentos: {total_docs:,}")
    
    # Muestra de documentos
    print("\n📄 Muestra de documentos:")
    sample_docs = list(collection.find().limit(3))
    for i, doc in enumerate(sample_docs, 1):
        print(f"\n{i}. {doc.get('artist')} - {doc.get('song_title')}")
        print(f"   Género: {doc.get('genre')}")
        print(f"   Emoción: {doc.get('emotion')}")
        print(f"   Letras (preview): {doc.get('lyrics', '')[:100]}...")
    
    # Top géneros
    print("\n🎵 Top 10 Géneros:")
    genres = collection.aggregate([
        {"$group": {"_id": "$genre", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ])
    for genre in genres:
        print(f"   {genre['_id']}: {genre['count']:,} canciones")
    
    # Top artistas
    print("\n🎤 Top 10 Artistas:")
    artists = collection.aggregate([
        {"$group": {"_id": "$artist", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ])
    for artist in artists:
        print(f"   {artist['_id']}: {artist['count']:,} canciones")
    
    # Distribución de emociones
    print("\n😊 Emociones:")
    emotions = collection.aggregate([
        {"$group": {"_id": "$emotion", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ])
    for emotion in emotions:
        print(f"   {emotion['_id']}: {emotion['count']:,}")
    
    # Consultas específicas
    print("\n🔍 Consultas específicas:")
    
    # Canciones de reggaeton
    reggaeton_count = collection.count_documents({"genre": "reggaeton"})
    print(f"   Reggaeton: {reggaeton_count:,} canciones")
    
    # Canciones alegres (joy)
    joy_count = collection.count_documents({"emotion": "joy"})
    print(f"   Canciones alegres: {joy_count:,}")
    
    # Artistas únicos
    unique_artists = len(collection.distinct("artist"))
    print(f"   Artistas únicos: {unique_artists:,}")
    
    # Géneros únicos
    unique_genres = len(collection.distinct("genre"))
    print(f"   Géneros únicos: {unique_genres:,}")
    
    print("\n🎯 Consultas de ejemplo:")
    
    # Buscar por artista específico
    print("📍 Ejemplo: Canciones de Bad Bunny")
    bad_bunny = list(collection.find({"artist": {"$regex": "Bad Bunny", "$options": "i"}}).limit(3))
    for song in bad_bunny:
        print(f"   - {song.get('song_title')} ({song.get('genre')})")
    
    # Buscar flamenco alegre
    print("📍 Ejemplo: Flamenco con emoción 'joy'")
    flamenco_joy = list(collection.find({"genre": "flamenco", "emotion": "joy"}).limit(3))
    for song in flamenco_joy:
        print(f"   - {song.get('artist')} - {song.get('song_title')}")
    
    client.close()
    print("\n🔌 Conexión cerrada")

def export_sample_json():
    """Exportar una muestra pequeña a JSON para revisión"""
    client = MongoClient(get_mongodb_uri())
    db = client[get_database_name()]
    collection = db[get_collection_name()]
    
    # Obtener muestra variada
    sample = list(collection.aggregate([
        {"$sample": {"size": 50}},  # 50 canciones aleatorias
        {"$project": {
            "_id": 0,
            "artist": 1,
            "song_title": 1,
            "genre": 1,
            "emotion": 1,
            "lyrics": {"$substr": ["$lyrics", 0, 200]}  # Solo primeros 200 caracteres
        }}
    ]))
    
    # Guardar muestra
    with open('mongodb_sample.json', 'w', encoding='utf-8') as f:
        json.dump(sample, f, ensure_ascii=False, indent=2)
    
    print(f"📁 Muestra exportada: mongodb_sample.json ({len(sample)} canciones)")
    client.close()

if __name__ == "__main__":
    print("🗄️ VERIFICACIÓN DE MONGODB ATLAS")
    print("=" * 50)
    
    try:
        # Consultas principales
        connect_and_query()
        
        # Exportar muestra
        print()
        export_sample_json()
        
        print()
        print("🎉 ¡Verificación completada!")
        print("🌐 Datos correctamente almacenados en MongoDB Atlas")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
