// Configuration MoodifyBot
const API_BASE_URL = window.location.origin;
let currentChatId = null;
let isTyping = false;
let chatHistory = JSON.parse(localStorage.getItem('moodifyBotHistory')) || {};

// Initialisation
document.addEventListener('DOMContentLoaded', init);

function init() {
    setupEventListeners();
    loadChatHistory();
    createNewChat();
    applyTheme();
    setupGuideModal();
}

function setupEventListeners() {
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const newChatButton = document.getElementById('new-chat');
    const clearHistoryButton = document.getElementById('clear-history');
    const toggleThemeButton = document.getElementById('toggle-theme');

    // Événements principaux
    sendButton.addEventListener('click', handleSendMessage);
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });
    
    newChatButton.addEventListener('click', createNewChat);
    clearHistoryButton.addEventListener('click', clearAllHistory);
    toggleThemeButton.addEventListener('click', toggleTheme);

    // Auto-resize du textarea
    userInput.addEventListener('input', () => {
        userInput.style.height = 'auto';
        userInput.style.height = Math.min(userInput.scrollHeight, 120) + 'px';
    });
}

function setupGuideModal() {
    const guideButton = document.getElementById('guide-button');
    const modal = document.getElementById('guide-modal');
    const closeBtn = modal.querySelector('.close');

    // Ouvrir la modal
    guideButton.addEventListener('click', () => {
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden'; // Empêcher le scroll du body
    });

    // Fermer la modal avec le X
    closeBtn.addEventListener('click', closeGuideModal);

    // Fermer la modal en cliquant en dehors
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeGuideModal();
        }
    });

    // Fermer avec la touche Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.style.display === 'block') {
            closeGuideModal();
        }
    });
}

function closeGuideModal() {
    const modal = document.getElementById('guide-modal');
    modal.style.display = 'none';
    document.body.style.overflow = ''; // Rétablir le scroll du body
}

async function handleSendMessage() {
    if (isTyping) return;
    
    const userInput = document.getElementById('user-input');
    const message = userInput.value.trim();
    if (!message) return;

    // Afficher le message utilisateur
    addMessageToUI('user', message);
    userInput.value = '';
    userInput.style.height = 'auto';

    // Sauvegarder dans l'historique
    if (!chatHistory[currentChatId]) {
        createNewChat();
    }
    
    chatHistory[currentChatId].messages.push({
        role: 'user',
        content: message,
        timestamp: Date.now()
    });

    // Mettre à jour le titre si c'est le premier message
    if (chatHistory[currentChatId].messages.length === 1) {
        const title = message.length > 30 ? message.substring(0, 30) + '...' : message;
        chatHistory[currentChatId].title = title;
        document.getElementById('current-chat-title').textContent = title;
    }

    saveChatHistory();
    
    try {
        showTypingIndicator();
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        });

        const data = await response.json();
        
        if (data.success) {
            removeTypingIndicator();
            addMessageToUI('ai', data.response);
            
            chatHistory[currentChatId].messages.push({
                role: 'assistant',
                content: data.response,
                timestamp: Date.now()
            });
            saveChatHistory();
        } else {
            throw new Error(data.error || 'Erreur inconnue');
        }
    } catch (error) {
        removeTypingIndicator();
        addMessageToUI('ai', `😅 Problème de connexion ! Reformulez votre question musicale et je vous aiderai ! 🎵`);
    }
}

function addMessageToUI(sender, content) {
    const messagesContainer = document.getElementById('messages');
    
    // Supprimer le message d'intro s'il existe
    const introMessage = messagesContainer.querySelector('.intro-message');
    if (introMessage) {
        introMessage.remove();
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    
    if (sender === 'ai') {
        messageContent.innerHTML = formatResponse(content);
    } else {
        messageContent.textContent = content;
    }
    
    messageDiv.appendChild(messageContent);
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function formatResponse(content) {
    // Formatage pour MoodifyBot avec support des liens et markdown
    return content
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/• /g, '• ')
        .replace(/🔗 \*\*Plus d'infos :\*\* \[([^\]]+)\]\(([^)]+)\)/g, '🔗 <strong>Plus d\'infos:</strong> <a href="$2" target="_blank" rel="noopener">$1</a>')
        .replace(/🔗 \*\*Source :\*\* \[([^\]]+)\]\(([^)]+)\)/g, '🔗 <strong>Source:</strong> <a href="$2" target="_blank" rel="noopener">$1</a>')
        .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
        .replace(/\n/g, '<br>');
}

function showTypingIndicator() {
    isTyping = true;
    const messagesContainer = document.getElementById('messages');
    
    const typingDiv = document.createElement('div');
    typingDiv.className = 'typing-indicator';
    typingDiv.id = 'typing-indicator';
    
    // Créer les 3 points animés
    for (let i = 0; i < 3; i++) {
        const dot = document.createElement('div');
        dot.className = 'typing-dot';
        typingDiv.appendChild(dot);
    }
    
    messagesContainer.appendChild(typingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function removeTypingIndicator() {
    isTyping = false;
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

function createNewChat() {
    const chatId = 'chat_' + Date.now();
    currentChatId = chatId;
    
    chatHistory[chatId] = {
        id: chatId,
        title: 'Nouvelle conversation',
        timestamp: Date.now(),
        messages: []
    };
    
    // Nettoyer l'interface et remettre le message d'intro avec le guide
    const messagesContainer = document.getElementById('messages');
    messagesContainer.innerHTML = `
        <div class="intro-message">
            <h1>🎵 Bienvenue sur MoodifyBot</h1>
            <p>Votre assistant musical intelligent ! Posez-moi des questions sur la musique, les artistes, les genres musicaux, et je vous aiderai à découvrir de nouveaux sons !</p>
            <div class="guide-container">
                <button id="guide-button" class="guide-btn">
                    <i class="fas fa-question-circle"></i>
                    Comment ça marche ?
                </button>
            </div>
        </div>
    `;
    
    // Remettre le titre par défaut
    document.getElementById('current-chat-title').textContent = 'MoodifyBot - Assistant Musical Intelligent';
    
    // Réattacher l'événement au nouveau bouton guide
    setTimeout(() => {
        setupGuideModal();
    }, 100);
    
    saveChatHistory();
    updateChatHistoryUI();
}

function saveChatHistory() {
    localStorage.setItem('moodifyBotHistory', JSON.stringify(chatHistory));
}

function loadChatHistory() {
    updateChatHistoryUI();
}

function updateChatHistoryUI() {
    const historyContainer = document.getElementById('chat-history');
    historyContainer.innerHTML = '';
    
    const sortedChats = Object.values(chatHistory)
        .sort((a, b) => b.timestamp - a.timestamp);
    
    sortedChats.forEach(chat => {
        const chatItem = document.createElement('div');
        chatItem.className = 'chat-history-item';
        
        // Ajouter la classe active si c'est le chat courant
        if (chat.id === currentChatId) {
            chatItem.classList.add('active');
        }
        
        chatItem.innerHTML = `
            <i class="fas fa-music"></i>
            <span>${chat.title}</span>
        `;
        
        chatItem.addEventListener('click', () => loadChat(chat.id));
        historyContainer.appendChild(chatItem);
    });
}

function loadChat(chatId) {
    if (!chatHistory[chatId]) return;
    
    currentChatId = chatId;
    const chat = chatHistory[chatId];
    document.getElementById('current-chat-title').textContent = chat.title;
    
    const messagesContainer = document.getElementById('messages');
    messagesContainer.innerHTML = '';
    
    // Afficher tous les messages du chat
    chat.messages.forEach(message => {
        addMessageToUI(message.role === 'user' ? 'user' : 'ai', message.content);
    });
    
    // Mettre à jour l'UI de l'historique pour refléter le chat actif
    updateChatHistoryUI();
}

function clearAllHistory() {
    if (confirm('Êtes-vous sûr de vouloir effacer tout l\'historique des conversations ?')) {
        chatHistory = {};
        localStorage.removeItem('moodifyBotHistory');
        createNewChat();
    }
}

function toggleTheme() {
    document.body.classList.toggle('dark-mode');
    const isDark = document.body.classList.contains('dark-mode');
    localStorage.setItem('moodifyBotTheme', isDark ? 'dark' : 'light');
    
    const themeButton = document.getElementById('toggle-theme');
    const icon = themeButton.querySelector('i');
    const text = themeButton.querySelector('span');
    
    if (isDark) {
        icon.className = 'fas fa-sun';
        text.textContent = 'Mode clair';
    } else {
        icon.className = 'fas fa-moon';
        text.textContent = 'Mode sombre';
    }
}

function applyTheme() {
    const savedTheme = localStorage.getItem('moodifyBotTheme');
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-mode');
        const themeButton = document.getElementById('toggle-theme');
        const icon = themeButton.querySelector('i');
        const text = themeButton.querySelector('span');
        icon.className = 'fas fa-sun';
        text.textContent = 'Mode clair';
    }
}

// Fonction utilitaire pour copier du texte (pour les futurs boutons de copie)
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        // Optionnel: afficher une notification
        console.log('Texte copié !');
    }).catch(err => {
        console.error('Erreur lors de la copie:', err);
    });
}

// Gestion des erreurs globales
window.addEventListener('error', (e) => {
    console.error('Erreur JavaScript:', e.error);
});

// Gestion de la perte de connexion
window.addEventListener('online', () => {
    console.log('Connexion rétablie');
});

window.addEventListener('offline', () => {
    console.log('Connexion perdue');
    addMessageToUI('ai', '📡 Connexion internet perdue. Vérifiez votre connexion et réessayez.');
});