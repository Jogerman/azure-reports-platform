// src/hooks/useReports.js - VERSIÓN CORREGIDA CON BACKEND REAL
import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';

// Import configuración de API
import { API_CONFIG } from '../config/api';

// API Base URL - usando configuración centralizada
const API_BASE_URL = API_CONFIG.BASE_URL;

// Helper para obtener token de autenticación
const getAuthToken = () => {
  // Buscar en múltiples lugares
  const token = 
    localStorage.getItem('access_token') || 
    sessionStorage.getItem('access_token') ||
    localStorage.getItem('accessToken') ||
    sessionStorage.getItem('accessToken') ||
    localStorage.getItem('token') ||
    sessionStorage.getItem('token');
  
  console.log('🔐 Token encontrado:', token ? `${token.substring(0, 20)}...` : 'NO ENCONTRADO');
  return token;
};


// Helper para headers con autenticación
const getAuthHeaders = () => {
  const token = getAuthToken();
  
  const headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
    console.log('🔑 Header Authorization agregado');
  } else {
    console.warn('⚠️ No se encontró token de autenticación');
  }
  
  return headers;
};

const isAuthenticated = () => {
  const token = getAuthToken();
  if (!token) return false;
  
  try {
    // Verificar si el token no está expirado (básico)
    const payload = JSON.parse(atob(token.split('.')[1]));
    const now = Date.now() / 1000;
    return payload.exp > now;
  } catch (error) {
    console.error('Error verificando token:', error);
    return false;
  }
};


const refreshTokenIfNeeded = async () => {
  const refreshToken = localStorage.getItem('refresh_token') || 
                      sessionStorage.getItem('refresh_token');
  
  if (!refreshToken) {
    console.warn('⚠️ No hay refresh token, redirigiendo al login');
    // Limpiar storage y redirigir
    localStorage.clear();
    sessionStorage.clear();
    window.location.href = '/';
    return false;
  }
  
  try {
    console.log('🔄 Intentando refrescar token...');
    const response = await fetch(`${API_BASE_URL}/auth/refresh/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        refresh: refreshToken
      }),
    });
    
    if (response.ok) {
      const data = await response.json();
      localStorage.setItem('access_token', data.access);
      console.log('✅ Token refrescado exitosamente');
      return true;
    } else {
      console.error('❌ Error refrescando token');
      // Token refresh falló, limpiar y redirigir
      localStorage.clear();
      sessionStorage.clear();
      window.location.href = '/';
      return false;
    }
  } catch (error) {
    console.error('❌ Error en refresh:', error);
    localStorage.clear();
    sessionStorage.clear();
    window.location.href = '/';
    return false;
  }
};


// Servicio API para archivos
const fileService = {
  async uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    // Agregar metadatos opcionales
    formData.append('file_type', 'csv');
    formData.append('source', 'azure_advisor');

    try {
      console.log('📤 Iniciando upload de archivo:', file.name);
      
      const response = await fetchWithAuth(`${API_BASE_URL}/files/upload/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`,
          // NO agregar Content-Type para FormData - el browser lo hace automáticamente
        },
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ 
          detail: 'Error de conexión con el servidor' 
        }));
        throw new Error(error.detail || error.error || `Error ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      console.log('✅ Upload exitoso:', result);
      
      return result;
    } catch (error) {
      console.error('❌ Error en upload:', error);
      throw error;
    }
  },

 async getFiles() {
    try {
      console.log('📁 Obteniendo archivos del backend...');
      const response = await fetchWithAuth(`${API_BASE_URL}/files/`);

      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      console.log('✅ Archivos obtenidos del backend:', data);
      
      // Asegurar formato correcto
      if (data && Array.isArray(data.results)) {
        return data;
      } else if (Array.isArray(data)) {
        return { results: data, count: data.length };
      } else {
        console.warn('⚠️ Formato de respuesta inesperado:', data);
        return { results: [], count: 0 };
      }
      
    } catch (error) {
      console.error('❌ Error obteniendo archivos del backend:', error);
      
      // FALLBACK VACÍO - NO MOCK DATA para evitar IDs falsos
      console.log('🔄 Retornando array vacío (sin mock data)');
      return {
        results: [],
        count: 0
      };
    }
  },
  // Obtener archivo específico
  async getFile(fileId) {
    try {
      const response = await fetchWithAuth(`${API_BASE_URL}/files/${fileId}/`);
      if (!response.ok) {
        throw new Error('Error obteniendo archivo');
      }
      return response.json();
    } catch (error) {
      console.error('Get file error:', error);
      throw error;
    }
  },

  async deleteFile(fileId) {
    try {
      const response = await fetchWithAuth(`${API_BASE_URL}/files/${fileId}/`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        throw new Error('Error eliminando archivo');
      }
      return true;
    } catch (error) {
      console.error('Delete file error:', error);
      throw error;
    }
  },
};

const fetchWithAuth = async (url, options = {}) => {
  // Verificar autenticación antes de hacer la petición
  if (!isAuthenticated()) {
    console.log('🔄 Token expirado, intentando refresh...');
    const refreshed = await refreshTokenIfNeeded();
    if (!refreshed) {
      throw new Error('Sesión expirada');
    }
  }
  
  // Hacer petición con headers de autenticación
  const response = await fetch(url, {
    ...options,
    headers: {
      ...getAuthHeaders(),
      ...options.headers,
    },
  });
  
  // Manejar 401 Unauthorized
  if (response.status === 401) {
    console.log('❌ 401 Unauthorized recibido, intentando refresh...');
    const refreshed = await refreshTokenIfNeeded();
    
    if (refreshed) {
      // Retry la petición original con nuevo token
      console.log('🔄 Reintentando petición con nuevo token...');
      return fetch(url, {
        ...options,
        headers: {
          ...getAuthHeaders(),
          ...options.headers,
        },
      });
    }
  }
  
  return response;
};

// Servicio API para reportes
const reportService = {
  
  // Generar reporte
  async generateReport(fileId, reportConfig) {
    const response = await fetch(`${API_BASE_URL}/reports/generate/`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        file_id: fileId,
        title: reportConfig.title,
        description: reportConfig.description,
        report_type: reportConfig.type,
        generation_config: {
          include_charts: reportConfig.includeCharts,
          include_tables: reportConfig.includeTables,
          include_recommendations: reportConfig.includeRecommendations,
        },
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Error generando reporte');
    }

    return response.json();
  },

  // Obtener reportes del usuario
  async getReports(filters = {}) {
    try {
      const queryParams = new URLSearchParams();
      
      Object.entries(filters).forEach(([key, value]) => {
        if (value && value !== '') {
          queryParams.append(key, value);
        }
      });

      console.log('📋 Obteniendo reportes del backend...');
      const response = await fetchWithAuth(`${API_BASE_URL}/reports/?${queryParams}`);

      if (response.status === 404) {
        console.warn('⚠️ Endpoint /reports/ no implementado');
        return { results: [], count: 0 };  // Array vacío, no mock
      }

      if (!response.ok) {
        throw new Error('Error obteniendo reportes');
      }

      const data = await response.json();
      console.log('✅ Reportes obtenidos del backend:', data);
      return data;
    } catch (error) {
      console.error('❌ Error obteniendo reportes:', error);
      // Fallback vacío para evitar IDs mock problemáticos
      return { results: [], count: 0 };
    }
  },

  // Método getMockReports REMOVIDO o simplificado
  getMockReports(filters = {}) {
    // Retornar array vacío para evitar conflictos con IDs
    return {
      results: [],
      count: 0
    };
  },

  // Obtener reporte específico
  async getReport(reportId) {
    const response = await fetch(`${API_BASE_URL}/reports/${reportId}/`, {
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error('Error obteniendo reporte');
    }

    return response.json();
  },

  // Obtener HTML del reporte para visualización
  async getReportHTML(reportId) {
    const response = await fetch(`${API_BASE_URL}/reports/${reportId}/html/`, {
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error('Error obteniendo HTML del reporte');
    }

    return response.text(); // Retorna HTML como texto
  },

  // Descargar reporte en PDF
  async downloadReportPDF(reportId, filename) {
    const response = await fetch(`${API_BASE_URL}/reports/${reportId}/download/`, {
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error('Error descargando reporte');
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename || `reporte_${reportId}.pdf`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  },

  // Eliminar reporte
  async deleteReport(reportId) {
    const response = await fetch(`${API_BASE_URL}/reports/${reportId}/`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error('Error eliminando reporte');
    }

    return true;
  },
};

// Servicio para estadísticas del dashboard
const dashboardService = {
  async getStats() {
    try {
      console.log('📊 Obteniendo stats del dashboard...');
      const response = await fetchWithAuth(`${API_BASE_URL}/dashboard/stats/`);

      if (response.status === 404) {
        console.warn('⚠️ Endpoint /dashboard/stats/ no implementado, usando mock');
        return this.getMockStats();
      }

      if (!response.ok) {
        throw new Error('Error obteniendo estadísticas');
      }

      const data = await response.json();
      console.log('✅ Stats obtenidas del backend:', data);
      return data;
    } catch (error) {
      console.error('Get dashboard stats error:', error);
      return this.getMockStats();
    }
  },

  getMockStats() {
    console.log('📊 Usando stats mock');
    return {
      total_files: 2,
      total_reports: 1,
      completed_reports: 1,
      total_recommendations: 25,
      potential_savings: 15420,
      success_rate: 100,
      last_updated: new Date().toISOString()
    };
  }
};


// HOOKS CORREGIDOS

// Hook para subir archivos
export const useFileUpload = () => {
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const queryClient = useQueryClient();

  const uploadFile = async (file) => {
    setIsUploading(true);
    setProgress(0);

    try {
      // Simular progreso mientras se sube
      const progressInterval = setInterval(() => {
        setProgress(prev => {
          const newProgress = prev + Math.random() * 15;
          return newProgress >= 90 ? 90 : newProgress;
        });
      }, 200);

      const result = await fileService.uploadFile(file);

      // Completar progreso
      clearInterval(progressInterval);
      setProgress(100);

      // Invalidar consultas para refrescar la lista
      queryClient.invalidateQueries(['files']);
      queryClient.invalidateQueries(['dashboard-stats']);

      console.log('📁 Upload completado exitosamente');
      
      return result;
    } catch (error) {
      console.error('❌ Error en upload:', error);
      throw error;
    } finally {
      setIsUploading(false);
      // Resetear progreso después de un delay
      setTimeout(() => setProgress(0), 1000);
    }
  };

  return { uploadFile, isUploading, progress };
};
// Hook para obtener archivos

export const useStorageFiles = () => {
  return useQuery({
    queryKey: ['files'],
    queryFn: fileService.getFiles,
    staleTime: 30000,
    select: (data) => {
      console.log('🔍 useStorageFiles - Procesando datos:', data);
      
      if (data && Array.isArray(data.results)) {
        return data.results;
      } else if (Array.isArray(data)) {
        return data;
      } else {
        console.warn('⚠️ useStorageFiles: Formato inesperado, usando array vacío');
        return [];
      }
    },
    onError: (error) => {
      console.error('❌ Error en useStorageFiles:', error);
    },
  });
};

// Hook para generar reportes
export const useReportGeneration = () => {
  const [isGenerating, setIsGenerating] = useState(false);
  const queryClient = useQueryClient();

  const generateReport = async (fileId, reportConfig) => {
    setIsGenerating(true);

    try {
      toast.loading('🔄 Analizando datos y generando reporte...', { id: 'generating' });

      const report = await reportService.generateReport(fileId, reportConfig);

      // Invalidar consultas para refrescar listas
      queryClient.invalidateQueries(['reports']);
      queryClient.invalidateQueries(['recent-reports']);
      queryClient.invalidateQueries(['dashboard-stats']);

      toast.success(
        `🎉 Reporte "${report.title}" generado exitosamente`, 
        { id: 'generating' }
      );

      // Mostrar estadísticas del reporte si están disponibles
      if (report.analysis_summary) {
        toast.success(
          `📊 ${report.analysis_summary.total_recommendations || 0} recomendaciones incluidas`
        );
      }

      return report;
    } catch (error) {
      console.error('Error generating report:', error);
      toast.error(`❌ Error: ${error.message}`, { id: 'generating' });
      throw error;
    } finally {
      setIsGenerating(false);
    }
  };

  return { generateReport, isGenerating };
};

// Hook para obtener reportes
export const useReports = (filters = {}) => {
  return useQuery({
    queryKey: ['reports', filters],
    queryFn: () => reportService.getReports(filters),
    staleTime: 30000,
    onError: (error) => {
      console.error('Error fetching reports:', error);
      toast.error('Error cargando reportes');
    },
  });
};

// Hook para reportes recientes
export const useRecentReports = (limit = 5) => {
  return useQuery({
    queryKey: ['recent-reports', limit],
    queryFn: () => reportService.getReports({ limit, ordering: '-created_at' }),
    staleTime: 30000,
    select: (data) => data.results?.slice(0, limit) || data.slice(0, limit) || [],
    onError: (error) => {
      console.error('Error fetching recent reports:', error);
    },
  });
};

// Hook para estadísticas del dashboard
export const useDashboardStats = () => {
  return useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: dashboardService.getStats,
    staleTime: 60000, // 1 minuto
    onError: (error) => {
      console.error('Error fetching dashboard stats:', error);
    },
  });
};

// Hook para obtener HTML de reporte
export const useReportHTML = (reportId) => {
  return useQuery({
    queryKey: ['report-html', reportId],
    queryFn: () => reportService.getReportHTML(reportId),
    enabled: !!reportId,
    staleTime: 300000, // 5 minutos
    onError: (error) => {
      console.error('Error fetching report HTML:', error);
      toast.error('Error cargando visualización del reporte');
    },
  });
};

// Hook para mutaciones de reportes
export const useReportMutations = () => {
  const queryClient = useQueryClient();

  const deleteReport = useMutation({
    mutationFn: reportService.deleteReport,
    onSuccess: () => {
      queryClient.invalidateQueries(['reports']);
      queryClient.invalidateQueries(['recent-reports']);
      queryClient.invalidateQueries(['dashboard-stats']);
      toast.success('Reporte eliminado exitosamente');
    },
    onError: (error) => {
      toast.error(`Error eliminando reporte: ${error.message}`);
    },
  });

  const downloadReport = useMutation({
    mutationFn: ({ reportId, filename }) => 
      reportService.downloadReportPDF(reportId, filename),
    onSuccess: () => {
      toast.success('📥 Descarga iniciada');
    },
    onError: (error) => {
      toast.error(`Error descargando reporte: ${error.message}`);
    },
  });

  return {
    deleteReport,
    downloadReport,
  };
};

// Hook para mutaciones de archivos
export const useFileMutations = () => {
  const queryClient = useQueryClient();

  const deleteFile = useMutation({
    mutationFn: fileService.deleteFile,
    onSuccess: () => {
      queryClient.invalidateQueries(['files']);
      queryClient.invalidateQueries(['dashboard-stats']);
      toast.success('Archivo eliminado exitosamente');
    },
    onError: (error) => {
      toast.error(`Error eliminando archivo: ${error.message}`);
    },
  });

  return {
    deleteFile,
  };
};

// Hook para actividad reciente (mock temporal hasta implementar en backend)
export const useRecentActivity = (limit = 5) => {
  const [data, setData] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    setIsLoading(true);
    // Simular carga de actividad reciente
    setTimeout(() => {
      setData([
        {
          id: 'activity-1',
          description: 'Archivo procesado: ejemplo_data.csv (454 filas)',
          timestamp: new Date(Date.now() - 21 * 60 * 1000).toISOString(),
          type: 'file_processed'
        },
        {
          id: 'activity-2', 
          description: 'Reporte generado: Análisis Completo - ejemplo 2.csv',
          timestamp: new Date(Date.now() - 45 * 60 * 1000).toISOString(),
          type: 'report_generated'
        },
        {
          id: 'activity-3',
          description: 'Archivo procesado: ejemplo2.csv (297 filas)', 
          timestamp: new Date(Date.now() - 65 * 60 * 1000).toISOString(),
          type: 'file_processed'
        }
      ].slice(0, limit));
      setIsLoading(false);
    }, 300);
  }, [limit]);

  return { data, isLoading };
};

// Export del servicio para uso directo si es necesario
export { fileService, reportService, dashboardService };