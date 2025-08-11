"""
Dashboard mejorado para visualizar el dataset de canciones españolas enriquecidas y limpiadas
Incluye análisis de contenido explícito, emociones, y características musicales
"""
import streamlit as st
import pickle
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import random
from typing import Dict, List, Any

# Configuración de la página
st.set_page_config(
    page_title="🎵 Dashboard Musical Español Enriquecido",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    font-weight: bold;
    text-align: center;
    margin-bottom: 2rem;
    background: linear-gradient(90deg, #ff6b6b, #4ecdc4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.metric-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1rem;
    border-radius: 10px;
    color: white;
    text-align: center;
    margin: 0.5rem;
}

.explicit-warning {
    background-color: #ff4444;
    color: white;
    padding: 0.5rem;
    border-radius: 5px;
    text-align: center;
    font-weight: bold;
}

.emotion-badge {
    display: inline-block;
    padding: 0.3rem 0.6rem;
    border-radius: 15px;
    font-size: 0.8rem;
    font-weight: bold;
    margin: 0.2rem;
}

.emotion-joy { background-color: #ffd93d; color: #333; }
.emotion-sadness { background-color: #6c757d; color: white; }
.emotion-anger { background-color: #dc3545; color: white; }
.emotion-fear { background-color: #6f42c1; color: white; }
.emotion-love { background-color: #e83e8c; color: white; }
.emotion-surprise { background-color: #fd7e14; color: white; }
.emotion-unknown { background-color: #6c757d; color: white; }

.characteristics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 0.5rem;
    margin: 1rem 0;
}

.char-item {
    background: #f8f9fa;
    padding: 0.5rem;
    border-radius: 5px;
    text-align: center;
    border-left: 4px solid #007bff;
}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """Cargar y procesar datos del dataset limpio y enriquecido"""
    try:
        with open('spanish_songs_emotions_fixed.pickle', 'rb') as f:
            data = pickle.load(f)
        return data
    except FileNotFoundError:
        st.error("❌ No se encontró el archivo spanish_songs_emotions_fixed.pickle")
        return None

def create_dataframe_from_nested_dict(data: Dict) -> pd.DataFrame:
    """Convertir el diccionario anidado en DataFrame para análisis"""
    rows = []
    
    for genre, artists in data.items():
        for artist_path, songs in artists.items():
            artist_name_clean = artist_path.strip('/')
            for song_path, song_data in songs.items():
                song_name_clean = song_path.strip('/')
                
                row = {
                    'genre': genre,
                    'artist_path': artist_path,
                    'song_path': song_path,
                    'artist_name_clean': artist_name_clean,
                    'song_name_clean': song_name_clean,
                    **song_data
                }
                rows.append(row)
    
    return pd.DataFrame(rows)

def get_emotion_color(emotion: str) -> str:
    """Obtener color para cada emoción"""
    emotion_colors = {
        'joy': '#ffd93d',
        'sadness': '#6c757d',
        'anger': '#dc3545',
        'fear': '#6f42c1',
        'love': '#e83e8c',
        'surprise': '#fd7e14',
        'unknown': '#6c757d'
    }
    return emotion_colors.get(emotion.lower(), '#6c757d')

def main():
    """Función principal del dashboard"""
    
    # Header principal
    st.markdown('<h1 class="main-header">🎵 Dashboard Musical Español Enriquecido</h1>', unsafe_allow_html=True)
    
    # Cargar datos
    data = load_data()
    if not data:
        return
    
    # Convertir a DataFrame
    df = create_dataframe_from_nested_dict(data)
    
    # Sidebar con filtros
    st.sidebar.header("🔍 Filtros")
    
    # Filtro por género
    genres = list(data.keys())
    selected_genre = st.sidebar.selectbox("Seleccionar Género", ["Todos"] + genres)
    
    # Filtro por contenido explícito
    explicit_filter = st.sidebar.radio(
        "Contenido Explícito",
        ["Todos", "Solo Explícito", "Solo No Explícito"]
    )
    
    # Filtro por emoción
    emotions = df['emotion'].unique() if 'emotion' in df.columns else []
    selected_emotion = st.sidebar.selectbox("Filtrar por Emoción", ["Todas"] + list(emotions))
    
    # Aplicar filtros
    filtered_df = df.copy()
    
    if selected_genre != "Todos":
        filtered_df = filtered_df[filtered_df['genre'] == selected_genre]
    
    if explicit_filter != "Todos":
        if explicit_filter == "Solo Explícito":
            filtered_df = filtered_df[filtered_df['explicit'] == 'Yes']
        else:
            filtered_df = filtered_df[filtered_df['explicit'] == 'No']
    
    if selected_emotion != "Todas" and 'emotion' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['emotion'] == selected_emotion]
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🎵 Total Canciones", len(filtered_df))
    
    with col2:
        explicit_count = len(filtered_df[filtered_df['explicit'] == 'Yes']) if 'explicit' in filtered_df.columns else 0
        st.metric("🔞 Contenido Explícito", explicit_count)
    
    with col3:
        avg_popularity = filtered_df['popularity'].mean() if 'popularity' in filtered_df.columns else 0
        st.metric("⭐ Popularidad Promedio", f"{avg_popularity:.1f}")
    
    with col4:
        genres_count = filtered_df['genre'].nunique()
        st.metric("🎼 Géneros", genres_count)
    
    # Tabs principales
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Análisis General", 
        "🎭 Emociones", 
        "🔞 Contenido Explícito", 
        "🎵 Características Musicales", 
        "🔍 Explorador de Canciones"
    ])
    
    with tab1:
        st.header("📊 Análisis General del Dataset")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Distribución por género
            genre_counts = filtered_df['genre'].value_counts()
            fig_genres = px.pie(
                values=genre_counts.values, 
                names=genre_counts.index,
                title="Distribución por Géneros"
            )
            st.plotly_chart(fig_genres, use_container_width=True)
        
        with col2:
            # Distribución de popularidad
            if 'popularity' in filtered_df.columns:
                fig_pop = px.histogram(
                    filtered_df, 
                    x='popularity',
                    title="Distribución de Popularidad en Spotify",
                    nbins=20
                )
                st.plotly_chart(fig_pop, use_container_width=True)
    
    with tab2:
        st.header("🎭 Análisis de Emociones")
        
        if 'emotion' in filtered_df.columns:
            col1, col2 = st.columns(2)
            
            with col1:
                # Distribución de emociones
                emotion_counts = filtered_df['emotion'].value_counts()
                colors = [get_emotion_color(emotion) for emotion in emotion_counts.index]
                
                fig_emotions = px.bar(
                    x=emotion_counts.index,
                    y=emotion_counts.values,
                    title="Distribución de Emociones en las Letras",
                    color=emotion_counts.index,
                    color_discrete_sequence=colors
                )
                st.plotly_chart(fig_emotions, use_container_width=True)
            
            with col2:
                # Emociones por género
                if selected_genre == "Todos":
                    emotion_genre = pd.crosstab(filtered_df['emotion'], filtered_df['genre'])
                    fig_emotion_genre = px.imshow(
                        emotion_genre.values,
                        x=emotion_genre.columns,
                        y=emotion_genre.index,
                        title="Mapa de Calor: Emociones por Género",
                        color_continuous_scale="Viridis"
                    )
                    st.plotly_chart(fig_emotion_genre, use_container_width=True)
                else:
                    st.info("Selecciona 'Todos' los géneros para ver el mapa de calor")
        else:
            st.info("No hay datos de emociones disponibles")
    
    with tab3:
        st.header("🔞 Análisis de Contenido Explícito")
        
        if 'explicit' in filtered_df.columns:
            col1, col2 = st.columns(2)
            
            with col1:
                # Distribución de contenido explícito
                explicit_counts = filtered_df['explicit'].value_counts()
                fig_explicit = px.pie(
                    values=explicit_counts.values,
                    names=explicit_counts.index,
                    title="Distribución de Contenido Explícito",
                    color_discrete_map={'Yes': '#ff4444', 'No': '#44ff44'}
                )
                st.plotly_chart(fig_explicit, use_container_width=True)
            
            with col2:
                # Contenido explícito por popularidad
                fig_explicit_pop = px.box(
                    filtered_df,
                    x='explicit',
                    y='popularity',
                    title="Popularidad por Tipo de Contenido"
                )
                st.plotly_chart(fig_explicit_pop, use_container_width=True)
            
            # Tabla de canciones explícitas más populares
            if len(filtered_df[filtered_df['explicit'] == 'Yes']) > 0:
                st.subheader("🔞 Canciones Explícitas Más Populares")
                explicit_songs = filtered_df[filtered_df['explicit'] == 'Yes'].nlargest(10, 'popularity')
                display_cols = ['song_title', 'artist_name', 'popularity', 'genre']
                available_cols = [col for col in display_cols if col in explicit_songs.columns]
                st.dataframe(explicit_songs[available_cols])
    
    with tab4:
        st.header("🎵 Características Musicales Estimadas")
        
        # Características musicales disponibles
        music_features = [
            'energy_estimated', 'danceability_estimated', 'positiveness_estimated',
            'speechiness_estimated', 'liveness_estimated', 'acousticness_estimated',
            'instrumentalness_estimated'
        ]
        
        available_features = [feat for feat in music_features if feat in filtered_df.columns]
        
        if available_features:
            # Radar chart de características promedio
            feature_means = {}
            for feature in available_features:
                feature_means[feature.replace('_estimated', '')] = filtered_df[feature].mean()
            
            fig_radar = go.Figure()
            
            fig_radar.add_trace(go.Scatterpolar(
                r=list(feature_means.values()),
                theta=list(feature_means.keys()),
                fill='toself',
                name='Promedio'
            ))
            
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100]
                    )),
                showlegend=True,
                title="Características Musicales Promedio"
            )
            
            st.plotly_chart(fig_radar, use_container_width=True)
            
            # Histogramas de características
            col1, col2 = st.columns(2)
            
            with col1:
                selected_feature = st.selectbox(
                    "Seleccionar Característica",
                    available_features
                )
                
                fig_hist = px.histogram(
                    filtered_df,
                    x=selected_feature,
                    title=f"Distribución de {selected_feature.replace('_estimated', '').title()}",
                    nbins=20
                )
                st.plotly_chart(fig_hist, use_container_width=True)
            
            with col2:
                # Correlación entre características
                corr_features = [feat for feat in available_features if feat in filtered_df.columns]
                if len(corr_features) >= 2:
                    corr_matrix = filtered_df[corr_features].corr()
                    
                    fig_corr = px.imshow(
                        corr_matrix.values,
                        x=[feat.replace('_estimated', '') for feat in corr_matrix.columns],
                        y=[feat.replace('_estimated', '') for feat in corr_matrix.index],
                        title="Correlación entre Características",
                        color_continuous_scale="RdBu"
                    )
                    st.plotly_chart(fig_corr, use_container_width=True)
    
    with tab5:
        st.header("🔍 Explorador de Canciones")
        
        # Selección de canción aleatoria
        col1, col2 = st.columns([3, 1])
        
        with col2:
            if st.button("🎲 Canción Aleatoria"):
                st.session_state.random_song = filtered_df.sample(1).iloc[0]
        
        # Mostrar canción seleccionada o aleatoria
        if hasattr(st.session_state, 'random_song'):
            song = st.session_state.random_song
        elif len(filtered_df) > 0:
            song = filtered_df.iloc[0]
        else:
            st.info("No hay canciones disponibles con los filtros seleccionados")
            return
        
        # Información de la canción
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader(f"🎵 {song.get('song_title', 'Título no disponible')}")
            st.write(f"**Artista:** {song.get('artist_name', 'Artista no disponible')}")
            st.write(f"**Género:** {song.get('genre', 'No disponible')}")
            st.write(f"**Álbum:** {song.get('album', 'No disponible')}")
            
            if 'explicit' in song:
                if song['explicit'] == 'Yes':
                    st.markdown('<div class="explicit-warning">🔞 CONTENIDO EXPLÍCITO</div>', unsafe_allow_html=True)
                else:
                    st.success("✅ Contenido Apropiado")
        
        with col2:
            if 'popularity' in song:
                st.metric("⭐ Popularidad", f"{song['popularity']}/100")
            
            if 'emotion' in song and song['emotion']:
                emotion = song['emotion']
                color = get_emotion_color(emotion)
                st.markdown(f'''
                <div class="emotion-badge emotion-{emotion.lower()}">
                    🎭 {emotion.title()}
                </div>
                ''', unsafe_allow_html=True)
        
        # Características musicales de la canción
        if any(feat in song for feat in music_features):
            st.subheader("🎼 Características Musicales")
            
            characteristics_html = '<div class="characteristics-grid">'
            for feature in available_features:
                if feature in song:
                    clean_name = feature.replace('_estimated', '').replace('_', ' ').title()
                    value = song[feature]
                    characteristics_html += f'''
                    <div class="char-item">
                        <div style="font-weight: bold;">{clean_name}</div>
                        <div style="font-size: 1.2em; color: #007bff;">{value}</div>
                    </div>
                    '''
            characteristics_html += '</div>'
            st.markdown(characteristics_html, unsafe_allow_html=True)
        
        # Spotify embed si está disponible
        if 'spotify_embed' in song and song['spotify_embed']:
            st.subheader("🎧 Reproducir en Spotify")
            st.components.v1.html(song['spotify_embed'], height=400)
        
        # Letras limpias
        if 'lyrics' in song and song['lyrics'] and len(song['lyrics']) > 10:
            st.subheader("📝 Letras")
            st.text_area("Letras de la canción", song['lyrics'], height=300, label_visibility="collapsed")
        else:
            st.info("Letras no disponibles para esta canción")

if __name__ == "__main__":
    main()
