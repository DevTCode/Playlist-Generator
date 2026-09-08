# WikiBot - Chatbot Wikipedia

Un chatbot intelligent qui répond aux questions en utilisant Wikipedia comme source d'information.

## Fonctionnalités

- 🔍 Recherche intelligente sur Wikipedia
- 💬 Interface de chat moderne et responsive
- 🌙 Mode sombre/clair
- 📱 Compatible mobile
- 💾 Historique des conversations (local)
- 🎯 Suggestions de questions

## Installation

1. Cloner le projet
2. Créer un environnement virtuel: `python -m venv venv`
3. Activer l'environnement: `source venv/bin/activate` (Linux/Mac) ou `venv\Scripts\activate` (Windows)
4. Installer les dépendances: `pip install -r requirements.txt`
5. Lancer l'application: `python app.py`
6. Ouvrir http://localhost:5000

## Utilisation

Posez simplement une question dans le chat et WikiBot recherchera les informations pertinentes sur Wikipedia.

## Technologies utilisées

- Backend: Flask, Wikipedia-API
- Frontend: HTML5, CSS3, JavaScript (Vanilla)
- Stockage: LocalStorage (côté client)