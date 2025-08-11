#!/usr/bin/env python3
"""
SCRIPT COMPLETO: LIMPIEZA + EXPORTACIÓN A MONGODB
Procesa el dataset del servidor con limpieza avanzada de letras y exporta a MongoDB Atlas
"""

import pickle
import json
import re
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import BulkWriteError
import logging
import sys
from tqdm import tqdm

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('prepare_and_export.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuración MongoDB
MONGODB_URI = "mongodb+srv://admin:Wwc8mSrm7WhfHbu1@notez.lwzox.mongodb.net/?retryWrites=true&w=majority&appName=Notez"
DATABASE_NAME = "ml-workshop"
COLLECTION_NAME = "songs"

def clean_lyrics_text(lyrics: str) -> str:
    """
    Limpia el texto de las letras eliminando contenido HTML y navegación
    """
    if not lyrics or not isinstance(lyrics, str):
        return ""
    
    # Patrones de limpieza específicos
    navigation_patterns = [
        # Texto de login/navegación
        r'Iniciar sesión o crear cuenta\s*\n*\s*Cuenta',
        r'Iniciar sesión o crear cuenta.*?Cuenta',
        
        # Comentarios y UI en portugués
        r'<p class="commentSection-description[^>]*>.*?</p>',
        r'<p class="commentsModal-text[^>]*>.*?</p>',
        r'<p class="commentSection-userGuide[^>]*>.*?</p>',
        r'<p class="sendAlert-description[^>]*>.*?</p>',
        r'<p class="selectionOptions-title[^>]*>.*?</p>',
        r'<p class="contributorsModal-empty-text[^>]*>.*?</p>',
        
        # Textos específicos de la UI
        r'Envie dúvidas, explicações e curiosidades sobre a letra',
        r'Tire dúvidas sobre idiomas, interaja com outros fãs.*?da música\.',
        r'Confira nosso.*?para deixar comentários\.',
        r'Dúvidas enviadas podem receber respostas de professores e alunos da plataforma\.',
        r'Opções de seleção',
        r'Todavía no recibimos esta contribución.*?enviárnosla\?',
        r'¿Los datos están equivocados\? Avísanos\.',
        r'Compuesta por:.*?¿Los datos están equivocados\? Avísanos\.',
        r'¿Sabes quién compuso esta canción\? Envíanoslo\.',
        
        # Limpieza de HTML
        r'<[^>]+>',  # Tags HTML
        r'class="[^"]*"',  # Atributos de clase
        r'href="[^"]*"',  # Enlaces
        r'target="_blank"',  # Atributos
        r'\s+font --base[^"]*',  # Clases de fuente
    ]
    
    cleaned_text = lyrics
    
    # Aplicar patrones de limpieza
    for pattern in navigation_patterns:
        cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE | re.DOTALL)
    
    # Limpiar espacios y saltos de línea excesivos
    cleaned_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned_text)  # Max 2 saltos
    cleaned_text = re.sub(r'[ \t]+', ' ', cleaned_text)  # Espacios múltiples
    cleaned_text = cleaned_text.strip()
    
    return cleaned_text

def is_valid_lyrics(lyrics: str) -> bool:
    """
    Determina si las letras son válidas (no solo navegación)
    """
    if not lyrics:
        return False
    
    cleaned = clean_lyrics_text(lyrics)
    
    # Verificaciones de validez
    if len(cleaned) < 15:  # Muy cortas
        return False
    
    # Patrones de contenido inválido
    invalid_patterns = [
        r'^[\s\n]*$',  # Solo espacios
        r'^[\s\n]*Iniciar.*?Cuenta[\s\n]*$',  # Solo navegación
        r'^[\s\n]*N/A[\s\n]*$',  # Marcadores de no disponible
        r'^[\s\n]*(null|undefined|None)[\s\n]*$',  # Valores nulos
    ]
    
    for pattern in invalid_patterns:
        if re.match(pattern, cleaned, flags=re.DOTALL | re.IGNORECASE):
            return False
    
    return True

def is_placeholder_song(song_key: str, artist_path: str, lyrics: str) -> bool:
    """
    Detecta canciones placeholder (artista repetido sin letras reales)
    """
    artist_name = artist_path.strip('/').lower().replace('-', '').replace(' ', '')
    song_name = song_key.strip('/').lower().replace('-', '').replace(' ', '')
    
    # Si son muy similares y las letras no son válidas
    if (artist_name == song_name or song_name.startswith(artist_name)) and not is_valid_lyrics(lyrics):
        return True
    
    return False

def clean_and_process_dataset(input_file: str = "spanish_songs_server_final.pickle"):
    """
    Procesa y limpia el dataset completo
    """
    logger.info(f"🧹 PROCESANDO Y LIMPIANDO: {input_file}")
    
    # Cargar datos
    try:
        with open(input_file, 'rb') as f:
            data = pickle.load(f)
        logger.info(f"✅ Dataset cargado: {len(data)} géneros")
    except Exception as e:
        logger.error(f"❌ Error cargando archivo: {e}")
        return None
    
    # Estadísticas de limpieza
    stats = {
        'total_initial': 0,
        'placeholder_removed': 0,
        'invalid_lyrics_removed': 0,
        'cleaned_lyrics': 0,
        'total_final': 0
    }
    
    processed_documents = []
    
    logger.info("🔄 Procesando géneros...")
    for genre_name, genre_data in tqdm(data.items(), desc="Géneros"):
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
                
                stats['total_initial'] += 1
                
                # Obtener letras originales
                original_lyrics = song_data.get('lyrics', '')
                
                # Verificar si es placeholder
                if is_placeholder_song(song_key, artist_path, original_lyrics):
                    stats['placeholder_removed'] += 1
                    continue
                
                # Limpiar letras
                cleaned_lyrics = clean_lyrics_text(original_lyrics)
                
                # Verificar validez después de limpieza
                if not is_valid_lyrics(cleaned_lyrics):
                    stats['invalid_lyrics_removed'] += 1
                    continue
                
                # Crear documento limpio
                song_title = song_key.strip('/').replace('-', ' ').title()
                
                # Contar limpieza realizada
                if len(cleaned_lyrics) < len(original_lyrics) * 0.8:
                    stats['cleaned_lyrics'] += 1
                
                doc = {
                    'artist': artist_name,
                    'song_title': song_title,
                    'genre': genre_name,
                    'lyrics': cleaned_lyrics,
                    'lyrics_word_count': len(cleaned_lyrics.split()),
                    'composer': clean_lyrics_text(song_data.get('composer', '')),
                    'emotion': song_data.get('emotion', 'unknown'),
                    'processed_date': datetime.now().isoformat(),
                    'source': 'server_processed_cleaned',
                    'dataset_version': 'v2.1'
                }
                
                # Agregar datos adicionales si existen
                extra_fields = [
                    'popularity', 'energy', 'danceability', 'valence', 'tempo',
                    'speechiness', 'acousticness', 'instrumentalness', 'liveness',
                    'loudness', 'key', 'mode', 'time_signature', 'explicit_content',
                    'spotify_found', 'duration_ms', 'release_date', 'is_estimated'
                ]
                
                for field in extra_fields:
                    if field in song_data and song_data[field] is not None:
                        doc[field] = song_data[field]
                
                # Crear ID único
                clean_artist = ''.join(c for c in artist_name.lower() if c.isalnum())[:20]
                clean_song = ''.join(c for c in song_title.lower() if c.isalnum())[:20]
                clean_genre = ''.join(c for c in genre_name.lower() if c.isalnum())[:15]
                doc['unique_id'] = f"{clean_artist}_{clean_song}_{clean_genre}"
                
                processed_documents.append(doc)
                stats['total_final'] += 1
    
    # Mostrar estadísticas de limpieza
    logger.info("")
    logger.info("📊 ESTADÍSTICAS DE LIMPIEZA:")
    logger.info(f"   🎵 Canciones iniciales: {stats['total_initial']:,}")
    logger.info(f"   🗑️ Placeholders eliminados: {stats['placeholder_removed']:,}")
    logger.info(f"   ❌ Letras inválidas eliminadas: {stats['invalid_lyrics_removed']:,}")
    logger.info(f"   🧹 Letras limpiadas: {stats['cleaned_lyrics']:,}")
    logger.info(f"   ✅ Canciones finales válidas: {stats['total_final']:,}")
    
    return processed_documents

def export_to_mongodb(documents: list, batch_size: int = 500):
    """
    Exportar documentos limpios a MongoDB Atlas
    """
    if not documents:
        logger.error("❌ No hay documentos para exportar")
        return False
    
    logger.info("🚀 EXPORTANDO A MONGODB ATLAS")
    
    # Conectar
    try:
        client = MongoClient(MONGODB_URI)
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        
        # Test conexión
        client.admin.command('ismaster')
        logger.info("✅ Conexión exitosa a MongoDB Atlas")
        
        # Limpiar colección anterior
        collection.drop()
        logger.info("🗑️ Colección anterior eliminada")
        
    except Exception as e:
        logger.error(f"❌ Error conectando: {e}")
        return False
    
    # Insertar en lotes
    inserted_total = 0
    error_total = 0
    
    logger.info(f"📤 Insertando {len(documents):,} documentos...")
    
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
        collection.create_index([("genre", 1)])
        collection.create_index([("artist", 1)])
        collection.create_index([("emotion", 1)])
        collection.create_index([("lyrics_word_count", 1)])
        logger.info("🔍 Índices creados")
    except Exception as e:
        logger.warning(f"Error creando índices: {e}")
    
    # Estadísticas finales
    final_count = collection.count_documents({})
    
    logger.info("")
    logger.info("✅ EXPORTACIÓN COMPLETADA")
    logger.info(f"📊 Estadísticas MongoDB:")
    logger.info(f"   📝 Documentos insertados: {inserted_total:,}")
    logger.info(f"   ❌ Errores: {error_total:,}")
    logger.info(f"   📚 Total en colección: {final_count:,}")
    logger.info(f"   🗄️ Base: {DATABASE_NAME}")
    logger.info(f"   📦 Colección: {COLLECTION_NAME}")
    
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
            logger.info(f"   🎵 {stat['_id']}: {stat['count']:,}")
    
    client.close()
    return final_count > 0

if __name__ == "__main__":
    logger.info("🧹🗄️ LIMPIEZA COMPLETA + EXPORTACIÓN MONGODB")
    logger.info("=" * 60)
    
    # Paso 1: Limpiar y procesar dataset
    documents = clean_and_process_dataset()
    
    if not documents:
        logger.error("❌ No se pudieron procesar los documentos")
        sys.exit(1)
    
    # Paso 2: Exportar a MongoDB
    success = export_to_mongodb(documents)
    
    if success:
        logger.info("")
        logger.info("🎉 ¡PROCESO COMPLETADO EXITOSAMENTE!")
        logger.info("🌐 Dataset limpio disponible en MongoDB Atlas")
        logger.info("🔗 Cluster: notez.lwzox.mongodb.net")
        logger.info("📚 Base de datos: ml-workshop") 
        logger.info("📦 Colección: songs")
    else:
        logger.error("❌ Error en la exportación")
        sys.exit(1)
