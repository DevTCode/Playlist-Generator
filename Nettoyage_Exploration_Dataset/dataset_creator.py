import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import numpy as np
import time
import logging
import random

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleDatasetCreator:
    """Version corrigée et simplifiée"""
    
    def __init__(self, client_id: str, client_secret: str):
        self.sp = spotipy.Spotify(
            client_credentials_manager=SpotifyClientCredentials(
                client_id=client_id,
                client_secret=client_secret
            )
        )
        logger.info("✅ API Spotify configurée")
        
        # Genres enrichis
        self.genres = {
            'pop': {'energy': 0.75, 'valence': 0.80, 'tempo': 125},
            'rock': {'energy': 0.85, 'valence': 0.65, 'tempo': 140},
            'electronic': {'energy': 0.90, 'valence': 0.70, 'tempo': 128},
            'hip-hop': {'energy': 0.75, 'valence': 0.60, 'tempo': 95},
            'jazz': {'energy': 0.50, 'valence': 0.65, 'tempo': 120},
            'classical': {'energy': 0.35, 'valence': 0.55, 'tempo': 80},
            'folk': {'energy': 0.45, 'valence': 0.70, 'tempo': 110},
            'reggae': {'energy': 0.65, 'valence': 0.85, 'tempo': 75},
            'blues': {'energy': 0.60, 'valence': 0.45, 'tempo': 90},
            'country': {'energy': 0.60, 'valence': 0.75, 'tempo': 120},
            'metal': {'energy': 0.95, 'valence': 0.50, 'tempo': 150},
            'indie': {'energy': 0.65, 'valence': 0.60, 'tempo': 115}
        }
        
        # Contextes
        self.contextes = {
            'temporel': ['matin', 'journee', 'apres-midi', 'soiree', 'nuit', 'weekend'],
            'meteo': ['ensoleille', 'nuageux', 'pluvieux', 'neutre', 'orageux', 'froid', 'chaud'],
            'activite': ['sport', 'travail', 'detente', 'fete', 'loisir', 'etude', 'conduite', 'cuisine'],
            'emotionnel': ['joyeux', 'triste', 'motive', 'calme', 'romantique', 'energique', 'nostalgique'],
            'social': ['seul', 'amis', 'famille', 'groupe', 'couple', 'collegues', 'enfants'],
            'lieu': ['maison', 'exterieur', 'club', 'voiture', 'bureau', 'cafe', 'plage', 'restaurant']
        }
    
    def search_tracks(self, count: int = 1000):
        """Recherche de tracks"""
        logger.info(f"🎵 Recherche de {count} tracks...")
        
        terms = ['pop', 'rock', 'electronic', 'hip hop', 'jazz', 'classical', 'folk', 'reggae',
                'blues', 'country', 'metal', 'indie', 'happy', 'sad', 'energetic', 'chill',
                'party', 'workout', 'romantic', 'dance', 'relax', '2020', '2010', '2000']
        
        all_tracks = []
        per_term = count // len(terms)
        
        for term in terms:
            try:
                results = self.sp.search(q=term, type='track', limit=per_term, market='US')
                if results and 'tracks' in results:
                    for track in results['tracks']['items']:
                        if self.is_valid(track):
                            all_tracks.append(track)
                time.sleep(0.1)
            except Exception as e:
                logger.warning(f"Erreur {term}: {e}")
        
        # Déduplication
        unique = {t['id']: t for t in all_tracks}
        return list(unique.values())
    
    def is_valid(self, track):
        """Validation track"""
        return (track and track.get('id') and not track.get('is_local', False) 
                and track.get('artists') and 30000 <= track.get('duration_ms', 0) <= 600000)
    
    def detect_genre(self, artist, title):
        """Détection genre simple"""
        text = f"{artist} {title}".lower()
        for genre in self.genres:
            if genre in text or any(word in text for word in [genre.replace('-', ' ')]):
                return genre
        return 'pop'  # défaut
    
    def estimate_features(self, track, genre):
        """Estimation cohérente des features"""
        base = self.genres[genre]
        popularity = track.get('popularity', 50)
        
        # Base avec variation contrôlée
        energie = max(0.1, min(0.95, base['energy'] + random.uniform(-0.15, 0.15)))
        valence = max(0.1, min(0.95, base['valence'] + random.uniform(-0.15, 0.15)))
        
        # Cohérence énergie-valence (éviter les extrêmes contradictoires)
        if energie > 0.8 and valence < 0.3:  # Très énergique mais triste
            valence = max(0.4, valence + 0.2)  # Augmenter un peu la valence
        elif energie < 0.3 and valence > 0.9:  # Très peu énergique mais très joyeux
            energie = max(0.4, energie + 0.2)  # Augmenter un peu l'énergie
        
        # Danceability cohérent avec énergie
        danceability = max(0.1, min(0.95, (energie * 0.7 + valence * 0.3) + random.uniform(-0.1, 0.1)))
        
        # Acousticness inversement lié à l'énergie
        acousticness = max(0.05, min(0.9, (1 - energie * 0.6) + random.uniform(-0.2, 0.2)))
        
        # Instrumentalness basé sur genre
        if genre in ['classical', 'jazz']:
            instrumentalness = random.uniform(0.3, 0.8)
        elif genre == 'electronic':
            instrumentalness = random.uniform(0.4, 0.9)
        elif genre == 'hip-hop':
            instrumentalness = random.uniform(0.0, 0.2)
        else:
            instrumentalness = random.uniform(0.0, 0.4)
        
        # Speechiness basé sur genre
        if genre == 'hip-hop':
            speechiness = random.uniform(0.15, 0.4)
        elif genre in ['pop', 'rock', 'country']:
            speechiness = random.uniform(0.03, 0.12)
        else:
            speechiness = random.uniform(0.02, 0.08)
        
        # Liveness standard
        liveness = random.uniform(0.05, 0.35)
        
        # Tempo cohérent avec énergie
        base_tempo = base['tempo']
        if energie > 0.8:
            tempo = base_tempo + random.uniform(10, 30)
        elif energie < 0.4:
            tempo = base_tempo + random.uniform(-20, -5)
        else:
            tempo = base_tempo + random.uniform(-10, 15)
        
        tempo = max(60, min(200, tempo))
        
        # Boost popularité pour cohérence
        if popularity > 70:
            energie = min(0.95, energie + 0.05)
            valence = min(0.95, valence + 0.05)
        
        return {
            'energie': energie,
            'valence': valence,
            'danceability': danceability,
            'acousticness': acousticness,
            'instrumentalness': instrumentalness,
            'speechiness': speechiness,
            'liveness': liveness,
            'tempo': tempo
        }
    
    def assign_context(self, features, genre):
        """Attribution contextuelle COHÉRENTE"""
        energie = features['energie']
        valence = features['valence']
        danceability = features['danceability']
        acousticness = features['acousticness']
        tempo = features['tempo']
        
        context = {}
        
        # 1. CONTEXTE ÉMOTIONNEL (priorité - influence les autres)
        if valence > 0.8 and energie > 0.7:
            context['emotionnel'] = 'joyeux'
        elif valence > 0.7 and energie > 0.8:
            context['emotionnel'] = 'energique'
        elif energie > 0.7 and valence > 0.6:
            context['emotionnel'] = 'motive'
        elif valence < 0.3:
            context['emotionnel'] = 'triste'
        elif energie < 0.4:
            context['emotionnel'] = 'calme'
        elif valence > 0.6 and acousticness > 0.5:
            context['emotionnel'] = 'romantique'
        elif valence < 0.5 and acousticness > 0.6:
            context['emotionnel'] = 'nostalgique'
        else:
            context['emotionnel'] = 'neutre'
        
        # 2. CONTEXTE TEMPOREL (basé sur énergie et émotion)
        if context['emotionnel'] in ['calme', 'triste', 'nostalgique'] or energie < 0.3:
            context['temporel'] = random.choice(['nuit', 'soiree'])
        elif context['emotionnel'] == 'joyeux' and danceability > 0.7:
            context['temporel'] = 'weekend'
        elif energie < 0.5 and acousticness > 0.6:
            context['temporel'] = 'matin'
        elif energie > 0.7:
            context['temporel'] = 'journee'
        else:
            context['temporel'] = 'apres-midi'
        
        # 3. CONTEXTE ACTIVITÉ (basé sur énergie, tempo et émotion)
        if tempo > 130 and energie > 0.7:
            context['activite'] = 'sport'
        elif context['emotionnel'] in ['joyeux', 'energique'] and danceability > 0.8:
            context['activite'] = 'fete'
        elif energie < 0.4 and acousticness > 0.6:
            context['activite'] = random.choice(['etude', 'travail'])
        elif context['emotionnel'] in ['calme', 'romantique']:
            context['activite'] = 'detente'
        elif energie > 0.5 and valence > 0.6:
            context['activite'] = random.choice(['conduite', 'cuisine'])
        else:
            context['activite'] = 'loisir'
        
        # 4. CONTEXTE MÉTÉO (basé sur valence et émotion)
        if context['emotionnel'] in ['joyeux', 'energique'] or valence > 0.8:
            context['meteo'] = random.choice(['ensoleille', 'chaud'])
        elif context['emotionnel'] in ['triste', 'nostalgique'] or valence < 0.4:
            context['meteo'] = random.choice(['pluvieux', 'nuageux'])
        elif context['emotionnel'] == 'calme':
            context['meteo'] = random.choice(['neutre', 'froid'])
        else:
            context['meteo'] = 'neutre'
        
        # 5. CONTEXTE SOCIAL (basé sur activité et émotion)
        if context['activite'] in ['fete', 'sport'] or danceability > 0.8:
            context['social'] = random.choice(['groupe', 'amis'])
        elif context['emotionnel'] == 'romantique' or (acousticness > 0.6 and valence > 0.6):
            context['social'] = 'couple'
        elif context['activite'] in ['etude', 'travail'] or acousticness > 0.7:
            context['social'] = 'seul'
        elif context['emotionnel'] == 'joyeux' and valence > 0.7:
            context['social'] = random.choice(['amis', 'famille'])
        elif context['activite'] == 'travail':
            context['social'] = 'collegues'
        else:
            context['social'] = random.choice(['famille', 'amis'])
        
        # 6. CONTEXTE LIEU (basé sur activité, social et énergie)
        if context['activite'] == 'sport':
            context['lieu'] = random.choice(['exterieur', 'salle_sport'])
        elif context['activite'] == 'fete' and energie > 0.8:
            context['lieu'] = 'club'
        elif context['activite'] in ['etude', 'travail']:
            context['lieu'] = random.choice(['bureau', 'bibliotheque']) if context['activite'] == 'etude' else 'bureau'
        elif context['social'] == 'couple' and context['emotionnel'] == 'romantique':
            context['lieu'] = random.choice(['restaurant', 'maison'])
        elif context['activite'] == 'conduite':
            context['lieu'] = 'voiture'
        elif acousticness > 0.6 or context['emotionnel'] in ['calme', 'nostalgique']:
            context['lieu'] = random.choice(['maison', 'cafe'])
        elif context['meteo'] in ['ensoleille', 'chaud'] and valence > 0.7:
            context['lieu'] = random.choice(['exterieur', 'plage', 'parc'])
        elif context['social'] in ['amis', 'groupe'] and energie > 0.6:
            context['lieu'] = random.choice(['cafe', 'restaurant', 'exterieur'])
        else:
            context['lieu'] = 'maison'
        
        return context
    
    def calculate_rating(self, track, features):
        """Calcul note avec cohérence améliorée"""
        pop_score = track.get('popularity', 0) / 100
        
        # Score d'équilibre musical (éviter contradictions)
        energy_balance = 1 - abs(features['energie'] - 0.7)  # Optimal autour de 0.7
        valence_balance = 1 - abs(features['valence'] - 0.6)  # Optimal autour de 0.6
        
        # Score de cohérence énergie-valence
        coherence_score = 1 - abs(features['energie'] - features['valence']) * 0.5
        
        # Score de qualité audio
        audio_quality = (
            (1 - features['speechiness']) * 0.3 +  # Moins de speech = plus musical
            features['danceability'] * 0.4 +       # Danceability = qualité
            (1 - abs(features['acousticness'] - 0.5)) * 0.3  # Équilibre acoustique
        )
        
        # Note finale pondérée
        final_rating = (
            pop_score * 0.3 +
            energy_balance * 0.2 +
            valence_balance * 0.2 +
            coherence_score * 0.15 +
            audio_quality * 0.15
        ) * 10
        
        return round(max(1, min(10, final_rating)), 1)
    
    def create_dataset(self, target_tracks=1000, output_file="dataset_enrichi.csv"):
        """Création du dataset"""
        logger.info("🚀 Création dataset enrichi...")
        
        # 1. Recherche
        tracks = self.search_tracks(target_tracks)
        logger.info(f"✅ {len(tracks)} tracks trouvées")
        
        # 2. Enrichissement
        enriched = []
        for i, track in enumerate(tracks):
            try:
                artist = track['artists'][0]['name']
                title = track['name']
                genre = self.detect_genre(artist.lower(), title.lower())
                features = self.estimate_features(track, genre)
                context = self.assign_context(features, genre)  # Ajout du genre
                rating = self.calculate_rating(track, features)
                
                enriched_track = {
                    'id': track['id'],
                    'artiste': artist,
                    'titre': title,
                    'genre': genre,
                    'contexte_temporel': context['temporel'],
                    'contexte_meteo': context['meteo'],
                    'contexte_activite': context['activite'],
                    'contexte_emotionnel': context['emotionnel'],
                    'contexte_social': context['social'],
                    'contexte_lieu': context['lieu'],
                    'bpm_estime': int(features['tempo']),
                    'energie': round(features['energie'], 3),
                    'valence': round(features['valence'], 3),
                    'danceability': round(features['danceability'], 3),
                    'acousticness': round(features['acousticness'], 3),
                    'instrumentalness': round(features['instrumentalness'], 3),
                    'speechiness': round(features['speechiness'], 3),
                    'liveness': round(features['liveness'], 3),
                    'notes': rating
                }
                enriched.append(enriched_track)
                
                if (i + 1) % 100 == 0:
                    logger.info(f"   ⚡ {i + 1}/{len(tracks)} tracks traitées")
                    
            except Exception as e:
                logger.debug(f"Erreur track: {e}")
        
        # 3. DataFrame et sauvegarde
        df = pd.DataFrame(enriched)
        df = df.drop_duplicates(subset=['id'])
        df.to_csv(output_file, index=False, encoding='utf-8')
        
        # 4. Stats
        print(f"\n✅ DATASET CRÉÉ: {output_file}")
        print(f"📊 {len(df)} tracks | {df['genre'].nunique()} genres | {df['artiste'].nunique()} artistes")
        print(f"🎯 Genres: {list(df['genre'].value_counts().head(5).index)}")
        
        return df

def main():
    """Fonction principale"""
    print("⚡ GÉNÉRATEUR DATASET - VERSION CORRIGÉE")
    print("=" * 50)
    
    # VOS CLÉS
    CLIENT_ID = "1a1fcf3039b54d78b8266d32451a75ba"
    CLIENT_SECRET = "dfc45caedccf4e1a8ae363559c4d1f65"
    
    try:
        creator = SimpleDatasetCreator(CLIENT_ID, CLIENT_SECRET)
        dataset = creator.create_dataset(1000, "dataset_musical_final.csv")
        
        print(f"\n🎉 SUCCÈS! {len(dataset)} tracks créées")
        print("📁 Fichier: dataset_musical_final.csv")
        
        # Aperçu
        cols = ['artiste', 'titre', 'genre', 'contexte_emotionnel', 'energie', 'notes']
        print(f"\n📋 APERÇU:")
        print(dataset[cols].head().to_string(index=False))
        
        return dataset
        
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        return None

if __name__ == "__main__":
    main()