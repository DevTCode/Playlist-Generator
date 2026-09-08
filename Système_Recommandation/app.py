
# app.py
from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify, send_file
import pandas as pd
import random
import io # For exporting text file
import os # For os.path.join

# Import the SpotifyManager class
from SpotifyManager import SpotifyManager 

app = Flask(__name__)
# IMPORTANT: Change this to a strong, random key in production!
app.secret_key = 'your_super_secret_key_here_please_change_this_for_security' 

# List of offensive keywords to filter
OFFENSIVE_KEYWORDS = ["bitch", "fuck", "shit", "asshole", "cunt", "motherfucker", "nigga", "nigger", "whore", "slut"]

# Themes for emotional colors (used in CSS)
THEMES = {
    "joyeux": {"primary": "#9933CC", "secondary": "#CC66FF", "bg": "linear-gradient(135deg, #9933CC, #CC66FF)", "desc": "Ambiance mauve éclatante"},
    "energique": {"primary": "#FF00FF", "secondary": "#FF66FF", "bg": "linear-gradient(135deg, #FF00FF, #FF66FF)", "desc": "Énergie rose vive"},
    "calme": {"primary": "#2B6CB0", "secondary": "#4299E1", "bg": "linear-gradient(135deg, #2B6CB0, #4299E1)", "desc": "Sérénité"}, # inchangé par rapport à la demande précédente
    "nostalgique": {"primary": "#4A4A4A", "secondary": "#666666", "bg": "linear-gradient(135deg, #4A4A4A, #666666)", "desc": "Gris foncé mélancolique"},
    "romantique": {"primary": "#CC0000", "secondary": "#FF3333", "bg": "linear-gradient(135deg, #CC0000, #FF3333)", "desc": "Tendresse rouge passion"},
    "neutre": {"primary": "#A78BFA", "secondary": "#6B23B7", "bg": "linear-gradient(135deg, #A78BFA, #6B23B7)", "desc": "Équilibre sombre"}
}

# Questions for the quiz
QUESTIONS = [
    ("💬 Comment vous sentez-vous ?", "emotionnel", ["joyeux", "energique", "calme", "nostalgique", "romantique", "neutre"]),
    ("🌤️ Quel temps fait-it ?", "meteo", ["ensoleille", "nuageux", "pluvieux", "chaud", "froid", "neutre"]),
    ("🏃 Que faites-vous en ce moment ?", "activite", ["sport", "detente", "travail", "fete", "cuisine", "etude", "conduite", "loisir"]),
    ("📍 Où êtes-vous ?", "lieu", ["maison", "plage", "voiture", "cafe", "parc", "club", "exterieur", "bibliotheque", "restaurant", "bureau", "salle_sport"]),
    ("👥 Avec qui êtes-vous ?", "social", ["seul", "amis", "famille", "groupe", "couple"]),
    ("🕐 Quel moment ?", "temporel", ["matin", "apres_midi", "soiree", "nuit", "journee", "weekend"])
]

# Load data globally once
# Use os.path.join for cross-platform path compatibility
DATASET_PATH = os.path.join(os.path.dirname(__file__), "tracks_dataset_enriched.csv")
try:
    df = pd.read_csv(DATASET_PATH)
    # Ensure 'id' column exists and is unique for proper indexing/identification
    if 'id' not in df.columns:
        df['id'] = range(len(df)) # Add a simple ID if not present
    df.set_index('id', inplace=True) # Assuming 'id' is a unique identifier, potentially a string Spotify ID
    print("Dataset loaded successfully!")
except FileNotFoundError:
    print(f"Error: Dataset not found at {DATASET_PATH}. Please ensure it's in the same directory as app.py.")
    df = pd.DataFrame() # Create empty DataFrame to prevent errors
except Exception as e:
    print(f"Error loading dataset: {e}")
    df = pd.DataFrame() 

# Initialize SpotifyManager once globally
spotify_manager = SpotifyManager()

# --- Utility Functions ---

def check_perfect_match(song, answers):
    context_columns = ['contexte_emotionnel', 'contexte_meteo', 'contexte_activite', 
                        'contexte_lieu', 'contexte_social', 'contexte_temporel']
    
    matches = 0
    total_contexts = 0
    
    for context_type, user_answer in answers.items():
        col_name = f"contexte_{context_type}"
        if col_name in song.index:
            total_contexts += 1
            song_context = str(song[col_name]).lower()
            if song_context == str(user_answer).lower():
                matches += 1
    
    return matches == total_contexts and total_contexts > 0, matches, total_contexts

def calculate_score(song, answers):
    """
    Calcule le score de correspondance d'une chanson avec les réponses utilisateur
    Si correspondance parfaite = 100% automatiquement
    """

    # VÉRIFICATION CORRESPONDANCE PARFAITE EN PREMIER
    is_perfect_match, matches, total_contexts = check_perfect_match(song, answers)

    # Si correspondance parfaite, retourner 100% directement
    if is_perfect_match:
        return 100

    # Sinon, calculer le score normalement
    score = 0

    # === SCORE CONTEXTUEL (50 points) ===
    context_weights = {
        'emotionnel': 20,  # Le plus important
        'activite': 15,    # Très important
        'meteo': 5,        # Influence modérée
        'lieu': 4,         # Influence faible
        'social': 3,       # Influence faible
        'temporel': 3      # Influence faible
    }

    for context, weight in context_weights.items():
        col = f"contexte_{context}"
        if col in song.index and context in answers:
            if str(song[col]).lower() == str(answers[context]).lower():
                score += weight

    # === SCORE AUDIO FEATURES (25 points) ===
    audio_score = 0

    # Valence (8 points) - Directly linked to emotional context
    if 'emotionnel' in answers and 'valence' in song.index:
        valence = float(song['valence']) if pd.notnull(song['valence']) else 0.5
        mood = answers['emotionnel']
        mood_valence_ranges = {
            'joyeux': (0.6, 1.0),
            'energique': (0.7, 1.0),
            'calme': (0.2, 0.6),
            'nostalgique': (0.0, 0.4),
            'romantique': (0.3, 0.7),
            'neutre': (0.3, 0.7)
        }
        if mood in mood_valence_ranges:
            min_val, max_val = mood_valence_ranges[mood]
            if min_val <= valence <= max_val:
                audio_score += 8

    # Energie (8 points) - Modulated by emotional and temporal state
    if 'energie' in song.index:
        energy = float(song['energie']) if pd.notnull(song['energie']) else 0.5
        
        # Apply mood-based energy scoring
        if 'emotionnel' in answers:
            mood = answers['emotionnel']
            mood_energy_ranges = {
                'joyeux': (0.5, 1.0),
                'energique': (0.7, 1.0),
                'calme': (0.0, 0.5),
                'nostalgique': (0.2, 0.6),
                'romantique': (0.3, 0.7),
                'neutre': (0.3, 0.7)
            }
            if mood in mood_energy_ranges:
                min_val, max_val = mood_energy_ranges[mood]
                if min_val <= energy <= max_val:
                    audio_score += 6 # Give primary points for mood match

        # Apply temporal-based energy scoring (additive bonus)
        if 'temporel' in answers:
            temporal = answers['temporel']
            temporal_energy_ranges = {
                'matin': (0.4, 0.8),    # Moderate energy for morning
                'apres_midi': (0.5, 0.9), # Slightly higher for afternoon
                'soiree': (0.6, 1.0),   # High energy for evening (party, etc.)
                'nuit': (0.0, 0.4),     # Low energy for night (sleep, calm)
                'journee': (0.4, 0.8),  # General day
                'weekend': (0.5, 1.0)   # Higher flexibility for weekend
            }
            if temporal in temporal_energy_ranges:
                min_val, max_val = temporal_energy_ranges[temporal]
                if min_val <= energy <= max_val:
                    # Add a smaller bonus if temporal also matches
                    audio_score += 2
    
    # Danceability (6 points) - Adapted based on emotion, activity and social context
    if 'danceability' in song.index:
        danceability = float(song['danceability']) if pd.notnull(song['danceability']) else 0.5
        
        # Define danceability ranges based on emotion, activity, and social context
        contextual_dance_ranges = {
            # Emotional contexts
            'joyeux': (0.6, 1.0),      # High danceability for happy
            'energique': (0.7, 1.0),   # Very high for energetic
            'calme': (0.1, 0.4),       # Low for calm
            'nostalgique': (0.2, 0.5), # Low to moderate for nostalgic
            'romantique': (0.3, 0.7),  # Moderate for romantic
            'neutre': (0.3, 0.7),      # Moderate for neutral

            # Activity contexts
            'sport': (0.6, 1.0),      # High for sport
            'fete': (0.7, 1.0),       # Very high for party
            'detente': (0.2, 0.5),    # Low for relaxation
            'etude': (0.1, 0.4),      # Very low for study
            'travail': (0.1, 0.4),    # Very low for work
            'cuisine': (0.4, 0.8),    # Moderate for cooking
            'conduite': (0.3, 0.7),   # Moderate for driving
            'loisir': (0.5, 0.9),     # Moderate to high for general leisure

            # Social contexts
            'amis': (0.6, 0.9),       # High for friends gathering
            'groupe': (0.6, 0.9),     # High for group
            'seul': (0.3, 0.7),       # Moderate flexibility when alone
            'famille': (0.4, 0.8),    # Moderate for family time
            'couple': (0.4, 0.8)      # Moderate to high for romantic/intimate settings
        }
        
        # Check contexts in order of priority (e.g., activity/social might be stronger than general emotion for danceability)
        contexts_to_check = []
        if 'activite' in answers: contexts_to_check.append(answers['activite'])
        if 'social' in answers: contexts_to_check.append(answers['social'])
        if 'emotionnel' in answers: contexts_to_check.append(answers['emotionnel'])

        matched_danceability = False
        for context_value in contexts_to_check:
            if context_value in contextual_dance_ranges:
                min_dance, max_dance = contextual_dance_ranges[context_value]
                if min_dance <= danceability <= max_dance:
                    # Grant points based on the first matching and relevant context
                    audio_score += 6
                    matched_danceability = True
                    break # Only apply points once for danceability

    # BPM (3 points) - Linked to social context primarily
    if 'social' in answers and 'bpm_estime' in song.index:
        social_context = answers['social']
        bpm = float(song['bpm_estime']) if pd.notnull(song['bpm_estime']) else 120

        social_bpm_ranges = {
            'fete': (110, 140),       # High BPM for parties
            'amis': (100, 130),       # Moderate to high for friends gatherings
            'groupe': (100, 130),     # Moderate to high for group settings
            'seul': (80, 120),        # Flexible for alone time
            'famille': (80, 120),     # Flexible for family time
            'couple': (70, 110)       # Lower for romantic/calm settings
        }

        if social_context in social_bpm_ranges:
            min_bpm, max_bpm = social_bpm_ranges[social_context]
            if min_bpm <= bpm <= max_bpm:
                audio_score += 3

    score += audio_score

    # === SCORES SPÉCIALISÉS (20 points) ===
    specialized_score = 0

    if 'activite' in answers:
        activity = answers['activite']

        # Sport suitability (5 points)
        if activity == 'sport' and 'sport_suitability' in song.index:
            sport_suit = float(song['sport_suitability']) if pd.notnull(song['sport_suitability']) else 0
            if sport_suit >= 0.7:
                specialized_score += 5
            elif sport_suit >= 0.5:
                specialized_score += 3

        # Relax suitability (5 points)
        elif activity == 'detente' and 'relax_suitability' in song.index:
            relax_suit = float(song['relax_suitability']) if pd.notnull(song['relax_suitability']) else 0
            if relax_suit >= 0.7:
                specialized_score += 5
            elif relax_suit >= 0.5:
                specialized_score += 3

        # Study suitability (5 points)
        elif activity in ['etude', 'travail'] and 'study_suitability' in song.index:
            study_suit = float(song['study_suitability']) if pd.notnull(song['study_suitability']) else 0
            if study_suit >= 0.7:
                specialized_score += 5
            elif study_suit >= 0.5:
                specialized_score += 3

        # Party factor (5 points)
        elif activity == 'fete' and 'party_factor' in song.index:
            party_factor = float(song['party_factor']) if pd.notnull(song['party_factor']) else 0
            if party_factor >= 0.7:
                specialized_score += 5
            elif party_factor >= 0.5:
                specialized_score += 3

    # Mood score général (5 points)
    if 'mood_score' in song.index:
        mood_score = float(song['mood_score']) if pd.notnull(song['mood_score']) else 0
        if mood_score >= 0.8:
            specialized_score += 5
        elif mood_score >= 0.6:
            specialized_score += 3
        elif mood_score >= 0.4:
            specialized_score += 1

    score += specialized_score

    # === BONUS POPULARITÉ ET DIVERSITÉ (5 points) ===
    bonus_score = 0

    # Bonus popularité contextuelle
    if 'context_popularity_score' in song.index:
        pop_score = float(song['context_popularity_score']) if pd.notnull(song['context_popularity_score']) else 0
        if pop_score >= 0.7:
            bonus_score += 2
        elif pop_score >= 0.5:
            bonus_score += 1

    # Bonus diversité
    if 'diversity_index' in song.index:
        diversity = float(song['diversity_index']) if pd.notnull(song['diversity_index']) else 0
        if diversity >= 0.6:
            bonus_score += 2
        elif diversity >= 0.4:
            bonus_score += 1

    # Bonus organic score (pour authenticité)
    if 'organic_score' in song.index:
        organic = float(song['organic_score']) if pd.notnull(song['organic_score']) else 0
        if organic >= 0.7:
            bonus_score += 1

    score += bonus_score

    return min(score, 100)  # Limitation à 100 points maximum

def get_recommendations(df, answers, exclude_song_indices=None, num=6):
    if exclude_song_indices is None:
        exclude_song_indices = set()

    # Filter the DataFrame to include only available songs and exclude already recommended
    available = df.loc[~df.index.isin(list(exclude_song_indices))].copy()

    # Filter offensive song titles
    available = available[~available['titre'].astype(str).str.lower().apply(
        lambda x: any(keyword in x for keyword in OFFENSIVE_KEYWORDS)
    )]

    if available.empty:
        return [] # Return an empty list instead of empty DataFrame for consistency

    all_candidate_songs = []

    # Calculate score and perfect match status for each available song
    for idx, song in available.iterrows():
        is_perfect, matches, total = check_perfect_match(song, answers)
        score = calculate_score(song, answers)

        # Convert song Series to dict directly for easier storage and manipulation
        song_with_info = song.copy().to_dict()
        song_with_info['score'] = score
        song_with_info['is_perfect_match'] = is_perfect
        song_with_info['matches'] = matches
        song_with_info['total_contexts'] = total
        song_with_info['original_index'] = idx # Store the original DataFrame index (which is the Spotify ID)

        all_candidate_songs.append(song_with_info)

    # CORRECTION: Tri prioritaire par score, puis par correspondances parfaites
    # Tri: Perfect matches first, puis par SCORE (desc), puis par nombre de matches (desc)
    sorted_candidates = sorted(
        all_candidate_songs,
        key=lambda x: (
            x['is_perfect_match'],  # Perfect matches en premier (True > False)
            x['score'],             # Score le plus élevé en priorité
            x['matches'],           # Nombre de correspondances contextuelles
            x.get('bpm_estime', 0)  # BPM en dernier critère
        ),
        reverse=True # Tri décroissant
    )

    recommendations_list = []
    used_artists = set()

    # Select top N recommendations, avoiding too many from same artist if possible
    for song in sorted_candidates:
        if len(recommendations_list) >= num:
            break

        artist = str(song.get('artiste', '')).lower()
        # Add to recommendations if artist is not already used OR if we still need to fill half the slots
        # This ensures some artist diversity but doesn't strictly limit only one song per artist.
        if artist not in used_artists or len(recommendations_list) < num // 2:
            recommendations_list.append(song)
            used_artists.add(artist)

    return recommendations_list

def is_song_in_playlist(song_index, playlist_songs):
    """
    Vérifie si une chanson (identifiée par son index) existe déjà dans une playlist.
    """
    for existing_song in playlist_songs:
        if existing_song.get('original_index') == song_index:
            return True
    return False

# --- Flask Routes ---

@app.route('/', methods=['GET', 'POST'])
def index():
    # Initialize session variables if they don't exist
    if 'step' not in session:
        session['step'] = 0
        session['answers'] = {}
        session['playlists'] = {}
        session['current_view'] = "quiz"
        # Store original df indices (Spotify IDs) of all songs ever recommended in this session
        session['all_recommended_song_indices'] = [] 
        # Stores the current batch of songs being displayed
        session['displayed_songs_data'] = [] 

    # Handle quiz answers (POST request)
    if request.method == 'POST':
        form_data = request.form
        if 'answer' in form_data:
            current_question = QUESTIONS[session['step']]
            context_key = current_question[1]
            session['answers'][context_key] = form_data['answer']
            session['step'] += 1
            session['current_view'] = "quiz" # Stay on quiz view until finished
            # If quiz is completed, trigger recommendations to be generated on next GET
            if session['step'] >= len(QUESTIONS):
                session['displayed_songs_data'] = [] # Clear existing to force new recommendations
                # DO NOT clear all_recommended_song_indices here. It should persist across quiz restarts or "new suggestions" clicks
                # if you want to avoid re-recommending the exact same songs.
                # However, if starting a NEW quiz, session.clear() in restart_quiz handles a full reset.
            return redirect(url_for('index'))
        
        elif 'prev_question' in form_data:
            if session['step'] > 0:
                session['step'] -= 1
            session['current_view'] = "quiz"
            return redirect(url_for('index'))
        
        elif 'new_suggestions' in form_data:
            session['displayed_songs_data'] = [] # Clear previous display
            # IMPORTANT RECTIFICATION: Do NOT clear 'all_recommended_song_indices' here.
            # This ensures that when new suggestions are fetched, previously seen songs (in this session) are excluded.
            # Clearing it would result in the same initial suggestions being shown again.
            session['current_view'] = "recommendations"
            return redirect(url_for('index'))

    current_mood = session['answers'].get('emotionnel', 'neutre')
    theme_data = THEMES.get(current_mood, THEMES["neutre"])

    if session['step'] < len(QUESTIONS):
        # Display quiz
        question_text, context_key, options = QUESTIONS[session['step']]
        return render_template(
            'index.html', 
            view="quiz",
            question=question_text,
            context_key=context_key,
            options=options,
            current_step=session['step'],
            total_steps=len(QUESTIONS),
            theme=theme_data
        )
    else:
        # Display recommendations
        session['current_view'] = "recommendations"
        
        # If recommendations not yet generated for current answers or forced refresh
        if not session['displayed_songs_data']: # Check if list is empty
             # Get recommendations, excluding previously recommended in this session
            recommended_songs_list = get_recommendations(df, session['answers'], 
                                                        exclude_song_indices=set(session['all_recommended_song_indices']))

            if recommended_songs_list:
                # Store the full song data (including calculated scores, etc.) for rendering
                session['displayed_songs_data'] = recommended_songs_list
                # Add unique indices (Spotify IDs) to the list of all recommended indices in this session
                session['all_recommended_song_indices'].extend([s['original_index'] for s in recommended_songs_list])
            else:
                flash("Aucune recommandation trouvée. Essayez de modifier vos réponses ou réinitialisez le questionnaire.", "warning")
                session['displayed_songs_data'] = [] # Ensure it's empty if no recommendations

        # Fetch Spotify info for displayed songs
        # We need to do this here before passing to template, as template can't call Python functions
        songs_with_spotify_info = []
        has_perfect_matches = False
        has_partial_matches = False

        if session['displayed_songs_data']:
            for song_data in session['displayed_songs_data']:
                # Ensure song_data is a dictionary, not a Series if coming direct from df
                song_dict = dict(song_data) if isinstance(song_data, pd.Series) else song_data

                spotify_info = spotify_manager.search_track(song_dict.get('artiste', ''), song_dict.get('titre', ''))
                song_dict['spotify_info'] = spotify_info
                
                # Recalculate perfect match for current display, using original df data
                # This ensures consistency even if song_data came from session.
                # Use .loc with the string original_index (Spotify ID)
                original_song_df_row = df.loc[song_dict['original_index']] 
                is_perfect_match_current_song = check_perfect_match(original_song_df_row, session['answers'])[0]
                song_dict['is_perfect_match'] = is_perfect_match_current_song
                
                if is_perfect_match_current_song:
                    has_perfect_matches = True
                else:
                    has_partial_matches = True

                songs_with_spotify_info.append(song_dict)
        
        perfect_matches_count = sum(1 for s in songs_with_spotify_info if s.get('is_perfect_match'))

        return render_template(
            'index.html', 
            view="recommendations",
            songs=songs_with_spotify_info,
            playlist_names=list(session['playlists'].keys()),
            perfect_matches_count=perfect_matches_count,
            total_recommendations_count=len(songs_with_spotify_info),
            has_partial_matches=has_partial_matches, # Passed for Jinja2 logic
            theme=theme_data
        )

@app.route('/restart_quiz')
def restart_quiz():
    # Sauvegarder les playlists avant de nettoyer la session
    saved_playlists = session.get('playlists', {}).copy()
    
    # Effacer toute la session
    session.clear()
    
    # Restaurer les playlists sauvegardées
    session['playlists'] = saved_playlists
    
    # Réinitialiser les variables de session nécessaires
    session['step'] = 0
    session['answers'] = {}
    session['current_view'] = "quiz"
    session['all_recommended_song_indices'] = []
    session['displayed_songs_data'] = []
    
    return redirect(url_for('index'))

@app.route('/help')
def show_help():
    session['current_view'] = "help"
    current_mood = session['answers'].get('emotionnel', 'neutre')
    theme_data = THEMES.get(current_mood, THEMES["neutre"])
    return render_template('index.html', view="help", theme=theme_data)

@app.route('/playlists', methods=['GET', 'POST'])
def manage_playlists():
    session['current_view'] = "manage_playlists"
    current_mood = session['answers'].get('emotionnel', 'neutre')
    theme_data = THEMES.get(current_mood, THEMES["neutre"])

    if request.method == 'POST':
        if 'new_playlist_name' in request.form:
            new_playlist_name = request.form['new_playlist_name'].strip()
            if new_playlist_name:
                if new_playlist_name not in session['playlists']:
                    session['playlists'][new_playlist_name] = []
                    flash(f"Playlist '{new_playlist_name}' créée avec succès !", "success")
                else:
                    flash(f"La playlist '{new_playlist_name}' existe déjà.", "warning")
            else:
                flash("Veuillez entrer un nom pour la playlist.", "warning")
            return redirect(url_for('manage_playlists'))
        
        elif 'delete_playlist' in request.form:
            playlist_to_delete = request.form['delete_playlist']
            if playlist_to_delete in session['playlists']:
                del session['playlists'][playlist_to_delete]
                flash(f"Playlist '{playlist_to_delete}' supprimée.", "success")
            return redirect(url_for('manage_playlists'))

    return render_template('playlists.html', 
                            playlists=session.get('playlists', {}), 
                            theme=theme_data)

@app.route('/add_to_playlist', methods=['POST'])
def add_to_playlist():
    # Keep as string, as df.index is likely string Spotify IDs if set_index('id') was used
    song_original_index = request.form['song_original_index'] 
    playlist_name = request.form['playlist_name']

    # For debugging: Print received data
    print(f"Attempting to add song with original_index: {song_original_index} to playlist: {playlist_name}")

    # Retrieve the full song data from the original DataFrame using the index (which is now a string Spotify ID)
    song_full_data = df.loc[song_original_index].to_dict()

    # Get Spotify info (it might have been fetched already, but re-fetch for safety or pass from frontend if available)
    spotify_info = spotify_manager.search_track(song_full_data.get('artiste', ''), song_full_data.get('titre', ''))
    song_full_data['spotify_info'] = spotify_info
    song_full_data['original_index'] = song_original_index  # Ajouter l'index original

    if playlist_name not in session['playlists']:
        session['playlists'][playlist_name] = []

    # Vérifier si la chanson existe déjà dans la playlist
    if is_song_in_playlist(song_original_index, session['playlists'][playlist_name]):
        flash(f"'{song_full_data['titre']}' est déjà dans la playlist '{playlist_name}'.", "warning")
        print(f"'{song_full_data['titre']}' already in playlist '{playlist_name}'.")
    else:
        # Ajouter la chanson à la playlist
        session['playlists'][playlist_name].append(song_full_data)
        flash(f"'{song_full_data['titre']}' ajouté à la playlist '{playlist_name}' avec succès !", "success")
        print(f"Successfully added '{song_full_data['titre']}' to playlist '{playlist_name}'.")
    
    # Redirect back to index (which will show recommendations if quiz is done)
    return redirect(url_for('index')) 

@app.route('/view_playlist/<playlist_name>')
def view_playlist(playlist_name):
    session['current_view'] = "view_playlist"
    current_mood = session['answers'].get('emotionnel', 'neutre')
    theme_data = THEMES.get(current_mood, THEMES["neutre"])
    
    songs_in_playlist = session['playlists'].get(playlist_name, [])
    
    return render_template('view_playlist.html', 
                            playlist_name=playlist_name, 
                            songs=songs_in_playlist,
                            theme=theme_data)

@app.route('/remove_from_playlist', methods=['POST'])
def remove_from_playlist():
    playlist_name = request.form['playlist_name']
    # This is the index within the list of songs in THAT specific playlist, NOT the df index
    song_index_in_playlist = int(request.form['song_index_in_playlist']) 

    if playlist_name in session['playlists'] and 0 <= song_index_in_playlist < len(session['playlists'][playlist_name]):
        removed_song = session['playlists'][playlist_name].pop(song_index_in_playlist)
        flash(f"'{removed_song.get('titre', 'Chanson')}' supprimé de la playlist '{playlist_name}'.", "success")
    else:
        flash("Erreur lors de la suppression de la chanson.", "error")
    
    return redirect(url_for('view_playlist', playlist_name=playlist_name))

@app.route('/export_playlist/<playlist_name>')
def export_playlist(playlist_name):
    songs = session['playlists'].get(playlist_name, [])
    if not songs:
        flash(f"La playlist '{playlist_name}' est vide, rien à exporter.", "warning")
        return redirect(url_for('view_playlist', playlist_name=playlist_name))

    txt_content = f"Playlist: {playlist_name}\n\n"
    for i, song in enumerate(songs):
        title = song.get('titre', 'Titre inconnu')
        artist = song.get('artiste', 'Artiste inconnu')
        spotify_url = song.get('spotify_info', {}).get('external_url', 'N/A')
        txt_content += f"{i+1}. {title} - {artist} (Spotify: {spotify_url})\n"
    
    buffer = io.BytesIO(txt_content.encode('utf-8'))
    return send_file(buffer, 
                      mimetype='text/plain', 
                      as_attachment=True, 
                      download_name=f"{playlist_name}_playlist.txt")


if __name__ == '__main__':
    app.run(debug=True, port=5001) # Changez le port ici. Vous pouvez utiliser 5001, 8000, 8080, etc.