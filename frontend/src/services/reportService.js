// src/services/reportService.js
import api from './api';

export const reportService = {
  // Obtener reportes del usuario
  getReports: async (params = {}) => {
    try {
      const response = await api.get('/reports/', { params });
      return response.data;
    } catch (_error) {
      throw new Error('Error obteniendo reportes');
    }
  },

  // Crear nuevo reporte
  createReport: async (data) => {
    try {
      const response = await api.post('/reports/', data);
      return response.data;
    } catch (_error) {
      throw new Error('Error creando reporte');
    }
  },

  // Obtener reporte específico
  getReport: async (id) => {
    try {
      const response = await api.get(`/reports/${id}/`);
      return response.data;
    } catch (_error) {
      throw new Error('Error obteniendo reporte');
    }
  },

  // Descargar reporte PDF
  downloadReport: async (id) => {
    try {
      const response = await api.get(`/reports/${id}/download/`, {
        responseType: 'blob',
      });
      return response.data;
    } catch (_error) {
      throw new Error('Error descargando reporte');
    }
  },

  // Obtener preview HTML
  getReportPreview: async (id) => {
    try {
      const response = await api.get(`/reports/${id}/preview/`);
      return response.data;
    } catch (_error) {
      throw new Error('Error obteniendo preview');
    }
  },

  // Regenerar reporte
  regenerateReport: async (id) => {
    try {
      const response = await api.post(`/reports/${id}/regenerate/`);
      return response.data;
    } catch (_error) {
      throw new Error('Error regenerando reporte');
    }
  },

  // Subir archivo CSV
  uploadCSV: async (file, onProgress) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await api.post('/csv-files/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          if (onProgress) onProgress(percentCompleted);
        },
      });
      
      return response.data;
    } catch (_error) {
      throw new Error(error.response?.data?.message || 'Error subiendo archivo');
    }
  },

  // Obtener archivos CSV
  getCSVFiles: async (params = {}) => {
    try {
      const response = await api.get('/csv-files/', { params });
      return response.data;
    } catch (_error) {
      throw new Error('Error obteniendo archivos CSV');
    }
  },

  // Obtener análisis de CSV
  getCSVAnalysis: async (id) => {
    try {
      const response = await api.get(`/csv-files/${id}/analysis_details/`);
      return response.data;
    } catch (_error) {
      throw new Error('Error obteniendo análisis');
    }
  },

  // Reprocesar CSV
  reprocessCSV: async (id) => {
    try {
      const response = await api.post(`/csv-files/${id}/reprocess/`);
      return response.data;
    } catch (_error) {
      throw new Error('Error reprocesando archivo');
    }
  },
};