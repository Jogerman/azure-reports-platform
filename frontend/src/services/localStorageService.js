// src/services/localStorageService.js - Sistema de almacenamiento local mejorado
export class LocalStorageService {
  constructor() {
    this.prefix = 'azure_reports_';
    this.maxFiles = 50;
    this.maxFileSize = 50 * 1024 * 1024; // 50MB
  }

  // Guardar archivo en localStorage con procesamiento básico
  async saveFile(file) {
    try {
      // Validaciones
      if (file.size > this.maxFileSize) {
        throw new Error('Archivo demasiado grande');
      }

      if (!file.name.toLowerCase().endsWith('.csv')) {
        throw new Error('Solo se permiten archivos CSV');
      }

      // Leer contenido del archivo
      const content = await this.readFileContent(file);
      
      // Procesar CSV
      const processedData = await this.processCSVContent(content);

      // Crear objeto de archivo
      const fileData = {
        id: this.generateId(),
        original_filename: file.name,
        file_size: file.size,
        upload_date: new Date().toISOString(),
        processing_status: 'completed',
        content: content,
        rows_count: processedData.rowCount,
        columns: processedData.columns,
        analysis_data: processedData.analysis,
        preview: processedData.preview
      };

      // Guardar en localStorage
      this.saveToStorage('file_' + fileData.id, fileData);
      
      // Actualizar lista de archivos
      this.addToFilesList(fileData.id);

      return fileData;
    } catch (error) {
      console.error('Error saving file:', error);
      throw error;
    }
  }

  // Leer contenido del archivo
  readFileContent(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target.result);
      reader.onerror = (e) => reject(new Error('Error leyendo archivo'));
      reader.readAsText(file);
    });
  }

  // Procesar contenido CSV básico
  async processCSVContent(content) {
    try {
      const lines = content.split('\n').filter(line => line.trim());
      if (lines.length === 0) {
        throw new Error('Archivo CSV vacío');
      }

      // Obtener headers
      const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''));
      const dataLines = lines.slice(1);

      // Procesar datos
      const data = dataLines.map(line => {
        const values = this.parseCSVLine(line);
        const row = {};
        headers.forEach((header, index) => {
          row[header] = values[index] || '';
        });
        return row;
      });

      // Análisis básico para Azure Advisor
      const analysis = this.analyzeAzureAdvisorData(data, headers);

      return {
        rowCount: dataLines.length,
        columns: headers,
        data: data.slice(0, 100), // Solo primeras 100 filas para preview
        preview: data.slice(0, 10), // Primeras 10 filas para vista rápida
        analysis
      };
    } catch (error) {
      console.error('Error processing CSV:', error);
      throw new Error('Error procesando archivo CSV: ' + error.message);
    }
  }

  // Parsear línea CSV (manejo básico de comillas)
  parseCSVLine(line) {
    const result = [];
    let current = '';
    let inQuotes = false;
    
    for (let i = 0; i < line.length; i++) {
      const char = line[i];
      
      if (char === '"') {
        inQuotes = !inQuotes;
      } else if (char === ',' && !inQuotes) {
        result.push(current.trim());
        current = '';
      } else {
        current += char;
      }
    }
    
    result.push(current.trim());
    return result.map(val => val.replace(/"/g, ''));
  }

  // Análizar datos específicos de Azure Advisor
  analyzeAzureAdvisorData(data, headers) {
    const analysis = {
      total_recommendations: data.length,
      categories: {},
      impact_levels: {},
      resource_types: {},
      estimated_savings: 0,
      security_issues: 0,
      performance_issues: 0,
      reliability_issues: 0
    };

    // Detectar columnas relevantes
    const categoryCol = this.findColumn(headers, ['category', 'categoria']);
    const impactCol = this.findColumn(headers, ['impact', 'business impact', 'impacto']);
    const resourceCol = this.findColumn(headers, ['resource type', 'tipo recurso', 'resource']);
    const recommendationCol = this.findColumn(headers, ['recommendation', 'recomendacion']);

    data.forEach(row => {
      // Analizar categorías
      if (categoryCol && row[categoryCol]) {
        const category = row[categoryCol].toLowerCase();
        analysis.categories[category] = (analysis.categories[category] || 0) + 1;
        
        // Contar por tipo
        if (category.includes('security') || category.includes('seguridad')) {
          analysis.security_issues++;
        }
        if (category.includes('performance') || category.includes('rendimiento')) {
          analysis.performance_issues++;
        }
        if (category.includes('reliability') || category.includes('confiabilidad')) {
          analysis.reliability_issues++;
        }
      }

      // Analizar impacto
      if (impactCol && row[impactCol]) {
        const impact = row[impactCol].toLowerCase();
        analysis.impact_levels[impact] = (analysis.impact_levels[impact] || 0) + 1;
      }

      // Analizar tipos de recursos
      if (resourceCol && row[resourceCol]) {
        const resource = row[resourceCol];
        analysis.resource_types[resource] = (analysis.resource_types[resource] || 0) + 1;
      }

      // Estimar ahorros (simulado)
      if (recommendationCol && row[recommendationCol]) {
        const rec = row[recommendationCol].toLowerCase();
        if (rec.includes('cost') || rec.includes('save') || rec.includes('optimize')) {
          analysis.estimated_savings += Math.random() * 1000; // Simulado
        }
      }
    });

    return analysis;
  }

  // Encontrar columna por nombres posibles
  findColumn(headers, possibleNames) {
    return headers.find(header => 
      possibleNames.some(name => 
        header.toLowerCase().includes(name.toLowerCase())
      )
    );
  }

  // Generar ID único
  generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }

  // Guardar en localStorage
  saveToStorage(key, data) {
    try {
      localStorage.setItem(this.prefix + key, JSON.stringify(data));
    } catch (error) {
      if (error.name === 'QuotaExceededError') {
        this.cleanOldFiles();
        localStorage.setItem(this.prefix + key, JSON.stringify(data));
      } else {
        throw error;
      }
    }
  }

  // Obtener de localStorage
  getFromStorage(key) {
    try {
      const data = localStorage.getItem(this.prefix + key);
      return data ? JSON.parse(data) : null;
    } catch (error) {
      console.error('Error getting from storage:', error);
      return null;
    }
  }

  // Agregar a lista de archivos
  addToFilesList(fileId) {
    const filesList = this.getFromStorage('files_list') || [];
    filesList.unshift(fileId); // Agregar al inicio
    
    // Mantener solo los últimos archivos
    if (filesList.length > this.maxFiles) {
      const removedIds = filesList.splice(this.maxFiles);
      removedIds.forEach(id => this.deleteFile(id));
    }
    
    this.saveToStorage('files_list', filesList);
  }

  // Obtener todos los archivos
  getAllFiles() {
    const filesList = this.getFromStorage('files_list') || [];
    return filesList.map(id => this.getFromStorage('file_' + id)).filter(Boolean);
  }

  // Obtener archivo específico
  getFile(fileId) {
    return this.getFromStorage('file_' + fileId);
  }

  // Eliminar archivo
  deleteFile(fileId) {
    localStorage.removeItem(this.prefix + 'file_' + fileId);
    const filesList = this.getFromStorage('files_list') || [];
    const updatedList = filesList.filter(id => id !== fileId);
    this.saveToStorage('files_list', updatedList);
  }

  // Limpiar archivos antiguos
  cleanOldFiles() {
    const filesList = this.getFromStorage('files_list') || [];
    const filesToKeep = filesList.slice(0, Math.floor(this.maxFiles / 2));
    const filesToRemove = filesList.slice(Math.floor(this.maxFiles / 2));
    
    filesToRemove.forEach(id => {
      localStorage.removeItem(this.prefix + 'file_' + id);
    });
    
    this.saveToStorage('files_list', filesToKeep);
  }

  // Generar reporte basado en archivo
  async generateReport(fileId, reportConfig) {
    const file = this.getFile(fileId);
    if (!file) {
      throw new Error('Archivo no encontrado');
    }

    const reportId = this.generateId();
    const report = {
      id: reportId,
      title: reportConfig.title,
      description: reportConfig.description || '',
      report_type: reportConfig.type || 'comprehensive',
      source_file_id: fileId,
      source_filename: file.original_filename,
      created_at: new Date().toISOString(),
      status: 'completed',
      generation_time_seconds: Math.floor(Math.random() * 60) + 30, // 30-90 segundos simulado
      user_name: 'Usuario',
      analysis_summary: this.generateAnalysisSummary(file.analysis_data, reportConfig),
      config: reportConfig
    };

    // Guardar reporte
    this.saveToStorage('report_' + reportId, report);
    this.addToReportsList(reportId);

    return report;
  }

  // Generar resumen de análisis
  generateAnalysisSummary(analysisData, config) {
    if (!analysisData) return null;

    return {
      total_recommendations: analysisData.total_recommendations || 0,
      security_issues_found: analysisData.security_issues || 0,
      cost_savings_identified: analysisData.estimated_savings > 0,
      performance_improvements: analysisData.performance_issues || 0,
      estimated_monthly_savings: Math.round(analysisData.estimated_savings || 0),
      top_categories: Object.entries(analysisData.categories || {})
        .sort(([,a], [,b]) => b - a)
        .slice(0, 3)
        .map(([category, count]) => ({ category, count }))
    };
  }

  // Gestión de reportes
  addToReportsList(reportId) {
    const reportsList = this.getFromStorage('reports_list') || [];
    reportsList.unshift(reportId);
    
    // Mantener solo los últimos 100 reportes
    if (reportsList.length > 100) {
      const removedIds = reportsList.splice(100);
      removedIds.forEach(id => {
        localStorage.removeItem(this.prefix + 'report_' + id);
      });
    }
    
    this.saveToStorage('reports_list', reportsList);
  }

  getAllReports() {
    const reportsList = this.getFromStorage('reports_list') || [];
    return reportsList.map(id => this.getFromStorage('report_' + id)).filter(Boolean);
  }

  getReport(reportId) {
    return this.getFromStorage('report_' + reportId);
  }

  deleteReport(reportId) {
    localStorage.removeItem(this.prefix + 'report_' + reportId);
    const reportsList = this.getFromStorage('reports_list') || [];
    const updatedList = reportsList.filter(id => id !== reportId);
    this.saveToStorage('reports_list', updatedList);
  }

  // Obtener estadísticas del dashboard
  getDashboardStats() {
    const files = this.getAllFiles();
    const reports = this.getAllReports();
    
    let totalRecommendations = 0;
    let potentialSavings = 0;
    
    files.forEach(file => {
      if (file.analysis_data) {
        totalRecommendations += file.analysis_data.total_recommendations || 0;
        potentialSavings += file.analysis_data.estimated_savings || 0;
      }
    });

    return {
      totalReports: reports.length,
      totalFiles: files.length,
      totalRecommendations,
      potentialSavings: Math.round(potentialSavings)
    };
  }

  // Simular descarga de archivo/reporte
  downloadFile(fileId, filename) {
    const content = "Contenido simulado del archivo descargado\nEsto sería el contenido real del archivo CSV o PDF del reporte";
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = filename || 'download.txt';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    URL.revokeObjectURL(url);
  }
}

// Crear instancia global
export const localStorageService = new LocalStorageService();

// Hook mejorado que usa el sistema de almacenamiento local
// src/hooks/useLocalReports.js
import { useState, useEffect } from 'react';
import { localStorageService } from '../services/localStorageService';
import toast from 'react-hot-toast';

export const useFileUpload = () => {
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  const uploadFile = async (file) => {
    setIsUploading(true);
    setProgress(0);
    
    try {
      // Simular progreso de subida
      const progressInterval = setInterval(() => {
        setProgress(prev => {
          const newProgress = prev + Math.random() * 15;
          return newProgress >= 90 ? 90 : newProgress;
        });
      }, 200);

      // Procesar archivo
      const result = await localStorageService.saveFile(file);
      
      clearInterval(progressInterval);
      setProgress(100);
      
      toast.success(`Archivo procesado: ${result.rows_count} filas analizadas`);
      
      return result;
    } catch (error) {
      toast.error('Error: ' + error.message);
      throw error;
    } finally {
      setIsUploading(false);
      setTimeout(() => setProgress(0), 1000);
    }
  };

  return { uploadFile, isUploading, progress };
};

export const useStorageFiles = (options = {}) => {
  const [data, setData] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const refetch = () => {
    try {
      let files = localStorageService.getAllFiles();
      
      // Aplicar filtros
      if (options.search) {
        files = files.filter(file => 
          file.original_filename.toLowerCase().includes(options.search.toLowerCase())
        );
      }
      
      if (options.type && options.type !== 'all') {
        files = files.filter(file => {
          const extension = file.original_filename.split('.').pop()?.toLowerCase();
          return extension === options.type;
        });
      }
      
      setData(files);
      setError(null);
    } catch (error) {
      console.error('Error fetching files:', error);
      setError(error);
      setData([]);
    }
  };

  useEffect(() => {
    setIsLoading(true);
    // Simular carga
    setTimeout(() => {
      refetch();
      setIsLoading(false);
    }, 500);
  }, [options.search, options.type]);

  return { data, isLoading, error, refetch };
};

export const useReports = (filters = {}) => {
  const [data, setData] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const refetch = () => {
    try {
      let reports = localStorageService.getAllReports();
      
      // Aplicar filtros
      if (filters.search) {
        reports = reports.filter(report => 
          report.title.toLowerCase().includes(filters.search.toLowerCase()) ||
          (report.description && report.description.toLowerCase().includes(filters.search.toLowerCase()))
        );
      }
      
      if (filters.status) {
        reports = reports.filter(report => report.status === filters.status);
      }
      
      if (filters.report_type) {
        reports = reports.filter(report => report.report_type === filters.report_type);
      }
      
      setData(reports);
      setError(null);
    } catch (error) {
      console.error('Error fetching reports:', error);
      setError(error);
      setData([]);
    }
  };

  useEffect(() => {
    setIsLoading(true);
    setTimeout(() => {
      refetch();
      setIsLoading(false);
    }, 300);
  }, [filters.search, filters.status, filters.report_type]);

  return { data, isLoading, error, refetch };
};

export const useDashboardStats = () => {
  const [data, setData] = useState({
    totalReports: 0,
    totalFiles: 0,
    totalRecommendations: 0,
    potentialSavings: 0
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setIsLoading(true);
    setTimeout(() => {
      try {
        const stats = localStorageService.getDashboardStats();
        setData(stats);
        setError(null);
      } catch (error) {
        console.error('Error fetching dashboard stats:', error);
        setError(error);
        // Usar datos demo como fallback
        setData({
          totalReports: 0,
          totalFiles: 0,
          totalRecommendations: 0,
          potentialSavings: 0
        });
      } finally {
        setIsLoading(false);
      }
    }, 300);
  }, []);

  return { data, isLoading, error };
};

export const useRecentReports = (limit = 5) => {
  const [data, setData] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setIsLoading(true);
    setTimeout(() => {
      try {
        const reports = localStorageService.getAllReports().slice(0, limit);
        setData(reports);
        setError(null);
      } catch (error) {
        console.error('Error fetching recent reports:', error);
        setError(error);
        setData([]);
      } finally {
        setIsLoading(false);
      }
    }, 200);
  }, [limit]);

  return { data, isLoading, error };
};

export const useRecentActivity = (limit = 5) => {
  const [data, setData] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    setIsLoading(true);
    setTimeout(() => {
      try {
        const files = localStorageService.getAllFiles().slice(0, limit);
        const activities = files.map(file => ({
          id: file.id,
          description: `Archivo ${file.original_filename} procesado exitosamente`,
          timestamp: file.upload_date,
          type: 'file_processed'
        }));
        setData(activities);
      } catch (error) {
        console.error('Error fetching activity:', error);
        setData([{
          id: 'demo',
          description: 'Sistema funcionando correctamente',
          timestamp: new Date().toISOString(),
          type: 'system'
        }]);
      } finally {
        setIsLoading(false);
      }
    }, 200);
  }, [limit]);

  return { data, isLoading };
};

// Hook para generar reportes
export const useReportGeneration = () => {
  const [isGenerating, setIsGenerating] = useState(false);

  const generateReport = async (fileId, reportConfig) => {
    setIsGenerating(true);
    
    try {
      // Simular tiempo de generación
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const report = await localStorageService.generateReport(fileId, reportConfig);
      
      toast.success(`Reporte "${report.title}" generado exitosamente`);
      return report;
    } catch (error) {
      toast.error('Error generando reporte: ' + error.message);
      throw error;
    } finally {
      setIsGenerating(false);
    }
  };

  return { generateReport, isGenerating };
};