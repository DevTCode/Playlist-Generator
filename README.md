# 🎵 Moodify : Assistant Musical Intelligent
Moodify est une application web intelligente qui combine un système de recommandation musicale personnalisé et un chatbot conversationnel. Elle propose des morceaux adaptés à l'humeur et au contexte de l'utilisateur tout en permettant d'obtenir des informations via Wikipedia.

 ## ✨ Fonctionnalités
🎵 Recommandations personnalisées basées sur un questionnaire intelligent de 6 questions.
🎯 Matching avancé avec scores de compatibilité pour chaque morceau.
🎧 Intégration Spotify pour écouter et prévisualiser les titres.
🎼 Gestion des playlists : création, modification et export.
🤖 Chatbot intelligent avec recherche d'informations sur Wikipedia.
💬 Suggestions de questions et historique des conversations.
🌙 Thèmes adaptatifs selon l'humeur + mode sombre/clair.
📱 Interface responsive compatible mobile, tablette et desktop.
🔍 Filtrage intelligent pour limiter les contenus offensants et favoriser la diversité.
🛠️ Technologies
Backend: Python, Flask, Pandas, Spotipy, Wikipedia-API
Frontend: HTML5, CSS3, JavaScript (Vanilla)
APIs: Spotify Web API, Wikipedia API
Stockage: Flask Session & LocalStorage
Données: Dataset CSV enrichi avec des caractéristiques et contextes musicaux.

🚀 Installation
git clone https://github.com/your-username/moodify.git
cd moodify
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
pip install -r requirements.txt
Configurez vos clés Spotify dans un fichier .env, puis placez tracks_dataset_enriched.csv à la racine du projet.

Lancez l'application :

python app.py
Puis ouvrez http://localhost:5001.

🎯 Utilisation
Répondez aux 6 questions pour obtenir des recommandations adaptées à votre humeur et votre contexte, écoutez vos titres via Spotify, créez vos playlists et utilisez le chatbot pour rechercher des informations sur Wikipedia.
