// frontend/src/pages/Reports.jsx - ACTUALIZADO CON BACKEND REAL
import React, { useState, useEffect } from 'react';
import { Upload, FileText, AlertCircle, CheckCircle, Clock, Loader2 } from 'lucide-react';
import { useFileUpload, useStorageFiles } from '../hooks/useReports';
import toast from 'react-hot-toast';

const FileUploadComponent = ({ onFileUploadComplete }) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const { uploadFile, isUploading, progress } = useFileUpload();

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    const files = Array.from(e.dataTransfer.files);
    handleFiles(files);
  };

  const handleFileInput = (e) => {
    const files = Array.from(e.target.files);
    handleFiles(files);
  };

  const handleFiles = async (files) => {
    if (files.length === 0) return;
    
    const file = files[0];
    
    // Validar tipo de archivo
    if (!file.name.toLowerCase().endsWith('.csv')) {
      toast.error('Por favor, selecciona un archivo CSV');
      return;
    }

    // Validar tamaño (50MB máximo)
    if (file.size > 50 * 1024 * 1024) {
      toast.error('El archivo no puede ser mayor a 50MB');
      return;
    }

    try {
      const result = await uploadFile(file);
      console.log('Archivo subido:', result);
      
      // Notificar al componente padre que se completó la subida
      if (onFileUploadComplete) {
        onFileUploadComplete(result);
      }
      
    } catch (error) {
      console.error('Error en la subida:', error);
      // El error ya se muestra en el hook
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
      <div
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          isDragOver
            ? 'border-blue-400 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400'
        }`}
        onDrop={handleDrop}
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragOver(true);
        }}
        onDragLeave={() => setIsDragOver(false)}
      >
        {isUploading ? (
          <div className="space-y-4">
            <div className="w-16 h-16 mx-auto bg-blue-100 rounded-full flex items-center justify-center">
              <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
            </div>
            <div>
              <p className="text-lg font-medium text-gray-900 mb-2">Subiendo archivo...</p>
              <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
              <p className="text-sm text-gray-500">{progress}% completado</p>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="w-16 h-16 mx-auto bg-gray-100 rounded-full flex items-center justify-center">
              <Upload className="w-8 h-8 text-gray-400" />
            </div>
            <div>
              <p className="text-lg font-medium text-gray-900 mb-2">
                Sube tu archivo CSV de Azure Advisor
              </p>
              <p className="text-gray-500 mb-4">
                Arrastra y suelta tu archivo aquí, o haz clic para seleccionar
              </p>
              <input
                type="file"
                accept=".csv"
                onChange={handleFileInput}
                className="hidden"
                id="file-upload"
                disabled={isUploading}
              />
              <label
                htmlFor="file-upload"
                className={`inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-lg text-white transition-colors cursor-pointer ${
                  isUploading 
                    ? 'bg-gray-400 cursor-not-allowed' 
                    : 'bg-blue-600 hover:bg-blue-700'
                }`}
              >
                {isUploading ? 'Subiendo...' : 'Seleccionar archivo'}
              </label>
            </div>
            <p className="text-xs text-gray-400">
              Formatos soportados: CSV (máximo 50MB)
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

// Componente para mostrar el estado de procesamiento
const ProcessingStatusBadge = ({ status }) => {
  const statusConfig = {
    pending: {
      icon: Clock,
      text: 'Pendiente',
      className: 'bg-yellow-100 text-yellow-800',
      iconClassName: 'text-yellow-500'
    },
    processing: {
      icon: Loader2,
      text: 'Procesando',
      className: 'bg-blue-100 text-blue-800',
      iconClassName: 'text-blue-500 animate-spin'
    },
    completed: {
      icon: CheckCircle,
      text: 'Completado',
      className: 'bg-green-100 text-green-800',
      iconClassName: 'text-green-500'
    },
    failed: {
      icon: AlertCircle,
      text: 'Error',
      className: 'bg-red-100 text-red-800',
      iconClassName: 'text-red-500'
    }
  };

  const config = statusConfig[status] || statusConfig.pending;
  const Icon = config.icon;

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.className}`}>
      <Icon className={`w-4 h-4 mr-1 ${config.iconClassName}`} />
      {config.text}
    </span>
  );
};

// Componente para lista de archivos
const FilesList = ({ files, onRefresh }) => {
  if (files.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
        <div className="text-center space-y-4">
          <div className="w-16 h-16 mx-auto bg-gray-100 rounded-full flex items-center justify-center">
            <FileText className="w-8 h-8 text-gray-400" />
          </div>
          <div>
            <h3 className="text-lg font-medium text-gray-900">No hay archivos</h3>
            <p className="text-gray-500">Sube tu primer archivo CSV para comenzar</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200">
      <div className="p-6 border-b border-gray-200 flex justify-between items-center">
        <h2 className="text-lg font-semibold text-gray-900">Archivos Recientes</h2>
        <button 
          onClick={onRefresh}
          className="text-sm text-blue-600 hover:text-blue-700 font-medium"
        >
          Actualizar
        </button>
      </div>
      <div className="divide-y divide-gray-200">
        {files.map((file) => (
          <div key={file.id} className="p-6 hover:bg-gray-50 transition-colors">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                  <FileText className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <h3 className="font-medium text-gray-900">{file.original_filename}</h3>
                  <div className="flex items-center space-x-4 mt-1">
                    <p className="text-sm text-gray-500">
                      {new Date(file.upload_date).toLocaleString()}
                    </p>
                    <p className="text-sm text-gray-500">
                      {(file.file_size / 1024).toFixed(1)} KB
                    </p>
                    {file.rows_count && (
                      <p className="text-sm text-gray-500">
                        {file.rows_count} filas
                      </p>
                    )}
                  </div>
                </div>
              </div>
              
              <div className="flex items-center space-x-3">
                <ProcessingStatusBadge status={file.processing_status} />
                
                {file.processing_status === 'completed' && file.analysis_data && (
                  <button className="text-sm text-blue-600 hover:text-blue-700 font-medium">
                    Ver Análisis
                  </button>
                )}
              </div>
            </div>
            
            {file.processing_status === 'failed' && file.error_message && (
              <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-600">
                  <strong>Error:</strong> {file.error_message}
                </p>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

const Reports = () => {
  const { data: files, isLoading, error, refetch } = useStorageFiles();
  const [refreshKey, setRefreshKey] = useState(0);

  // Auto-refresh cada 30 segundos para archivos en procesamiento
  useEffect(() => {
    const hasProcessingFiles = files.some(file => 
      file.processing_status === 'processing' || file.processing_status === 'pending'
    );

    if (hasProcessingFiles) {
      const interval = setInterval(() => {
        setRefreshKey(prev => prev + 1);
      }, 30000); // 30 segundos

      return () => clearInterval(interval);
    }
  }, [files]);

  const handleFileUploadComplete = (uploadedFile) => {
    // Refrescar la lista cuando se complete la subida
    setRefreshKey(prev => prev + 1);
    toast.success('El archivo se está procesando. Recibirás una notificación cuando esté listo.');
  };

  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1);
  };

  if (error) {
    return (
      <div className="space-y-8">
        <div className="bg-red-50 border border-red-200 rounded-xl p-6">
          <div className="flex items-center space-x-3">
            <AlertCircle className="w-6 h-6 text-red-600" />
            <div>
              <h3 className="font-medium text-red-900">Error cargando reportes</h3>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8" key={refreshKey}>
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Reportes</h1>
        <p className="text-gray-600">
          Sube y gestiona tus archivos CSV de Azure Advisor para generar análisis detallados
        </p>
      </div>

      {/* Upload Section */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Subir Nuevo Archivo</h2>
        <FileUploadComponent onFileUploadComplete={handleFileUploadComplete} />
      </div>

      {/* Files List */}
      <div>
        {isLoading ? (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
            <div className="text-center">
              <Loader2 className="w-8 h-8 text-gray-400 animate-spin mx-auto mb-4" />
              <p className="text-gray-500">Cargando archivos...</p>
            </div>
          </div>
        ) : (
          <FilesList files={files} onRefresh={handleRefresh} />
        )}
      </div>

      {/* Información adicional */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
        <div className="flex items-start space-x-3">
          <AlertCircle className="w-6 h-6 text-blue-600 mt-0.5 flex-shrink-0" />
          <div>
            <h3 className="font-medium text-blue-900 mb-1">
              ¿Cómo obtener tu archivo CSV de Azure Advisor?
            </h3>
            <div className="text-sm text-blue-800 space-y-2">
              <p>1. Ve a Azure Portal → Azure Advisor</p>
              <p>2. Selecciona las recomendaciones que quieres analizar</p>
              <p>3. Haz clic en "Download as CSV" o "Descargar como CSV"</p>
              <p>4. Sube el archivo descargado aquí para obtener análisis detallados</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Reports;