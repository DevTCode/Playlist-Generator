# Moodify - Assistant Musical Intelligent

Un assistant musical intelligent qui crée des playlists personnalisées basées sur votre humeur et votre contexte.

## Fonctionnalités

🎵 **Recommandations personnalisées** - Système de questionnaire intelligent à 6 questions
🎯 **Algorithme de matching avancé** - Correspondances parfaites et scores de compatibilité
🎧 **Intégration Spotify** - Aperçu et écoute directe des pistes
📱 **Interface responsive** - Design moderne avec thèmes émotionnels dynamiques
🎼 **Gestion de playlists** - Création, modification et export de playlists personnelles
🌙 **Thèmes adaptatifs** - Couleurs qui changent selon votre humeur
🔍 **Filtrage intelligent** - Évite les contenus offensants et assure la diversité

## Installation

1. **Cloner le projet**
2. **Créer un environnement virtuel**: `python -m venv venv`
3. **Activer l'environnement**: `source venv/bin/activate` (Linux/Mac) ou `venv\Scripts\activate` (Windows)
4. **Installer les dépendances**: `pip install -r requirements.txt`
5. **Configurer Spotify API**:
   - Créer une application sur [Spotify Developer Dashboard](https://developer.spotify.com/)
   - Créer un fichier `.env` avec vos clés API
6. **Préparer le dataset**: Placer `tracks_dataset_enriched.csv` dans le répertoire racine
7. **Lancer l'application**: `python app.py`
8. **Ouvrir** http://localhost:5001

## Utilisation

1. **Répondez aux 6 questions** sur votre état émotionnel et contexte
2. **Découvrez vos recommandations** avec scores de compatibilité
3. **Écoutez sur Spotify** ou créez vos playlists personnalisées
4. **Gérez vos playlists** et exportez-les au format texte

## Technologies utilisées

- **Backend**: Flask, pandas, spotipy
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **API**: Spotify Web API
- **Stockage**: Session Flask (côté serveur)
- **Données**: Dataset CSV enrichi avec contextes musicaux