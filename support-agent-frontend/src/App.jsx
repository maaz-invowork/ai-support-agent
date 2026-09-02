import { useState } from 'react';
import './styles.css';
import './auth.css';
import { useAuth } from './context/AuthContext';
import LoginForm from './components/LoginForm';
import RegisterForm from './components/RegisterForm';
import ChatInterface from './components/ChatInterface';


export default function App() {
  const { user, loading, token } = useAuth();
  const [authMode, setAuthMode] = useState('login');

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        width: '100vw',
        background: "#000"
      }}>
        <div style={{ color: 'white', fontSize: '1.2rem' }}>Loading...</div>
      </div>
    );
  }

  if (!token || !user) {
    return (
      <>
        {authMode === 'login' ? (
          <LoginForm onSwitchToRegister={() => setAuthMode('register')} />
        ) : (
          <RegisterForm onSwitchToLogin={() => setAuthMode('login')} />
        )}
      </>
    );
  }

  return <ChatInterface />;
}