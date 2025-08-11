#!/usr/bin/env python3
"""
Monitor de procesamiento en servidor
Ejecutar en paralelo para monitorear el progreso
"""

import time
import os
import psutil
import requests
from pymongo import MongoClient
import logging

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - MONITOR - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración MongoDB
MONGODB_URI = os.getenv('MONGODB_URI', "mongodb://localhost:27017/")
DATABASE_NAME = os.getenv('DATABASE_NAME', "ml-workshop")
COLLECTION_NAME = os.getenv('COLLECTION_NAME', "songs")

def get_system_stats():
    """Obtener estadísticas del sistema"""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    
    # Buscar proceso Python
    python_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            if 'python' in proc.info['name'].lower():
                python_processes.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    return {
        'cpu_percent': cpu_percent,
        'memory_percent': memory.percent,
        'memory_available_gb': memory.available / (1024**3),
        'python_processes': len(python_processes)
    }

def check_mongodb_count():
    """Verificar cuántos documentos hay en MongoDB"""
    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        
        count = collection.count_documents({})
        client.close()
        return count
    except Exception as e:
        logger.warning(f"No se pudo conectar a MongoDB: {e}")
        return None

def check_spotify_requests():
    """Verificar si se están haciendo requests a Spotify"""
    try:
        # Verificar conexiones de red a Spotify
        connections = psutil.net_connections()
        spotify_connections = [
            conn for conn in connections 
            if conn.raddr and 'api.spotify.com' in str(conn.raddr)
        ]
        return len(spotify_connections)
    except Exception:
        return 0

def monitor_processing(check_interval=30):
    """Monitor principal del procesamiento"""
    logger.info("🔍 INICIANDO MONITOR DE PROCESAMIENTO")
    logger.info(f"   Intervalo de verificación: {check_interval} segundos")
    logger.info("=" * 60)
    
    last_mongo_count = 0
    start_time = time.time()
    
    while True:
        try:
            # Estadísticas del sistema
            sys_stats = get_system_stats()
            
            # Contar documentos en MongoDB
            mongo_count = check_mongodb_count()
            
            # Verificar requests a Spotify
            spotify_requests = check_spotify_requests()
            
            # Calcular progreso
            if mongo_count is not None:
                new_documents = mongo_count - last_mongo_count
                docs_per_min = (mongo_count / (time.time() - start_time)) * 60 if mongo_count > 0 else 0
                
                logger.info("📊 ESTADO DEL PROCESAMIENTO:")
                logger.info(f"   💾 Documentos en MongoDB: {mongo_count:,}")
                logger.info(f"   📈 Nuevos documentos: +{new_documents:,}")
                logger.info(f"   ⚡ Velocidad: {docs_per_min:.1f} docs/min")
                logger.info(f"   🖥️ CPU: {sys_stats['cpu_percent']:.1f}%")
                logger.info(f"   🧠 RAM: {sys_stats['memory_percent']:.1f}% ({sys_stats['memory_available_gb']:.1f}GB disponible)")
                logger.info(f"   🐍 Procesos Python: {sys_stats['python_processes']}")
                logger.info(f"   🎵 Conexiones Spotify: {spotify_requests}")
                
                # Estimar tiempo restante (aproximado)
                if docs_per_min > 0 and mongo_count < 26291:
                    remaining_docs = 26291 - mongo_count
                    eta_minutes = remaining_docs / docs_per_min
                    logger.info(f"   ⏰ ETA: {eta_minutes:.0f} minutos (~{eta_minutes/60:.1f} horas)")
                
                last_mongo_count = mongo_count
            else:
                logger.info("❌ No se pudo conectar a MongoDB para verificar progreso")
            
            logger.info("-" * 60)
            
            # Verificar si el proceso ha terminado
            if mongo_count and mongo_count >= 26290:  # Dataset completo aproximado
                logger.info("🎉 ¡PROCESAMIENTO COMPLETADO!")
                break
                
            time.sleep(check_interval)
            
        except KeyboardInterrupt:
            logger.info("⏹️ Monitor detenido por usuario")
            break
        except Exception as e:
            logger.error(f"❌ Error en monitoreo: {e}")
            time.sleep(10)

if __name__ == "__main__":
    import sys
    
    # Permitir especificar intervalo como argumento
    interval = 30
    if len(sys.argv) > 1:
        try:
            interval = int(sys.argv[1])
        except ValueError:
            logger.warning("Intervalo inválido, usando 30 segundos por defecto")
    
    monitor_processing(interval)
