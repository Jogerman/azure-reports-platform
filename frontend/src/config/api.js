// src/config/api.js - VERSIÓN CORREGIDA SIN PROCESS
export const API_CONFIG = {
  // URL base del backend - CORREGIDA
  BASE_URL: (() => {
    // Para producción
    if (window.location.hostname !== 'localhost') {
      return window.location.origin + '/api';
    }
    
    // Para desarrollo local - CORREGIDO
    return 'http://localhost:8000/api';
  })(),
  
  // Timeouts
  TIMEOUT: 30000, // 30 segundos
  UPLOAD_TIMEOUT: 300000, // 5 minutos para uploads
  
   ENDPOINTS: {
    AUTH: {
      LOGIN: '/auth/login/',
      REGISTER: '/auth/register/',
      LOGOUT: '/auth/logout/',
      REFRESH: '/auth/refresh/',
      PROFILE: '/auth/users/profile/',
      MICROSOFT_LOGIN: '/auth/microsoft/login/',  // CORREGIDO
      MICROSOFT_CALLBACK: '/auth/microsoft/callback/',
    },
    
    FILES: {
      UPLOAD: '/files/upload/',
      LIST: '/files/',
      DETAIL: '/files/:id/',
      DELETE: '/files/:id/',
      DOWNLOAD: '/files/:id/download/',
    },
    
    REPORTS: {
      GENERATE: '/reports/generate/',  // CORREGIDO
      LIST: '/reports/',
      DETAIL: '/reports/:id/',
      HTML: '/reports/:id/html/',
      DOWNLOAD: '/reports/:id/download/',
      DELETE: '/reports/:id/',
    },
    
    DASHBOARD: {
      STATS: '/dashboard/stats/',     // CORREGIDO
      ACTIVITY: '/dashboard/activity/',
    },
    
    HEALTH: '/health/',
  },
  
  DEFAULT_HEADERS: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
  
  // Configuración de retry
  RETRY: {
    ATTEMPTS: 3,
    DELAY: 1000, // 1 segundo
    EXPONENTIAL: true,
  },
};

// FUNCIÓN CORREGIDA para fetch con autenticación
export const fetchWithAuth = async (url, options = {}) => {
  const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
  
  const config = {
    ...options,
    headers: {
      ...API_CONFIG.DEFAULT_HEADERS,
      ...options.headers,
      ...(token && { Authorization: `Bearer ${token}` }),
    },
    timeout: API_CONFIG.TIMEOUT,
  };

  try {
    const response = await fetch(url, config);
    
    if (response.status === 401) {
      // Token expirado
      localStorage.removeItem('access_token');
      sessionStorage.removeItem('access_token');
      window.location.href = '/';
      throw new Error('Sesión expirada');
    }
    
    return response;
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};


// Helper para construir URLs
export const buildUrl = (endpoint, params = {}) => {
  let url = API_CONFIG.BASE_URL + endpoint;
  
  // Reemplazar parámetros en la URL
  Object.entries(params).forEach(([key, value]) => {
    url = url.replace(`:${key}`, value);
  });
  
  return url;
};

// Helper para obtener headers con autenticación
export const getAuthHeaders = () => {
  const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
  
  return {
    ...API_CONFIG.DEFAULT_HEADERS,
    ...(token && { Authorization: `Bearer ${token}` }),
  };
};

// Helper para manejar respuestas de API
export const handleApiResponse = async (response) => {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ 
      detail: 'Error de conexión con el servidor' 
    }));
    
    // Manejar errores específicos
    switch (response.status) {
      case 401:
        // Token expirado o inválido
        localStorage.removeItem('access_token');
        sessionStorage.removeItem('access_token');
        window.location.href = '/';
        throw new Error('Sesión expirada. Por favor, inicia sesión nuevamente.');
        
      case 403:
        throw new Error('No tienes permisos para realizar esta acción.');
        
      case 404:
        throw new Error('Recurso no encontrado.');
        
      case 413:
        throw new Error('El archivo es demasiado grande. Máximo 50MB.');
        
      case 422:
        throw new Error('Datos inválidos. Verifica la información enviada.');
        
      case 429:
        throw new Error('Demasiadas solicitudes. Intenta nuevamente en unos minutos.');
        
      case 500:
        throw new Error('Error interno del servidor. Intenta nuevamente.');
        
      default:
        throw new Error(error.detail || error.message || 'Error desconocido');
    }
  }
  
  return response.json();
};

// Helper para realizar peticiones con retry
export const fetchWithRetry = async (url, options = {}, retryCount = 0) => {
  try {
    const response = await fetch(url, {
      timeout: options.timeout || API_CONFIG.TIMEOUT,
      ...options,
    });
    
    return await handleApiResponse(response);
  } catch (error) {
    if (retryCount < API_CONFIG.RETRY.ATTEMPTS) {
      const delay = API_CONFIG.RETRY.EXPONENTIAL 
        ? API_CONFIG.RETRY.DELAY * Math.pow(2, retryCount)
        : API_CONFIG.RETRY.DELAY;
        
      await new Promise(resolve => setTimeout(resolve, delay));
      return fetchWithRetry(url, options, retryCount + 1);
    }
    
    throw error;
  }
};

// Detectar entorno
const isProduction = typeof window !== 'undefined' && window.location.hostname !== 'localhost';
const isDevelopment = !isProduction;

// Configuración específica para desarrollo
export const DEV_CONFIG = {
  // Mock responses para desarrollo sin backend
  USE_MOCK: isDevelopment && API_CONFIG.BASE_URL.includes('localhost'),
  
  // Delays simulados para desarrollo
  MOCK_DELAYS: {
    UPLOAD: 2000,
    GENERATE_REPORT: 3000,
    API_CALL: 500,
  },
  
  // Datos mock
  MOCK_DATA: {
    USER: {
      id: 1,
      username: 'usuario_demo',
      email: 'demo@azurereports.com',
      first_name: 'Usuario',
      last_name: 'Demo',
    },
    
    STATS: {
      total_reports: 1,
      total_files: 2,
      total_recommendations: 751,
      potential_savings: 45757,
    },
  },
};

export default API_CONFIG;