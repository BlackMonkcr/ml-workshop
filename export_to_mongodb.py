#!/usr/bin/env python3
"""
EXPORTADOR A MONGODB ATLAS
Exporta el dataset procesado del servidor a tu cluster MongoDB
"""

import pickle
import json
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import BulkWriteError, DuplicateKeyError
import logging
import sys
from tqdm import tqdm

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('mongodb_export.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuración MongoDB
MONGODB_URI = "mongodb+srv://admin:Wwc8mSrm7WhfHbu1@notez.lwzox.mongodb.net/?retryWrites=true&w=majority&appName=Notez"
DATABASE_NAME = "ml-workshop"
COLLECTION_NAME = "songs"

def clean_song_data(song_data):
    """Limpiar y preparar datos para MongoDB"""
    cleaned_data = {}
    
    # Campos básicos
    cleaned_data['artist'] = song_data.get('artist', '').strip()
    cleaned_data['song_title'] = song_data.get('song_title', '').strip()
    cleaned_data['genre'] = song_data.get('genre', '').strip()
    cleaned_data['lyrics'] = song_data.get('lyrics', '').strip()
    cleaned_data['composer'] = song_data.get('composer', '').strip()
    
    # Emoción extraída
    cleaned_data['emotion'] = song_data.get('emotion', 'unknown')
    
    # Datos de Spotify (si existen)
    spotify_fields = [
        'spotify_found', 'popularity', 'explicit_content', 'duration_ms',
        'release_date', 'energy', 'danceability', 'valence', 'speechiness',
        'acousticness', 'instrumentalness', 'liveness', 'loudness', 'tempo',
        'key', 'mode', 'time_signature', 'is_estimated'
    ]
    
    for field in spotify_fields:
        if field in song_data:
            cleaned_data[field] = song_data[field]
    
    # Metadatos
    cleaned_data['processed_date'] = song_data.get('processed_date', datetime.now().isoformat())
    cleaned_data['source'] = 'server_48_cores_processing'
    cleaned_data['dataset_version'] = 'v2.0'
    
    # Crear ID único
    artist_clean = cleaned_data['artist'].lower().replace(' ', '_')
    song_clean = cleaned_data['song_title'].lower().replace(' ', '_')
    cleaned_data['unique_id'] = f"{artist_clean}_{song_clean}_{cleaned_data['genre']}"
    
    return cleaned_data

def export_to_mongodb(input_file="spanish_songs_server_final.pickle", batch_size=1000):
    """Exportar dataset a MongoDB Atlas"""
    
    logger.info("🚀 INICIANDO EXPORTACIÓN A MONGODB ATLAS")
    logger.info(f"📁 Archivo: {input_file}")
    logger.info(f"🗄️ Base de datos: {DATABASE_NAME}")
    logger.info(f"📦 Colección: {COLLECTION_NAME}")
    
    # Conectar a MongoDB
    try:
        logger.info("🔌 Conectando a MongoDB Atlas...")
        client = MongoClient(MONGODB_URI)
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        
        # Test de conexión
        client.admin.command('ismaster')
        logger.info("✅ Conexión exitosa a MongoDB Atlas")
        
    except Exception as e:
        logger.error(f"❌ Error conectando a MongoDB: {e}")
        return False
    
    # Cargar datos
    logger.info("📂 Cargando archivo procesado...")
    try:
        with open(input_file, 'rb') as f:
            data = pickle.load(f)
        logger.info(f"✅ Archivo cargado: {len(data)} géneros")
    except Exception as e:
        logger.error(f"❌ Error cargando archivo: {e}")
        return False
    
    # Convertir a documentos MongoDB
    logger.info("🔄 Convirtiendo datos a documentos MongoDB...")
    documents = []
    total_songs = 0
    
    for genre_name, genre_data in data.items():
        if isinstance(genre_data, dict):
            for artist_path, artist_songs in genre_data.items():
                if isinstance(artist_songs, dict):
                    for song_key, song_data in artist_songs.items():
                        if isinstance(song_data, dict):
                            doc = clean_song_data(song_data)
                            documents.append(doc)
                            total_songs += 1
    
    logger.info(f"📊 Total documentos preparados: {total_songs:,}")
    
    # Crear índice único
    try:
        collection.create_index([("unique_id", 1)], unique=True)
        logger.info("🔍 Índice único creado en 'unique_id'")
    except Exception as e:
        logger.info(f"ℹ️ Índice ya existe: {e}")
    
    # Insertar en lotes
    logger.info(f"📤 Insertando documentos en lotes de {batch_size}...")
    inserted_count = 0
    updated_count = 0
    error_count = 0
    
    with tqdm(total=len(documents), desc="Insertando en MongoDB") as pbar:
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i+batch_size]
            
            try:
                # Usar upsert para evitar duplicados
                operations = []
                for doc in batch:
                    operations.append({
                        'replaceOne': {
                            'filter': {'unique_id': doc['unique_id']},
                            'replacement': doc,
                            'upsert': True
                        }
                    })
                
                result = collection.bulk_write(operations, ordered=False)
                inserted_count += result.upserted_count
                updated_count += result.modified_count
                
            except BulkWriteError as e:
                error_count += len(e.details['writeErrors'])
                logger.warning(f"⚠️ Errores en lote: {len(e.details['writeErrors'])}")
                
            except Exception as e:
                error_count += len(batch)
                logger.error(f"❌ Error en lote: {e}")
            
            pbar.update(len(batch))
    
    # Estadísticas finales
    final_count = collection.count_documents({})
    
    logger.info("")
    logger.info("✅ EXPORTACIÓN COMPLETADA")
    logger.info(f"📊 Estadísticas:")
    logger.info(f"   📝 Documentos insertados: {inserted_count:,}")
    logger.info(f"   🔄 Documentos actualizados: {updated_count:,}")
    logger.info(f"   ❌ Errores: {error_count:,}")
    logger.info(f"   📚 Total en colección: {final_count:,}")
    logger.info(f"   🗄️ Base de datos: {DATABASE_NAME}")
    logger.info(f"   📦 Colección: {COLLECTION_NAME}")
    
    # Estadísticas de la colección
    logger.info("")
    logger.info("📈 Estadísticas de la colección:")
    
    # Por género
    genre_stats = collection.aggregate([
        {"$group": {"_id": "$genre", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ])
    
    logger.info("   🎵 Top 10 géneros:")
    for stat in genre_stats:
        logger.info(f"      {stat['_id']}: {stat['count']:,} canciones")
    
    # Por emoción
    emotion_stats = collection.aggregate([
        {"$group": {"_id": "$emotion", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ])
    
    logger.info("   😊 Distribución de emociones:")
    for stat in emotion_stats:
        logger.info(f"      {stat['_id']}: {stat['count']:,} canciones")
    
    client.close()
    logger.info("🔌 Conexión cerrada")
    
    return True

def verify_mongodb_data():
    """Verificar datos en MongoDB"""
    logger.info("🔍 VERIFICANDO DATOS EN MONGODB")
    
    try:
        client = MongoClient(MONGODB_URI)
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        
        # Contar documentos
        total = collection.count_documents({})
        logger.info(f"📊 Total documentos: {total:,}")
        
        # Muestra de documento
        sample = collection.find_one()
        if sample:
            logger.info("📄 Documento de muestra:")
            logger.info(f"   Artista: {sample.get('artist')}")
            logger.info(f"   Canción: {sample.get('song_title')}")
            logger.info(f"   Género: {sample.get('genre')}")
            logger.info(f"   Emoción: {sample.get('emotion')}")
            logger.info(f"   Campos: {len(sample)} campos")
        
        client.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error verificando datos: {e}")
        return False

if __name__ == "__main__":
    logger.info("🗄️ EXPORTADOR A MONGODB ATLAS")
    logger.info("=" * 50)
    
    # Exportar
    success = export_to_mongodb()
    
    if success:
        # Verificar
        verify_mongodb_data()
        logger.info("")
        logger.info("🎉 ¡EXPORTACIÓN EXITOSA!")
        logger.info("🌐 Datos disponibles en MongoDB Atlas")
        logger.info(f"📱 Connection String: mongodb+srv://admin:***@notez.lwzox.mongodb.net/{DATABASE_NAME}")
        
    else:
        logger.error("❌ Exportación falló")
        sys.exit(1)
