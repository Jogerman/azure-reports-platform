// src/services/api.js
import axios from 'axios';

// Configuración base de axios
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para incluir token en requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Interceptor para manejar respuestas y errores
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expirado o inválido
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user_data');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Servicios de autenticación
export const authService = {
  // Login con email/password
  login: async (credentials) => {
    const response = await api.post('/auth/login/', credentials);
    if (response.data.token) {
      localStorage.setItem('auth_token', response.data.token);
      localStorage.setItem('user_data', JSON.stringify(response.data.user));
    }
    return response.data;
  },

  // Registro de nuevo usuario
  register: async (userData) => {
    const response = await api.post('/auth/register/', userData);
    return response.data;
  },

  // Logout
  logout: async () => {
    try {
      await api.post('/auth/logout/');
    } finally {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user_data');
    }
  },

  // Obtener perfil del usuario actual
  getCurrentUser: async () => {
    const response = await api.get('/auth/profile/');
    return response.data;
  },

  // Verificar si hay token válido
  isAuthenticated: () => {
    return !!localStorage.getItem('auth_token');
  },

  // Obtener datos del usuario del localStorage
  getUserData: () => {
    const userData = localStorage.getItem('user_data');
    return userData ? JSON.parse(userData) : null;
  }
};

// Servicios para CSV y reportes
export const reportService = {
  // Subir archivo CSV
  uploadCSV: async (file, onProgress) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/reports/csv-upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      },
    });
    return response.data;
  },

  // Listar archivos CSV del usuario
  getCSVFiles: async () => {
    const response = await api.get('/reports/csv-files/');
    return response.data;
  },

  // Generar reporte
  generateReport: async (data) => {
    const response = await api.post('/reports/generate/', data);
    return response.data;
  },

  // Listar reportes del usuario
  getReports: async (filters = {}) => {
    const params = new URLSearchParams(filters).toString();
    const response = await api.get(`/reports/?${params}`);
    return response.data;
  },

  // Obtener detalles de un reporte
  getReportDetails: async (reportId) => {
    const response = await api.get(`/reports/${reportId}/`);
    return response.data;
  },

  // Descargar reporte PDF
  downloadReport: async (reportId) => {
    const response = await api.get(`/reports/${reportId}/download/`, {
      responseType: 'blob',
    });
    
    // Crear URL para descargar
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `reporte_${reportId}.pdf`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },

  // Obtener vista previa HTML del reporte
  getReportPreview: async (reportId) => {
    const response = await api.get(`/reports/${reportId}/preview/`);
    return response.data;
  },

  // Eliminar reporte
  deleteReport: async (reportId) => {
    const response = await api.delete(`/reports/${reportId}/`);
    return response.data;
  }
};

// Servicios para dashboard y estadísticas
export const dashboardService = {
  // Obtener estadísticas del dashboard
  getStats: async () => {
    const response = await api.get('/dashboard/stats/');
    return response.data;
  },

  // Obtener reportes recientes
  getRecentReports: async (limit = 5) => {
    const response = await api.get(`/dashboard/recent-reports/?limit=${limit}`);
    return response.data;
  },

  // Obtener actividad reciente
  getRecentActivity: async (limit = 10) => {
    const response = await api.get(`/dashboard/activity/?limit=${limit}`);
    return response.data;
  }
};

// Servicios de almacenamiento (Azure Blob)
export const storageService = {
  // Listar archivos en storage
  getStorageFiles: async (filters = {}) => {
    const params = new URLSearchParams(filters).toString();
    const response = await api.get(`/storage/files/?${params}`);
    return response.data;
  },

  // Obtener URL de descarga de archivo
  getFileUrl: async (fileName) => {
    const response = await api.get(`/storage/files/${fileName}/url/`);
    return response.data.url;
  }
};

// Servicios de configuración
export const settingsService = {
  // Obtener configuraciones del usuario
  getUserSettings: async () => {
    const response = await api.get('/settings/user/');
    return response.data;
  },

  // Actualizar configuraciones del usuario
  updateUserSettings: async (settings) => {
    const response = await api.put('/settings/user/', settings);
    return response.data;
  },

  // Cambiar contraseña
  changePassword: async (passwordData) => {
    const response = await api.post('/settings/change-password/', passwordData);
    return response.data;
  }
};

export default api;