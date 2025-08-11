#!/usr/bin/env python3
"""
Monitor simple para procesamiento JSON en servidor
"""

import time
import os
import json
from pathlib import Path
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - MONITOR - %(message)s'
)
logger = logging.getLogger(__name__)

def monitor_json_progress(interval=20):
    """Monitor para archivos JSON"""
    logger.info("🔍 MONITOR DE PROCESAMIENTO JSON")
    logger.info(f"   Verificando cada {interval} segundos")
    logger.info("=" * 50)
    
    json_dir = Path("json_output")
    last_count = 0
    start_time = time.time()
    
    while True:
        try:
            if json_dir.exists():
                # Contar archivos JSON
                json_files = list(json_dir.glob("spanish_songs_batch_*.json"))
                current_count = len(json_files)
                
                # Contar documentos totales
                total_docs = 0
                for json_file in json_files:
                    try:
                        with open(json_file, 'r') as f:
                            data = json.load(f)
                            total_docs += len(data)
                    except:
                        continue
                
                # Estadísticas
                new_files = current_count - last_count
                elapsed_time = time.time() - start_time
                files_per_min = (current_count / elapsed_time) * 60 if elapsed_time > 0 else 0
                
                logger.info("📊 PROGRESO ACTUAL:")
                logger.info(f"   📄 Archivos JSON: {current_count}")
                logger.info(f"   📈 Nuevos archivos: +{new_files}")
                logger.info(f"   🎵 Total documentos: {total_docs:,}")
                logger.info(f"   ⚡ Velocidad: {files_per_min:.1f} archivos/min")
                logger.info("   🎯 SOLO DATOS REALES DE SPOTIFY")
                
                # Verificar archivo de resumen
                summary_file = json_dir / "processing_summary.json"
                if summary_file.exists():
                    try:
                        with open(summary_file, 'r') as f:
                            summary = json.load(f)
                        expected_files = summary.get('total_files', 0)
                        if expected_files > 0:
                            progress = (current_count / expected_files) * 100
                            logger.info(f"   📊 Progreso: {progress:.1f}% ({current_count}/{expected_files})")
                    except:
                        pass
                
                # Verificar si el procesamiento terminó
                if summary_file.exists() and current_count > 0:
                    try:
                        with open(summary_file, 'r') as f:
                            summary = json.load(f)
                        if current_count >= summary.get('total_files', 0):
                            logger.info("🎉 ¡PROCESAMIENTO COMPLETADO!")
                            logger.info(f"   📂 Total archivos: {current_count}")
                            logger.info(f"   📊 Total documentos: {summary.get('total_documents', 0):,}")
                            break
                    except:
                        pass
                
                last_count = current_count
                
            else:
                logger.info("⏳ Esperando que se cree el directorio json_output...")
            
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
    
    interval = 20
    if len(sys.argv) > 1:
        try:
            interval = int(sys.argv[1])
        except ValueError:
            pass
    
    monitor_json_progress(interval)
