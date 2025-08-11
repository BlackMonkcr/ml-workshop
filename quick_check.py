#!/usr/bin/env python3
"""
Verificación rápida del estado del procesamiento
"""

import os
from pymongo import MongoClient

def quick_check():
    """Verificación rápida"""
    try:
        # Conectar a MongoDB
        MONGODB_URI = os.getenv('MONGODB_URI', "mongodb+srv://admin:Wwc8mSrm7WhfHbu1@notez.lwzox.mongodb.net/?retryWrites=true&w=majority&appName=Notez")
        
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=3000)
        db = client["ml-workshop"]
        collection = db["songs"]
        
        # Obtener estadísticas rápidas
        total = collection.count_documents({})
        spotify_found = collection.count_documents({"spotify_found": True})
        
        print(f"📊 ESTADO ACTUAL:")
        print(f"   Total documentos: {total:,}")
        print(f"   Con Spotify: {spotify_found:,}")
        print(f"   Progreso: {(total/26291)*100:.1f}%")
        
        # Última canción procesada
        latest = collection.find_one({}, sort=[("processed_date", -1)])
        if latest:
            print(f"   Última: {latest.get('artist', 'N/A')} - {latest.get('song_title', 'N/A')}")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    quick_check()
