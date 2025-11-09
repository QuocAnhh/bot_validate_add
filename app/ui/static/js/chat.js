// Chat UI JavaScript - Single Agent Version
const API_BASE = '/api';
const DEFAULT_AGENT = 'agent'; // Single agent config name
let currentConversationId = 'test-123';
let eventSource = null;

// DOM elements
const conversationIdInput = document.getElementById('conversation-id');
const resetConversationBtn = document.getElementById('reset-conversation');
const chatMessages = document.getElementById('chat-messages');
const messageInput = document.getElementById('message-input');
const sendButton = document.getElementById('send-button');
const agentInfo = document.getElementById('agent-info');
const agentNameEl = document.getElementById('agent-name');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadAgentInfo();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    conversationIdInput.addEventListener('change', (e) => {
        currentConversationId = e.target.value || 'test-123';
    });

    resetConversationBtn.addEventListener('click', () => {
        resetConversation();
    });

    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
}

// Load agent info (single agent)
async function loadAgentInfo() {
    try {
        const response = await fetch(`${API_BASE}/agents/${DEFAULT_AGENT}`);
        const data = await response.json();
        
        if (agentNameEl) {
            agentNameEl.textContent = data.agent?.name || 'Assistant';
        }
        
        if (agentInfo) {
            agentInfo.innerHTML = `
                <p><strong>Name:</strong> ${data.agent?.name || 'Assistant'}</p>
                <p><strong>Description:</strong> ${data.agent?.description || 'N/A'}</p>
                <p><strong>Model:</strong> ${data.model?.model_name || 'N/A'}</p>
                <p><strong>Tools:</strong> None</p>
                <p><strong>Memory:</strong> Disabled</p>
            `;
        }
    } catch (error) {
        console.error('Error loading agent info:', error);
        // Use defaults if API fails
        if (agentNameEl) {
            agentNameEl.textContent = 'Assistant';
        }
    }
}

// Send message
async function sendMessage() {
    const message = messageInput.value.trim();
    
    if (!message) {
        return;
    }
    
    // Disable input
    messageInput.disabled = true;
    sendButton.disabled = true;
    
    // Add user message to chat
    addMessage('user', message);
    messageInput.value = '';
    
    // Update conversation ID
    currentConversationId = conversationIdInput.value || 'test-123';
    
    // Close previous event source if exists
    if (eventSource) {
        eventSource.close();
    }
    
    // Start streaming response
    try {
        const payload = {
            message: message,
            conversation_id: currentConversationId,
            agent_name: DEFAULT_AGENT  // Single agent
        };
        
        const response = await fetch(`${API_BASE}/chat/stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'text/event-stream'
            },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // Create assistant message element
        const assistantMessageId = `msg-${Date.now()}`;
        const assistantMsgEl = addMessage('assistant', '', assistantMessageId);
        const contentEl = assistantMsgEl.querySelector('.message-content');
        
        // Read stream
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        
        while (true) {
            const { done, value } = await reader.read();
            
            if (done) {
                break;
            }
            
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const dataStr = line.slice(6);
                    try {
                        const data = JSON.parse(dataStr);
                        
                        if (data.content) {
                            contentEl.textContent += data.content;
                            // Auto scroll
                            chatMessages.scrollTop = chatMessages.scrollHeight;
                        } else if (data.error) {
                            contentEl.innerHTML = `<span class="error">${data.error}</span>`;
                        }
                    } catch (e) {
                        console.error('Error parsing SSE data:', e);
                    }
                }
            }
        }
        
    } catch (error) {
        console.error('Error sending message:', error);
        addSystemMessage(`Error: ${error.message}`);
    } finally {
        // Re-enable input
        messageInput.disabled = false;
        sendButton.disabled = false;
        messageInput.focus();
    }
}

// Add message to chat
function addMessage(role, content, messageId = null) {
    const messageEl = document.createElement('div');
    messageId = messageId || `msg-${Date.now()}`;
    messageEl.id = messageId;
    messageEl.className = `message ${role}`;
    
    const contentEl = document.createElement('div');
    contentEl.className = 'message-content';
    contentEl.textContent = content;
    
    const timeEl = document.createElement('div');
    timeEl.className = 'message-time';
    timeEl.textContent = new Date().toLocaleTimeString('vi-VN');
    
    messageEl.appendChild(contentEl);
    messageEl.appendChild(timeEl);
    
    chatMessages.appendChild(messageEl);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return messageEl;
}

// Add system message
function addSystemMessage(content) {
    addMessage('system', content);
}

// Reset conversation
async function resetConversation() {
    if (!confirm('Are you sure you want to reset this conversation?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/agents/${DEFAULT_AGENT}/reset`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                conversation_id: currentConversationId
            })
        });
        
        if (response.ok) {
            // Clear chat messages
            chatMessages.innerHTML = `
                <div class="message system">
                    <p>Conversation reset. Start a new conversation!</p>
                </div>
            `;
            addSystemMessage('Conversation reset successfully');
        } else {
            throw new Error('Failed to reset conversation');
        }
    } catch (error) {
        console.error('Error resetting conversation:', error);
        addSystemMessage(`Error resetting conversation: ${error.message}`);
    }
}

