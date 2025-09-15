// src/services/api.js
import axios from 'axios';
import toast from 'react-hot-toast';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 segundos
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const { response } = error;
    
    if (response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/';
      toast.error('Tu sesión ha expirado. Por favor, inicia sesión nuevamente.');
    } else if (response?.status === 403) {
      toast.error('No tienes permisos para realizar esta acción');
    } else if (response?.status === 404) {
      toast.error('Recurso no encontrado');
    } else if (response?.status >= 500) {
      toast.error('Error del servidor. Por favor, intenta más tarde.');
    } else {
      const message = response?.data?.message || 
                     response?.data?.detail || 
                     error.message || 
                     'Error desconocido';
      toast.error(message);
    }
    
    return Promise.reject(error);
  }
);

export default api;