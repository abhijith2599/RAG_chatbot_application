import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import ChatWindow from '../components/ChatWindow';
import { getChatSessions, createChatSession, getSessionMessages } from '../services/api';
import '../App.css';

function ChatPage() {
  const [sessions, setSessions] = useState([]);
  const [activeSession, setActiveSession] = useState(null);
  // --- FIX 1: DEFINE THE MISSING STATE ---
  const [isSidebarVisible, setIsSidebarVisible] = useState(true);

  useEffect(() => {
    const loadSessions = async () => {
      try {
        const response = await getChatSessions();
        setSessions(response.data);
      } catch (error) {
        console.error("Failed to load sessions:", error);
      }
    };
    loadSessions();
  }, []);

  const handleCreateNewSession = async () => {
    try {
      const response = await createChatSession();
      const newSession = { ...response.data, messages: [] };
      setSessions([newSession, ...sessions]);
      setActiveSession(newSession);
    } catch (error) {
      console.error("Failed to create new session:", error);
    }
  };

  const handleSessionSelect = async (sessionId) => {
    try {
      const response = await getSessionMessages(sessionId);
      setActiveSession(response.data);
    } catch (error) {
      console.error("Failed to load session messages:", error);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    window.location.href = '/';
  };

  const updateSessionTitle = (sessionId, newTitle) => {
    setSessions(prevSessions =>
      prevSessions.map(session =>
        session.id === sessionId ? { ...session, title: newTitle } : session
      )
    );
    if (activeSession && activeSession.id === sessionId) {
      setActiveSession(prev => ({ ...prev, title: newTitle }));
    }
  };

  return (
    <div className={`chat-page-container ${isSidebarVisible ? '' : 'sidebar-hidden'}`}>
      <Sidebar 
        sessions={sessions} 
        onSessionSelect={handleSessionSelect}
        onCreateNew={handleCreateNewSession}
      />
      <div className="main-content">
        <header className="app-header">
          <button className="sidebar-toggle" onClick={() => setIsSidebarVisible(!isSidebarVisible)}>
            &#9776;
          </button>
          <Link to="/documents">My Documents</Link>
          <button onClick={handleLogout}>Logout</button>
        </header>
        <ChatWindow 
          activeSession={activeSession}
          onNewMessage={updateSessionTitle}
        />
      </div>
    </div>
  );
}

export default ChatPage;