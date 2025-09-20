// frontend/src/services/authService.js
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Crear instancia de axios principal
const axiosInstance = axios.create({
  baseURL: `${API_URL}/api`,
  timeout: 10000,
});

// Interceptor para agregar token automáticamente a TODAS las peticiones
axiosInstance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Interceptor para manejar tokens expirados
axiosInstance.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      
      try {
        await authService.refreshToken();
        const newToken = localStorage.getItem('access_token');
        original.headers.Authorization = `Bearer ${newToken}`;
        return axiosInstance(original);
      } catch (refreshError) {
        console.error('Error renovando token:', refreshError);
        authService.clearAuthData();
        window.location.href = '/';
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

export const authService = {
  // Login con email y password
  async login(credentials) {
    try {
      const response = await axiosInstance.post('/auth/login/', credentials);
      const { access, refresh, user } = response.data;
      
      // Guardar tokens
      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);
      localStorage.setItem('user_data', JSON.stringify(user));
      localStorage.setItem('auth_timestamp', Date.now().toString());
      localStorage.setItem('auth_method', 'local');
      
      return { user, access, refresh };
    } catch (error) {
      console.error('Error en login:', error);
      throw error;
    }
  },

  // Registro de usuario
  async register(userData) {
    try {
      const response = await axiosInstance.post('/auth/register/', userData);
      return response.data;
    } catch (error) {
      console.error('Error en registro:', error);
      throw error;
    }
  },

  // Logout
  async logout() {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        await axiosInstance.post('/auth/logout/', {
          refresh: refreshToken
        });
      }
    } catch (error) {
      console.error('Error en logout:', error);
    } finally {
      this.clearAuthData();
    }
  },

  // Refresh token
  async refreshToken() {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      const response = await axios.post(`${API_URL}/api/auth/refresh/`, {
        refresh: refreshToken
      });

      const { access } = response.data;
      localStorage.setItem('access_token', access);
      
      console.log('Token renovado exitosamente');
      return access;
    } catch (error) {
      console.error('Error renovando token:', error);
      this.clearAuthData();
      throw error;
    }
  },

  // Obtener usuario actual
  async getCurrentUser() {
    try {
      const response = await axiosInstance.get('/auth/users/');
      const userData = response.data.results?.[0] || response.data;
      
      // Actualizar datos en localStorage
      localStorage.setItem('user_data', JSON.stringify(userData));
      
      return userData;
    } catch (error) {
      console.error('Error obteniendo usuario actual:', error);
      throw error;
    }
  },

  // Verificar si está autenticado
  isAuthenticated() {
    const accessToken = localStorage.getItem('access_token');
    const refreshToken = localStorage.getItem('refresh_token');
    
    if (!accessToken || !refreshToken) {
      return false;
    }

    try {
      // Verificar si el token no está expirado
      const payload = JSON.parse(atob(accessToken.split('.')[1]));
      const now = Date.now() / 1000;
      
      // Si el token expira en menos de 5 minutos, considerarlo como necesita refresh
      if (payload.exp < now + 300) {
        return 'refresh_needed';
      }
      
      return true;
    } catch (error) {
      console.error('Error verificando token:', error);
      return false;
    }
  },

  // Limpiar datos de autenticación
  clearAuthData() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_id');
    localStorage.removeItem('user_data');
    localStorage.removeItem('auth_timestamp');
    localStorage.removeItem('auth_method');
  },

  // Obtener información del token
  getTokenInfo() {
    const accessToken = localStorage.getItem('access_token');
    if (!accessToken) return null;

    try {
      const payload = JSON.parse(atob(accessToken.split('.')[1]));
      return {
        user_id: payload.user_id,
        username: payload.username,
        exp: payload.exp,
        iat: payload.iat,
        isExpired: payload.exp < Date.now() / 1000
      };
    } catch (error) {
      console.error('Error parsing token:', error);
      return null;
    }
  }
};

// Exportar también la instancia de axios configurada para usar en otros servicios
export const apiClient = axiosInstance;

export default authService;