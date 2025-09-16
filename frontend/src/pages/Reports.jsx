// src/pages/Reports.jsx - VERSIÓN COMPLETA Y FUNCIONAL
import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  FileText, 
  Upload, 
  Plus,
  BarChart3,
  RefreshCw,
  Zap,
  TrendingUp,
  Shield,
  DollarSign,
  Database,
  Settings
} from 'lucide-react';
import { 
  useStorageFiles, 
  useRecentReports, 
  useReportGeneration 
} from '../hooks/useReports';
import FileUpload from '../components/reports/FileUpload';
import ReportsList from '../components/reports/ReportsList';
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

  // Hooks para datos
  const { data: files, isLoading: filesLoading, refetch: refetchFiles } = useStorageFiles();
  const { data: recentReports, isLoading: reportsLoading, refetch: refetchReports } = useRecentReports(3);
  const { generateReport, isGenerating } = useReportGeneration();

  // Manejadores de eventos
  const handleUploadComplete = (uploadedFiles) => {
    setShowUpload(false);
    refetchFiles();
    toast.success(`${uploadedFiles.length} archivo(s) subido(s) y procesado(s) exitosamente`);
    
    // Si solo se subió un archivo, seleccionarlo automáticamente
    if (uploadedFiles.length === 1) {
      const uploadedFile = uploadedFiles[0];
      setSelectedFile(uploadedFile);
      setReportConfig(prev => ({
        ...prev,
        title: `Análisis Completo - ${uploadedFile.original_filename}`
      }));
      
      // Scroll al generador de reportes
      setTimeout(() => {
        document.getElementById('report-generator')?.scrollIntoView({ behavior: 'smooth' });
      }, 1000);
    }
  };

  const handleGenerateReport = async () => {
    if (!selectedFile) {
      toast.error('Selecciona un archivo CSV primero');
      return;
    }

    if (!reportConfig.title.trim()) {
      toast.error('Ingresa un título para el reporte');
      return;
    }

    try {
      const report = await generateReport(selectedFile.id, reportConfig);
      
      // Resetear formulario después del éxito
      setSelectedFile(null);
      setReportConfig({
        title: '',
        description: '',
        type: 'comprehensive',
        includeCharts: true,
        includeTables: true,
        includeRecommendations: true
      });
      
      // Refrescar reportes recientes
      refetchReports();
      
      // Opcional: redirigir al historial después de un delay
      setTimeout(() => {
        if (window.confirm('¿Quieres ir al historial para ver tu nuevo reporte?')) {
          window.location.href = '/app/history';
        }
      }, 2000);
      
    } catch (error) {
      console.error('Error generating report:', error);
    }
  };

  const handleQuickGenerate = async (file, type) => {
    const titles = {
      security: `Análisis de Seguridad - ${file.original_filename}`,
      cost: `Optimización de Costos - ${file.original_filename}`,
      performance: `Análisis de Rendimiento - ${file.original_filename}`,
      comprehensive: `Análisis Completo - ${file.original_filename}`
    };

    const config = {
      title: titles[type] || titles.comprehensive,
      description: `Reporte generado automáticamente desde ${file.original_filename}`,
      type,
      includeCharts: true,
      includeTables: true,
      includeRecommendations: true
    };

    try {
      await generateReport(file.id, config);
      refetchReports();
      
      setTimeout(() => {
        if (window.confirm('¿Quieres ir al historial para ver tu nuevo reporte?')) {
          window.location.href = '/app/history';
        }
      }, 2000);
    } catch (error) {
      console.error('Error in quick generate:', error);
    }
  };

  const reportTypes = [
    {
      value: 'security',
      label: 'Análisis de Seguridad',
      description: 'Enfocado en recomendaciones de seguridad y vulnerabilidades',
      icon: Shield,
      color: 'text-red-600 bg-red-100',
      borderColor: 'border-red-200'
    },
    {
      value: 'cost',
      label: 'Optimización de Costos',
      description: 'Análisis de ahorros y optimización financiera',
      icon: DollarSign,
      color: 'text-green-600 bg-green-100',
      borderColor: 'border-green-200'
    },
    {
      value: 'performance',
      label: 'Análisis de Rendimiento',
      description: 'Mejoras de rendimiento y eficiencia operacional',
      icon: TrendingUp,
      color: 'text-blue-600 bg-blue-100',
      borderColor: 'border-blue-200'
    },
    {
      value: 'comprehensive',
      label: 'Análisis Completo',
      description: 'Incluye todas las categorías y recomendaciones',
      icon: BarChart3,
      color: 'text-purple-600 bg-purple-100',
      borderColor: 'border-purple-200'
    }
  ];

  // Mostrar loading mientras cargan los archivos
  if (filesLoading) {
    return <Loading fullScreen text="Cargando archivos..." />;
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl p-8 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">Crear Reportes</h1>
            <p className="text-blue-100 text-lg">
              Sube archivos CSV de Azure Advisor y genera reportes inteligentes
            </p>
            <div className="mt-4 flex items-center space-x-4 text-sm text-blue-100">
              <span>📊 {files?.length || 0} archivos</span>
              <span>📈 {recentReports?.length || 0} reportes recientes</span>
              <span>🔄 Procesamiento automático</span>
            </div>
          </div>
          <div className="hidden md:block">
            <div className="w-20 h-20 bg-white/20 rounded-2xl flex items-center justify-center">
              <FileText className="w-10 h-10" />
            </div>
          </div>
        </div>
      </div>

      {/* Acciones rápidas */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Subir nuevo archivo */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-xl shadow-soft border border-gray-200 p-6 hover:shadow-medium transition-all cursor-pointer"
          onClick={() => setShowUpload(true)}
        >
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                <Upload className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Subir Nuevo Archivo</h3>
                <p className="text-sm text-gray-500">Sube archivos CSV de Azure Advisor</p>
              </div>
            </div>
            <Plus className="w-5 h-5 text-gray-400" />
          </div>
          
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-4 text-xs text-gray-600">
              <div className="flex items-center">
                <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                CSV hasta 50MB
              </div>
              <div className="flex items-center">
                <div className="w-2 h-2 bg-blue-500 rounded-full mr-2"></div>
                Análisis automático
              </div>
              <div className="flex items-center">
                <div className="w-2 h-2 bg-purple-500 rounded-full mr-2"></div>
                Azure Advisor
              </div>
              <div className="flex items-center">
                <div className="w-2 h-2 bg-orange-500 rounded-full mr-2"></div>
                Procesamiento rápido
              </div>
            </div>
            
            <button
              onClick={(e) => {
                e.stopPropagation();
                setShowUpload(true);
              }}
              className="w-full btn-primary"
            >
              <Upload className="w-4 h-4 mr-2" />
              Seleccionar Archivos
            </button>
          </div>
        </motion.div>

        {/* Crear reporte personalizado */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white rounded-xl shadow-soft border border-gray-200 p-6 hover:shadow-medium transition-all"
        >
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center">
                <BarChart3 className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Crear Reporte</h3>
                <p className="text-sm text-gray-500">Genera análisis inteligentes</p>
              </div>
            </div>
            <Zap className="w-5 h-5 text-purple-500" />
          </div>
          
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-4 text-xs text-gray-600">
              <div className="flex items-center">
                <div className="w-2 h-2 bg-red-500 rounded-full mr-2"></div>
                Análisis de seguridad
              </div>
              <div className="flex items-center">
                <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                Optimización costos
              </div>
              <div className="flex items-center">
                <div className="w-2 h-2 bg-blue-500 rounded-full mr-2"></div>
                Rendimiento
              </div>
              <div className="flex items-center">
                <div className="w-2 h-2 bg-purple-500 rounded-full mr-2"></div>
                Reporte completo
              </div>
            </div>
            
            <button
              onClick={() => {
                if (files && files.length > 0) {
                  document.getElementById('report-generator')?.scrollIntoView({ behavior: 'smooth' });
                } else {
                  toast.error('Primero sube un archivo CSV');
                  setShowUpload(true);
                }
              }}
              className="w-full btn-primary"
            >
              <BarChart3 className="w-4 h-4 mr-2" />
              Ir al Generador
            </button>
          </div>
        </motion.div>
      </div>

      {/* Archivos recientes con acciones rápidas */}
      {files && files.length > 0 && (
        <div className="bg-white rounded-xl shadow-soft border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-3">
              <Database className="w-5 h-5 text-gray-600" />
              <h3 className="text-lg font-semibold text-gray-900">
                Archivos Disponibles ({files.length})
              </h3>
            </div>
            <button
              onClick={() => refetchFiles()}
              className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700 transition-colors"
            >
              <RefreshCw className="w-4 h-4 mr-1" />
              Actualizar
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {files.slice(0, 6).map((file, index) => (
              <motion.div
                key={file.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-all hover:border-blue-200"
              >
                <div className="flex items-center space-x-3 mb-3">
                  <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                    <FileText className="w-5 h-5 text-green-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h4 className="font-medium text-gray-900 truncate text-sm">
                      {file.original_filename}
                    </h4>
                    <div className="flex items-center space-x-2 text-xs text-gray-500">
                      <span>{formatFileSize(file.file_size || 0)}</span>
                      <span>•</span>
                      <span>{formatRelativeTime(file.upload_date)}</span>
                    </div>
                  </div>
                </div>

                {/* Estado del procesamiento */}
                <div className="mb-3">
                  <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                    file.processing_status === 'completed' 
                      ? 'text-green-800 bg-green-100'
                      : file.processing_status === 'processing'
                      ? 'text-yellow-800 bg-yellow-100'
                      : 'text-red-800 bg-red-100'
                  }`}>
                    {file.processing_status === 'completed' ? '✅ Procesado' : 
                     file.processing_status === 'processing' ? '⏳ Procesando' : '❌ Error'}
                  </span>
                </div>

                {/* Información de análisis */}
                {file.analysis_data && file.processing_status === 'completed' && (
                  <div className="bg-gray-50 rounded-lg p-3 mb-3">
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div className="text-center">
                        <div className="font-semibold text-blue-600">
                          {file.analysis_data.total_recommendations || 0}
                        </div>
                        <div className="text-gray-500">Recomendaciones</div>
                      </div>
                      <div className="text-center">
                        <div className="font-semibold text-green-600">
                          ${Math.round(file.analysis_data.estimated_savings || 0)}
                        </div>
                        <div className="text-gray-500">Ahorros Est.</div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Información adicional */}
                {file.rows_count && (
                  <div className="text-xs text-gray-500 mb-3 text-center">
                    📊 {file.rows_count} filas de datos analizadas
                  </div>
                )}

                {/* Acciones rápidas */}
                {file.processing_status === 'completed' && (
                  <div className="space-y-2">
                    <div className="grid grid-cols-2 gap-2">
                      <button
                        onClick={() => handleQuickGenerate(file, 'security')}
                        disabled={isGenerating}
                        className="flex items-center justify-center px-2 py-1 text-xs font-medium text-red-700 bg-red-50 rounded hover:bg-red-100 transition-colors disabled:opacity-50"
                      >
                        <Shield className="w-3 h-3 mr-1" />
                        Seguridad
                      </button>
                      <button
                        onClick={() => handleQuickGenerate(file, 'cost')}
                        disabled={isGenerating}
                        className="flex items-center justify-center px-2 py-1 text-xs font-medium text-green-700 bg-green-50 rounded hover:bg-green-100 transition-colors disabled:opacity-50"
                      >
                        <DollarSign className="w-3 h-3 mr-1" />
                        Costos
                      </button>
                    </div>
                    <button
                      onClick={() => {
                        setSelectedFile(file);
                        setReportConfig(prev => ({
                          ...prev,
                          title: `Análisis Completo - ${file.original_filename}`
                        }));
                        document.getElementById('report-generator')?.scrollIntoView({ behavior: 'smooth' });
                      }}
                      disabled={isGenerating}
                      className="w-full flex items-center justify-center px-2 py-1 text-xs font-medium text-blue-700 bg-blue-50 rounded hover:bg-blue-100 transition-colors disabled:opacity-50"
                    >
                      <Settings className="w-3 h-3 mr-1" />
                      Reporte Personalizado
                    </button>
                  </div>
                )}
              </motion.div>
            ))}
          </div>

          {files.length > 6 && (
            <div className="mt-4 text-center">
              <button
                onClick={() => window.location.href = '/app/storage'}
                className="text-sm text-blue-600 hover:text-blue-700 font-medium"
              >
                Ver todos los archivos ({files.length - 6} más) →
              </button>
            </div>
          )}
        </div>
      )}

      {/* Generador de reportes */}
      <div id="report-generator" className="bg-white rounded-xl shadow-soft border border-gray-200 p-6">
        <div className="flex items-center space-x-3 mb-6">
          <div className="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center">
            <BarChart3 className="w-5 h-5 text-purple-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              Generador de Reportes Personalizado
            </h3>
            <p className="text-sm text-gray-500">
              Configura y genera tu reporte de análisis detallado
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Configuración del reporte */}
          <div className="space-y-6">
            {/* Selección de archivo */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Archivo CSV Fuente
              </label>
              {files && files.length > 0 ? (
                <select
                  value={selectedFile?.id || ''}
                  onChange={(e) => {
                    const file = files.find(f => f.id === e.target.value);
                    setSelectedFile(file);
                    if (file && !reportConfig.title) {
                      setReportConfig(prev => ({
                        ...prev,
                        title: `Análisis Completo - ${file.original_filename}`
                      }));
                    }
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                >
                  <option value="">Selecciona un archivo...</option>
                  {files.filter(f => f.processing_status === 'completed').map(file => (
                    <option key={file.id} value={file.id}>
                      {file.original_filename} ({formatFileSize(file.file_size || 0)}) - {file.analysis_data?.total_recommendations || 0} recomendaciones
                    </option>
                  ))}
                </select>
              ) : (
                <div className="p-4 border-2 border-dashed border-gray-300 rounded-lg text-center">
                  <p className="text-sm text-gray-500 mb-2">No hay archivos disponibles</p>
                  <button
                    onClick={() => setShowUpload(true)}
                    className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                  >
                    Subir primer archivo
                  </button>
                </div>
              )}
            </div>

            {/* Título del reporte */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Título del Reporte
              </label>
              <input
                type="text"
                value={reportConfig.title}
                onChange={(e) => setReportConfig(prev => ({ ...prev, title: e.target.value }))}
                placeholder="Ej: Análisis de Seguridad Azure - Enero 2024"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>

            {/* Descripción */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Descripción (Opcional)
              </label>
              <textarea
                value={reportConfig.description}
                onChange={(e) => setReportConfig(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Describe el propósito y alcance del reporte..."
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>

            {/* Tipo de reporte */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Tipo de Análisis
              </label>
              <div className="grid grid-cols-1 gap-3">
                {reportTypes.map(type => {
                  const IconComponent = type.icon;
                  return (
                    <label key={type.value} className="cursor-pointer">
                      <input
                        type="radio"
                        name="reportType"
                        value={type.value}
                        checked={reportConfig.type === type.value}
                        onChange={(e) => setReportConfig(prev => ({ ...prev, type: e.target.value }))}
                        className="sr-only"
                      />
                      <div className={`p-4 border-2 rounded-lg transition-all ${
                        reportConfig.type === type.value
                          ? `border-primary-500 bg-primary-50 ${type.borderColor}`
                          : 'border-gray-200 hover:border-gray-300'
                      }`}>
                        <div className="flex items-center space-x-3">
                          <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${type.color}`}>
                            <IconComponent className="w-4 h-4" />
                          </div>
                          <div>
                            <div className="font-medium text-gray-900">
                              {type.label}
                            </div>
                            <div className="text-sm text-gray-500">
                              {type.description}
                            </div>
                          </div>
                        </div>
                      </div>
                    </label>
                  );
                })}
              </div>
            </div>

            {/* Opciones de contenido */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Opciones de Contenido
              </label>
              <div className="space-y-3">
                <label className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={reportConfig.includeCharts}
                    onChange={(e) => setReportConfig(prev => ({ ...prev, includeCharts: e.target.checked }))}
                    className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <div>
                    <span className="text-sm font-medium text-gray-700">Incluir gráficos y visualizaciones</span>
                    <p className="text-xs text-gray-500">Gráficos de barras, tortas y tendencias</p>
                  </div>
                </label>
                
                <label className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={reportConfig.includeTables}
                    onChange={(e) => setReportConfig(prev => ({ ...prev, includeTables: e.target.checked }))}
                    className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <div>
                    <span className="text-sm font-medium text-gray-700">Incluir tablas detalladas</span>
                    <p className="text-xs text-gray-500">Tablas con datos específicos y métricas</p>
                  </div>
                </label>
                
                <label className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={reportConfig.includeRecommendations}
                    onChange={(e) => setReportConfig(prev => ({ ...prev, includeRecommendations: e.target.checked }))}
                    className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <div>
                    <span className="text-sm font-medium text-gray-700">Incluir recomendaciones de acción</span>
                    <p className="text-xs text-gray-500">Pasos específicos para implementar mejoras</p>
                  </div>
                </label>
              </div>
            </div>
          </div>

          {/* Vista previa y acciones */}
          <div className="space-y-6">
            {/* Vista previa del archivo seleccionado */}
            {selectedFile && (
              <div className="p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border border-blue-200">
                <h4 className="font-medium text-gray-900 mb-3 flex items-center">
                  <FileText className="w-4 h-4 mr-2 text-blue-600" />
                  Archivo Seleccionado
                </h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Nombre:</span>
                    <span className="font-medium">{selectedFile.original_filename}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Tamaño:</span>
                    <span>{formatFileSize(selectedFile.file_size || 0)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Filas procesadas:</span>
                    <span className="font-medium text-blue-600">{selectedFile.rows_count || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Subido:</span>
                    <span>{formatRelativeTime(selectedFile.upload_date)}</span>
                  </div>
                  {selectedFile.analysis_data && (
                    <div className="mt-3 pt-3 border-t border-blue-200">
                      <div className="grid grid-cols-2 gap-2">
                        <div className="text-center">
                          <div className="font-semibold text-blue-600">
                            {selectedFile.analysis_data.total_recommendations || 0}
                          </div>
                          <div className="text-xs text-gray-500">Recomendaciones</div>
                        </div>
                        <div className="text-center">
                          <div className="font-semibold text-green-600">
                            ${Math.round(selectedFile.analysis_data.estimated_savings || 0)}
                        <div className="text-center">
                          <div className="font-semibold text-green-600">
                            ${Math.round(selectedFile.analysis_data.estimated_savings || 0)}
                          </div>
                          <div className="text-xs text-gray-500">Ahorros Est.</div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Configuración del reporte */}
            <div className="p-4 bg-gray-50 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-3 flex items-center">
                <Settings className="w-4 h-4 mr-2 text-purple-600" />
                Configuración del Reporte
              </h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Tipo:</span>
                  <span className="font-medium">
                    {reportTypes.find(t => t.value === reportConfig.type)?.label}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Gráficos:</span>
                  <span className={reportConfig.includeCharts ? 'text-green-600' : 'text-gray-400'}>
                    {reportConfig.includeCharts ? '✅ Incluidos' : '❌ No incluidos'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Tablas:</span>
                  <span className={reportConfig.includeTables ? 'text-green-600' : 'text-gray-400'}>
                    {reportConfig.includeTables ? '✅ Incluidas' : '❌ No incluidas'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Recomendaciones:</span>
                  <span className={reportConfig.includeRecommendations ? 'text-green-600' : 'text-gray-400'}>
                    {reportConfig.includeRecommendations ? '✅ Incluidas' : '❌ No incluidas'}
                  </span>
                </div>
              </div>
            </div>

            {/* Progreso de generación */}
            {isGenerating && (
              <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                <div className="flex items-center space-x-3">
                  <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                  <div>
                    <p className="text-sm font-medium text-blue-900">Generando reporte...</p>
                    <p className="text-xs text-blue-700">Procesando análisis y creando visualizaciones</p>
                  </div>
                </div>
                <div className="mt-3 w-full bg-blue-200 rounded-full h-2">
                  <div className="bg-blue-600 h-2 rounded-full animate-pulse" style={{width: '60%'}}></div>
                </div>
              </div>
            )}

            {/* Botón de generar */}
            <button
              onClick={handleGenerateReport}
              disabled={!selectedFile || !reportConfig.title.trim() || isGenerating}
              className="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center py-3 text-lg font-semibold"
            >
              {isGenerating ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-3"></div>
                  Generando Reporte...
                </>
              ) : (
                <>
                  <BarChart3 className="w-5 h-5 mr-3" />
                  Generar Reporte Personalizado
                </>
              )}
            </button>

            {/* Información de tiempo estimado */}
            <div className="text-center p-4 bg-gradient-to-r from-gray-50 to-blue-50 rounded-lg border border-gray-200">
              <div className="space-y-2 text-sm text-gray-600">
                <p className="flex items-center justify-center">
                  <span className="mr-2">⏱️</span>
                  Tiempo estimado: 2-4 minutos
                </p>
                <p className="flex items-center justify-center">
                  <span className="mr-2">🔄</span>
                  Procesamiento automático de datos
                </p>
                <p className="flex items-center justify-center">
                  <span className="mr-2">📊</span>
                  Incluye análisis inteligente de Azure Advisor
                </p>
                <p className="flex items-center justify-center">
                  <span className="mr-2">📧</span>
                  Disponible inmediatamente al completarse
                </p>
              </div>
            </div>

            {/* Consejos */}
            <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">
              <h5 className="font-medium text-yellow-800 mb-2 flex items-center">
                <span className="mr-2">💡</span>
                Consejos para mejores reportes
              </h5>
              <ul className="text-xs text-yellow-700 space-y-1">
                <li>• Usa títulos descriptivos que incluyan la fecha</li>
                <li>• Los reportes de seguridad priorizan vulnerabilidades</li>
                <li>• Los análisis de costos destacan oportunidades de ahorro</li>
                <li>• Incluye gráficos para presentaciones ejecutivas</li>
              </ul>
            </div>
          </div>
        </div>

      {/* Reportes recientes */}
      {recentReports && recentReports.length > 0 && (
        <div className="bg-white rounded-xl shadow-soft border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-3">
              <BarChart3 className="w-5 h-5 text-green-600" />
              <h3 className="text-lg font-semibold text-gray-900">
                Reportes Recientes
              </h3>
            </div>
            <button
              onClick={() => window.location.href = '/app/history'}
              className="text-sm text-blue-600 hover:text-blue-700 font-medium flex items-center"
            >
              Ver todos
              <span className="ml-1">→</span>
            </button>
          </div>
          
          <ReportsList 
            reports={recentReports} 
            onUpdate={refetchReports}
          />

          {recentReports.length === 0 && (
            <div className="text-center py-8">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <BarChart3 className="w-8 h-8 text-gray-400" />
              </div>
              <h4 className="text-sm font-medium text-gray-900 mb-2">
                No hay reportes recientes
              </h4>
              <p className="text-sm text-gray-500">
                Los reportes que generes aparecerán aquí
              </p>
            </div>
          )}
        </div>
      )}

      {/* Sección de ayuda */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl p-6 border border-blue-200">
        <div className="flex items-start space-x-4">
          <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center flex-shrink-0">
            <span className="text-2xl">🤖</span>
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">
              ¿Cómo obtener archivos de Azure Advisor?
            </h3>
            <div className="space-y-2 text-sm text-gray-700">
              <p><strong>1.</strong> Ve a Azure Portal → Advisor</p>
              <p><strong>2.</strong> Selecciona las recomendaciones que quieres analizar</p>
              <p><strong>3.</strong> Haz clic en "Download as CSV" o "Descargar como CSV"</p>
              <p><strong>4.</strong> Sube el archivo aquí para generar reportes inteligentes</p>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              <span className="inline-flex items-center px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs">
                Seguridad
              </span>
              <span className="inline-flex items-center px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs">
                Costos
              </span>
              <span className="inline-flex items-center px-2 py-1 bg-purple-100 text-purple-700 rounded-full text-xs">
                Rendimiento
              </span>
              <span className="inline-flex items-center px-2 py-1 bg-orange-100 text-orange-700 rounded-full text-xs">
                Confiabilidad
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Modal de subida */}
      {showUpload && (
        <FileUpload
          onUploadComplete={handleUploadComplete}
          onClose={() => setShowUpload(false)}
        />
      )}
    </div>
  );
};

export default Reports;