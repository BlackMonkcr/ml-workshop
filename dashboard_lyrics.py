import streamlit as st
import pickle
import os

st.set_page_config(page_title="Dashboard de Letras", layout="wide")

st.title("🎵 Dashboard de Letras por Género, Artista y Canción")

PICKLE_PATH = "lyrics_by_genre_parallel.pickle"

# Cargar datos
@st.cache_data(show_spinner=True)
def load_data(path):
    with open(path, "rb") as f:
        data = pickle.load(f)
    return data

def get_kpis(data):
    num_genres = len(data)
    num_artists = sum(len(artists) for artists in data.values())
    num_songs = sum(
        len(songs)
        for genre_data in data.values()
        for songs in genre_data.values()
    )
    return num_genres, num_artists, num_songs

if not os.path.exists(PICKLE_PATH):
    st.error(f"No se encontró el archivo {PICKLE_PATH}")
    st.stop()

data = load_data(PICKLE_PATH)

# KPIs
num_genres, num_artists, num_songs = get_kpis(data)
col1, col2, col3 = st.columns(3)
col1.metric("Géneros", num_genres)
col2.metric("Artistas", num_artists)
col3.metric("Canciones", num_songs)

st.markdown("---")

# Sidebar para selección
st.sidebar.header("Filtros")
genres = sorted(list(data.keys()))
selected_genre = st.sidebar.selectbox("Selecciona un género", genres)

artists = sorted(list(data[selected_genre].keys()))
selected_artist = st.sidebar.selectbox("Selecciona un artista", artists)

songs = sorted(list(data[selected_genre][selected_artist].keys()))
selected_song = st.sidebar.selectbox("Selecciona una canción", songs)

# Mostrar letra y compositor
details = data[selected_genre][selected_artist][selected_song]

st.subheader(f"Letra de la canción: {selected_song}")
st.markdown(f"**Artista:** {selected_artist}")
st.markdown(f"**Género:** {selected_genre}")
if details.get('composer'):
    st.markdown(f"**Compositor:** {details['composer']}")

st.markdown("---")

if details.get('lyrics'):
    st.text_area("Letra", details['lyrics'], height=400)
else:
    st.warning("No hay letra disponible para esta canción.")

# Estadísticas adicionales
with st.expander("Ver estadísticas por género"):
    st.write({g: len(data[g]) for g in genres})
