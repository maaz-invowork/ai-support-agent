import React, { useState, useEffect, useRef } from 'react';
import './styles.css';

const CONFIG = {
  apiBaseUrl: "http://localhost:8000",
  apiEndpoints: {
    health: "/api/health",
    chat: "/api/chat"
  },
  settings: {
    autoScroll: true,
    persistChat: true,
    enableMarkdown: true
  }
};

export default function App() {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const messagesEndRef = useRef(null);

  // Initialize chat history and health check
  useEffect(() => {
    let initialMessages = [];
    if (CONFIG.settings.persistChat) {
      const saved = localStorage.getItem('chatMessages');
      if (saved) {
        try {
          initialMessages = JSON.parse(saved);
        } catch (e) {
          console.error('Failed to parse saved chat history:', e);
        }
      }
    }

    if (initialMessages.length === 0) {
      initialMessages = [
        {
          id: Date.now(),
          content: 'Welcome to the AI Support Agent! 👋 How can I help you today?',
          role: 'assistant',
          timestamp: new Date().toISOString()
        }
      ];
    }
    setMessages(initialMessages);

    // Test health connection
    testConnection();
  }, []);

  // Save to localStorage when messages update
  useEffect(() => {
    if (CONFIG.settings.persistChat && messages.length > 0) {
      localStorage.setItem('chatMessages', JSON.stringify(messages));
    }
    if (CONFIG.settings.autoScroll) {
      scrollToBottom();
    }
  }, [messages, loading]);

  const testConnection = async () => {
    try {
      const response = await fetch(`${CONFIG.apiBaseUrl}${CONFIG.apiEndpoints.health}`);
      if (!response.ok) {
        setError(`Backend not available (${response.status})`);
      }
    } catch (err) {
      setError(`Cannot connect to backend at ${CONFIG.apiBaseUrl}.mm`);
      console.error('Connection error:', err);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Helper to extract clean text from structured responses or arrays
  const parseRawText = (raw) => {
    if (typeof raw === 'string') return raw;

    if (Array.isArray(raw)) {
      return raw
        .map(item => {
          if (typeof item === 'object' && item !== null) {
            return item.text || item.content || '';
          }
          return String(item);
        })
        .join('');
    }

    if (typeof raw === 'object' && raw !== null) {
      return raw.text || raw.content || JSON.stringify(raw);
    }

    return String(raw);
  };

  // Simple Markdown-like formatter
  const formatMessage = (text) => {
    if (!CONFIG.settings.enableMarkdown || typeof text !== 'string') return text;

    let html = text;

    // Bold
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/__(.*?)__/g, '<strong>$1</strong>');

    // Italic
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
    html = html.replace(/_(.*?)_/g, '<em>$1</em>');

    // Code Blocks
    html = html.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');

    // Inline Code
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Links
    html = html.replace(
      /https?:\/\/[^\s]+/g,
      '<a href="$&" target="_blank" rel="noopener noreferrer">$&</a>'
    );

    // Lists
    html = html.replace(/^\s*[-*+]\s+(.+)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
    html = html.replace(/^\s*\d+\.\s+(.+)$/gm, '<li>$1</li>');

    // Line breaks
    html = html.replace(/\n/g, '<br>');

    return html;
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    const trimmedInput = inputValue.trim();
    if (!trimmedInput || loading) return;

    const userMsg = {
      id: Date.now(),
      content: trimmedInput,
      role: 'user',
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMsg]);
    setInputValue('');
    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${CONFIG.apiBaseUrl}${CONFIG.apiEndpoints.chat}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: trimmedInput }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      const rawResponse = data.response || data.message || 'No response received';
      const cleanResponse = parseRawText(rawResponse);

      const assistantMsg = {
        id: Date.now() + 1,
        content: cleanResponse,
        role: 'assistant',
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, assistantMsg]);
    } catch (err) {
      console.error('Error:', err);
      setError(`Error: ${err.message}. Make sure the backend is running at ${CONFIG.apiBaseUrl}`);
      
      const errorMsg = {
        id: Date.now() + 1,
        content: '❌ Sorry, there was an error processing your request. Please try again.',
        role: 'assistant',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <div className="chat-header">
        <h1>Support Agent Chat</h1>
        <p className="subtitle">Ask your questions here</p>
      </div>

      <div className="chat-messages" id="chatMessages">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`message ${msg.role === 'user' ? 'user-message' : 'assistant-message'}`}
          >
            <div
              className="message-content"
              dangerouslySetInnerHTML={{ __html: formatMessage(msg.content) }}
            />
          </div>
        ))}

        {loading && (
          <div className="message assistant-message">
            <div className="message-content">
              <div className="loading-spinner">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-area">
        <form onSubmit={handleSendMessage}>
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Type your question here..."
            disabled={loading}
            className="chat-input"
            autoComplete="off"
          />
          <button
            type="submit"
            disabled={loading || !inputValue.trim()}
            className="send-button"
          >
            {!loading ? (
              'Send'
            ) : (
              <span className="button-loader">Sending...</span>
            )}
          </button>
        </form>
      </div>

      {error && (
        <div className="error-message dismissible" onClick={() => setError('')}>
          <span>{error}</span>
          <button type="button" className="close-error">×</button>
        </div>
      )}
    </div>
  );
}