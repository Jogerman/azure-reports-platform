// src/pages/Reports.jsx - VERSIÓN CON DEBUG MEJORADO
import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  FileText, 
  Upload, 
  BarChart3,
  RefreshCw,
  Zap,
  TrendingUp,
  Shield,
  DollarSign,
  Database,
  Settings,
  AlertCircle
} from 'lucide-react';

import { 
  useFiles,
  useRecentReports,
  useReportGeneration
} from '../hooks/useReports';

import FileUpload from '../components/reports/FileUpload';
import Loading from '../components/common/Loading';
import { formatFileSize, formatRelativeTime } from '../utils/helpers';
import toast from 'react-hot-toast';

const Reports = () => {
  const [showUpload, setShowUpload] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [reportConfig, setReportConfig] = useState({
    title: '',
    description: '',
    type: 'comprehensive',
    includeCharts: true,
    includeTables: true,
    includeRecommendations: true
  });

  // Hooks con debug
  const { data: files, isLoading: filesLoading, refetch: refetchFiles, error: filesError } = useFiles();
  const { data: recentReports, isLoading: reportsLoading, refetch: refetchReports } = useRecentReports(3);
  const { generateReport, isGenerating } = useReportGeneration();

  // Debug en consola
  React.useEffect(() => {
    console.log('🔍 Debug Reports - Estado actual:', {
      files: files,
      filesCount: files?.length || 0,
      filesLoading,
      filesError,
      selectedFile,
      recentReports,
      reportsLoading
    });
  }, [files, filesLoading, filesError, selectedFile, recentReports, reportsLoading]);

  const reportTypes = [
    { value: 'comprehensive', label: 'Análisis Completo', icon: BarChart3, description: 'Análisis detallado con todas las métricas' },
    { value: 'security', label: 'Análisis de Seguridad', icon: Shield, description: 'Enfoque en vulnerabilidades y seguridad' },
    { value: 'performance', label: 'Análisis de Rendimiento', icon: Zap, description: 'Optimización y eficiencia del sistema' },
    { value: 'cost', label: 'Análisis de Costos', icon: DollarSign, description: 'Optimización financiera y ahorros' },
    { value: 'trend', label: 'Análisis de Tendencias', icon: TrendingUp, description: 'Patrones y proyecciones futuras' }
  ];

  const handleUploadComplete = (uploadedFiles) => {
    console.log('📤 Upload completado, archivos recibidos:', uploadedFiles);
    
    setShowUpload(false);
    
    // Refrescar lista de archivos
    console.log('🔄 Refrescando lista de archivos...');
    refetchFiles();
    
    toast.success(`${uploadedFiles.length} archivo(s) subido(s) exitosamente`);
    
    // Auto-seleccionar primer archivo
    if (uploadedFiles.length > 0) {
      const firstFile = uploadedFiles[0];
      console.log('🎯 Auto-seleccionando archivo:', firstFile);
      
      setSelectedFile(firstFile);
      setReportConfig(prev => ({
        ...prev,
        title: `Análisis de ${firstFile.original_filename || firstFile.filename}`,
        description: `Reporte automático para ${firstFile.original_filename || firstFile.filename}`
      }));
    }
  };

  const handleFileSelect = (file) => {
    console.log('📋 Archivo seleccionado:', file);
    setSelectedFile(file);
    setReportConfig(prev => ({
      ...prev,
      title: `Análisis de ${file.original_filename || file.filename}`,
      description: `Reporte automático para ${file.original_filename || file.filename}`
    }));
  };

  const handleGenerateReport = async () => {
    if (!selectedFile) {
      toast.error('Selecciona un archivo primero');
      return;
    }

    console.log('🚀 Generando reporte:', {
      fileId: selectedFile.id,
      reportConfig
    });

    try {
      const result = await generateReport(selectedFile.id, reportConfig);
      console.log('✅ Reporte generado exitosamente:', result);
      
      // Refrescar reportes
      refetchReports();
      
      // Limpiar formulario
      setSelectedFile(null);
      setReportConfig({
        title: '',
        description: '',
        type: 'comprehensive',
        includeCharts: true,
        includeTables: true,
        includeRecommendations: true
      });
      
      // ✅ REDIRECCIÓN CORREGIDA: Ahora sí existe la ruta
      if (result.id) {
        toast.success('¡Reporte generado exitosamente! Redirigiendo...', { duration: 2000 });
        
        setTimeout(() => {
          // Usar navigate en lugar de window.location para mejor UX
          window.location.href = `/app/reports/${result.id}`;
        }, 1000);
      }
      
    } catch (error) {
      console.error('❌ Error generando reporte:', error);
      toast.error(`Error generando reporte: ${error.message}`);
    }
  };

  const handleRefreshFiles = () => {
    console.log('🔄 Refrescando archivos manualmente...');
    refetchFiles();
    toast.info('Actualizando lista de archivos...');
  };

  if (filesLoading) {
    return <Loading />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Generador de Reportes</h1>
          <p className="text-gray-600 mt-1">
            Sube archivos CSV y genera reportes inteligentes con IA
          </p>
        </div>
        <button
          onClick={() => setShowUpload(true)}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Upload className="w-4 h-4" />
          Subir Archivo
        </button>
      </div>

      {/* Debug Panel (solo en desarrollo) */}
      {process.env.NODE_ENV === 'development' && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <h3 className="font-medium text-yellow-800 mb-2">🔍 Debug Info</h3>
          <div className="text-sm space-y-1">
            <div>📁 Archivos cargados: {files?.length || 0}</div>
            <div>🔄 Cargando archivos: {filesLoading ? 'Sí' : 'No'}</div>
            <div>❌ Error archivos: {filesError ? filesError.message : 'No'}</div>
            <div>📋 Archivo seleccionado: {selectedFile ? selectedFile.original_filename : 'Ninguno'}</div>
            <div>📊 Reportes recientes: {recentReports?.length || 0}</div>
          </div>
        </div>
      )}

      {/* Error de archivos */}
      {filesError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-red-500" />
            <h3 className="font-medium text-red-800">Error cargando archivos</h3>
          </div>
          <p className="text-red-700 mt-1">{filesError.message}</p>
          <button
            onClick={handleRefreshFiles}
            className="mt-2 text-red-600 hover:text-red-800 underline"
          >
            Intentar de nuevo
          </button>
        </div>
      )}

      {/* Modal de subida */}
      {showUpload && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl mx-4">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">Subir Archivo CSV</h2>
              <button
                onClick={() => setShowUpload(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            <FileUpload onUploadComplete={handleUploadComplete} />
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Panel de archivos */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <Database className="w-5 h-5" />
                Archivos Disponibles ({files?.length || 0})
              </h2>
              <button
                onClick={handleRefreshFiles}
                className="text-blue-600 hover:text-blue-700 flex items-center gap-1"
              >
                <RefreshCw className="w-4 h-4" />
                Actualizar
              </button>
            </div>

            {files && files.length > 0 ? (
              <div className="space-y-3">
                {files.map((file) => (
                  <motion.div
                    key={file.id}
                    whileHover={{ scale: 1.02 }}
                    className={`p-4 border rounded-lg cursor-pointer transition-all ${
                      selectedFile?.id === file.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => handleFileSelect(file)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <FileText className="w-8 h-8 text-blue-500" />
                        <div>
                          <h3 className="font-medium text-gray-900">
                            {file.original_filename || file.filename || 'Archivo sin nombre'}
                          </h3>
                          <p className="text-sm text-gray-500">
                            {formatFileSize(file.file_size || file.size || 0)} • {(file.rows_count || 0).toLocaleString()} filas
                          </p>
                          {process.env.NODE_ENV === 'development' && (
                            <p className="text-xs text-gray-400">ID: {file.id}</p>
                          )}
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-sm text-gray-500">
                          {formatRelativeTime(file.upload_date || file.created_at)}
                        </p>
                        {selectedFile?.id === file.id && (
                          <span className="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded mt-1">
                            Seleccionado
                          </span>
                        )}
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <FileText className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-500">No hay archivos disponibles</p>
                <button
                  onClick={() => setShowUpload(true)}
                  className="text-blue-600 hover:text-blue-700 mt-2"
                >
                  Sube tu primer archivo
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Panel de configuración */}
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Settings className="w-5 h-5" />
              Configuración
            </h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Título del Reporte
                </label>
                <input
                  type="text"
                  value={reportConfig.title}
                  onChange={(e) => setReportConfig(prev => ({ ...prev, title: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Ej: Análisis de Rendimiento Q4"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Descripción
                </label>
                <textarea
                  value={reportConfig.description}
                  onChange={(e) => setReportConfig(prev => ({ ...prev, description: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows={3}
                  placeholder="Descripción del análisis..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Tipo de Análisis
                </label>
                <div className="space-y-2">
                  {reportTypes.map((type) => {
                    const IconComponent = type.icon;
                    return (
                      <label
                        key={type.value}
                        className={`flex items-center gap-3 p-3 border rounded-lg cursor-pointer transition-colors ${
                          reportConfig.type === type.value
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        <input
                          type="radio"
                          name="reportType"
                          value={type.value}
                          checked={reportConfig.type === type.value}
                          onChange={(e) => setReportConfig(prev => ({ ...prev, type: e.target.value }))}
                          className="sr-only"
                        />
                        <IconComponent className="w-5 h-5 text-blue-500" />
                        <div>
                          <div className="font-medium text-gray-900">{type.label}</div>
                          <div className="text-sm text-gray-500">{type.description}</div>
                        </div>
                      </label>
                    );
                  })}
                </div>
              </div>

              <button
                onClick={handleGenerateReport}
                disabled={!selectedFile || isGenerating}
                className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-3 px-4 rounded-lg font-medium hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
              >
                {isGenerating ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Generando...
                  </>
                ) : (
                  <>
                    <Zap className="w-4 h-4" />
                    Generar Reporte
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Reportes recientes */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              Reportes Recientes
            </h2>

            {reportsLoading ? (
              <div className="text-center py-4">
                <RefreshCw className="w-6 h-6 animate-spin text-gray-400 mx-auto" />
              </div>
            ) : recentReports && recentReports.length > 0 ? (
              <div className="space-y-3">
                {recentReports.map((report) => (
                  <div key={report.id} className="p-3 border border-gray-200 rounded-lg">
                    <h3 className="font-medium text-gray-900 text-sm">{report.title}</h3>
                    <p className="text-xs text-gray-500 mt-1">
                      {formatRelativeTime(report.created_at)}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500 text-center py-4">
                No hay reportes recientes
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Reports;