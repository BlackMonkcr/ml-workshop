#!/usr/bin/env python3
"""
CONFIGURACIÓN SEGURA PARA MONGODB
"""
import os

# Configuración MongoDB (usar variables de entorno en producción)
MONGODB_CONFIG = {
    "uri": "mongodb+srv://admin:Wwc8mSrm7WhfHbu1@notez.lwzox.mongodb.net/?retryWrites=true&w=majority&appName=Notez",
    "database": "ml-workshop",
    "collection": "songs"
}

def get_mongodb_uri():
    """Obtener URI de MongoDB de variables de entorno o config"""
    return os.getenv('MONGODB_URI', MONGODB_CONFIG['uri'])

def get_database_name():
    """Obtener nombre de base de datos"""
    return os.getenv('MONGODB_DATABASE', MONGODB_CONFIG['database'])

def get_collection_name():
    """Obtener nombre de colección"""
    return os.getenv('MONGODB_COLLECTION', MONGODB_CONFIG['collection'])
