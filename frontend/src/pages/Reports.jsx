// src/pages/Reports.jsx
import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  FileText, 
  Upload, 
  Plus,
  BarChart3,
  Eye,
  Download,
  RefreshCw,
  Calendar,
  Filter,
  Zap,
  TrendingUp,
  Shield,
  DollarSign
} from 'lucide-react';
import { useStorageFiles, useRecentReports } from '../hooks/useReports';
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

  const { data: files, isLoading: filesLoading, refetch: refetchFiles } = useStorageFiles();
  const { data: recentReports, isLoading: reportsLoading } = useRecentReports(3);

  const handleUploadComplete = (uploadedFiles) => {
    setShowUpload(false);
    refetchFiles();
    toast.success(`${uploadedFiles.length} archivo(s) subido(s) exitosamente`);
  };

  const handleGenerateReport = () => {
    if (!selectedFile) {
      toast.error('Selecciona un archivo CSV primero');
      return;
    }

    if (!reportConfig.title.trim()) {
      toast.error('Ingresa un título para el reporte');
      return;
    }

    // Simular generación de reporte
    toast.success('Generando reporte...');
    
    setTimeout(() => {
      toast.success('¡Reporte generado exitosamente!');
      // Resetear formulario
      setSelectedFile(null);
      setReportConfig({
        title: '',
        description: '',
        type: 'comprehensive',
        includeCharts: true,
        includeTables: true,
        includeRecommendations: true
      });
    }, 3000);
  };

  const handleQuickGenerate = (file, type) => {
    const titles = {
      security: `Análisis de Seguridad - ${file.original_filename}`,
      cost: `Optimización de Costos - ${file.original_filename}`,
      performance: `Análisis de Rendimiento - ${file.original_filename}`,
      comprehensive: `Análisis Completo - ${file.original_filename}`
    };

    setSelectedFile(file);
    setReportConfig({
      title: titles[type] || titles.comprehensive,
      description: `Reporte generado automáticamente desde ${file.original_filename}`,
      type,
      includeCharts: true,
      includeTables: true,
      includeRecommendations: true
    });

    toast.success(`Generando reporte de ${type}...`);
    setTimeout(() => {
      toast.success('¡Reporte generado exitosamente!');
      setSelectedFile(null);
      setReportConfig({
        title: '',
        description: '',
        type: 'comprehensive',
        includeCharts: true,
        includeTables: true,
        includeRecommendations: true
      });
    }, 2500);
  };

  const reportTypes = [
    {
      value: 'security',
      label: 'Análisis de Seguridad',
      description: 'Enfocado en recomendaciones de seguridad',
      icon: Shield,
      color: 'text-red-600 bg-red-100'
    },
    {
      value: 'cost',
      label: 'Optimización de Costos',
      description: 'Análisis de ahorros y optimización',
      icon: DollarSign,
      color: 'text-green-600 bg-green-100'
    },
    {
      value: 'performance',
      label: 'Rendimiento',
      description: 'Mejoras de rendimiento y eficiencia',
      icon: TrendingUp,
      color: 'text-blue-600 bg-blue-100'
    },
    {
      value: 'comprehensive',
      label: 'Análisis Completo',
      description: 'Incluye todas las categorías',
      icon: BarChart3,
      color: 'text-purple-600 bg-purple-100'
    }
  ];

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
          className="bg-white rounded-xl shadow-soft border border-gray-200 p-6"
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
          
          <div className="space-y-4">
            <div className="text-sm text-gray-600">
              <p>• Formatos soportados: CSV (máximo 50MB)</p>
              <p>• Archivos de Azure Advisor recomendados</p>
              <p>• Procesamiento automático incluido</p>
            </div>
            
            <button
              onClick={() => setShowUpload(true)}
              className="w-full btn-primary"
            >
              Seleccionar Archivos
            </button>
          </div>
        </motion.div>

        {/* Crear reporte personalizado */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white rounded-xl shadow-soft border border-gray-200 p-6"
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
          
          <div className="space-y-4">
            <div className="text-sm text-gray-600">
              <p>• Análisis automático de datos</p>
              <p>• Gráficos y tablas incluidos</p>
              <p>• Recomendaciones personalizadas</p>
            </div>
            
            <button
              onClick={() => {
                if (files && files.length > 0) {
                  document.getElementById('report-generator').scrollIntoView({ behavior: 'smooth' });
                } else {
                  toast.error('Primero sube un archivo CSV');
                }
              }}
              className="w-full btn-primary"
            >
              Ir al Generador
            </button>
          </div>
        </motion.div>
      </div>

      {/* Archivos recientes con acciones rápidas */}
      {files && files.length > 0 && (
        <div className="bg-white rounded-xl shadow-soft border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-gray-900">
              Archivos Recientes ({files.length})
            </h3>
            <button
              onClick={() => refetchFiles()}
              className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700"
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
                className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
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
                {file.processing_status && (
                  <div className="mb-3">
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                      file.processing_status === 'completed' 
                        ? 'text-green-800 bg-green-100'
                        : file.processing_status === 'processing'
                        ? 'text-yellow-800 bg-yellow-100'
                        : 'text-red-800 bg-red-100'
                    }`}>
                      {file.processing_status === 'completed' ? 'Procesado' : 
                       file.processing_status === 'processing' ? 'Procesando' : 'Error'}
                    </span>
                  </div>
                )}

                {/* Información adicional */}
                {file.rows_count && (
                  <div className="text-xs text-gray-500 mb-3">
                    {file.rows_count} filas de datos
                  </div>
                )}

                {/* Acciones rápidas */}
                <div className="space-y-2">
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      onClick={() => handleQuickGenerate(file, 'security')}
                      className="flex items-center justify-center px-2 py-1 text-xs font-medium text-red-700 bg-red-50 rounded hover:bg-red-100 transition-colors"
                    >
                      <Shield className="w-3 h-3 mr-1" />
                      Seguridad
                    </button>
                    <button
                      onClick={() => handleQuickGenerate(file, 'cost')}
                      className="flex items-center justify-center px-2 py-1 text-xs font-medium text-green-700 bg-green-50 rounded hover:bg-green-100 transition-colors"
                    >
                      <DollarSign className="w-3 h-3 mr-1" />
                      Costos
                    </button>
                  </div>
                  <button
                    onClick={() => {
                      setSelectedFile(file);
                      document.getElementById('report-generator').scrollIntoView({ behavior: 'smooth' });
                    }}
                    className="w-full flex items-center justify-center px-2 py-1 text-xs font-medium text-blue-700 bg-blue-50 rounded hover:bg-blue-100 transition-colors"
                  >
                    <BarChart3 className="w-3 h-3 mr-1" />
                    Reporte Personalizado
                  </button>
                </div>
              </motion.div>
            ))}
          </div>

          {files.length > 6 && (
            <div className="mt-4 text-center">
              <button
                onClick={() => window.location.href = '/app/storage'}
                className="text-sm text-blue-600 hover:text-blue-700 font-medium"
              >
                Ver todos los archivos ({files.length - 6} más)
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
              Generador de Reportes
            </h3>
            <p className="text-sm text-gray-500">
              Personaliza y genera tu reporte de análisis
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Configuración del reporte */}
          <div className="space-y-6">
            {/* Selección de archivo */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Archivo CSV
              </label>
              {files && files.length > 0 ? (
                <select
                  value={selectedFile?.id || ''}
                  onChange={(e) => {
                    const file = files.find(f => f.id === e.target.value);
                    setSelectedFile(file);
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                >
                  <option value="">Selecciona un archivo...</option>
                  {files.filter(f => f.processing_status === 'completed').map(file => (
                    <option key={file.id} value={file.id}>
                      {file.original_filename} ({formatFileSize(file.file_size || 0)})
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
                          ? 'border-primary-500 bg-primary-50'
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

            {/* Opciones adicionales */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Opciones de Contenido
              </label>
              <div className="space-y-3">
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={reportConfig.includeCharts}
                    onChange={(e) => setReportConfig(prev => ({ ...prev, includeCharts: e.target.checked }))}
                    className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span className="text-sm text-gray-700">Incluir gráficos y visualizaciones</span>
                </label>
                
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={reportConfig.includeTables}
                    onChange={(e) => setReportConfig(prev => ({ ...prev, includeTables: e.target.checked }))}
                    className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span className="text-sm text-gray-700">Incluir tablas detalladas</span>
                </label>
                
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={reportConfig.includeRecommendations}
                    onChange={(e) => setReportConfig(prev => ({ ...prev, includeRecommendations: e.target.checked }))}
                    className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span className="text-sm text-gray-700">Incluir recomendaciones de acción</span>
                </label>
              </div>
            </div>
          </div>

          {/* Vista previa y acciones */}
          <div className="space-y-6">
            {/* Vista previa del archivo seleccionado */}
            {selectedFile && (
              <div className="p-4 bg-gray-50 rounded-lg">
                <h4 className="font-medium text-gray-900 mb-3">Archivo Seleccionado</h4>
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
                    <span className="text-gray-600">Filas:</span>
                    <span>{selectedFile.rows_count || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Subido:</span>
                    <span>{formatRelativeTime(selectedFile.upload_date)}</span>
                  </div>
                </div>
              </div>
            )}

            {/* Configuración del reporte */}
            <div className="p-4 bg-gray-50 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-3">Configuración del Reporte</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Tipo:</span>
                  <span>{reportTypes.find(t => t.value === reportConfig.type)?.label}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Gráficos:</span>
                  <span>{reportConfig.includeCharts ? 'Incluidos' : 'No incluidos'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Tablas:</span>
                  <span>{reportConfig.includeTables ? 'Incluidas' : 'No incluidas'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Recomendaciones:</span>
                  <span>{reportConfig.includeRecommendations ? 'Incluidas' : 'No incluidas'}</span>
                </div>
              </div>
            </div>

            {/* Botón de generar */}
            <button
              onClick={handleGenerateReport}
              disabled={!selectedFile || !reportConfig.title.trim()}
              className="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <BarChart3 className="w-5 h-5 mr-2" />
              Generar Reporte
            </button>

            {/* Información de tiempo estimado */}
            <div className="text-center text-sm text-gray-500">
              <p>⏱️ Tiempo estimado: 2-3 minutos</p>
              <p>📧 Recibirás una notificación cuando esté listo</p>
            </div>
          </div>
        </div>
      </div>

      {/* Reportes recientes */}
      {recentReports && recentReports.length > 0 && (
        <div className="bg-white rounded-xl shadow-soft border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-gray-900">
              Reportes Recientes
            </h3>
            <button
              onClick={() => window.location.href = '/app/history'}
              className="text-sm text-blue-600 hover:text-blue-700 font-medium"
            >
              Ver todos
            </button>
          </div>
          
          <ReportsList reports={recentReports} />
        </div>
      )}

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