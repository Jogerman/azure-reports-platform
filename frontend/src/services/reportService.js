// frontend/src/services/reportService.js
import api from './api';

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