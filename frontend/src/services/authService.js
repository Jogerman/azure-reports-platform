// frontend/src/services/authService.js
import api from './api';

// Mock data para desarrollo
const MOCK_USER = {
  id: 1,
  username: 'admin',
  email: 'admin@azurereports.com',
  first_name: 'Admin',
  last_name: 'User'
};

const DEMO_CREDENTIALS = {
  email: 'admin@azurereports.com',
  password: 'admin123'
};

export const authService = {
  // Login con credenciales
  login: async (credentials) => {
    try {
      // Primero intentar con el backend real
      const response = await api.post('/auth/login/', credentials);
      const { access, refresh, user } = response.data;
      
      localStorage.setItem('token', access);
      localStorage.setItem('refreshToken', refresh);
      localStorage.setItem('user', JSON.stringify(user));
      
      return { user, token: access };
    } catch (error) {
      // Si el backend no está disponible y son las credenciales demo, usar mock
      if (error.code === 'ERR_NETWORK' || error.response?.status >= 500) {
        if (credentials.email === DEMO_CREDENTIALS.email && 
            credentials.password === DEMO_CREDENTIALS.password) {
          
          console.log('🔧 Modo desarrollo: usando autenticación mock');
          
          // Simular token JWT mock
          const mockToken = 'mock-jwt-token-for-development';
          
          localStorage.setItem('token', mockToken);
          localStorage.setItem('refreshToken', mockToken);
          localStorage.setItem('user', JSON.stringify(MOCK_USER));
          
          return { user: MOCK_USER, token: mockToken };
        }
      }
      
      // Re-lanzar error original para otros casos
      throw new Error(error.response?.data?.detail || error.message || 'Error de inicio de sesión');
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
      // Si hay un usuario mock en localStorage, devolverlo
      const mockUser = localStorage.getItem('user');
      if (mockUser && localStorage.getItem('token') === 'mock-jwt-token-for-development') {
        return JSON.parse(mockUser);
      }
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
      
      // Si es mock token, devolverlo tal como está
      if (refreshToken === 'mock-jwt-token-for-development') {
        return refreshToken;
      }
      
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