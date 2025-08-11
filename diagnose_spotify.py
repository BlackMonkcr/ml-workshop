#!/usr/bin/env python3
"""
Diagnóstico de búsquedas en Spotify
Analizar por qué tantas canciones no se encuentran
"""

import pickle
import re
import requests
import base64
import json
from collections import defaultdict
import random

# Configuración Spotify
SPOTIFY_CLIENT_ID = "cb54f009842e4529b1297a1428da7fc6"
SPOTIFY_CLIENT_SECRET = "d23ed8ab01dd4fcea1b48354189399b6"

class SpotifyDiagnostic:
    def __init__(self):
        self.access_token = None
        self.get_access_token()
    
    def get_access_token(self):
        auth_url = "https://accounts.spotify.com/api/token"
        auth_header = base64.b64encode(f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode()).decode()
        
        headers = {"Authorization": f"Basic {auth_header}"}
        data = {"grant_type": "client_credentials"}
        
        try:
            response = requests.post(auth_url, headers=headers, data=data)
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data["access_token"]
                print("✅ Token de Spotify obtenido")
                return True
        except Exception as e:
            print(f"❌ Error obteniendo token: {e}")
        
        return False
    
    def test_different_search_strategies(self, artist, song_title):
        """Probar diferentes estrategias de búsqueda"""
        if not self.access_token:
            return {}
        
        strategies = {
            'original': f"artist:{artist} track:{song_title}",
            'simple': f"{artist} {song_title}",
            'clean_artist': f"artist:\"{re.sub(r'[^a-zA-Z0-9 ]', '', artist)}\" track:\"{re.sub(r'[^a-zA-Z0-9 ]', '', song_title)}\"",
            'just_song': f"\"{song_title}\"",
            'partial_artist': f"artist:{artist.split()[0] if artist.split() else artist}",
            'no_quotes': f"artist:{artist} track:{song_title}".replace('"', ''),
        }
        
        results = {}
        
        for strategy_name, query in strategies.items():
            try:
                search_url = "https://api.spotify.com/v1/search"
                headers = {"Authorization": f"Bearer {self.access_token}"}
                params = {"q": query, "type": "track", "limit": 3}
                
                response = requests.get(search_url, headers=headers, params=params, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    tracks = data.get("tracks", {}).get("items", [])
                    
                    results[strategy_name] = {
                        'found': len(tracks) > 0,
                        'count': len(tracks),
                        'query': query,
                        'tracks': [
                            {
                                'name': track.get('name'),
                                'artist': ', '.join([a.get('name') for a in track.get('artists', [])]),
                                'popularity': track.get('popularity')
                            } for track in tracks[:2]
                        ] if tracks else []
                    }
                else:
                    results[strategy_name] = {'error': f"HTTP {response.status_code}"}
                    
            except Exception as e:
                results[strategy_name] = {'error': str(e)}
        
        return results

def diagnose_spotify_searches():
    """Diagnosticar búsquedas de Spotify"""
    print("🔍 DIAGNÓSTICO DE BÚSQUEDAS EN SPOTIFY")
    print("=" * 60)
    
    # Cargar datos
    try:
        with open("spanish_songs_server_final.pickle", 'rb') as f:
            data = pickle.load(f)
        print(f"✅ Dataset cargado: {len(data)} géneros")
    except Exception as e:
        print(f"❌ Error cargando dataset: {e}")
        return
    
    # Recopilar muestra de canciones
    sample_songs = []
    for genre_name, genre_data in data.items():
        if len(sample_songs) >= 20:
            break
            
        for artist_path, artist_songs in genre_data.items():
            if not isinstance(artist_songs, dict):
                continue
            
            artist_name = artist_path.strip('/').replace('-', ' ').title()
            
            for song_key, song_data in artist_songs.items():
                if len(sample_songs) >= 20:
                    break
                    
                song_title = song_key.strip('/').replace('-', ' ').title()
                sample_songs.append({
                    'artist': artist_name,
                    'song_title': song_title,
                    'genre': genre_name
                })
    
    # Seleccionar muestra aleatoria
    sample_songs = random.sample(sample_songs, min(10, len(sample_songs)))
    
    print(f"🎵 Analizando {len(sample_songs)} canciones de muestra...")
    print()
    
    # Inicializar Spotify
    spotify = SpotifyDiagnostic()
    if not spotify.access_token:
        print("❌ No se pudo inicializar Spotify API")
        return
    
    # Analizar cada canción
    strategy_success = defaultdict(int)
    total_songs = len(sample_songs)
    
    for i, song in enumerate(sample_songs, 1):
        print(f"🎵 {i}/{total_songs}: {song['artist']} - {song['song_title']}")
        print(f"   Género: {song['genre']}")
        
        results = spotify.test_different_search_strategies(song['artist'], song['song_title'])
        
        found_any = False
        for strategy, result in results.items():
            if result.get('found'):
                strategy_success[strategy] += 1
                found_any = True
                print(f"   ✅ {strategy}: {result['count']} resultados")
                for track in result.get('tracks', []):
                    print(f"      • {track['artist']} - {track['name']} (pop: {track['popularity']})")
            else:
                error = result.get('error', 'No encontrado')
                print(f"   ❌ {strategy}: {error}")
        
        if not found_any:
            print("   ⚠️ NO ENCONTRADA CON NINGUNA ESTRATEGIA")
        
        print()
    
    # Resumen de estrategias
    print("📊 RESUMEN DE ESTRATEGIAS:")
    print("=" * 40)
    
    for strategy, success_count in sorted(strategy_success.items(), key=lambda x: x[1], reverse=True):
        success_rate = (success_count / total_songs) * 100
        print(f"{strategy:15}: {success_count:2}/{total_songs} ({success_rate:5.1f}%)")
    
    # Recomendaciones
    print("\n💡 RECOMENDACIONES:")
    if strategy_success:
        best_strategy = max(strategy_success.items(), key=lambda x: x[1])
        print(f"✅ Mejor estrategia: {best_strategy[0]} ({best_strategy[1]}/{total_songs} éxito)")
    
    print("\n🔧 POSIBLES MEJORAS:")
    print("1. Limpiar mejor los nombres de artistas/canciones")
    print("2. Probar búsquedas más flexibles")
    print("3. Usar búsqueda por similaridad de texto")
    print("4. Aumentar el timeout de requests")
    print("5. Implementar retry con backoff")

if __name__ == "__main__":
    diagnose_spotify_searches()
