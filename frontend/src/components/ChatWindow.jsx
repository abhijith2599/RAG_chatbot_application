import React, { useState, useEffect, useRef } from 'react';
import { sendMessage } from '../services/api';

function ChatWindow({ activeSession, onNewMessage }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);

  useEffect(() => {
    setMessages(activeSession ? activeSession.messages : []);
  }, [activeSession]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || !activeSession) return;

    // --- FIX 2: CHECK THE CONDITION *BEFORE* THE API CALL ---
    const isFirstMessage = messages.length === 0;

    const userMessage = { is_from_ai: false, message: input };
    // Optimistically update the UI with the user's message
    setMessages(prev => [...prev, userMessage]);
    setInput('');

    try {
      const response = await sendMessage(activeSession.id, input);
      const botMessage = { is_from_ai: true, message: response.data.answer, sources: response.data.sources };
      // Update the UI with the bot's response
      setMessages(prev => [...prev, botMessage]);

      // If it was the first message, trigger the title update
      if (isFirstMessage) {
        const newTitle = input.substring(0, 30) + (input.length > 30 ? '...' : '');
        onNewMessage(activeSession.id, newTitle);
      }

    } catch (error) {
      console.error("Error sending message:", error);
      const errorMessage = { is_from_ai: true, message: 'Sorry, I encountered an error.' };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  if (!activeSession) {
    return <div className="chat-window-placeholder">Select a chat or start a new one.</div>;
  }

  return (
    <div className="chat-window">
      <div className="message-list">
        {messages.map((msg, index) => (
          // Use the 'is_from_ai' field from our database model
          <div key={index} className={`message ${msg.is_from_ai ? 'ai' : 'user'}`}>
            <p>{msg.message}</p>
            {msg.sources && msg.sources.length > 0 && (
              <p className="sources">Sources: {msg.sources.join(', ')}</p>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      <div className="input-area">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask a question..."
        />
        <button onClick={handleSend}>Send</button>
      </div>
    </div>
  );
}

export default ChatWindow;