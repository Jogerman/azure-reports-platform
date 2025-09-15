// src/hooks/useReports.js
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { reportService, dashboardService, storageService } from '../services/api';
import toast from 'react-hot-toast';

// Hook para obtener lista de reportes
export const useReports = (filters = {}) => {
  return useQuery({
    queryKey: ['reports', filters],
    queryFn: () => reportService.getReports(filters),
    staleTime: 5 * 60 * 1000, // 5 minutos
    cacheTime: 10 * 60 * 1000, // 10 minutos
  });
};

// Hook para obtener detalles de un reporte específico
export const useReportDetails = (reportId) => {
  return useQuery({
    queryKey: ['report', reportId],
    queryFn: () => reportService.getReportDetails(reportId),
    enabled: !!reportId,
  });
};

// Hook para obtener archivos CSV
export const useCSVFiles = () => {
  return useQuery({
    queryKey: ['csvFiles'],
    queryFn: reportService.getCSVFiles,
    staleTime: 2 * 60 * 1000, // 2 minutos
  });
};

// Hook para subir archivos CSV
export const useUploadCSV = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ file, onProgress }) => reportService.uploadCSV(file, onProgress),
    onSuccess: (data) => {
      // Invalidar caché de archivos CSV
      queryClient.invalidateQueries(['csvFiles']);
      toast.success(`Archivo "${data.original_filename}" subido exitosamente`);
    },
    onError: (error) => {
      const message = error.response?.data?.detail || 'Error al subir archivo';
      toast.error(message);
    }
  });
};

// Hook para generar reportes
export const useGenerateReport = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: reportService.generateReport,
    onSuccess: (data) => {
      // Invalidar caché de reportes
      queryClient.invalidateQueries(['reports']);
      queryClient.invalidateQueries(['dashboardStats']);
      toast.success('Reporte generado exitosamente');
    },
    onError: (error) => {
      const message = error.response?.data?.detail || 'Error al generar reporte';
      toast.error(message);
    }
  });
};

// Hook para descargar reportes
export const useDownloadReport = () => {
  return useMutation({
    mutationFn: reportService.downloadReport,
    onSuccess: () => {
      toast.success('Descarga iniciada');
    },
    onError: (error) => {
      const message = error.response?.data?.detail || 'Error al descargar reporte';
      toast.error(message);
    }
  });
};

// Hook para eliminar reportes
export const useDeleteReport = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: reportService.deleteReport,
    onSuccess: () => {
      queryClient.invalidateQueries(['reports']);
      queryClient.invalidateQueries(['dashboardStats']);
      toast.success('Reporte eliminado exitosamente');
    },
    onError: (error) => {
      const message = error.response?.data?.detail || 'Error al eliminar reporte';
      toast.error(message);
    }
  });
};

// Hook para estadísticas del dashboard
export const useDashboardStats = () => {
  return useQuery({
    queryKey: ['dashboardStats'],
    queryFn: dashboardService.getStats,
    staleTime: 5 * 60 * 1000, // 5 minutos
  });
};

// Hook para reportes recientes
export const useRecentReports = (limit = 5) => {
  return useQuery({
    queryKey: ['recentReports', limit],
    queryFn: () => dashboardService.getRecentReports(limit),
    staleTime: 2 * 60 * 1000, // 2 minutos
  });
};

// Hook para actividad reciente
export const useRecentActivity = (limit = 10) => {
  return useQuery({
    queryKey: ['recentActivity', limit],
    queryFn: () => dashboardService.getRecentActivity(limit),
    staleTime: 1 * 60 * 1000, // 1 minuto
  });
};

// Hook para archivos en storage
export const useStorageFiles = (filters = {}) => {
  return useQuery({
    queryKey: ['storageFiles', filters],
    queryFn: () => storageService.getStorageFiles(filters),
    staleTime: 5 * 60 * 1000, // 5 minutos
  });
};

// Hook para crear reportes
export const useCreateReport = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: reportService.generateReport,
    onSuccess: (data) => {
      // Invalidar caché de reportes
      queryClient.invalidateQueries(['reports']);
      queryClient.invalidateQueries(['dashboardStats']);
      toast.success('Reporte creado exitosamente');
    },
    onError: (error) => {
      const message = error.response?.data?.detail || 'Error al crear reporte';
      toast.error(message);
    }
  });
};