import React from 'react';
import { useAuth } from '../context/AuthContext';

function Sidebar({ sessions, onSessionSelect, onCreateNew }) {
    const { user } = useAuth();

  return (
    <div className="sidebar">
      <button className="new-chat-btn" onClick={onCreateNew}>
        + New Chat
      </button>
      <div className="session-list">
        {sessions.map(session => (
          <div 
            key={session.id} 
            className="session-item"
            onClick={() => onSessionSelect(session.id)}
          >
            {session.title}
          </div>
        ))}
      </div>
      <div className="user-profile">
        {user && <span>Welcome, {user.username}</span>}
      </div>
    </div>
  );
}

export default Sidebar;