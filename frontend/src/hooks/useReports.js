// src/hooks/useReports.js - VERSIÓN CORREGIDA CON BACKEND REAL
import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';

// API Base URL - ajusta según tu configuración
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Helper para obtener token de autenticación
const getAuthToken = () => {
  return localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
};

// Helper para headers con autenticación
const getAuthHeaders = () => {
  const token = getAuthToken();
  return {
    'Authorization': token ? `Bearer ${token}` : '',
    'Content-Type': 'application/json',
  };
};

// Servicio API para archivos
const fileService = {
  // Subir archivo CSV
  async uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('file_type', 'csv');
    formData.append('source', 'azure_advisor');

    const response = await fetch(`${API_BASE_URL}/files/upload/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`,
        // No incluir Content-Type para FormData
      },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Error subiendo archivo');
    }

    return response.json();
  },

  // Obtener archivos del usuario
  async getFiles() {
    const response = await fetch(`${API_BASE_URL}/files/`, {
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error('Error obteniendo archivos');
    }

    return response.json();
  },

  // Obtener archivo específico
  async getFile(fileId) {
    const response = await fetch(`${API_BASE_URL}/files/${fileId}/`, {
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error('Error obteniendo archivo');
    }

    return response.json();
  },

  // Eliminar archivo
  async deleteFile(fileId) {
    const response = await fetch(`${API_BASE_URL}/files/${fileId}/`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error('Error eliminando archivo');
    }

    return true;
  },
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
    const queryParams = new URLSearchParams();
    
    Object.entries(filters).forEach(([key, value]) => {
      if (value && value !== '') {
        queryParams.append(key, value);
      }
    });

    const response = await fetch(`${API_BASE_URL}/reports/?${queryParams}`, {
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error('Error obteniendo reportes');
    }

    return response.json();
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
    const response = await fetch(`${API_BASE_URL}/dashboard/stats/`, {
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error('Error obteniendo estadísticas');
    }

    return response.json();
  },
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

      toast.success(`📁 ${file.name} subido y procesado exitosamente`);
      
      return result;
    } catch (error) {
      console.error('Error uploading file:', error);
      toast.error(`❌ Error: ${error.message}`);
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
    staleTime: 30000, // 30 segundos
    onError: (error) => {
      console.error('Error fetching files:', error);
      toast.error('Error cargando archivos');
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