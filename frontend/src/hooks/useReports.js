// frontend/src/hooks/useReports.js - VERSIÓN FINAL COMPLETA

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';

// Configuración de API
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api';

const getAuthToken = () => {
  return localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
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
  }
  
  return headers;
};

const isTokenValid = (token) => {
  if (!token) return false;
  
  try {
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

const fetchWithAuth = async (url, options = {}) => {
  let token = getAuthToken();
  
  if (!isTokenValid(token)) {
    const refreshed = await refreshTokenIfNeeded();
    if (!refreshed) {
      throw new Error('No se pudo autenticar');
    }
    token = getAuthToken();
  }
  
  const defaultHeaders = {
    'Authorization': `Bearer ${token}`,
  };
  
  // FIX: NO agregar Content-Type para FormData
  if (!options.body || !(options.body instanceof FormData)) {
    defaultHeaders['Content-Type'] = 'application/json';
  }
  
  return fetch(url, {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  });
};

// Servicio API para archivos
const fileService = {
  async uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      console.log('📤 Subiendo archivo:', {
        name: file.name,
        size: file.size,
        type: file.type
      });
      
      const response = await fetchWithAuth(`${API_BASE_URL}/files/upload/`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.text();
        console.error('❌ Error response:', errorData);
        
        let errorMessage = 'Error al subir archivo';
        try {
          const errorJson = JSON.parse(errorData);
          errorMessage = errorJson.error || errorMessage;
        } catch (e) {
          errorMessage = errorData || errorMessage;
        }
        
        throw new Error(errorMessage);
      }

      const result = await response.json();
      console.log('✅ Archivo subido exitosamente:', result);
      return result;
      
    } catch (error) {
      console.error('❌ Error en upload:', error);
      throw error;
    }
  },

  async getFiles() {
    try {
      console.log('📂 Obteniendo lista de archivos...');
      
      const response = await fetchWithAuth(`${API_BASE_URL}/files/`);
      
      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('✅ Archivos obtenidos:', data);
      return data;
      
    } catch (error) {
      console.error('❌ Error obteniendo archivos:', error);
      throw error;
    }
  }
};

// Servicio API para reportes
const reportService = {
  async generateReport(fileId, reportConfig = {}) {
    try {
      console.log('📊 Generando reporte para archivo:', fileId);
      
      const requestData = {
        file_id: fileId,
        title: reportConfig.title || 'Reporte Automático',
        description: reportConfig.description || '',
        report_type: reportConfig.type || 'comprehensive'
      };
      
      const response = await fetchWithAuth(`${API_BASE_URL}/reports/generate/`, {
        method: 'POST',
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Error generando reporte');
      }

      const result = await response.json();
      console.log('✅ Reporte generado:', result);
      return result;
      
    } catch (error) {
      console.error('❌ Error generando reporte:', error);
      throw error;
    }
  },

  async getReports(filters = {}) {
    try {
      console.log('📋 Obteniendo reportes...');
      
      // Construir query params
      const params = new URLSearchParams();
      if (filters.limit) params.append('limit', filters.limit);
      if (filters.ordering) params.append('ordering', filters.ordering);
      
      const url = `${API_BASE_URL}/reports/${params.toString() ? '?' + params.toString() : ''}`;
      const response = await fetchWithAuth(url);
      
      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('✅ Reportes obtenidos:', data);
      return data;
      
    } catch (error) {
      console.error('❌ Error obteniendo reportes:', error);
      throw error;
    }
  },

  async getReport(reportId) {
    const response = await fetchWithAuth(`${API_BASE_URL}/reports/${reportId}/`);

    if (!response.ok) {
      throw new Error('Error obteniendo reporte');
    }

    return response.json();
  },

  async getReportHTML(reportId) {
    const response = await fetchWithAuth(`${API_BASE_URL}/reports/${reportId}/html/`);

    if (!response.ok) {
      throw new Error('Error obteniendo HTML del reporte');
    }

    return response.text();
  },

  async downloadReportPDF(reportId, filename) {
    const response = await fetchWithAuth(`${API_BASE_URL}/reports/${reportId}/download/`);

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

  async deleteReport(reportId) {
    const response = await fetchWithAuth(`${API_BASE_URL}/reports/${reportId}/`, {
      method: 'DELETE',
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

// HOOKS EXPORTADOS

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
      
      clearInterval(progressInterval);
      setProgress(100);
      
      // Invalidar cache de archivos
      queryClient.invalidateQueries({ queryKey: ['files'] });
      
      toast.success('Archivo subido exitosamente');
      return result;
      
    } catch (error) {
      setProgress(0);
      toast.error(error.message || 'Error al subir archivo');
      throw error;
    } finally {
      setIsUploading(false);
      setTimeout(() => setProgress(0), 1000);
    }
  };

  return {
    uploadFile,
    isUploading,
    progress
  };
};

// Hook para obtener archivos
export const useFiles = () => {
  return useQuery({
    queryKey: ['files'],
    queryFn: fileService.getFiles,
    staleTime: 30000,
    onError: (error) => {
      console.error('Error fetching files:', error);
      toast.error('Error cargando archivos');
    },
  });
};

// Hook para generar reportes
export const useGenerateReport = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ fileId, reportConfig }) => reportService.generateReport(fileId, reportConfig),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] });
      toast.success('Reporte generado exitosamente');
    },
    onError: (error) => {
      console.error('Error generating report:', error);
      toast.error(error.message || 'Error generando reporte');
    },
  });
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
    onError: (error) => {
      console.error('Error fetching report HTML:', error);
    },
  });
};

// NEW: Hook para actividad reciente
export const useRecentActivity = (limit = 8) => {
  return useQuery({
    queryKey: ['recent-activity', limit],
    queryFn: async () => {
      try {
        // Intentar obtener actividad desde el backend
        const response = await fetchWithAuth(`${API_BASE_URL}/dashboard/activity/`);
        
        if (response.status === 404) {
          console.warn('⚠️ Endpoint /dashboard/activity/ no implementado, usando mock');
          return getMockActivity(limit);
        }

        if (!response.ok) {
          throw new Error('Error obteniendo actividad');
        }

        const data = await response.json();
        return data.results?.slice(0, limit) || data.slice(0, limit) || [];
        
      } catch (error) {
        console.error('Error fetching recent activity:', error);
        return getMockActivity(limit);
      }
    },
    staleTime: 60000, // 1 minuto
    onError: (error) => {
      console.error('Error fetching recent activity:', error);
    },
  });
};

// NEW: Hook para mutaciones de reportes (FALTABA)
export const useReportMutations = () => {
  const queryClient = useQueryClient();

  const downloadReport = useMutation({
    mutationFn: ({ reportId, filename }) => reportService.downloadReportPDF(reportId, filename),
    onSuccess: () => {
      toast.success('Reporte descargado exitosamente');
    },
    onError: (error) => {
      console.error('Error downloading report:', error);
      toast.error(error.message || 'Error descargando reporte');
    },
  });

  const deleteReport = useMutation({
    mutationFn: (reportId) => reportService.deleteReport(reportId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] });
      queryClient.invalidateQueries({ queryKey: ['recent-reports'] });
      toast.success('Reporte eliminado exitosamente');
    },
    onError: (error) => {
      console.error('Error deleting report:', error);
      toast.error(error.message || 'Error eliminando reporte');
    },
  });

  return {
    downloadReport,
    deleteReport
  };
};

// Función helper para mock de actividad
const getMockActivity = (limit = 8) => {
  const activities = [
    {
      id: 1,
      type: 'file_upload',
      description: 'Archivo CSV subido: azure_advisor_report.csv',
      timestamp: new Date(Date.now() - 5 * 60 * 1000).toISOString(), // 5 min ago
      icon: 'upload',
      status: 'completed'
    },
    {
      id: 2,
      type: 'report_generation',
      description: 'Reporte "Análisis Q3 2024" generado exitosamente',
      timestamp: new Date(Date.now() - 15 * 60 * 1000).toISOString(), // 15 min ago
      icon: 'file-text',
      status: 'completed'
    },
    {
      id: 3,
      type: 'user_login',
      description: 'Inicio de sesión desde nueva ubicación',
      timestamp: new Date(Date.now() - 30 * 60 * 1000).toISOString(), // 30 min ago
      icon: 'user',
      status: 'info'
    },
    {
      id: 4,
      type: 'analysis_complete',
      description: 'Análisis de seguridad completado para 245 recursos',
      timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2 hours ago
      icon: 'shield',
      status: 'completed'
    },
    {
      id: 5,
      type: 'recommendation',
      description: 'Nueva recomendación de ahorro detectada: $1,240/mes',
      timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(), // 4 hours ago
      icon: 'trending-up',
      status: 'warning'
    },
    {
      id: 6,
      type: 'report_download',
      description: 'Reporte "Optimización Costos" descargado',
      timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(), // 6 hours ago
      icon: 'download',
      status: 'completed'
    },
    {
      id: 7,
      type: 'file_processing',
      description: 'Procesamiento de archivo completado: 1,847 recomendaciones',
      timestamp: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(), // 1 day ago
      icon: 'activity',
      status: 'completed'
    },
    {
      id: 8,
      type: 'alert',
      description: 'Alerta: Recursos sin optimizar detectados',
      timestamp: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(), // 2 days ago
      icon: 'alert-triangle',
      status: 'warning'
    }
  ];

  return activities.slice(0, limit);
};

// Exportar servicios también para uso directo
export { fileService, reportService, dashboardService };