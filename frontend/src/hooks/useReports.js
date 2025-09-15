// src/hooks/useReports.js
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { reportService } from '../services/reportService';
import toast from 'react-hot-toast';

export const useReports = (params = {}) => {
  return useQuery({
    queryKey: ['reports', params],
    queryFn: () => reportService.getReports(params),
    staleTime: 1000 * 60 * 5, // 5 minutos
  });
};

export const useReport = (id) => {
  return useQuery({
    queryKey: ['report', id],
    queryFn: () => reportService.getReport(id),
    enabled: !!id,
  });
};

export const useCreateReport = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: reportService.createReport,
    onSuccess: (_data) => {
      queryClient.invalidateQueries(['reports']);
      toast.success('Reporte creado exitosamente');
    },
    onError: (error) => {
      toast.error(error.message);
    },
  });
};

export const useUploadCSV = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ file, onProgress }) => reportService.uploadCSV(file, onProgress),
    onSuccess: () => {
      queryClient.invalidateQueries(['csv-files']);
      toast.success('Archivo subido exitosamente');
    },
    onError: (error) => {
      toast.error(error.message);
    },
  });
};

export const useCSVFiles = (params = {}) => {
  return useQuery({
    queryKey: ['csv-files', params],
    queryFn: () => reportService.getCSVFiles(params),
    staleTime: 1000 * 60 * 2, // 2 minutos
  });
};

export const useCSVAnalysis = (id) => {
  return useQuery({
    queryKey: ['csv-analysis', id],
    queryFn: () => reportService.getCSVAnalysis(id),
    enabled: !!id,
  });
};
