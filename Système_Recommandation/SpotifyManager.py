# SpotifyManager.py
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import streamlit as st # Keep st.error for now, but in Flask it would be logging or flash messages

class SpotifyManager:
    def __init__(self):
        # In a production Flask app, these would be environment variables
        # For local testing, you can keep them here or load from .env
        self.SPOTIFY_CLIENT_ID = "aa2a7bd2dcc84f19bb479185b3224ff6"
        self.SPOTIFY_CLIENT_SECRET = "49802f5d2d754ea8a78f01432b062d8b"
        self.spotify = None
        self.connected = False
        self.setup_spotify()
    
    def setup_spotify(self):
        try:
            client_credentials_manager = SpotifyClientCredentials(
                client_id=self.SPOTIFY_CLIENT_ID, 
                client_secret=self.SPOTIFY_CLIENT_SECRET
            )
            self.spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
            # Test de connexion
            self.spotify.search(q="test", type='track', limit=1)
            self.connected = True
        except Exception as e:
            # In Flask, you'd use Flask's logging or flash messages here
            print(f"Erreur de connexion à Spotify: {e}. Vérifiez vos identifiants CLIENT_ID et CLIENT_SECRET.")
            self.connected = False
    
    def search_track(self, artist, title):
        if not self.connected:
            return None
        try:
            query = f"artist:{artist} track:{title}"
            results = self.spotify.search(q=query, type='track', limit=1)
            if results['tracks']['items']:
                track = results['tracks']['items'][0]
                return {
                    'preview_url': track['preview_url'],
                    'external_url': track['external_urls']['spotify'],
                    'album_image': track['album']['images'][0]['url'] if track['album']['images'] else None,
                    'album_name': track['album']['name'],
                    'track_id': track['id']
                }
        except Exception as e:
            # Log the error for debugging, don't show to user directly
            print(f"Error searching track {artist} - {title}: {e}")
            pass 
        return None