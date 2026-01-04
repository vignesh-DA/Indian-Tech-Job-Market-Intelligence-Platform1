/* Chatbot Widget - Appears on All Pages */

let chatbotOpen = false;
let chatHistory = [];

// Initialize chatbot on all pages
document.addEventListener('DOMContentLoaded', function() {
    initializeChatbot();
});

function initializeChatbot() {
    console.log('🤖 Initializing chatbot');
    
    const chatbotButton = document.getElementById('chatbot-button');
    const chatbotWidget = document.getElementById('chatbot-widget');
    const chatbotClose = document.getElementById('chatbot-close');
    const chatbotSend = document.getElementById('chatbot-send');
    const chatbotInput = document.getElementById('chatbot-input');

    if (!chatbotButton || !chatbotWidget) {
        console.warn('Chatbot elements not found in DOM');
        return;
    }

    // Toggle chatbot widget
    chatbotButton.addEventListener('click', function(e) {
        e.stopPropagation();
        chatbotOpen = !chatbotOpen;
        
        if (chatbotOpen) {
            console.log('Opening chatbot');
            chatbotWidget.classList.add('active');
            setTimeout(() => {
                if (chatbotInput) chatbotInput.focus();
            }, 100);
        } else {
            console.log('Closing chatbot');
            chatbotWidget.classList.remove('active');
        }
    });

    // Close chatbot
    chatbotClose.addEventListener('click', function(e) {
        e.stopPropagation();
        chatbotOpen = false;
        chatbotWidget.classList.remove('active');
    });

    // Send message on button click
    chatbotSend.addEventListener('click', function() {
        sendChatbotMessage();
    });

    // Send message on Enter key
    chatbotInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendChatbotMessage();
        }
    });

    // Load chat history from localStorage
    loadChatHistory();
}

function sendChatbotMessage() {
    const chatbotInput = document.getElementById('chatbot-input');
    const message = chatbotInput.value.trim();

    if (!message) return;

    // Disable send button and input
    const chatbotSend = document.getElementById('chatbot-send');
    chatbotSend.disabled = true;
    chatbotInput.disabled = true;

    // Add user message to chat
    addChatMessage(message, 'user');
    chatbotInput.value = '';

    // Show typing indicator
    showTypingIndicator();

    // Get current user profile context
    const userProfile = getUserProfileContext();

    // Send to backend API
    fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            message: message,
            user_profile: userProfile,
            conversation_history: chatHistory
        })
    })
    .then(response => {
        console.log('Response status:', response.status);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Chat response data:', data);
        removeTypingIndicator();
        
        if (data.success) {
            addChatMessage(data.message, 'bot');
            // Save to history
            chatHistory.push({role: 'user', content: message});
            chatHistory.push({role: 'bot', content: data.message});
            saveChatHistory();
        } else {
            console.error('API returned error:', data.message);
            addChatMessage('Sorry, I encountered an error. Please try again.', 'bot');
        }
    })
    .catch(error => {
        console.error('Chat error details:', error);
        removeTypingIndicator();
        addChatMessage('Sorry, I could not process your request. Please try again.', 'bot');
    })
    .finally(() => {
        chatbotSend.disabled = false;
        chatbotInput.disabled = false;
        chatbotInput.focus();
    });
}

function addChatMessage(text, sender) {
    const messagesContainer = document.getElementById('chatbot-messages');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `chatbot-message ${sender}-message`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = text;
    
    const timeDiv = document.createElement('div');
    timeDiv.className = 'message-time';
    timeDiv.textContent = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    
    messageDiv.appendChild(contentDiv);
    messageDiv.appendChild(timeDiv);
    messagesContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function showTypingIndicator() {
    const messagesContainer = document.getElementById('chatbot-messages');
    
    const typingDiv = document.createElement('div');
    typingDiv.className = 'chatbot-message bot-message';
    typingDiv.id = 'typing-indicator';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'typing-indicator';
    contentDiv.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
    
    typingDiv.appendChild(contentDiv);
    messagesContainer.appendChild(typingDiv);
    
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function removeTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) {
        indicator.remove();
    }
}

function getUserProfileContext() {
    // Try to get profile from recommendations page
    const roleSelect = document.getElementById('roleSelect');
    const experienceSelect = document.getElementById('experienceSelect');
    const locationSelect = document.getElementById('locationSelect');
    const skillsInput = document.getElementById('skillsInput');
    const totalMatchesMetric = document.getElementById('totalMatchesMetric');

    return {
        role: roleSelect?.value || '',
        experience: experienceSelect?.value || '',
        location: locationSelect?.value || '',
        skills: typeof userSkills !== 'undefined' ? userSkills : [],
        total_matched_jobs: totalMatchesMetric?.textContent || '0'
    };
}

function saveChatHistory() {
    localStorage.setItem('chatbot_history', JSON.stringify(chatHistory));
}

function loadChatHistory() {
    try {
        const saved = localStorage.getItem('chatbot_history');
        if (saved) {
            chatHistory = JSON.parse(saved);
            // Restore chat history from localStorage
            // Don't manipulate DOM here - messages will be displayed when user opens chatbot
            const messagesContainer = document.getElementById('chatbot-messages');
            
            // Clear container and reload messages to avoid duplicates
            if (messagesContainer) {
                messagesContainer.innerHTML = '';
                chatHistory.forEach(msg => {
                    addChatMessage(msg.content, msg.role);
                });
            }
        }
    } catch (error) {
        console.warn('Could not load chat history:', error);
        chatHistory = [];
    }
}
