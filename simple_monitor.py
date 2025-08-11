#!/usr/bin/env python3
"""
Monitor simple de procesamiento
"""

import time
import os
from pymongo import MongoClient
import logging

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - MONITOR - %(message)s'
)
logger = logging.getLogger(__name__)

def check_mongodb_progress():
    """Verificar progreso en MongoDB"""
    try:
        # Usar configuración del servidor
        MONGODB_URI = os.getenv('MONGODB_URI', "mongodb+srv://admin:Wwc8mSrm7WhfHbu1@notez.lwzox.mongodb.net/?retryWrites=true&w=majority&appName=Notez")
        DATABASE_NAME = os.getenv('DATABASE_NAME', "ml-workshop")
        COLLECTION_NAME = os.getenv('COLLECTION_NAME', "songs")
        
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        
        # Contar documentos totales
        total_count = collection.count_documents({})
        
        # Contar documentos con Spotify
        spotify_found_count = collection.count_documents({"spotify_found": True})
        spotify_not_found_count = collection.count_documents({"spotify_found": False})
        
        # Últimos documentos procesados
        latest_docs = list(collection.find().sort("processed_date", -1).limit(3))
        
        client.close()
        
        return {
            'total': total_count,
            'spotify_found': spotify_found_count,
            'spotify_not_found': spotify_not_found_count,
            'latest_docs': latest_docs
        }
    except Exception as e:
        logger.error(f"Error conectando a MongoDB: {e}")
        return None

def simple_monitor(interval=30):
    """Monitor simple"""
    logger.info("🔍 MONITOR SIMPLE DE PROCESAMIENTO")
    logger.info(f"   Verificando cada {interval} segundos")
    logger.info("=" * 50)
    
    last_count = 0
    start_time = time.time()
    
    while True:
        try:
            progress = check_mongodb_progress()
            
            if progress:
                current_count = progress['total']
                new_docs = current_count - last_count
                elapsed_time = time.time() - start_time
                docs_per_min = (current_count / elapsed_time) * 60 if elapsed_time > 0 else 0
                
                logger.info("📊 PROGRESO ACTUAL:")
                logger.info(f"   📄 Total documentos: {current_count:,}")
                logger.info(f"   📈 Nuevos: +{new_docs}")
                logger.info(f"   🎵 Spotify encontradas: {progress['spotify_found']:,}")
                logger.info(f"   ⚠️ Spotify no encontradas: {progress['spotify_not_found']:,}")
                logger.info(f"   ⚡ Velocidad: {docs_per_min:.1f} docs/min")
                
                # ETA aproximado
                if docs_per_min > 0 and current_count < 26291:
                    remaining = 26291 - current_count
                    eta_minutes = remaining / docs_per_min
                    logger.info(f"   ⏰ ETA: {eta_minutes:.0f} min (~{eta_minutes/60:.1f}h)")
                
                # Mostrar últimas canciones procesadas
                if progress['latest_docs']:
                    logger.info("   🎶 Últimas canciones:")
                    for doc in progress['latest_docs'][:2]:
                        artist = doc.get('artist', 'Unknown')[:20]
                        song = doc.get('song_title', 'Unknown')[:25]
                        spotify_status = "✅" if doc.get('spotify_found') else "⚠️"
                        logger.info(f"      {spotify_status} {artist} - {song}")
                
                last_count = current_count
                
                # Verificar si terminó
                if current_count >= 26290:
                    logger.info("🎉 ¡PROCESAMIENTO COMPLETADO!")
                    break
            else:
                logger.warning("❌ No se pudo obtener progreso de MongoDB")
            
            logger.info("-" * 50)
            time.sleep(interval)
            
        except KeyboardInterrupt:
            logger.info("⏹️ Monitor detenido")
            break
        except Exception as e:
            logger.error(f"Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    import sys
    
    # Cargar configuración del servidor
    try:
        exec(open('server_config.sh').read().replace('export ', '').replace('=', ' = ').replace('$', ''))
    except:
        pass
    
    interval = 30
    if len(sys.argv) > 1:
        try:
            interval = int(sys.argv[1])
        except ValueError:
            pass
    
    simple_monitor(interval)
