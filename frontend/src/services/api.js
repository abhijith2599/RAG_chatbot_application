import axios from 'axios';

const API_URL = 'http://127.0.0.1:8000/api/';

const api = axios.create({
  baseURL: API_URL,
});

api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('accessToken');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  error => Promise.reject(error)
);

export const registerUser = (username, password) => api.post('users/register/', { username, password });
export const loginUser = (username, password) => api.post('users/login/', { username, password });
export const getDocuments = () => api.get('users/documents/');
export const uploadDocument = (file) => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post('users/documents/upload/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

// --- ADD THESE NEW CHAT FUNCTIONS ---
export const getChatSessions = () => api.get('sessions/');
export const createChatSession = (title = "New Chat") => api.post('sessions/', { title });
export const getSessionMessages = (sessionId) => api.get(`sessions/${sessionId}/`);
export const sendMessage = (sessionId, message) => api.post(`sessions/${sessionId}/send/`, { message });