from flask import Flask, render_template, request, jsonify
import requests
import re
import logging
from typing import Optional, Dict, Any, List
import json

# Import conditionnel pour éviter les erreurs
try:
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials
    SPOTIPY_AVAILABLE = True
except ImportError:
    print("⚠️  Spotipy non installé - pip install spotipy")
    SPOTIPY_AVAILABLE = False

try:
    import pylast
    PYLAST_AVAILABLE = True
except ImportError:
    print("⚠️  Pylast non installé - pip install pylast")
    PYLAST_AVAILABLE = False

try:
    import lyricsgenius
    GENIUS_AVAILABLE = True
except ImportError:
    print("⚠️  LyricsGenius non installé - pip install lyricsgenius")
    GENIUS_AVAILABLE = False

try:
    import musicbrainzngs
    MUSICBRAINZ_AVAILABLE = True
except ImportError:
    print("⚠️  MusicBrainz non installé - pip install musicbrainzngs")
    MUSICBRAINZ_AVAILABLE = False

try:
    from fuzzywuzzy import fuzz
    FUZZYWUZZY_AVAILABLE = True
except ImportError:
    print("⚠️  FuzzyWuzzy non installé - pip install fuzzywuzzy")
    FUZZYWUZZY_AVAILABLE = False

try:
    import wikipedia
    WIKIPEDIA_AVAILABLE = True
except ImportError:
    print("❌ Wikipedia requis ! Installez avec: pip install wikipedia")
    exit(1)

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ====================================
# 🔑 CONFIGURATION DES CLÉS API
# ====================================
# Remplacez "VOTRE_CLE_ICI" par vos vraies clés

# Spotify (RECOMMANDÉ pour les meilleures fonctionnalités)
SPOTIFY_CLIENT_ID = "e09eb5a015dc4a2ab710b6b1b17f409e"
SPOTIFY_CLIENT_SECRET = "c3f84321ecd44de399831912b15130fa"

# Last.fm (OPTIONNEL pour les biographies)
LASTFM_API_KEY = "78d22b18b58bde175a2e0e4118e392bb"
LASTFM_SECRET = "1f5bdc5bcee5746fdd8af7310c94d62c"

# Genius (OPTIONNEL pour les significations)
GENIUS_ACCESS_TOKEN = "0aJO2dN6zyyLT8Bf9kShYR4EKtjPUV1WkTg7L2r95CyXAoBCSJd5gpvbTLGgg3jK"

class MoodifyBot:
    """Assistant musical intelligent pour MoodifyBot avec analyse contextuelle améliorée"""
    
    def __init__(self):
        self._setup_apis()
        self._setup_enhanced_keywords()
        
        # Réponses de base
        self.basic_responses = {
            'salut': "Salut ! 🎵 Prêt à explorer la musique ensemble ?",
            'bonjour': "Bonjour ! 🎶 Je suis MoodifyBot, votre assistant musical !",
            'hello': "Hello! 🎵 I'm MoodifyBot, your music assistant!",
            'hi': "Hi! 🎶 Ready to discover some music?",
            'merci': "De rien ! 😊 Autre question musicale ?",
            'thank you': "You're welcome! 😊 Any other music question?",
            'aide': "🎯 Je peux vous aider avec la musique ! Demandez-moi tout !",
            'help': "🎯 I can help you with music! Ask me anything!"
        }
    
    def _setup_apis(self):
        """Configuration robuste des APIs"""
        # Spotify
        if (SPOTIPY_AVAILABLE and SPOTIFY_CLIENT_ID and 
            SPOTIFY_CLIENT_ID != "VOTRE_SPOTIFY_CLIENT_ID_ICI"):
            try:
                client_credentials = SpotifyClientCredentials(
                    client_id=SPOTIFY_CLIENT_ID,
                    client_secret=SPOTIFY_CLIENT_SECRET
                )
                self.spotify = spotipy.Spotify(client_credentials_manager=client_credentials)
                logger.info("✅ Spotify API configurée")
            except Exception as e:
                self.spotify = None
                logger.warning(f"⚠️  Spotify erreur: {e}")
        else:
            self.spotify = None
            logger.info("⚠️  Spotify non configuré")
        
        # Last.fm
        if (PYLAST_AVAILABLE and LASTFM_API_KEY and 
            LASTFM_API_KEY != "VOTRE_LASTFM_API_KEY_ICI"):
            try:
                self.lastfm = pylast.LastFMNetwork(
                    api_key=LASTFM_API_KEY,
                    api_secret=LASTFM_SECRET if LASTFM_SECRET != "VOTRE_LASTFM_SECRET_ICI" else None
                )
                logger.info("✅ Last.fm API configurée")
            except Exception as e:
                self.lastfm = None
                logger.warning(f"⚠️  Last.fm erreur: {e}")
        else:
            self.lastfm = None
            logger.info("⚠️  Last.fm non configuré")
        
        # Genius
        if (GENIUS_AVAILABLE and GENIUS_ACCESS_TOKEN and 
            GENIUS_ACCESS_TOKEN != "VOTRE_GENIUS_TOKEN_ICI"):
            try:
                self.genius = lyricsgenius.Genius(GENIUS_ACCESS_TOKEN)
                self.genius.verbose = False
                logger.info("✅ Genius API configurée")
            except Exception as e:
                self.genius = None
                logger.warning(f"⚠️  Genius erreur: {e}")
        else:
            self.genius = None
            logger.info("⚠️  Genius non configuré")
        
        # Wikipedia (toujours disponible)
        wikipedia.set_lang("fr")
        self.wikipedia = wikipedia
        logger.info("✅ Wikipedia configuré")
    
    def _setup_enhanced_keywords(self):
        """Mots-clés améliorés avec analyse contextuelle"""
        self.intent_patterns = {
            'top_songs': {
                'primary': [
                    # Patterns français
                    r'(?:meilleures?|meilleurs?|top|hits?|succès|tubes?|singles?)\s+(?:chansons?|titres?|morceaux?|tracks?)\s+(?:de |d\'|of |by )\s*([A-Za-z][A-Za-z\s\-\'\.]+?)(?:\s*\?|$)',
                    r'(?:chansons?|titres?|morceaux?|songs?|tracks?)\s+(?:populaires?|connues?|célèbres?|famous?)\s+(?:de |d\'|of |by )\s*([A-Za-z][A-Za-z\s\-\'\.]+?)(?:\s*\?|$)',
                    # Patterns anglais
                    r'(?:best|top|greatest|popular)\s+(?:songs?|tracks?|hits?)\s+(?:of |by |from )\s*([A-Za-z][A-Za-z\s\-\'\.]+?)(?:\s*\?|$)',
                ],
                'keywords': ['meilleures chansons', 'top songs', 'hits', 'succès', 'tubes', 'best songs', 'greatest hits'],
                'confidence_boost': 2
            },
            'artist_bio': {
                'primary': [
                    r'(?:qui est|who is)\s+([A-Za-z][A-Za-z\s\-\'\.]+?)(?:\s*\?|$)',
                    r'(?:biographie|biography|histoire|story|life)\s+(?:de |d\'|of )\s*([A-Za-z][A-Za-z\s\-\'\.]+?)(?:\s*\?|$)',
                    r'(?:parle\s+moi\s+de|tell\s+me\s+about|raconte\s+moi|présente\s+moi)\s+([A-Za-z][A-Za-z\s\-\'\.]+?)(?:\s*\?|$)',
                ],
                'keywords': ['qui est', 'biographie', 'who is', 'biography', 'histoire', 'parcours', 'life of'],
                'confidence_boost': 3
            },
            'song_meaning': {
                'primary': [
                    # Patterns pour chanson + artiste
                    r'(?:quelles\s+sont\s+les\s+paroles|paroles|lyrics)\s+(?:de |d\'|of )\s*[\'""]([^\'""]+)[\'""][\s]+(?:de |d\'|of |by )\s*([A-Za-z][A-Za-z\s\-\'\.]+?)(?:\s*\?|$)',
                    r'(?:de\s+quoi\s+parle|signification|meaning)\s+[\'""]([^\'""]+)[\'""][\s]+(?:de |d\'|of |by )\s*([A-Za-z][A-Za-z\s\-\'\.]+?)(?:\s*\?|$)',
                    r'(?:thème|sujet|message|histoire)\s+(?:de\s+la\s+chanson\s+)?[\'""]([^\'""]+)[\'""][\s]+(?:de |d\'|of |by )\s*([A-Za-z][A-Za-z\s\-\'\.]+?)(?:\s*\?|$)',
                    # Patterns pour chanson seule (sans artiste)
                    r'(?:de\s+quoi\s+parle|what\s+is\s+about|signification\s+de|meaning\s+of)\s+[\'""]([^\'""]+)[\'""](?:\s*\?|$)',
                    r'(?:thème|sujet|message|histoire)\s+(?:de\s+la\s+chanson\s+|of\s+the\s+song\s+)?[\'""]([^\'""]+)[\'""](?:\s*\?|$)',
                    r'[\'""]([^\'""]+)[\'""]\s+(?:de\s+quoi\s+parle|signification|meaning)(?:\s*\?|$)',
                    r'(?:quelles\s+sont\s+les\s+paroles|paroles|lyrics)\s+(?:de |d\'|of )\s*[\'""]([^\'""]+)[\'""](?:\s*\?|$)',
                ],
                'keywords': ['de quoi parle', 'signification', 'meaning', 'thème', 'sujet', 'message', 'histoire de la chanson', 'paroles', 'lyrics', 'quelles sont les paroles'],
                'confidence_boost': 3
            },
            'discography': {
                'primary': [
                    r'(?:albums?|discographie|discography)\s+(?:de |d\'|of |by )\s*([A-Za-z][A-Za-z\s\-\'\.]+?)(?:\s*\?|$)',
                    r'(?:liste\s+des\s+albums?|all\s+albums?)\s+(?:de |d\'|of |by )\s*([A-Za-z][A-Za-z\s\-\'\.]+?)(?:\s*\?|$)',
                ],
                'keywords': ['albums', 'discographie', 'discography', 'œuvres', 'sorties', 'liste des albums'],
                'confidence_boost': 2
            },
            'genre_info': {
                'primary': [
                    r'(?:qu\'est-ce\s+que\s+le|qu\'est\s+ce\s+que\s+le|what\s+is)\s+([a-z]+(?:\s+[a-z]+)?)\s*\?',
                    r'(?:c\'est\s+quoi\s+le|définition\s+du|define)\s+([a-z]+(?:\s+[a-z]+)?)',
                    r'(?:genre\s+musical|style\s+de\s+musique|music\s+genre)\s+([a-z]+(?:\s+[a-z]+)?)',
                ],
                'keywords': ['qu\'est-ce que', 'définition', 'genre musical', 'style', 'what is', 'define'],
                'confidence_boost': 2
            },
            'comparison': {
                'primary': [
                    r'(?:différence\s+entre|difference\s+between)\s+([a-z\s]+)\s+(?:et|and)\s+([a-z\s]+)',
                    r'(?:compare|comparer)\s+([a-z\s]+)\s+(?:et|and|with)\s+([a-z\s]+)',
                ],
                'keywords': ['différence entre', 'difference between', 'compare', 'comparer', 'versus', 'vs'],
                'confidence_boost': 3
            }
        }
    
    def process_message(self, user_message: str) -> Dict[str, Any]:
        """Traitement principal des messages avec analyse contextuelle améliorée"""
        logger.info(f"🔍 Question: {user_message}")
        
        # Vérifier réponses basiques
        clean_msg = user_message.lower().strip()
        for keyword, response in self.basic_responses.items():
            if keyword in clean_msg:
                return {
                    'success': True,
                    'response': response + "\n\n🎶 **Exemples de questions :**\n• \"Meilleures chansons de [artiste]\"\n• \"Qui est [artiste] ?\"\n• \"Qu'est-ce que le jazz ?\"\n• \"Quelles sont les paroles de '[titre]' de [artiste] ?\"",
                    'type': 'basic'
                }
        
        # Analyser l'intention avec le nouveau système
        intent_result = self._advanced_intent_detection(user_message)
        intent = intent_result['intent']
        entities = intent_result['entities']
        confidence = intent_result['confidence']
        
        logger.info(f"🎯 Intention: {intent} (confiance: {confidence:.2f})")
        logger.info(f"📊 Entités extraites: {entities}")
        
        # Validation de confiance minimale
        if confidence < 0.3:
            return self._handle_ambiguous_question(user_message)
        
        # Router selon l'intention avec les entités extraites
        if intent == 'top_songs':
            return self._handle_top_songs_enhanced(user_message, entities)
        elif intent == 'artist_bio':
            return self._handle_artist_bio_enhanced(user_message, entities)
        elif intent == 'song_meaning':
            return self._handle_song_meaning_enhanced(user_message, entities)
        elif intent == 'discography':
            return self._handle_discography_enhanced(user_message, entities)
        elif intent == 'genre_info':
            return self._handle_genre_info_enhanced(user_message, entities)
        elif intent == 'comparison':
            return self._handle_comparison(user_message, entities)
        else:
            return self._handle_general_search(user_message)
    
    def _advanced_intent_detection(self, message: str) -> Dict[str, Any]:
        """Détection d'intention avancée avec extraction d'entités"""
        message_lower = message.lower()
        best_intent = 'general'
        best_confidence = 0.0
        best_entities = {}
        
        for intent, config in self.intent_patterns.items():
            confidence = 0.0
            entities = {}
            
            # Vérifier les patterns primaires (regex)
            for pattern in config['primary']:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    confidence += 0.8 * config['confidence_boost']
                    # Extraire les entités du match
                    if intent in ['top_songs', 'artist_bio', 'discography']:
                        entities['artist'] = match.group(1).strip()
                    elif intent == 'song_meaning':
                        # Gérer les cas avec et sans artiste - amélioration pour détecter les patterns complexes
                        groups = match.groups()
                        for i, group in enumerate(groups):
                            if group and group.strip():
                                if 'song' not in entities:
                                    entities['song'] = group.strip()
                                elif 'artist' not in entities:
                                    entities['artist'] = group.strip()
                                    break
                    elif intent == 'genre_info':
                        entities['genre'] = match.group(1).strip()
                    elif intent == 'comparison':
                        entities['item1'] = match.group(1).strip()
                        entities['item2'] = match.group(2).strip()
                    break
            
            # Vérifier les mots-clés secondaires
            keyword_matches = 0
            for keyword in config['keywords']:
                if keyword in message_lower:
                    keyword_matches += 1
            
            if keyword_matches > 0:
                keyword_confidence = (keyword_matches / len(config['keywords'])) * 0.5
                confidence += keyword_confidence
            
            # Bonus pour correspondance exacte de phrase
            if any(keyword in message_lower for keyword in config['keywords'][:2]):  # Top 2 keywords
                confidence += 0.2
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_intent = intent
                best_entities = entities
        
        return {
            'intent': best_intent,
            'confidence': best_confidence,
            'entities': best_entities
        }
    
    def _handle_ambiguous_question(self, message: str) -> Dict[str, Any]:
        """Gérer les questions ambiguës avec messages généraux"""
        response = "🤔 **Je ne suis pas sûr de bien comprendre votre question.**\n\n"
        
        response += "💡 **Voici des exemples de questions que je peux traiter :**\n\n"
        
        response += "🎤 **Pour les artistes :**\n"
        response += "• \"Qui est [nom de l'artiste] ?\"\n"
        response += "• \"Meilleures chansons de [artiste]\"\n"
        response += "• \"Albums de [artiste]\"\n\n"
        
        response += "🎵 **Pour les chansons :**\n"
        response += "• \"De quoi parle '[titre de la chanson]' ?\"\n"
        response += "• \"Quelles sont les paroles de '[titre]' de [artiste] ?\"\n"
        response += "• Mettez les titres entre guillemets\n\n"
        
        response += "🎼 **Pour les genres musicaux :**\n"
        response += "• \"Qu'est-ce que le [genre] ?\"\n"
        response += "• \"Différence entre [genre1] et [genre2]\"\n\n"
        
        response += "💭 **Reformulez votre question** plus clairement et je vous aiderai !"
        
        return {
            'success': True,
            'response': response,
            'type': 'ambiguous_clarification'
        }
    
    def _extract_potential_entities(self, message: str) -> Dict[str, str]:
        """Extraire des entités potentielles même sans intention claire"""
        entities = {}
        
        # Chercher des noms entre guillemets
        quotes_match = re.search(r'[\'""]([^\'""]+)[\'""]', message)
        if quotes_match:
            entities['song'] = quotes_match.group(1)
        
        # Chercher des noms propres (mots avec majuscules)
        proper_nouns = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', message)
        if proper_nouns:
            # Filtrer les mots courants
            common_words = {'The', 'Le', 'La', 'Les', 'Du', 'De', 'Des', 'What', 'Who', 'How'}
            filtered_nouns = [noun for noun in proper_nouns if noun not in common_words]
            if filtered_nouns:
                entities['artist'] = filtered_nouns[0]  # Prendre le premier
        
        return entities
    
    def _handle_top_songs_enhanced(self, message: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Gérer les demandes de top chansons avec entités"""
        artist_name = entities.get('artist')
        
        if not artist_name:
            artist_name = self._extract_artist_name(message)
        
        if not artist_name:
            return self._create_error_response(
                "Je n'ai pas pu identifier l'artiste dans votre question.",
                "Essayez : \"Meilleures chansons de [nom de l'artiste]\""
            )
        
        # Validation de l'artiste
        if len(artist_name) < 2 or len(artist_name) > 50:
            return self._create_error_response(
                f"'{artist_name}' ne semble pas être un nom d'artiste valide.",
                "Vérifiez l'orthographe et réessayez."
            )
        
        if self.spotify:
            try:
                # Rechercher l'artiste avec validation
                results = self.spotify.search(q=artist_name, type='artist', limit=5)
                
                if not results['artists']['items']:
                    return self._fallback_search(f"chansons {artist_name}", 
                                                f"Aucun artiste trouvé pour '{artist_name}'")
                
                # Trouver la meilleure correspondance
                best_artist = self._find_best_artist_match(artist_name, results['artists']['items'])
                
                if not best_artist:
                    return self._fallback_search(f"chansons {artist_name}")
                
                # Récupérer les top tracks
                top_tracks = self.spotify.artist_top_tracks(best_artist['id'], country='FR')
                
                if not top_tracks['tracks']:
                    return self._fallback_search(f"chansons {artist_name}")
                
                # Formater la réponse améliorée
                response = f"🎵 **Top chansons de {best_artist['name']}**\n\n"
                
                for i, track in enumerate(top_tracks['tracks'][:8], 1):
                    duration_min = track['duration_ms'] // 60000
                    duration_sec = (track['duration_ms'] % 60000) // 1000
                    response += f"**{i}. {track['name']}**\n"
                    response += f"💿 Album: {track['album']['name']}\n"
                    response += f"⏱️ Durée: {duration_min}:{duration_sec:02d}\n"
                    response += f"📊 Popularité: {track['popularity']}/100\n\n"
                
                response += f"🎤 **Infos {best_artist['name']} :**\n"
                response += f"👥 {best_artist['followers']['total']:,} followers\n"
                response += f"🔥 Popularité: {best_artist['popularity']}/100\n"
                
                if best_artist['genres']:
                    response += f"🎼 Genres: {', '.join(best_artist['genres'][:3])}\n"
                
                response += "\n🎶 **Autre question sur cet artiste ?**"
                
                return {
                    'success': True,
                    'response': response,
                    'type': 'spotify_success'
                }
                
            except Exception as e:
                logger.error(f"❌ Erreur Spotify: {e}")
                return self._fallback_search(f"meilleures chansons {artist_name}")
        
        else:
            return self._fallback_search(f"meilleures chansons {artist_name}")
    
    def _find_best_artist_match(self, query: str, artists: List[Dict]) -> Optional[Dict]:
        """Trouver la meilleure correspondance d'artiste"""
        if not artists:
            return None
        
        query_lower = query.lower()
        
        # Recherche exacte d'abord
        for artist in artists:
            if artist['name'].lower() == query_lower:
                return artist
        
        # Recherche par similarité si fuzzywuzzy disponible
        if FUZZYWUZZY_AVAILABLE:
            best_match = None
            best_score = 0
            
            for artist in artists:
                score = fuzz.ratio(query_lower, artist['name'].lower())
                if score > best_score and score > 70:  # Seuil de similarité
                    best_score = score
                    best_match = artist
            
            if best_match:
                return best_match
        
        # Retourner le premier par défaut
        return artists[0]
    
    def _handle_artist_bio_enhanced(self, message: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Gérer les biographies avec entités extraites"""
        artist_name = entities.get('artist')
        
        if not artist_name:
            artist_name = self._extract_artist_name(message)
        
        if not artist_name:
            return self._create_error_response(
                "Je n'ai pas pu identifier l'artiste dans votre question.",
                "Essayez : \"Qui est [nom de l'artiste] ?\""
            )
        
        # Essayer Last.fm d'abord puis Wikipedia
        return self._get_artist_biography(artist_name)
    
    def _handle_song_meaning_enhanced(self, message: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Gérer les significations avec entités extraites et demande de précision"""
        song_title = entities.get('song')
        artist_name = entities.get('artist')
        
        if not song_title:
            # Fallback vers l'ancienne méthode
            song_info = self._extract_song_info(message)
            song_title = song_info.get('title')
            if not artist_name:
                artist_name = song_info.get('artist')
        
        if not song_title:
            return self._create_error_response(
                "Je n'ai pas pu identifier la chanson dans votre question.",
                "Essayez : \"Quelles sont les paroles de '[titre]' de [artiste] ?\""
            )
        
        # Si l'artiste n'est pas spécifié, demander une précision
        if not artist_name:
            response = f"🎵 **Précision nécessaire pour '{song_title}'**\n\n"
            response += "Pour éviter toute confusion entre artistes, pourriez-vous reformuler votre question ainsi :\n\n"
            response += f"💭 **\"Quelles sont les paroles de '{song_title}' de '[nom de l'artiste]' ?\"**\n\n"
            response += "Cela m'aidera à vous donner des informations précises sur la bonne version de la chanson.\n\n"
            response += "🎤 **Exemple :** \"Quelles sont les paroles de 'Imagine' de 'John Lennon' ?\""
            
            return {
                'success': True,
                'response': response,
                'type': 'precision_request'
            }
        
        return self._get_song_meaning(song_title, artist_name)
    
    def _handle_discography_enhanced(self, message: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Gérer les discographies avec entités extraites"""
        artist_name = entities.get('artist')
        
        if not artist_name:
            artist_name = self._extract_artist_name(message)
        
        if not artist_name:
            return self._create_error_response(
                "Je n'ai pas pu identifier l'artiste dans votre question.",
                "Essayez : \"Albums de [nom de l'artiste]\""
            )
        
        return self._get_artist_discography(artist_name)
    
    def _handle_genre_info_enhanced(self, message: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Gérer les infos sur les genres avec entités extraites"""
        genre = entities.get('genre')
        
        if not genre:
            # Extraire le genre depuis le message
            genre_patterns = [
                r'(?:qu\'est-ce\s+que\s+le|what\s+is)\s+([a-z]+(?:\s+[a-z]+)?)',
                r'(?:genre|style)\s+([a-z]+(?:\s+[a-z]+)?)',
            ]
            
            for pattern in genre_patterns:
                match = re.search(pattern, message.lower())
                if match:
                    genre = match.group(1).strip()
                    break
        
        if not genre:
            return self._create_error_response(
                "Je n'ai pas pu identifier le genre musical.",
                "Essayez : \"Qu'est-ce que le jazz ?\""
            )
        
        return self._get_genre_info(genre)
    
    def _handle_comparison(self, message: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Gérer les comparaisons entre genres/artistes"""
        item1 = entities.get('item1')
        item2 = entities.get('item2')
        
        if not item1 or not item2:
            return self._create_error_response(
                "Je n'ai pas pu identifier les éléments à comparer.",
                "Essayez : \"Différence entre jazz et blues\""
            )
        
        # Rechercher des informations sur les deux éléments
        return self._compare_musical_elements(item1, item2)
    
    def _compare_musical_elements(self, item1: str, item2: str) -> Dict[str, Any]:
        """Comparer deux éléments musicaux"""
        response = f"🎵 **Comparaison : {item1.title()} vs {item2.title()}**\n\n"
        
        # Rechercher des informations sur chaque élément
        info1 = self._get_quick_info(item1)
        info2 = self._get_quick_info(item2)
        
        if info1:
            response += f"📍 **{item1.title()} :**\n{info1}\n\n"
        
        if info2:
            response += f"📍 **{item2.title()} :**\n{info2}\n\n"
        
        response += "🎶 **Besoin de plus de détails sur l'un d'eux ?**"
        
        return {
            'success': True,
            'response': response,
            'type': 'comparison_success'
        }
    
    def _get_quick_info(self, term: str) -> str:
        """Obtenir des informations rapides sur un terme"""
        try:
            summary = self.wikipedia.summary(term, sentences=2)
            return summary
        except:
            return None
    
    # Méthodes utilitaires améliorées
    def _extract_artist_name(self, message: str) -> str:
        """Extraction améliorée du nom d'artiste avec validation"""
        patterns = [
            r'(?:chansons|hits|succès|tubes|songs|tracks)\s+(?:de |d\'|of |by )\s*([A-Za-z][A-Za-z\s\-\'\.]+?)(?:\s*\?|$)',
            r'(?:meilleures|meilleurs|best|top)\s+(?:chansons|songs|hits)\s+(?:de |d\'|of |by )\s*([A-Za-z][A-Za-z\s\-\'\.]+?)(?:\s*\?|$)',
            r'(?:qui est|who is)\s+([A-Za-z][A-Za-z\s\-\'\.]+?)(?:\s*\?|$)',
            r'(?:biographie|biography|histoire)\s+(?:de |d\'|of )\s*([A-Za-z][A-Za-z\s\-\'\.]+?)(?:\s*\?|$)',
            r'(?:albums?|discographie|discography)\s+(?:de |d\'|of )\s*([A-Za-z][A-Za-z\s\-\'\.]+?)(?:\s*\?|$)',
            r'"([^"]+)"',
            r"'([^']+)'"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                artist = match.group(1).strip()
                
                # Nettoyer et valider
                artist = self._clean_artist_name(artist)
                if self._validate_artist_name(artist):
                    logger.info(f"🎯 Artiste extrait: '{artist}' depuis '{message}'")
                    return artist
        
        logger.warning(f"❌ Aucun artiste trouvé dans: '{message}'")
        return ""
    
    def _clean_artist_name(self, artist: str) -> str:
        """Nettoyer le nom d'artiste"""
        # Supprimer les mots parasites
        stop_words = ['le', 'la', 'les', 'du', 'de', 'des', 'the', 'and', 'or', 'et', 'un', 'une']
        words = artist.split()
        clean_words = []
        
        for word in words:
            if word.lower() not in stop_words and len(word) > 1:
                clean_words.append(word)
        
        return ' '.join(clean_words) if clean_words else artist
    
    def _validate_artist_name(self, artist: str) -> bool:
        """Valider le nom d'artiste"""
        if not artist or len(artist) < 2 or len(artist) > 50:
            return False
        
        # Vérifier qu'il n'y a pas que des mots communs
        common_words = ['music', 'song', 'artist', 'band', 'group', 'musique', 'chanson', 'artiste', 'groupe']
        if artist.lower() in common_words:
            return False
        
        return True
    
    def _get_artist_biography(self, artist_name: str) -> Dict[str, Any]:
        """Obtenir la biographie d'un artiste"""
        # Essayer Last.fm d'abord
        if self.lastfm:
            try:
                artist = self.lastfm.get_artist(artist_name)
                bio = artist.get_bio_content()
                
                if bio and len(bio) > 100:
                    # Nettoyer le HTML
                    bio = re.sub(r'<[^>]+>', '', bio)
                    bio = bio.strip()
                    
                    # Limiter la longueur
                    if len(bio) > 600:
                        sentences = bio.split('. ')
                        bio = '. '.join(sentences[:4]) + '.'
                    
                    response = f"🎤 **{artist.get_name()}**\n\n{bio}\n\n"
                    
                    # Stats Last.fm
                    try:
                        listeners = artist.get_listener_count()
                        if listeners:
                            response += f"📊 **Last.fm :** {listeners:,} auditeurs\n\n"
                    except:
                        pass
                    
                    response += "🎶 **Autre question sur cet artiste ?**"
                    
                    return {
                        'success': True,
                        'response': response,
                        'type': 'lastfm_success'
                    }
            except Exception as e:
                logger.error(f"❌ Erreur Last.fm: {e}")
        
        # Fallback Wikipedia
        return self._fallback_search(f"biographie {artist_name}")
    
    def _get_song_meaning(self, song_title: str, artist_name: str = None) -> Dict[str, Any]:
        """Obtenir la signification d'une chanson"""
        if self.genius:
            try:
                song = self.genius.search_song(song_title, artist_name or '')
                
                if song:
                    response = f"🎵 **{song.title}**"
                    if song.artist:
                        response += f" - {song.artist}"
                    response += "\n\n"
                    
                    # Gérer l'album correctement
                    if song.album:
                        album_name = song.album
                        if hasattr(song.album, 'name'):
                            album_name = song.album.name
                        elif isinstance(song.album, dict):
                            album_name = song.album.get('name', song.album.get('title', str(song.album)))
                        elif hasattr(song.album, '__str__'):
                            album_str = str(song.album)
                            # Extraire le nom si c'est dans un format "Album(name='...', ...)"
                            import re
                            name_match = re.search(r"name='([^']+)'", album_str)
                            if name_match:
                                album_name = name_match.group(1)
                            else:
                                album_name = album_str
                        
                        response += f"💿 **Album:** {album_name}\n"
                    
                    if hasattr(song, 'year') and song.year:
                        response += f"📅 **Année:** {song.year}\n"
                    
                    response += "\n"
                    
                    # Description si disponible
                    if hasattr(song, 'description') and song.description:
                        desc = str(song.description)
                        if isinstance(song.description, dict):
                            desc = song.description.get('plain', '')
                        
                        if desc and len(desc) > 50:
                            desc = desc[:400] + "..." if len(desc) > 400 else desc
                            response += f"📝 **À propos :**\n{desc}\n\n"
                    
                    response += f"🔗 **Plus d'infos :** [Voir sur Genius]({song.url})\n\n"
                    response += "🎶 **Autre question ?**"
                    
                    return {
                        'success': True,
                        'response': response,
                        'type': 'genius_success'
                    }
            except Exception as e:
                logger.error(f"❌ Erreur Genius: {e}")
        
        # Fallback
        search_query = f"chanson {song_title}"
        if artist_name:
            search_query += f" {artist_name}"
        return self._fallback_search(search_query)
    
    def _get_artist_discography(self, artist_name: str) -> Dict[str, Any]:
        """Obtenir la discographie d'un artiste"""
        if self.spotify:
            try:
                results = self.spotify.search(q=artist_name, type='artist', limit=1)
                
                if not results['artists']['items']:
                    return self._fallback_search(f"albums {artist_name}")
                
                artist = results['artists']['items'][0]
                albums = self.spotify.artist_albums(
                    artist['id'], 
                    album_type='album', 
                    country='FR', 
                    limit=15
                )
                
                if not albums['items']:
                    return self._fallback_search(f"discographie {artist_name}")
                
                response = f"💿 **Discographie de {artist['name']}**\n\n"
                
                for album in albums['items']:
                    year = album['release_date'][:4] if album['release_date'] else "?"
                    response += f"• **{album['name']}** ({year}) - {album['total_tracks']} titres\n"
                
                response += "\n🎶 **Question sur un album spécifique ?**"
                
                return {
                    'success': True,
                    'response': response,
                    'type': 'spotify_discography'
                }
                
            except Exception as e:
                logger.error(f"❌ Erreur discographie: {e}")
                return self._fallback_search(f"discographie {artist_name}")
        
        else:
            return self._fallback_search(f"discographie {artist_name}")
    
    def _get_genre_info(self, genre: str) -> Dict[str, Any]:
        """Obtenir des informations sur un genre musical"""
        search_terms = [
            f"{genre} genre musical",
            f"{genre} music genre",
            f"musique {genre}",
            genre
        ]
        
        for term in search_terms:
            try:
                # Rechercher sur Wikipedia
                search_results = self.wikipedia.search(term, results=5)
                
                for result in search_results:
                    try:
                        summary = self.wikipedia.summary(result, sentences=4)
                        
                        # Vérifier que c'est bien lié à la musique
                        music_keywords = ['music', 'musical', 'genre', 'sound', 'style', 'musique', 'musical']
                        if any(keyword in summary.lower() for keyword in music_keywords):
                            page = self.wikipedia.page(result)
                            response = f"🎼 **{result}**\n\n"
                            response += summary + "\n\n"
                            response += f"🔗 **Source :** [Wikipedia]({page.url})\n\n"
                            response += "🎶 **Autre question musicale ?**"
                            
                            return {
                                'success': True,
                                'response': response,
                                'type': 'wikipedia_genre_success'
                            }
                    except:
                        continue
            except:
                continue
        
        return self._fallback_search(f"genre musical {genre}")
    
    def _extract_song_info(self, message: str) -> Dict[str, str]:
        """Extraire infos de chanson améliorée"""
        patterns = [
            r'"([^"]+)"\s*(?:de|par|by)\s*([A-Z][a-zA-Z\s]+)',
            r'chanson\s+"([^"]+)"',
            r'"([^"]+)"'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                if len(match.groups()) == 2:
                    return {'title': match.group(1).strip(), 'artist': match.group(2).strip()}
                else:
                    return {'title': match.group(1).strip()}
        
        return {}
    
    def _fallback_search(self, query: str, error_context: str = None) -> Dict[str, Any]:
        """Recherche Wikipedia améliorée avec filtrage musical"""
        try:
            # D'abord essayer la recherche directe
            search_results = self.wikipedia.search(query, results=10)
            
            # Filtrer pour privilégier les résultats musicaux
            music_keywords = [
                'music', 'musician', 'singer', 'artist', 'band', 'album', 'song',
                'musique', 'musicien', 'chanteur', 'artiste', 'groupe', 'chanson'
            ]
            
            filtered_results = []
            for result in search_results:
                result_lower = result.lower()
                if any(keyword in result_lower for keyword in music_keywords):
                    filtered_results.append(result)
            
            # Si pas de résultats musicaux, prendre les premiers résultats
            if not filtered_results:
                filtered_results = search_results[:5]
            
            # Essayer chaque résultat
            for result in filtered_results:
                try:
                    summary = self.wikipedia.summary(result, sentences=4)
                    
                    if len(summary) > 100:
                        page = self.wikipedia.page(result)
                        response = f"📚 **{result}**\n\n"
                        response += summary + "\n\n"
                        response += f"🔗 **Source :** [Wikipedia]({page.url})\n\n"
                        response += "🎶 **Autre question musicale ?**"
                        
                        logger.info(f"✅ Wikipedia trouvé: {result}")
                        return {
                            'success': True,
                            'response': response,
                            'type': 'wikipedia_success'
                        }
                except Exception as e:
                    logger.warning(f"⚠️ Erreur avec résultat '{result}': {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"❌ Erreur recherche Wikipedia: {e}")
        
        return self._create_smart_fallback(query, error_context)
    
    def _create_error_response(self, error_msg: str, suggestion: str = None) -> Dict[str, Any]:
        """Créer réponse d'erreur générale améliorée"""
        response = f"🤔 **{error_msg}**\n\n"
        
        if suggestion:
            response += f"💡 {suggestion}\n\n"
        
        response += "🎶 **Voici ce que je peux vous aider à découvrir :**\n\n"
        
        response += "🎤 **Artistes :**\n"
        response += "• \"Qui est [nom de l'artiste] ?\"\n"
        response += "• \"Meilleures chansons de [artiste]\"\n"
        response += "• \"Albums de [artiste]\"\n\n"
        
        response += "🎵 **Chansons :**\n"
        response += "• \"Quelles sont les paroles de '[titre]' de '[artiste]' ?\"\n\n"
        
        response += "🎼 **Genres musicaux :**\n"
        response += "• \"Qu'est-ce que le [genre] ?\"\n"
        response += "• \"Différence entre [genre1] et [genre2]\"\n\n"
        
        response += "💭 **Reformulez votre question et je vous aiderai !**"
        
        return {
            'success': True,
            'response': response,
            'type': 'error'
        }
    
    def _create_smart_fallback(self, query: str, error_context: str = None) -> Dict[str, Any]:
        """Réponse intelligente de fallback générale"""
        response = "🔍 **Je n'ai pas trouvé d'informations spécifiques pour votre question.**\n\n"
        
        if error_context:
            response += f"⚠️ {error_context}\n\n"
        
        response += "💡 **Voici comment bien formuler vos questions :**\n\n"
        
        response += "🎤 **Pour les artistes :**\n"
        response += "• \"Qui est [nom complet de l'artiste] ?\"\n"
        response += "• \"Meilleures chansons de [artiste]\"\n"
        response += "• \"Albums de [artiste]\"\n\n"
        
        response += "🎶 **Pour les chansons :**\n"
        response += "• \"Quelles sont les paroles de '[titre exact]' de '[artiste]' ?\"\n"
        response += "• Utilisez des guillemets pour les titres ET les artistes\n\n"
        
        response += "🎼 **Pour les genres :**\n"
        response += "• \"Qu'est-ce que le [genre musical] ?\"\n"
        response += "• \"Différence entre [genre1] et [genre2]\"\n\n"
        
        response += "🎯 **Reformulez votre question** et je trouverai sûrement une réponse !"
        
        return {
            'success': True,
            'response': response,
            'type': 'smart_fallback'
        }
    
    def _handle_general_search(self, message: str) -> Dict[str, Any]:
        """Recherche générale avec analyse contextuelle"""
        # Essayer d'extraire des entités même sans intention claire
        potential_entities = self._extract_potential_entities(message)
        
        if potential_entities:
            # Construire une recherche basée sur les entités trouvées
            search_query = message
            if potential_entities.get('artist'):
                search_query = f"musique {potential_entities['artist']}"
            elif potential_entities.get('song'):
                search_query = f"chanson {potential_entities['song']}"
        else:
            search_query = message
        
        return self._fallback_search(search_query)


# Instance du bot
moodify_bot = MoodifyBot()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({
                'success': False,
                'error': 'Message vide'
            })
        
        logger.info(f"💬 Question reçue: {user_message}")
        
        # Traiter avec MoodifyBot amélioré
        result = moodify_bot.process_message(user_message)
        
        logger.info(f"✅ Réponse générée (type: {result.get('type', 'unknown')})")
        
        return jsonify({
            'success': True,
            'response': result['response']
        })
    
    except Exception as e:
        logger.error(f"❌ Erreur serveur: {e}")
        return jsonify({
            'success': True,
            'response': "😅 Problème technique ! Reformulez votre question et je vous aiderai ! 🎵"
        })

@app.route('/health')
def health():
    """Statut des APIs"""
    return jsonify({
        'service': 'MoodifyBot Enhanced',
        'status': 'OK',
        'apis': {
            'spotify': bool(moodify_bot.spotify),
            'lastfm': bool(moodify_bot.lastfm),
            'genius': bool(moodify_bot.genius),
            'wikipedia': True
        },
        'features': {
            'advanced_intent_detection': True,
            'entity_extraction': True,
            'contextual_analysis': True,
            'fuzzy_matching': FUZZYWUZZY_AVAILABLE,
            'precise_lyrics_requests': True
        }
    })

if __name__ == '__main__':
    print("🎵 Démarrage de MoodifyBot Enhanced...")
    print("🔧 APIs configurées:")
    print(f"  • Spotify: {'✅' if moodify_bot.spotify else '❌ (ajoutez vos clés)'}")
    print(f"  • Last.fm: {'✅' if moodify_bot.lastfm else '❌ (ajoutez vos clés)'}")  
    print(f"  • Genius: {'✅' if moodify_bot.genius else '❌ (ajoutez votre token)'}")
    print(f"  • Wikipedia: ✅")
    print(f"  • FuzzyWuzzy: {'✅' if FUZZYWUZZY_AVAILABLE else '❌ (optionnel)'}")
    print("\n🚀 Nouvelles fonctionnalités:")
    print("   ✨ Analyse contextuelle avancée")
    print("   🎯 Extraction d'entités intelligente") 
    print("   🔍 Détection d'intention améliorée")
    print("   💬 Gestion des questions ambiguës")
    print("   🎵 Demandes de précision pour les paroles")
    print("\n🔑 Pour ajouter des clés API:")
    print("   1. Ouvrez app.py")
    print("   2. Remplacez 'VOTRE_CLE_ICI' par vos vraies clés")
    print("   3. Redémarrez l'application")
    print("🚀 MoodifyBot Enhanced démarré sur http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)