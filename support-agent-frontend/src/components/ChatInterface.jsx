import { useState, useEffect, useRef } from 'react';
import '../styles.css';
import '../context/AuthContext';
import { useAuth } from '../context/AuthContext';

const CONFIG = {
  apiBaseUrl: "http://localhost:8000",
  apiEndpoints: {
    health: "/api/health",
    chat: "/api/chat",
    messages: "/api/messages"
  },
  settings: {
    autoScroll: true,
    enableMarkdown: true
  }
};



export default function ChatInterface() {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const messagesEndRef = useRef(null);
  const { token, logout, user } = useAuth();

  // Initialize: test connection and load previous messages
  useEffect(() => {
    testConnection();
    loadPreviousMessages();
  }, [token]);

  // Auto scroll to bottom
  useEffect(() => {
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
      setError(`Cannot connect to backend at ${CONFIG.apiBaseUrl}`);
      console.error('Connection error:', err);
    }
  };

  const loadPreviousMessages = async () => {
    try {
      const response = await fetch(`${CONFIG.apiBaseUrl}${CONFIG.apiEndpoints.messages}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        if (data && data.length > 0) {
          const formattedMessages = data.map(msg => ({
            id: msg.id,
            content: msg.content,
            role: msg.role,
            timestamp: msg.created_at
          }));
          setMessages(formattedMessages);
        } else {
          setMessages([
            {
              id: Date.now(),
              content: 'Welcome to the AI Support Agent! 👋 How can I help you today?',
              role: 'assistant',
              timestamp: new Date().toISOString()
            }
          ]);
        }
        setError('');
      }
    } catch (err) {
      console.error('Failed to load messages:', err);
      // Set welcome message on error
      setMessages([
        {
          id: Date.now(),
          content: 'Welcome to the AI Support Agent! 👋 How can I help you today?',
          role: 'assistant',
          timestamp: new Date().toISOString()
        }
      ]);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

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

  const formatMessage = (text) => {
    if (!CONFIG.settings.enableMarkdown || typeof text !== 'string') return text;

    let html = text;
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/__(.*?)__/g, '<strong>$1</strong>');
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
    html = html.replace(/_(.*?)_/g, '<em>$1</em>');
    html = html.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    html = html.replace(
      /https?:\/\/[^\s]+/g,
      '<a href="$&" target="_blank" rel="noopener noreferrer">$&</a>'
    );
    html = html.replace(/^\s*[-*+]\s+(.+)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
    html = html.replace(/\n/g, '<br>');
    return html;
  };

  const formatTime = (timestamp) => {
  const date = new Date(timestamp);
  return date.toLocaleString([], {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
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
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ message: trimmedInput })
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
      setError(`Error: ${err.message}`);

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

  const handleLogout = () => {
    logout();
  };

  return (
    <div className="container">
      <div className="chat-header">
        <div className="header-top">
          <h1>Support Agent Chat</h1>
          <div className="header-right">
            {/* <span className="user-email">{user?.email}</span> */}
            <button onClick={handleLogout} className="logout-btn">Logout</button>
          </div>
        </div>
        <p className="subtitle">Ask your questions here</p>
      </div>

      <div className="chat-messages" id="chatMessages">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`message ${msg.role === 'user' ? 'user-message' : 'assistant-message'}`}
          >
            <div className="message-wrapper">
              <div
                className="message-content"
                dangerouslySetInnerHTML={{ __html: formatMessage(msg.content) }}
              />
              <span className="message-time">{formatTime(msg.timestamp)}</span>
            </div>
          </div>
        ))}

        {loading && (
          <div className="message assistant-message">
            <div className="message-wrapper">
              <div className="message-content">
                <div className="loading-spinner">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
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