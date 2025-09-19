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
  AlertCircle,
  Clock,
  CheckCircle,
  FileX
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
      filesError: filesError ?.message,
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

  const AvailableFiles = () => {
        if (filesLoading) {
          return (
            <div className="bg-white rounded-xl shadow-soft border border-gray-200 p-6">
              <div className="flex items-center space-x-3 mb-4">
                <Database className="w-5 h-5 text-blue-600" />
                <h3 className="text-lg font-semibold text-gray-900">Archivos Disponibles</h3>
              </div>
              <div className="animate-pulse space-y-3">
                {[1, 2, 3].map(i => (
                  <div key={i} className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg">
                    <div className="w-8 h-8 bg-gray-200 rounded"></div>
                    <div className="flex-1 space-y-1">
                      <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                      <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        }

        if (filesError) {
          return (
            <div className="bg-white rounded-xl shadow-soft border border-red-200 p-6">
              <div className="flex items-center space-x-3 mb-4">
                <AlertCircle className="w-5 h-5 text-red-600" />
                <h3 className="text-lg font-semibold text-gray-900">Error Cargando Archivos</h3>
              </div>
              <p className="text-gray-600 mb-4">
                No se pudieron cargar los archivos. Esto puede deberse a que el backend no está ejecutándose 
                o las APIs no están configuradas.
              </p>
              <button
                onClick={() => refetchFiles()}
                className="inline-flex items-center px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Reintentar
              </button>
            </div>
          );
        }

        if (!files || files.length === 0) {
          return (
            <div className="bg-white rounded-xl shadow-soft border border-gray-200 p-6">
              <div className="flex items-center space-x-3 mb-4">
                <Database className="w-5 h-5 text-blue-600" />
                <h3 className="text-lg font-semibold text-gray-900">Archivos Disponibles</h3>
              </div>
              <div className="text-center py-8">
                <FileX className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h4 className="text-lg font-medium text-gray-900 mb-2">No hay archivos</h4>
                <p className="text-gray-500 mb-4">
                  Sube tu primer archivo CSV de Azure Advisor para comenzar
                </p>
                <button
                  onClick={() => setShowUpload(true)}
                  className="btn-primary"
                >
                  Subir Archivo
                </button>
              </div>
            </div>
          );
        }

        return (
          <div className="bg-white rounded-xl shadow-soft border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-3">
                <Database className="w-5 h-5 text-blue-600" />
                <h3 className="text-lg font-semibold text-gray-900">
                  Archivos Disponibles ({files.length})
                </h3>
              </div>
              <button
                onClick={() => refetchFiles()}
                className="text-blue-600 hover:text-blue-700 text-sm font-medium flex items-center space-x-1"
              >
                <RefreshCw className="w-4 h-4" />
                <span>Actualizar</span>
              </button>
            </div>

            <div className="space-y-3">
              {files.map((file, index) => (
                <motion.div
                  key={file.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className={`p-4 border rounded-lg cursor-pointer transition-all ${
                    selectedFile?.id === file.id
                      ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-200'
                      : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                  }`}
                  onClick={() => setSelectedFile(file)}
                >
                  <div className="flex items-center space-x-4">
                    <div className="flex-shrink-0">
                      <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                        <FileText className="w-5 h-5 text-green-600" />
                      </div>
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2">
                        <h4 className="text-sm font-medium text-gray-900 truncate">
                          {file.original_filename || file.filename || `Archivo ${file.id}`}
                        </h4>
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          {(file.file_type || file.original_filename?.split('.').pop() || 'unknown').toUpperCase()}
                        </span>
                      </div>
                      
                      <div className="flex items-center space-x-4 text-xs text-gray-500 mt-1">
                        <span className="flex items-center space-x-1">
                          <Database className="w-3 h-3" />
                          <span>{formatFileSize(file.file_size || 0)}</span>
                        </span>
                        <span className="flex items-center space-x-1">
                          <Clock className="w-3 h-3" />
                          <span>
                            {file.upload_date 
                              ? formatRelativeTime(file.upload_date)
                              : 'Fecha desconocida'
                            }
                          </span>
                        </span>
                      </div>
                    </div>

                    {selectedFile?.id === file.id && (
                      <div className="flex-shrink-0">
                        <CheckCircle className="w-5 h-5 text-blue-600" />
                      </div>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>

            {selectedFile && (
              <div className="mt-6 pt-6 border-t border-gray-200">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-medium text-gray-900">
                      Archivo Seleccionado: {selectedFile.original_filename || selectedFile.filename}
                    </h4>
                    <p className="text-xs text-gray-500">
                      Listo para generar reporte
                    </p>
                  </div>
                  <button
                    onClick={() => setSelectedFile(null)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </div>
        );
      };

      return (
        <div className="space-y-8">
          {/* Header existente */}
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl p-8 text-white">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold mb-2">Generador de Reportes</h1>
                <p className="text-blue-100 text-lg">
                  Analiza tus datos de Azure Advisor y genera reportes inteligentes
                </p>
              </div>
              <div className="hidden md:block">
                <div className="w-20 h-20 bg-white/20 rounded-2xl flex items-center justify-center">
                  <BarChart3 className="w-10 h-10" />
                </div>
              </div>
            </div>
          </div>

          {/* Grid de contenido */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Panel izquierdo - Archivos disponibles */}
            <div>
              <AvailableFiles />
            </div>

            {/* Panel derecho - Generador de reportes */}
            <div className="space-y-6">
              {/* Configuración de reporte */}
              <div className="bg-white rounded-xl shadow-soft border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Configurar Reporte
                </h3>
                
                {!selectedFile ? (
                  <div className="text-center py-8">
                    <AlertCircle className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                    <h4 className="text-lg font-medium text-gray-900 mb-2">
                      Selecciona un archivo
                    </h4>
                    <p className="text-gray-500">
                      Primero selecciona un archivo CSV para configurar el reporte
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Título del Reporte
                      </label>
                      <input
                        type="text"
                        value={reportConfig.title}
                        onChange={(e) => setReportConfig(prev => ({ ...prev, title: e.target.value }))}
                        placeholder="Ej: Análisis de Seguridad Azure - Marzo 2025"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Tipo de Reporte
                      </label>
                      <select
                        value={reportConfig.type}
                        onChange={(e) => setReportConfig(prev => ({ ...prev, type: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="comprehensive">Análisis Completo</option>
                        <option value="security">Análisis de Seguridad</option>
                        <option value="cost">Análisis de Costos</option>
                        <option value="performance">Análisis de Rendimiento</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-3">
                        Opciones de Reporte
                      </label>
                      <div className="space-y-2">
                        <label className="flex items-center">
                          <input
                            type="checkbox"
                            checked={reportConfig.includeCharts}
                            onChange={(e) => setReportConfig(prev => ({ ...prev, includeCharts: e.target.checked }))}
                            className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                          />
                          <span className="ml-2 text-sm text-gray-700">Incluir gráficos</span>
                        </label>
                        <label className="flex items-center">
                          <input
                            type="checkbox"
                            checked={reportConfig.includeTables}
                            onChange={(e) => setReportConfig(prev => ({ ...prev, includeTables: e.target.checked }))}
                            className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                          />
                          <span className="ml-2 text-sm text-gray-700">Incluir tablas detalladas</span>
                        </label>
                        <label className="flex items-center">
                          <input
                            type="checkbox"
                            checked={reportConfig.includeRecommendations}
                            onChange={(e) => setReportConfig(prev => ({ ...prev, includeRecommendations: e.target.checked }))}
                            className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                          />
                          <span className="ml-2 text-sm text-gray-700">Incluir recomendaciones</span>
                        </label>
                      </div>
                    </div>

                    <button
                      onClick={async () => {
                        try {
                          await generateReport(selectedFile.id, reportConfig);
                          refetchReports();
                          toast.success('Reporte generado exitosamente!');
                        } catch (error) {
                          toast.error('Error generando reporte: ' + error.message);
                        }
                      }}
                      disabled={isGenerating}
                      className="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isGenerating ? (
                        <div className="flex items-center justify-center">
                          <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                          Generando Reporte...
                        </div>
                      ) : (
                        <div className="flex items-center justify-center">
                          <BarChart3 className="w-4 h-4 mr-2" />
                          Generar Reporte
                        </div>
                      )}
                    </button>
                  </div>
                )}
              </div>

              {/* Reportes recientes */}
              <div className="bg-white rounded-xl shadow-soft border border-gray-200 p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">
                    Reportes Recientes
                  </h3>
                  <button
                    onClick={() => refetchReports()}
                    className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                  >
                    <RefreshCw className="w-4 h-4" />
                  </button>
                </div>

                {reportsLoading ? (
                  <div className="space-y-3">
                    {[1, 2, 3].map(i => (
                      <div key={i} className="animate-pulse flex items-center space-x-3 p-3 border border-gray-200 rounded-lg">
                        <div className="w-8 h-8 bg-gray-200 rounded"></div>
                        <div className="flex-1 space-y-1">
                          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                          <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : recentReports && recentReports.length > 0 ? (
                  <div className="space-y-3">
                    {recentReports.map((report, index) => (
                      <motion.div
                        key={report.id}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.1 }}
                        className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                      >
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                          report.status === 'completed' ? 'bg-green-100' : 
                          report.status === 'processing' ? 'bg-yellow-100' : 'bg-gray-100'
                        }`}>
                          <FileText className={`w-4 h-4 ${
                            report.status === 'completed' ? 'text-green-600' : 
                            report.status === 'processing' ? 'text-yellow-600' : 'text-gray-600'
                          }`} />
                        </div>
                        
                        <div className="flex-1 min-w-0">
                          <h4 className="text-sm font-medium text-gray-900 truncate">
                            {report.title || `Reporte ${report.id}`}
                          </h4>
                          <div className="flex items-center space-x-2 text-xs text-gray-500">
                            <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                              report.status === 'completed' ? 'bg-green-100 text-green-800' : 
                              report.status === 'processing' ? 'bg-yellow-100 text-yellow-800' : 'bg-gray-100 text-gray-800'
                            }`}>
                              {report.status === 'completed' ? 'Completado' : 
                              report.status === 'processing' ? 'Procesando' : 'Desconocido'}
                            </span>
                            <span>•</span>
                            <span>{formatRelativeTime(report.created_at)}</span>
                          </div>
                        </div>

                        {report.status === 'completed' && (
                          <div className="flex items-center space-x-2">
                            <button
                              onClick={() => window.open(`/app/reports/${report.id}`, '_blank')}
                              className="p-1 text-gray-400 hover:text-blue-600"
                              title="Ver reporte"
                            >
                              <Eye className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => {
                                // TODO: Implementar descarga
                                toast.info('Descarga en desarrollo');
                              }}
                              className="p-1 text-gray-400 hover:text-green-600"
                              title="Descargar PDF"
                            >
                              <Download className="w-4 h-4" />
                            </button>
                          </div>
                        )}
                      </motion.div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-6">
                    <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                    <h4 className="text-sm font-medium text-gray-900 mb-1">
                      No hay reportes recientes
                    </h4>
                    <p className="text-xs text-gray-500">
                      Los reportes generados aparecerán aquí
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Modal de upload */}
          {showUpload && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
              <div className="bg-white rounded-xl p-6 w-full max-w-md mx-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">
                    Subir Archivo CSV
                  </h3>
                  <button
                    onClick={() => setShowUpload(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
                
                <FileUpload
                  onUploadComplete={(uploadedFiles) => {
                    console.log('📤 Upload completado:', uploadedFiles);
                    setShowUpload(false);
                    refetchFiles();
                    
                    if (uploadedFiles.length > 0) {
                      setSelectedFile(uploadedFiles[0]);
                      setReportConfig(prev => ({ 
                        ...prev, 
                        title: `Análisis ${uploadedFiles[0].original_filename?.replace('.csv', '') || 'Archivo'} - ${new Date().toLocaleDateString()}`
                      }));
                    }
                    
                    toast.success(`${uploadedFiles.length} archivo(s) subido(s) exitosamente`);
                  }}
                  onError={(error) => {
                    console.error('Error en upload:', error);
                    toast.error('Error subiendo archivo: ' + error.message);
                  }}
                />
              </div>
            </div>
          )}
        </div>
      );
   };

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