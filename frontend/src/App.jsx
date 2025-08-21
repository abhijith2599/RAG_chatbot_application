import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import ChatPage from './pages/ChatPage';
import DocumentPage from './pages/DocumentPage'; // Import the new page
import './App.css';

// A simple component to protect routes
const PrivateRoute = ({ children }) => {
  const isAuthenticated = !!localStorage.getItem('accessToken');
  return isAuthenticated ? children : <Navigate to="/" />;
};

function App() {
  return (
    <div className="App">
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route 
          path="/documents" 
          element={<PrivateRoute><DocumentPage /></PrivateRoute>} 
        />
        <Route 
          path="/chat" 
          element={<PrivateRoute><ChatPage /></PrivateRoute>} 
        />
      </Routes>
    </div>
  );
}

export default App;