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

  // Tipos de reportes disponibles
  const reportTypes = [
    { value: 'comprehensive', label: 'Análisis Completo', icon: BarChart3, description: 'Análisis detallado con todas las métricas' },
    { value: 'security', label: 'Análisis de Seguridad', icon: Shield, description: 'Enfoque en vulnerabilidades y seguridad' },
    { value: 'performance', label: 'Análisis de Rendimiento', icon: Zap, description: 'Optimización y eficiencia del sistema' },
    { value: 'cost', label: 'Análisis de Costos', icon: DollarSign, description: 'Optimización financiera y ahorros' },
    { value: 'trend', label: 'Análisis de Tendencias', icon: TrendingUp, description: 'Patrones y proyecciones futuras' }
  ];

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
      console.error('Error generando reporte:', error);
      toast.error('Error al generar el reporte. Intenta nuevamente.');
    }
  };

  const handleFileSelect = (file) => {
    setSelectedFile(file);
    
    // Auto-completar título si está vacío
    if (!reportConfig.title.trim()) {
      setReportConfig(prev => ({
        ...prev,
        title: `Análisis ${reportTypes.find(t => t.value === reportConfig.type)?.label} - ${file.original_filename}`
      }));
    }
  };

  const handleTypeChange = (newType) => {
    setReportConfig(prev => ({ ...prev, type: newType }));
    
    // Actualizar título si hay archivo seleccionado
    if (selectedFile && reportConfig.title.includes('Análisis')) {
      const typeLabel = reportTypes.find(t => t.value === newType)?.label;
      setReportConfig(prev => ({
        ...prev,
        title: `Análisis ${typeLabel} - ${selectedFile.original_filename}`
      }));
    }
  };

  const getFileMetrics = (file) => {
    if (!file.analysis_data) return null;
    
    return {
      rows: file.analysis_data.total_rows || 0,
      columns: file.analysis_data.total_columns || 0,
      recommendations: file.analysis_data.total_recommendations || 0,
      savings: file.analysis_data.estimated_savings || 0
    };
  };

  if (filesLoading) {
    return <Loading message="Cargando archivos disponibles..." />;
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Generar Reportes</h1>
          <p className="text-gray-600 mt-1">
            Crea reportes detallados a partir de tus archivos CSV analizados
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <button
            onClick={() => refetchFiles()}
            className="btn-secondary flex items-center"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Actualizar
          </button>
          <button
            onClick={() => setShowUpload(true)}
            className="btn-primary flex items-center"
          >
            <Plus className="w-4 h-4 mr-2" />
            Subir Archivo
          </button>
        </div>
      </div>

      {/* Reportes recientes */}
      {recentReports && recentReports.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-xl shadow-soft border border-gray-200 p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center">
              <FileText className="w-5 h-5 mr-2 text-purple-600" />
              Reportes Recientes
            </h2>
            <a 
              href="/app/history" 
              className="text-sm text-purple-600 hover:text-purple-700 font-medium"
            >
              Ver todos →
            </a>
          </div>
          
          {reportsLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="w-6 h-6 border-2 border-purple-600 border-t-transparent rounded-full animate-spin"></div>
            </div>
          ) : (
            <ReportsList reports={recentReports} showActions={false} />
          )}
        </motion.div>
      )}

      {/* Generador de reportes */}
      <div id="report-generator" className="grid lg:grid-cols-2 gap-8">
        {/* Selección de archivo */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="bg-white rounded-xl shadow-soft border border-gray-200 p-6"
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <Database className="w-5 h-5 mr-2 text-blue-600" />
            Seleccionar Archivo
          </h3>
          
          {!files || files.length === 0 ? (
            <div className="text-center py-8">
              <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500 mb-4">No hay archivos CSV disponibles</p>
              <button
                onClick={() => setShowUpload(true)}
                className="btn-primary flex items-center mx-auto"
              >
                <Plus className="w-4 h-4 mr-2" />
                Subir Primer Archivo
              </button>
            </div>
          ) : (
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {files.map((file) => {
                const metrics = getFileMetrics(file);
                const isSelected = selectedFile?.id === file.id;
                
                return (
                  <div
                    key={file.id}
                    onClick={() => handleFileSelect(file)}
                    className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                      isSelected 
                        ? 'border-primary-500 bg-primary-50' 
                        : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium text-gray-900 truncate">
                        {file.original_filename}
                      </h4>
                      <span className="text-xs text-gray-500">
                        {formatFileSize(file.file_size)}
                      </span>
                    </div>
                    
                    <div className="text-xs text-gray-500 mb-3">
                      Subido {formatRelativeTime(file.created_at)}
                    </div>
                    
                    {metrics && (
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div className="text-center">
                          <div className="font-semibold text-blue-600">
                            {metrics.rows.toLocaleString()}
                          </div>
                          <div className="text-xs text-gray-500">Filas</div>
                        </div>
                        <div className="text-center">
                          <div className="font-semibold text-purple-600">
                            {metrics.columns}
                          </div>
                          <div className="text-xs text-gray-500">Columnas</div>
                        </div>
                        <div className="text-center">
                          <div className="font-semibold text-orange-600">
                            {metrics.recommendations}
                          </div>
                          <div className="text-xs text-gray-500">Recomendaciones</div>
                        </div>
                        <div className="text-center">
                          <div className="font-semibold text-green-600">
                            ${Math.round(metrics.savings)}
                          </div>
                          <div className="text-xs text-gray-500">Ahorros Est.</div>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </motion.div>

        {/* Configuración del reporte */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="bg-white rounded-xl shadow-soft border border-gray-200 p-6"
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <Settings className="w-5 h-5 mr-2 text-purple-600" />
            Configuración del Reporte
          </h3>
          
          <div className="space-y-6">
            {/* Tipo de reporte */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Tipo de Análisis
              </label>
              <div className="grid grid-cols-1 gap-2">
                {reportTypes.map((type) => {
                  const Icon = type.icon;
                  return (
                    <label
                      key={type.value}
                      className={`flex items-center p-3 border rounded-lg cursor-pointer transition-all ${
                        reportConfig.type === type.value
                          ? 'border-primary-500 bg-primary-50'
                          : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      <input
                        type="radio"
                        name="reportType"
                        value={type.value}
                        checked={reportConfig.type === type.value}
                        onChange={(e) => handleTypeChange(e.target.value)}
                        className="sr-only"
                      />
                      <Icon className={`w-4 h-4 mr-3 ${
                        reportConfig.type === type.value ? 'text-primary-600' : 'text-gray-400'
                      }`} />
                      <div className="flex-1">
                        <div className="text-sm font-medium text-gray-700">
                          {type.label}
                        </div>
                        <div className="text-xs text-gray-500">
                          {type.description}
                        </div>
                      </div>
                    </label>
                  );
                })}
              </div>
            </div>

            {/* Título del reporte */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Título del Reporte *
              </label>
              <input
                type="text"
                value={reportConfig.title}
                onChange={(e) => setReportConfig(prev => ({ ...prev, title: e.target.value }))}
                placeholder="Ej: Análisis de Seguridad - Datos Q3 2024"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>

            {/* Descripción opcional */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Descripción (Opcional)
              </label>
              <textarea
                value={reportConfig.description}
                onChange={(e) => setReportConfig(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Descripción breve del propósito del reporte..."
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>

            {/* Opciones de contenido */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Contenido del Reporte
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
                    <span className="text-sm font-medium text-gray-700">Incluir visualizaciones</span>
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

          {/* Vista previa de configuración */}
          {selectedFile && (
            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-3 flex items-center">
                <Settings className="w-4 h-4 mr-2 text-purple-600" />
                Vista Previa
              </h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Archivo:</span>
                  <span className="font-medium truncate max-w-48">
                    {selectedFile.original_filename}
                  </span>
                </div>
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
          )}

          {/* Progreso de generación */}
          {isGenerating && (
            <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
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
            className="w-full mt-6 btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center py-3 text-lg font-semibold"
          >
            {isGenerating ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                Generando...
              </>
            ) : (
              <>
                <BarChart3 className="w-5 h-5 mr-2" />
                Generar Reporte
              </>
            )}
          </button>
        </motion.div>
      </div>

      {/* Modal de subida de archivos */}
      {showUpload && (
        <FileUpload
          onClose={() => setShowUpload(false)}
          onUploadComplete={handleUploadComplete}
          accept=".csv"
        />
      )}
    </div>
  );
};

export default Reports;