import streamlit as st
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os

st.set_page_config(page_title="Moodify", layout="wide")

# CSS amélioré avec cartes symétriques
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
    }
    
    .main-title {
        color: #9d4edd;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .stButton > button {
        background: linear-gradient(45deg, #9d4edd, #7209b7);
        color: white;
        border: none;
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: linear-gradient(45deg, #7209b7, #9d4edd);
        box-shadow: 0 4px 15px rgba(157, 78, 221, 0.3);
    }
    
    /* Conteneur pour les cartes avec grid layout */
    .recommendations-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
        gap: 1rem;
        padding: 1rem 0;
    }
    
    /* Style des cartes de recommandation */
    .song-card {
        background: linear-gradient(135deg, rgba(157, 78, 221, 0.15), rgba(114, 9, 183, 0.08));
        border: 1px solid rgba(157, 78, 221, 0.3);
        border-radius: 15px;
        padding: 1.5rem;
        height: 250px;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 20px rgba(157, 78, 221, 0.1);
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
    }
    
    .song-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 30px rgba(157, 78, 221, 0.2);
        border-color: rgba(157, 78, 221, 0.5);
    }
    
    .song-title {
        color: #9d4edd;
        font-size: 1.1rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
        line-height: 1.1;
        word-wrap: break-word;
        overflow-wrap: break-word;
        hyphens: auto;
        max-height: 3.9rem;
        overflow: hidden;
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
    }
    
    .song-artist {
        color: #b794f6;
        font-size: 1rem;
        margin-bottom: 0.5rem;
        line-height: 1.2;
        word-wrap: break-word;
        overflow-wrap: break-word;
        max-height: 2.4rem;
        overflow: hidden;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
    }
    
    .song-genre {
        color: #e0aaff;
        font-size: 0.9rem;
        margin-bottom: 1rem;
    }
    
    .song-actions {
        margin-top: auto;
        padding-top: 1rem;
        border-top: 1px solid rgba(157, 78, 221, 0.2);
    }
    
    .spotify-link {
        background: linear-gradient(45deg, #1db954, #1ed760);
        color: white !important;
        text-decoration: none !important;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: bold;
        display: inline-block;
        transition: all 0.3s ease;
        margin-bottom: 0.5rem;
    }
    
    .spotify-link:hover {
        background: linear-gradient(45deg, #1ed760, #1db954);
        transform: scale(1.05);
        box-shadow: 0 4px 15px rgba(29, 185, 84, 0.3);
    }
    
    .sidebar .stMetric {
        background: rgba(157, 78, 221, 0.1);
        padding: 0.5rem;
        border-radius: 8px;
        border: 1px solid rgba(157, 78, 221, 0.2);
    }
    
    .stSelectbox label {
        color: #b794f6 !important;
    }
    
    h3 {
        color: #9d4edd;
    }
    
    /* Style pour assurer la largeur égale des colonnes */
    .element-container {
        width: 100% !important;
    }
    
    .stColumn {
        width: 100% !important;
    }
    
    .fallback-indicator {
        background: rgba(255, 193, 7, 0.1);
        border: 1px solid rgba(255, 193, 7, 0.3);
        border-radius: 8px;
        padding: 0.8rem;
        margin-bottom: 1rem;
        color: #ffc107;
        text-align: center;
    }
    
    @media (max-width: 768px) {
        .recommendations-grid {
            grid-template-columns: 1fr;
            gap: 0.8rem;
        }
        
        .song-card {
            min-height: 250px;
            padding: 1rem;
        }
    }
</style>
""", unsafe_allow_html=True)

SPOTIFY_CLIENT_ID = "aa2a7bd2dcc84f19bb479185b3224ff6"
SPOTIFY_CLIENT_SECRET = "49802f5d2d754ea8a78f01432b062d8b"
DATASET_PATH = "tracks_dataset.csv"

class MusicRecommendationSystem:
    def __init__(self):
        self.df = None
        self.spotify = None
        self.scaler = StandardScaler()
        self.tfidf_vectorizer = TfidfVectorizer(stop_words='english')

    def load_data(self, df):
        self.df = df.copy()
        self.prepare_features()

    def load_dataset_from_file(self, file_path):
        try:
            if os.path.exists(file_path):
                df = pd.read_csv(file_path)
                self.load_data(df)
                return True, f"Dataset loaded successfully: {len(df)} songs"
            else:
                return False, f"File {file_path} not found"
        except Exception as e:
            return False, f"Error loading dataset: {str(e)}"

    def setup_spotify(self, client_id=None, client_secret=None):
        try:
            if not client_id: client_id = SPOTIFY_CLIENT_ID
            if not client_secret: client_secret = SPOTIFY_CLIENT_SECRET
            client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
            self.spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
            self.spotify.search(q="test", type='track', limit=1)
            return True, "Spotify connection successful!"
        except Exception as e:
            return False, f"Spotify connection error: {str(e)}"

    def prepare_features(self):
        numeric_cols = ['bpm_estime', 'energie', 'valence', 'danceability',
                        'acousticness', 'instrumentalness', 'speechiness', 'liveness']
        for col in numeric_cols:
            if col not in self.df.columns:
                self.df[col] = np.random.rand(len(self.df))
        self.df[numeric_cols] = self.scaler.fit_transform(self.df[numeric_cols])

        context_cols = ['contexte_meteo', 'contexte_activite', 'contexte_emotionnel',
                        'contexte_social', 'contexte_lieu']
        for col in context_cols:
            if col not in self.df.columns:
                self.df[col] = 'unknown'

        self.df['contexte_combine'] = self.df[context_cols].astype(str).agg(' '.join, axis=1)

    def count_context_matches(self, row, user_context):
        return sum([
            row['contexte_meteo'] == user_context['weather'],
            row['contexte_activite'] == user_context['activity'],
            row['contexte_emotionnel'] == user_context['mood'],
            row['contexte_social'] == user_context['social'],
            row['contexte_lieu'] == user_context['location']
        ])

    def get_fallback_recommendations(self, user_context, n_recommendations=10):
        """
        Système de fallback avec stratégies progressives de relâchement des contraintes
        """
        if self.df is None:
            return [], "No fallback strategy"
        
        # Stratégie 1: Relâcher une contrainte à la fois par ordre de priorité inverse
        context_priority = [
            ('contexte_lieu', 'location', '📍 location'),         # Lieu moins prioritaire - relâché en premier
            ('contexte_social', 'social', '👥 social context'),   
            ('contexte_meteo', 'weather', '☀️ weather'),          
            ('contexte_activite', 'activity', '🏃 activity'),     
            ('contexte_emotionnel', 'mood', '😊 mood')            # Humeur prioritaire - gardée le plus longtemps
        ]
        
        for i in range(len(context_priority)):
            # Créer un filtre en gardant les contraintes prioritaires
            filter_conditions = []
            excluded_contexts = []
            kept_contexts = []
            
            for j, (col, key, display_name) in enumerate(context_priority):
                if j <= i:  # Exclure les contraintes selon la priorité (du moins au plus prioritaire)
                    excluded_contexts.append(display_name)
                else:
                    filter_conditions.append(self.df[col] == user_context[key])
                    kept_contexts.append(display_name)
            
            if filter_conditions:
                # Combiner toutes les conditions avec AND
                combined_filter = filter_conditions[0]
                for condition in filter_conditions[1:]:
                    combined_filter = combined_filter & condition
                
                filtered_df = self.df[combined_filter]
            else:
                # Si toutes les contraintes sont relâchées, prendre tout le dataset
                filtered_df = self.df
                excluded_contexts = ['📍 location', '👥 social context', '☀️ weather', '🏃 activity', '😊 mood']
                kept_contexts = []
            
            if not filtered_df.empty and len(filtered_df) >= min(3, n_recommendations):
                # Calculer les scores de similarité
                filtered_df = filtered_df.copy()
                
                if kept_contexts:
                    # Calculer le score basé sur les contextes gardés
                    active_context_keys = [key for col, key, name in context_priority if name in kept_contexts]
                    filtered_df['match_score'] = filtered_df.apply(
                        lambda row: sum([
                            row[f'contexte_{ctx}'] == user_context[ctx] 
                            for ctx in active_context_keys 
                            if f'contexte_{ctx}' in row.index
                        ]), axis=1
                    )
                    
                    # Ajouter un bonus pour les correspondances partielles des contextes exclus
                    excluded_context_keys = [key for col, key, name in context_priority if name in excluded_contexts]
                    bonus_score = filtered_df.apply(
                        lambda row: sum([
                            0.2 * (row[f'contexte_{ctx}'] == user_context[ctx]) 
                            for ctx in excluded_context_keys 
                            if f'contexte_{ctx}' in row.index
                        ]), axis=1
                    )
                    filtered_df['match_score'] += bonus_score
                else:
                    # Si aucun contexte gardé, score aléatoire
                    filtered_df['match_score'] = np.random.rand(len(filtered_df))
                
                # Sélectionner les meilleures recommandations
                top_indices = filtered_df['match_score'].nlargest(n_recommendations).index
                recommendations = []
                for idx in top_indices:
                    song_data = filtered_df.loc[idx].to_dict()
                    song_data['fallback_level'] = i + 1
                    song_data['excluded_contexts'] = excluded_contexts.copy()
                    song_data['kept_contexts'] = kept_contexts.copy()
                    recommendations.append(song_data)
                
                # Créer un message de fallback personnalisé
                if kept_contexts:
                    if len(kept_contexts) == 1:
                        fallback_msg = f"No exact matches found. Here are songs that match your {kept_contexts[0]}."
                    else:
                        fallback_msg = f"No exact matches found. Here are songs that match your {' and '.join(kept_contexts)}."
                else:
                    fallback_msg = "No exact matches found. Here are some popular songs you might enjoy."
                
                return recommendations, fallback_msg
        
        # Stratégie finale: Recommandations populaires/aléatoires
        if not self.df.empty:
            random_sample = self.df.sample(min(n_recommendations, len(self.df)))
            recommendations = []
            for idx in random_sample.index:
                song_data = random_sample.loc[idx].to_dict()
                song_data['fallback_level'] = 'random'
                song_data['excluded_contexts'] = ['📍 location', '👥 social context', '☀️ weather', '🏃 activity', '😊 mood']
                song_data['kept_contexts'] = []
                recommendations.append(song_data)
            
            return recommendations, "No exact matches found. Here are some popular songs you might enjoy."
        
        return [], "No songs available in the dataset."

    def recommend_songs(self, user_context, n_recommendations=10):
        if self.df is None:
            return [], "No recommendations"

        # Essayer d'abord la correspondance exacte
        exact_filter = (
            (self.df['contexte_meteo'] == user_context['weather']) &
            (self.df['contexte_activite'] == user_context['activity']) &
            (self.df['contexte_emotionnel'] == user_context['mood']) &
            (self.df['contexte_social'] == user_context['social']) &
            (self.df['contexte_lieu'] == user_context['location'])
        )
        
        filtered_df = self.df[exact_filter]

        if not filtered_df.empty:
            # Correspondance exacte trouvée
            user_vector = f"{user_context['weather']} {user_context['activity']} {user_context['mood']} {user_context['social']} {user_context['location']}"
            contexts = list(filtered_df['contexte_combine']) + [user_vector]
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(contexts)
            user_tfidf = tfidf_matrix[-1]
            similarities = cosine_similarity(user_tfidf, tfidf_matrix[:-1]).flatten()

            filtered_df = filtered_df.copy()
            filtered_df['match_score'] = filtered_df.apply(lambda row: self.count_context_matches(row, user_context), axis=1)
            filtered_df['final_score'] = filtered_df['match_score'] * similarities

            top_indices = filtered_df['final_score'].nlargest(n_recommendations).index
            recommendations = []
            for idx in top_indices:
                song_data = filtered_df.loc[idx].to_dict()
                song_data['fallback_level'] = 0  # Correspondance exacte
                recommendations.append(song_data)

            return recommendations, "Exact match found"
        else:
            # Aucune correspondance exacte, utiliser le système de fallback
            return self.get_fallback_recommendations(user_context, n_recommendations)

    def search_spotify_track(self, artist, title):
        if not self.spotify:
            return None
        try:
            query = f"artist:{artist} track:{title}"
            results = self.spotify.search(q=query, type='track', limit=1)
            if results['tracks']['items']:
                track = results['tracks']['items'][0]
                return {
                    'spotify_id': track['id'],
                    'preview_url': track['preview_url'],
                    'external_url': track['external_urls']['spotify'],
                    'album_image': track['album']['images'][0]['url'] if track['album']['images'] else None
                }
        except Exception as e:
            st.error(f"Spotify search error: {e}")
        return None

def display_song_card(song, recommender, spotify_connected, container):
    """Affiche une carte de recommandation musicale dans un conteneur Streamlit"""
    titre = song.get('titre', 'Unknown title')
    artiste = song.get('artiste', 'Unknown artist')
    genre = song.get('genre', 'Unknown genre')
    fallback_level = song.get('fallback_level', 0)
    kept_contexts = song.get('kept_contexts', [])
    
    # Indicateur de correspondance plus subtil
    match_indicator = ""
    if fallback_level > 0:
        if fallback_level == 'random':
            match_indicator = "🎲 Popular Pick"
        elif kept_contexts:
            if len(kept_contexts) == 1:
                match_indicator = f"✨ Matches {kept_contexts[0]}"
            else:
                match_indicator = f"✨ Partial Match"
        else:
            match_indicator = "🎵 Suggested"
    else:
        match_indicator = "✅ Perfect Match"
    
    with container:
        # Utiliser un container avec style CSS - affichage complet des titres
        st.markdown(f"""
        <div class="song-card">
            <div class="song-title">🎵 {titre}</div>
            <div class="song-artist">👨‍🎤 {artiste}</div>
            <div class="song-genre">🎭 {genre}</div>
            <div style="color: #9d4edd; font-size: 0.8rem; margin-top: 0.5rem; opacity: 0.8;">
                {match_indicator}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Actions Spotify en dessous
        if spotify_connected:
            spotify_data = recommender.search_spotify_track(artiste, titre)
            if spotify_data:
                st.markdown(f"""
                <div style="text-align: center; margin-top: 1rem;">
                    <a href="{spotify_data['external_url']}" target="_blank" class="spotify-link">
                        🎧 Listen On Spotify
                    </a>
                </div>
                """, unsafe_allow_html=True)
                
                if spotify_data['preview_url']:
                    st.audio(spotify_data['preview_url'])

def main():
    st.markdown('<h1 class="main-title">🎵 Intelligent Music Recommendation System</h1>', unsafe_allow_html=True)
    st.markdown("---")

    if 'recommender' not in st.session_state:
        st.session_state.recommender = MusicRecommendationSystem()
        st.session_state.data_loaded = False
        st.session_state.spotify_connected = False

    if not st.session_state.data_loaded:
        with st.spinner("🔄 Loading dataset..."):
            success, message = st.session_state.recommender.load_dataset_from_file(DATASET_PATH)
            if success:
                st.session_state.data_loaded = True
            else:
                st.error(message)

    if st.session_state.data_loaded and not st.session_state.spotify_connected:
        with st.spinner("🔄 Connecting to Spotify..."):
            success, message = st.session_state.recommender.setup_spotify()
            if success:
                st.session_state.spotify_connected = True
            else:
                st.warning(f"⚠️ {message}")

    if st.session_state.data_loaded:
        df = st.session_state.recommender.df
        meteo_options = sorted(df['contexte_meteo'].dropna().unique())
        activite_options = sorted(df['contexte_activite'].dropna().unique())
        humeur_options = sorted(df['contexte_emotionnel'].dropna().unique())
        social_options = sorted(df['contexte_social'].dropna().unique())
        lieu_options = sorted(df['contexte_lieu'].dropna().unique())

        st.sidebar.header("ℹ️ Dataset Information")
        st.sidebar.metric("🎵 Number of songs", len(df))
        st.sidebar.metric("🎭 Available genres", df['genre'].nunique() if 'genre' in df.columns else "N/A")
        st.sidebar.metric("👨‍🎤 Unique artists", df['artiste'].nunique() if 'artiste' in df.columns else "N/A")
            
        with st.sidebar.expander("👀 Data Preview"):
            st.dataframe(df.head())

        col1, col2 = st.columns([2, 1])
        with col1:
            st.header("🧠 Mood and Context")
            with st.form("context_form"):
                col_a, col_b = st.columns(2)
                with col_a:
                    meteo = st.selectbox("☀️ Weather", meteo_options)
                    activite = st.selectbox("🏃 Activity", activite_options)
                    lieu = st.selectbox("📍 Location", lieu_options)
                with col_b:
                    humeur = st.selectbox("😊 Mood", humeur_options)
                    social = st.selectbox("👥 Social Context", social_options)
                
                submitted = st.form_submit_button("🎵 Get Recommendations", use_container_width=True)
                if submitted:
                    with st.spinner("🔄 Generating recommendations..."):
                        user_context = {
                            'weather': meteo,
                            'activity': activite,
                            'mood': humeur,
                            'social': social,
                            'location': lieu
                        }
                        recs, fallback_msg = st.session_state.recommender.recommend_songs(user_context)
                        st.session_state.recommendations = recs
                        st.session_state.fallback_message = fallback_msg
                        st.session_state.user_context = user_context
                        
                        if not recs:
                            st.error("❌ No recommendations found even with fallback strategies.")
                        elif fallback_msg != "Exact match found":
                            st.info(f"ℹ️ {fallback_msg}")

        with col2:
            st.header("📊 Dataset Statistics")
            if 'genre' in df.columns:
                fig_genre = px.pie(
                    df, 
                    names='genre', 
                    title="Distribution by Genre", 
                    height=300,
                    color_discrete_sequence=['#9d4edd', '#7209b7', '#b794f6', '#e0aaff', '#c77dff']
                )
                fig_genre.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='white'
                )
                st.plotly_chart(fig_genre, use_container_width=True)

        # Affichage des recommandations avec cartes symétriques
        if 'recommendations' in st.session_state and st.session_state.recommendations:
            st.markdown("---")
            st.header("🎼 Personalized Recommendations")
            
           
            recommendations = st.session_state.recommendations[:6]  # Limiter à 6 recommandations
            
            # Créer des colonnes pour l'affichage symétrique
            num_cols = 3  # Nombre de colonnes
            cols = st.columns(num_cols)
            
            for i, song in enumerate(recommendations):
                col_index = i % num_cols
                display_song_card(
                    song, 
                    st.session_state.recommender, 
                    st.session_state.spotify_connected,
                    cols[col_index]
                )

if __name__ == "__main__":
    main()