import requests
from bs4 import BeautifulSoup


def normalize_genre_name(genre_name):
    """
    Los géneros en genres.txt ya están normalizados para URLs.
    Esta función simplemente retorna el género tal como está.

    Args:
        genre_name (str): Nombre del género ya normalizado desde genres.txt

    Returns:
        str: Mismo nombre (ya normalizado para URL)
    """
    return genre_name.strip()


def load_genres(path):
    """
    Carga la lista de géneros desde un archivo de texto

    Args:
        path (str): Ruta al archivo de géneros

    Returns:
        list: Lista de géneros
    """
    with open(path, "r", encoding="utf-8") as f:
        genres = [line.strip() for line in f if line.strip()]
    return genres


def save_file(artists, path):
    with open(path, "w") as f:
        for artist in artists:
            f.write(artist + "\n")


def load_file(path):
    with open(path, "r") as f:
        text = f.read()
        text = text.split("\n")

        return text


def read_pickle(filename):
    import pickle

    with open(filename, "rb") as fh:
        list_name = pickle.load(fh)

    return list_name


def save_pickle(filename, obj):
    import pickle

    with open(filename, "wb") as f:
        pickle.dump(obj, f)


def get_artists(base_url, genre):
    """
    Obtiene la lista de artistas más populares de un género específico

    Args:
        base_url (str): URL base de letras.com
        genre (str): Género musical normalizado

    Returns:
        list: Lista de URLs de artistas
    """
    url = f"{base_url}/mais-acessadas/{genre}/"

    try:
        result = requests.get(url)
        result.raise_for_status()  # Lanza excepción si hay error HTTP
        src = result.content

        soup = BeautifulSoup(src, "lxml")
        links = soup.find("ol", class_="top-list_art")

        if not links:
            print(f"No se encontraron artistas para el género: {genre}")
            return []

        artists = []
        for link in links.find_all("li"):
            artist_link = link.find("a")
            if artist_link and "href" in artist_link.attrs:
                url_artist = artist_link.attrs["href"]
                artists.append(url_artist)

        print(f"Se encontraron {len(artists)} artistas para el género: {genre}")
        return artists

    except requests.exceptions.RequestException as e:
        print(f"Error al obtener artistas del género {genre}: {e}")
        return []
    except Exception as e:
        print(f"Error inesperado al procesar género {genre}: {e}")
        return []


def extract_songs_from_new_layout(soup):
    """Extrae canciones usando el nuevo layout de letras.com"""
    songs = []
    song_rows = soup.find_all("tr", class_="songList-table-row")

    if song_rows:
        for row in song_rows:
            song_link = row.find("a", href=True)
            if song_link:
                href = song_link.get("href")
                if href and href.startswith("/") and href.count("/") >= 2:
                    songs.append(href)

    return songs


def extract_songs_from_old_layout(soup):
    """Extrae canciones usando el layout antiguo de letras.com"""
    songs = []
    links = soup.find("ul", class_="cnt-list-songs -counter -top-songs js-song-list")

    if links:
        for link in links.find_all("li"):
            song_link = link.find("a")
            if song_link and "href" in song_link.attrs:
                songs.append(song_link.attrs["href"])

    return songs


def extract_songs_fallback(soup, url):
    """Método de fallback para extraer canciones"""
    songs = []
    all_links = soup.find_all("a", href=True)
    artist_name = url.split("/")[-2]

    for link in all_links:
        href = link.get("href", "")
        if (artist_name in href and
            href.startswith("/") and
            href.count("/") >= 2 and
            not any(skip in href for skip in ["ouvir", "radio", "discografia", "biografia"])):
            songs.append(href)

    return songs


def get_song_names(url):
    """
    Obtiene los nombres de las canciones más tocadas de un artista

    Args:
        url (str): URL de la página de canciones más tocadas del artista

    Returns:
        list: Lista de URLs de canciones
    """
    try:
        print(f"      🔍 Accediendo a: {url}")
        result = requests.get(url)
        result.raise_for_status()
        soup = BeautifulSoup(result.content, "lxml")

        # Intentar nuevo layout primero
        songs = extract_songs_from_new_layout(soup)
        if songs:
            print(f"      ✅ Encontradas {len(songs)} canciones (nuevo layout)")
            return songs

        # Intentar layout antiguo
        songs = extract_songs_from_old_layout(soup)
        if songs:
            print(f"      ✅ Encontradas {len(songs)} canciones (layout antiguo)")
            return songs

        # Método de fallback
        print("      🔍 Usando método de fallback...")
        songs = extract_songs_fallback(soup, url)

        # Eliminar duplicados
        unique_songs = list(dict.fromkeys(songs))
        print(f"      ✅ Encontradas {len(unique_songs)} canciones únicas")
        return unique_songs

    except requests.exceptions.RequestException as e:
        print(f"      ❌ Error de conexión en {url}: {e}")
        return []
    except Exception as e:
        print(f"      ❌ Error inesperado en {url}: {e}")
        return []


def extract_lyrics_new_layout(soup):
    """Extrae letras usando el nuevo layout de letras.com"""
    lyrics_text = ""
    composer_info = ""

    # Buscar contenedores modernos de letras
    possible_selectors = [
        {"tag": "div", "class": lambda x: x and "lyric" in str(x).lower()},
        {"tag": "div", "class": lambda x: x and "letra" in str(x).lower()},
        {"tag": "section", "class": lambda x: x and ("lyric" in str(x).lower() or "letra" in str(x).lower())},
    ]

    for selector in possible_selectors:
        container = soup.find(selector["tag"], class_=selector["class"])
        if container:
            # Extraer texto de párrafos
            paragraphs = container.find_all("p")
            if paragraphs:
                lyrics_parts = []
                for p in paragraphs:
                    text = str(p)
                    text = text.replace("<p>", "").replace("</p>", "")
                    text = text.replace("<br/>", "\n").replace("<br>", "\n")
                    lyrics_parts.append(text)
                lyrics_text = "\n\n".join(lyrics_parts)
                break
            else:
                # Si no hay párrafos, usar el texto completo
                lyrics_text = container.get_text(separator="\n")
                break

    # Buscar información del compositor con selectores modernos
    comp_selectors = [
        "div[class*='composer']",
        "div[class*='author']",
        "div[class*='comp']",
        "span[class*='composer']",
        "span[class*='author']"
    ]

    for selector in comp_selectors:
        comp_elem = soup.select_one(selector)
        if comp_elem:
            composer_info = comp_elem.get_text(strip=True)
            break

    return lyrics_text, composer_info


def extract_lyrics_old_layout(soup):
    """Extrae letras usando el layout antiguo de letras.com"""
    lyrics_text = ""
    composer_info = ""

    # Selector original
    container = soup.find("div", class_="cnt-letra p402_premium")
    if container:
        paragraphs = container.find_all("p")
        if paragraphs:
            lyrics_parts = []
            for p in paragraphs:
                text = str(p)
                text = text.replace("<p>", "").replace("</p>", "")
                text = text.replace("<br/>", "\n").replace("<br>", "\n")
                lyrics_parts.append(text)
            lyrics_text = "\n\n".join(lyrics_parts)

    # Compositor original
    comp_elem = soup.find("div", class_="letra-info_comp")
    if comp_elem:
        composer_info = comp_elem.get_text(strip=True)

    return lyrics_text, composer_info


def extract_lyrics_fallback(soup):
    """Método de fallback para extraer letras"""
    lyrics_text = ""
    composer_info = ""

    # Buscar el elemento con más texto (probablemente las letras)
    text_elements = []
    for elem in soup.find_all(['div', 'p', 'section']):
        text = elem.get_text(strip=True)
        if len(text) > 100:  # Elementos con bastante texto
            text_elements.append((elem, len(text)))

    if text_elements:
        # Ordenar por longitud de texto y tomar el más largo
        text_elements.sort(key=lambda x: x[1], reverse=True)
        longest_elem = text_elements[0][0]
        lyrics_text = longest_elem.get_text(separator="\n", strip=True)

    return lyrics_text, composer_info


def get_lyrics(url):
    """
    Extrae las letras de una canción desde su URL

    Args:
        url (str): URL de la página de la canción

    Returns:
        tuple: (letras, compositor)
    """
    try:
        result = requests.get(url)
        result.raise_for_status()
        soup = BeautifulSoup(result.content, "lxml")

        # Intentar nuevo layout primero
        lyrics, composer = extract_lyrics_new_layout(soup)
        if lyrics:
            return lyrics, composer

        # Intentar layout antiguo
        lyrics, composer = extract_lyrics_old_layout(soup)
        if lyrics:
            return lyrics, composer

        # Método de fallback
        lyrics, composer = extract_lyrics_fallback(soup)
        if lyrics:
            return lyrics, composer

        # Si nada funciona
        return "", ""

    except Exception as e:
        print(f"Error procesando {url}: {e}")
        song = url.split("/")[-1] if url.split("/")[-1] else url.split("/")[-2]
        print(f"Error on song {song}")
        return "", ""


if __name__ == "__main__":
    import os
    import time

    # Configuración general
    base_url = "https://www.letras.com"
    end_url = "mais-tocadas.html"
    genres_path = "genres.txt"
    artists_path = "artists_by_genre.pickle"
    lyrics_path = "lyrics_by_genre.pickle"

    # Límites de procesamiento
    MAX_ARTISTS_PER_GENRE = 50  # Reducido para manejar múltiples géneros
    MAX_SONGS_PER_ARTIST = 10   # Limitar canciones por artista

    print("🎵 Iniciando extracción de letras multi-género 🎵")
    print("=" * 50)

    # Cargar géneros
    if not os.path.exists(genres_path):
        print(f"❌ Error: No se encontró el archivo {genres_path}")
        exit(1)

    genres = load_genres(genres_path)
    print(f"📂 Se cargaron {len(genres)} géneros musicales")

    # Cargar o inicializar estructura de artistas por género
    if os.path.exists(artists_path):
        artists_by_genre = read_pickle(artists_path)
        print("📁 Cargada lista existente de artistas por género")
    else:
        artists_by_genre = {}
        print("🆕 Creando nueva estructura de artistas por género")

    # Cargar o inicializar estructura de letras por género
    if os.path.exists(lyrics_path):
        lyrics_by_genre = read_pickle(lyrics_path)
        print("📁 Cargada base de datos existente de letras")
    else:
        lyrics_by_genre = {}
        print("🆕 Creando nueva base de datos de letras")

    # Procesar cada género
    for i, genre in enumerate(genres, 1):
        print(f"\n🎸 Procesando género {i}/{len(genres)}: {genre}")
        print("-" * 40)

        # Los géneros ya están normalizados en genres.txt
        normalized_genre = normalize_genre_name(genre)
        print(f"🔗 Procesando: {normalized_genre}")

        # Verificar si ya tenemos artistas para este género
        if genre not in artists_by_genre:
            print(f"🔍 Buscando artistas de {genre}...")
            artists = get_artists(base_url, normalized_genre)
            if artists:
                artists_by_genre[genre] = artists
                save_pickle(artists_path, artists_by_genre)
                print(f"✅ Guardados {len(artists)} artistas de {genre}")
            else:
                print(f"⚠️  No se encontraron artistas para {genre}")
                continue
        else:
            artists = artists_by_genre[genre]
            print(f"📋 Ya tenemos {len(artists)} artistas de {genre}")

        # Inicializar estructura de letras para este género si no existe
        if genre not in lyrics_by_genre:
            lyrics_by_genre[genre] = {}

        # Procesar artistas del género (limitado)
        artists_to_process = artists[:MAX_ARTISTS_PER_GENRE]
        print(f"👥 Procesando {len(artists_to_process)} artistas de {genre}")

        for j, artist in enumerate(artists_to_process, 1):
            print(f"  🎤 Artista {j}/{len(artists_to_process)}: {artist}")

            # Verificar si ya procesamos este artista
            if artist in lyrics_by_genre[genre]:
                print(f"    ✓ Ya procesado: {artist}")
                continue

            try:
                # Obtener canciones del artista
                url_song = base_url + artist + end_url
                songs = get_song_names(url_song)

                if not songs:
                    print(f"    ⚠️  No se encontraron canciones para {artist}")
                    continue

                # Limitar número de canciones
                songs_to_process = songs[:MAX_SONGS_PER_ARTIST]
                lyrics_by_genre[genre][artist] = {}

                # Procesar canciones
                for k, song in enumerate(songs_to_process, 1):
                    song_name = song.split('/')[-2] if song.endswith('/') else song.split('/')[-1]
                    print(f"    🎵 Canción {k}/{len(songs_to_process)}: {song_name}")

                    url_lyrics = base_url + song
                    text, by = get_lyrics(url_lyrics)

                    if text:
                        print(f"      ✅ Letras extraídas ({len(text)} caracteres)")
                    else:
                        print("      ⚠️  No se pudieron extraer letras")

                    # Guardar letra
                    lyrics_by_genre[genre][artist][song] = {
                        'lyrics': text,
                        'composer': by,
                        'genre': genre
                    }

                    time.sleep(1)  # Pausa entre canciones

                print(f"    ✅ Procesadas {len(songs_to_process)} canciones de {artist}")

                # Guardar progreso después de cada artista
                save_pickle(lyrics_path, lyrics_by_genre)
                time.sleep(2)  # Pausa entre artistas

            except Exception as e:
                print(f"    ❌ Error procesando {artist}: {e}")
                continue

        print(f"✅ Completado género: {genre}")

        # Pausa entre géneros
        if i < len(genres):
            print("⏳ Pausa entre géneros...")
            time.sleep(5)

    print("\n🎉 ¡Extracción completada!")
    print("=" * 50)

    # Mostrar estadísticas finales
    total_genres = len(lyrics_by_genre)
    total_artists = sum(len(artists) for artists in lyrics_by_genre.values())
    total_songs = sum(
        len(songs)
        for genre_data in lyrics_by_genre.values()
        for songs in genre_data.values()
    )

    print("📊 Estadísticas finales:")
    print(f"   🎸 Géneros procesados: {total_genres}")
    print(f"   👥 Artistas procesados: {total_artists}")
    print(f"   🎵 Canciones extraídas: {total_songs}")
    print(f"   💾 Datos guardados en: {lyrics_path}")
