// frontend/src/services/authService.js
import api from './api';

export const authService = {
  // Login con credenciales
  login: async (credentials) => {
    try {
      const response = await api.post('/auth/login/', credentials);
      const { access, refresh, user } = response.data;
      
      localStorage.setItem('token', access);
      localStorage.setItem('refreshToken', refresh);
      localStorage.setItem('user', JSON.stringify(user));
      
      return { user, token: access };
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Error de inicio de sesión');
    }
  },

  // Registro de usuario
  register: async (userData) => {
    try {
      const response = await api.post('/auth/register/', userData);
      return response.data;
    } catch (error) {
      const errors = error.response?.data;
      if (errors) {
        const errorMessages = Object.values(errors).flat().join(', ');
        throw new Error(errorMessages);
      }
      throw new Error('Error de registro');
    }
  },

  // Logout
  logout: async () => {
    try {
      await api.post('/auth/logout/');
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('token');
      localStorage.removeItem('refreshToken');
      localStorage.removeItem('user');
    }
  },

  // Obtener usuario actual
  getCurrentUser: async () => {
    try {
      const response = await api.get('/auth/users/profile/');
      return response.data;
    } catch (error) {
      throw new Error('Error obteniendo perfil de usuario');
    }
  },

  // Actualizar perfil
  updateProfile: async (userData) => {
    try {
      const response = await api.patch('/auth/users/update_profile/', userData);
      localStorage.setItem('user', JSON.stringify(response.data));
      return response.data;
    } catch (error) {
      throw new Error('Error actualizando perfil');
    }
  },

  // Refresh token
  refreshToken: async () => {
    try {
      const refreshToken = localStorage.getItem('refreshToken');
      if (!refreshToken) throw new Error('No refresh token available');
      
      const response = await api.post('/auth/refresh/', {
        refresh: refreshToken
      });
      
      const { access } = response.data;
      localStorage.setItem('token', access);
      return access;
    } catch (error) {
      localStorage.removeItem('token');
      localStorage.removeItem('refreshToken');
      localStorage.removeItem('user');
      throw error;
    }
  },

  // Verificar si está autenticado
  isAuthenticated: () => {
    const token = localStorage.getItem('token');
    const user = localStorage.getItem('user');
    return !!(token && user);
  },

  // Obtener usuario desde localStorage
  getStoredUser: () => {
    try {
      const user = localStorage.getItem('user');
      return user ? JSON.parse(user) : null;
    } catch {
      return null;
    }
  }
};