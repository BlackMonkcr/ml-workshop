#!/usr/bin/env python3
"""
EXPORTADOR SIMPLIFICADO A MONGODB ATLAS
Version corregida con inserciones directas
"""

import pickle
import json
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import BulkWriteError, DuplicateKeyError
import logging
import sys
from tqdm import tqdm
from mongodb_config import get_mongodb_uri, get_database_name, get_collection_name

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('mongodb_export_fixed.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def clean_song_data_simple(song_data, genre, artist, song_title):
    """Limpiar y preparar datos para MongoDB - versión simplificada"""
    
    # Crear documento simple
    doc = {
        'artist': str(artist).strip(),
        'song_title': str(song_title).strip(),
        'genre': str(genre).strip(),
        'lyrics': str(song_data.get('lyrics', '')).strip()[:5000],  # Limitar a 5000 chars
        'composer': str(song_data.get('composer', '')).strip()[:500],  # Limitar
        'emotion': str(song_data.get('emotion', 'unknown')),
        'processed_date': datetime.now().isoformat(),
        'source': 'server_48_cores_processing',
        'dataset_version': 'v2.0'
    }
    
    # Crear ID único simple
    clean_artist = ''.join(c for c in doc['artist'].lower() if c.isalnum())[:20]
    clean_song = ''.join(c for c in doc['song_title'].lower() if c.isalnum())[:20]
    clean_genre = ''.join(c for c in doc['genre'].lower() if c.isalnum())[:15]
    
    doc['unique_id'] = f"{clean_artist}_{clean_song}_{clean_genre}"
    
    # Agregar datos adicionales si existen
    extra_fields = ['popularity', 'energy', 'danceability', 'valence', 'tempo']
    for field in extra_fields:
        if field in song_data and song_data[field] is not None:
            doc[field] = song_data[field]
    
    return doc

def export_to_mongodb_simple(input_file="spanish_songs_server_final.pickle", batch_size=500):
    """Exportar con método simplificado"""
    
    logger.info("🚀 EXPORTACIÓN SIMPLIFICADA A MONGODB")
    logger.info(f"📁 Archivo: {input_file}")
    
    # Conectar a MongoDB
    try:
        client = MongoClient(get_mongodb_uri())
        db = client[get_database_name()]
        collection = db[get_collection_name()]
        
        # Test de conexión
        client.admin.command('ismaster')
        logger.info("✅ Conexión exitosa a MongoDB Atlas")
        
        # Limpiar colección existente
        collection.drop()
        logger.info("🗑️ Colección anterior eliminada")
        
    except Exception as e:
        logger.error(f"❌ Error conectando: {e}")
        return False
    
    # Cargar datos
    try:
        with open(input_file, 'rb') as f:
            data = pickle.load(f)
        logger.info(f"✅ Archivo cargado: {len(data)} géneros")
    except Exception as e:
        logger.error(f"❌ Error cargando: {e}")
        return False
    
    # Procesar datos
    documents = []
    total_processed = 0
    
    for genre_name, genre_data in tqdm(data.items(), desc="Procesando géneros"):
        if not isinstance(genre_data, dict):
            continue
            
        for artist_path, artist_songs in genre_data.items():
            if not isinstance(artist_songs, dict):
                continue
                
            # Limpiar nombre de artista
            artist_name = artist_path.strip('/').replace('-', ' ').title()
            
            for song_key, song_data in artist_songs.items():
                if not isinstance(song_data, dict):
                    continue
                    
                # Limpiar título de canción
                song_title = song_key.strip('/').replace('-', ' ').title()
                
                try:
                    doc = clean_song_data_simple(song_data, genre_name, artist_name, song_title)
                    documents.append(doc)
                    total_processed += 1
                    
                except Exception as e:
                    logger.warning(f"Error procesando canción: {e}")
                    continue
    
    logger.info(f"📊 Total documentos preparados: {total_processed:,}")
    
    # Insertar en lotes
    inserted_total = 0
    error_total = 0
    
    logger.info("📤 Insertando documentos...")
    
    with tqdm(total=len(documents), desc="Insertando") as pbar:
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i+batch_size]
            
            try:
                result = collection.insert_many(batch, ordered=False)
                inserted_total += len(result.inserted_ids)
                
            except BulkWriteError as e:
                inserted_total += e.details['nInserted']
                error_total += len(e.details['writeErrors'])
                
            except Exception as e:
                logger.error(f"Error en lote: {e}")
                error_total += len(batch)
            
            pbar.update(len(batch))
    
    # Crear índices
    try:
        collection.create_index([("unique_id", 1)], unique=True)
        collection.create_index([("genre", 1)])
        collection.create_index([("artist", 1)])
        collection.create_index([("emotion", 1)])
        logger.info("🔍 Índices creados")
    except Exception as e:
        logger.warning(f"Error creando índices: {e}")
    
    # Estadísticas finales
    final_count = collection.count_documents({})
    
    logger.info("")
    logger.info("✅ EXPORTACIÓN COMPLETADA")
    logger.info(f"📊 Estadísticas finales:")
    logger.info(f"   📝 Documentos insertados: {inserted_total:,}")
    logger.info(f"   ❌ Errores: {error_total:,}")
    logger.info(f"   📚 Total en colección: {final_count:,}")
    logger.info(f"   🗄️ Base: {get_database_name()}")
    logger.info(f"   📦 Colección: {get_collection_name()}")
    
    # Estadísticas por género
    if final_count > 0:
        logger.info("")
        logger.info("📈 Top 10 géneros:")
        
        genre_stats = collection.aggregate([
            {"$group": {"_id": "$genre", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ])
        
        for stat in genre_stats:
            logger.info(f"   🎵 {stat['_id']}: {stat['count']:,} canciones")
        
        # Emociones
        logger.info("")
        logger.info("😊 Distribución de emociones:")
        
        emotion_stats = collection.aggregate([
            {"$group": {"_id": "$emotion", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ])
        
        for stat in emotion_stats:
            logger.info(f"   {stat['_id']}: {stat['count']:,}")
    
    client.close()
    return final_count > 0

if __name__ == "__main__":
    logger.info("🗄️ EXPORTADOR SIMPLIFICADO A MONGODB")
    
    success = export_to_mongodb_simple()
    
    if success:
        logger.info("")
        logger.info("🎉 ¡EXPORTACIÓN EXITOSA!")
        logger.info("🌐 Datos disponibles en tu cluster MongoDB Atlas")
        logger.info("🔗 Cluster: notez.lwzox.mongodb.net")
        logger.info("📚 Base de datos: ml-workshop")
        logger.info("📦 Colección: songs")
    else:
        logger.error("❌ Exportación falló")
        sys.exit(1)
