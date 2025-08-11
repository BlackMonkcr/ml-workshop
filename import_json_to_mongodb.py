#!/usr/bin/env python3
"""
IMPORTAR ARCHIVOS JSON A MONGODB
Script para ejecutar en tu PC local e importar los JSON del servidor a MongoDB
"""

import json
import os
from pathlib import Path
from pymongo import MongoClient
from pymongo.errors import BulkWriteError
import logging
from tqdm import tqdm
import sys

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración MongoDB
MONGODB_URI = "mongodb+srv://admin:Wwc8mSrm7WhfHbu1@notez.lwzox.mongodb.net/?retryWrites=true&w=majority&appName=Notez"
DATABASE_NAME = "ml-workshop"
COLLECTION_NAME = "songs"

def import_json_to_mongodb(json_dir: str = "json_output"):
    """Importar archivos JSON a MongoDB"""
    
    logger.info("🔄 IMPORTANDO ARCHIVOS JSON A MONGODB ATLAS")
    logger.info("=" * 60)
    
    # Verificar directorio
    json_path = Path(json_dir)
    if not json_path.exists():
        logger.error(f"❌ Directorio no encontrado: {json_dir}")
        logger.info("💡 Asegúrate de haber copiado los archivos JSON del servidor")
        return False
    
    # Buscar archivos JSON
    json_files = list(json_path.glob("spanish_songs_batch_*.json"))
    if not json_files:
        logger.error(f"❌ No se encontraron archivos JSON en: {json_dir}")
        return False
    
    json_files.sort()  # Ordenar por nombre
    logger.info(f"📂 Encontrados {len(json_files)} archivos JSON")
    
    # Leer resumen si existe
    summary_file = json_path / "processing_summary.json"
    if summary_file.exists():
        with open(summary_file, 'r', encoding='utf-8') as f:
            summary = json.load(f)
        logger.info(f"📊 Resumen del procesamiento:")
        logger.info(f"   Fecha: {summary.get('processing_date', 'N/A')}")
        logger.info(f"   Total documentos: {summary.get('total_documents', 0):,}")
        logger.info(f"   Versión dataset: {summary.get('dataset_version', 'N/A')}")
    
    try:
        # Conectar a MongoDB
        logger.info("🔌 Conectando a MongoDB Atlas...")
        client = MongoClient(MONGODB_URI)
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        
        # Probar conexión
        client.admin.command('hello')
        logger.info("✅ Conexión exitosa")
        
        # Limpiar colección
        logger.info("🗑️ Limpiando colección existente...")
        collection.drop()
        
        # Procesar archivos
        total_imported = 0
        
        for json_file in tqdm(json_files, desc="Importando archivos"):
            try:
                # Cargar datos del archivo
                with open(json_file, 'r', encoding='utf-8') as f:
                    documents = json.load(f)
                
                if not documents:
                    logger.warning(f"⚠️ Archivo vacío: {json_file.name}")
                    continue
                
                # Insertar en lotes
                try:
                    result = collection.insert_many(documents, ordered=False)
                    imported_count = len(result.inserted_ids)
                    total_imported += imported_count
                    
                    logger.info(f"✅ {json_file.name}: {imported_count:,} documentos")
                    
                except BulkWriteError as e:
                    # Algunos documentos pueden fallar, pero continuar
                    imported_count = len(documents) - len(e.details.get('writeErrors', []))
                    total_imported += imported_count
                    logger.warning(f"⚠️ {json_file.name}: {imported_count:,} documentos (con algunos errores)")
                
            except Exception as e:
                logger.error(f"❌ Error procesando {json_file.name}: {e}")
        
        # Crear índices
        logger.info("📇 Creando índices...")
        collection.create_index([("genre", 1)])
        collection.create_index([("artist", 1)])
        collection.create_index([("popularity", 1)])
        collection.create_index([("explicit_content", 1)])
        collection.create_index([("energy", 1)])
        collection.create_index([("danceability", 1)])
        collection.create_index([("valence", 1)])
        collection.create_index([("unique_id", 1)], unique=True)
        
        # Verificar importación
        final_count = collection.count_documents({})
        
        logger.info("\n🎉 IMPORTACIÓN COMPLETADA")
        logger.info(f"✅ Documentos importados: {total_imported:,}")
        logger.info(f"✅ Documentos en BD: {final_count:,}")
        logger.info(f"📊 Base de datos: {DATABASE_NAME}")
        logger.info(f"📊 Colección: {COLLECTION_NAME}")
        
        client.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error de conexión o importación: {e}")
        return False

def verify_import():
    """Verificar la importación"""
    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        
        # Estadísticas básicas
        total = collection.count_documents({})
        spotify_found = collection.count_documents({"spotify_found": True})
        genres_count = len(collection.distinct("genre"))
        artists_count = len(collection.distinct("artist"))
        
        logger.info("\n📊 VERIFICACIÓN DE LA IMPORTACIÓN:")
        logger.info(f"   Total canciones: {total:,}")
        logger.info(f"   Con Spotify: {spotify_found:,} ({(spotify_found/total)*100:.1f}%)")
        logger.info(f"   Géneros únicos: {genres_count}")
        logger.info(f"   Artistas únicos: {artists_count}")
        
        # Mostrar algunos ejemplos
        sample_docs = list(collection.find().limit(3))
        logger.info("\n🎵 Ejemplos de canciones importadas:")
        for doc in sample_docs:
            spotify_status = "✅" if doc.get('spotify_found') else "⚠️"
            logger.info(f"   {spotify_status} {doc.get('artist', 'N/A')} - {doc.get('song_title', 'N/A')} ({doc.get('genre', 'N/A')})")
        
        client.close()
        
    except Exception as e:
        logger.error(f"Error en verificación: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Importar archivos JSON a MongoDB')
    parser.add_argument('--json-dir', default='json_output', 
                        help='Directorio con archivos JSON (default: json_output)')
    parser.add_argument('--verify-only', action='store_true',
                        help='Solo verificar datos existentes en MongoDB')
    
    args = parser.parse_args()
    
    if args.verify_only:
        verify_import()
    else:
        success = import_json_to_mongodb(args.json_dir)
        
        if success:
            logger.info("\n🔍 Ejecutando verificación...")
            verify_import()
        else:
            logger.error("❌ Importación fallida")
            sys.exit(1)
