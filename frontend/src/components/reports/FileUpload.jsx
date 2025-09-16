// src/components/reports/FileUpload.jsx - VERSIÓN CORREGIDA
import React, { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { 
  Upload, 
  X, 
  FileText, 
  AlertCircle, 
  CheckCircle,
  Loader,
  File,
  Cloud
} from 'lucide-react';
import { useFileUpload } from '../../hooks/useReports';
import { formatFileSize } from '../../utils/helpers';
import toast from 'react-hot-toast';

const FileUpload = ({ onUploadComplete, onClose }) => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploadErrors, setUploadErrors] = useState({});
  const fileInputRef = useRef(null);
  
  const { uploadFile, isUploading, progress } = useFileUpload();

  // Validar archivo
  const validateFile = (file) => {
    const errors = [];
    
    // Validar extensión
    const validExtensions = ['.csv'];
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    if (!validExtensions.includes(fileExtension)) {
      errors.push('Solo se permiten archivos CSV');
    }
    
    // Validar tamaño (máximo 50MB)
    const maxSize = 50 * 1024 * 1024; // 50MB
    if (file.size > maxSize) {
      errors.push('El archivo debe ser menor a 50MB');
    }
    
    // Validar que no esté vacío
    if (file.size === 0) {
      errors.push('El archivo está vacío');
    }
    
    return errors;
  };

  // Manejar archivos seleccionados
  const handleFiles = (files) => {
    const fileArray = Array.from(files);
    const newFiles = [];
    const errors = {};
    
    fileArray.forEach(file => {
      const fileErrors = validateFile(file);
      if (fileErrors.length > 0) {
        errors[file.name] = fileErrors;
      } else {
        newFiles.push({
          file,
          id: Math.random().toString(36).substr(2, 9),
          name: file.name,
          size: file.size,
          status: 'pending'
        });
      }
    });
    
    setUploadErrors(errors);
    setSelectedFiles(prev => [...prev, ...newFiles]);
    
    // Mostrar errores si los hay
    if (Object.keys(errors).length > 0) {
      Object.values(errors).flat().forEach(error => {
        toast.error(error);
      });
    }
  };

  // Eventos de drag and drop
  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      handleFiles(files);
    }
  };

  // Manejar clic en input
  const handleFileInputChange = (e) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFiles(files);
    }
  };

  // Remover archivo
  const removeFile = (fileId) => {
    setSelectedFiles(prev => prev.filter(f => f.id !== fileId));
  };

  // Subir archivos - CORREGIDO PARA CERRAR MODAL AUTOMÁTICAMENTE
  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      toast.error('Selecciona al menos un archivo');
      return;
    }

    const filesToUpload = selectedFiles.filter(f => f.status === 'pending');
    const completedFiles = [];
    
    for (const fileObj of filesToUpload) {
      try {
        // Actualizar estado a "subiendo"
        setSelectedFiles(prev => 
          prev.map(f => f.id === fileObj.id ? { ...f, status: 'uploading' } : f)
        );

        const result = await uploadFile(fileObj.file);
        
        // Actualizar estado a "completado"
        setSelectedFiles(prev => 
          prev.map(f => f.id === fileObj.id ? { ...f, status: 'completed', result } : f)
        );

        // Agregar a la lista de archivos completados
        completedFiles.push({
          ...result,
          originalFileObj: fileObj
        });

      } catch (error) {
        // Actualizar estado a "error"
        setSelectedFiles(prev => 
          prev.map(f => f.id === fileObj.id ? { ...f, status: 'error', error: error.message } : f)
        );
        toast.error(`Error subiendo ${fileObj.name}: ${error.message}`);
      }
    }

    // CORRECCIÓN: Llamar onUploadComplete y cerrar modal DESPUÉS de que todo termine
    if (completedFiles.length > 0) {
      // Esperar un momento para que el usuario vea el éxito
      setTimeout(() => {
        if (onUploadComplete) {
          onUploadComplete(completedFiles);
        }
        // Cerrar modal automáticamente
        onClose();
      }, 1500);
    }
  };

  // Obtener icono según estado
  const getFileStatusIcon = (status) => {
    switch (status) {
      case 'uploading':
        return <Loader className="w-5 h-5 text-blue-500 animate-spin" />;
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      default:
        return <FileText className="w-5 h-5 text-gray-400" />;
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.9 }}
        className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-hidden"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
              <Upload className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                Subir Archivos CSV
              </h3>
              <p className="text-sm text-gray-500">
                Arrastra archivos CSV de Azure Advisor aquí
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Contenido */}
        <div className="p-6 overflow-y-auto max-h-[60vh]">
          {/* Zona de drop */}
          <div
            className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-all ${
              dragActive
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-300 hover:border-gray-400'
            }`}
            onDragEnter={handleDragEnter}
            onDragLeave={handleDragLeave}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
          >
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".csv"
              onChange={handleFileInputChange}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />
            
            <div className="flex flex-col items-center space-y-4">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
                <Cloud className="w-8 h-8 text-blue-600" />
              </div>
              
              <div>
                <p className="text-lg font-medium text-gray-900 mb-1">
                  Arrastra archivos aquí o{' '}
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="text-blue-600 hover:text-blue-700 underline"
                  >
                    selecciona archivos
                  </button>
                </p>
                <p className="text-sm text-gray-500">
                  Solo archivos CSV, máximo 50MB por archivo
                </p>
              </div>
            </div>
          </div>

          {/* Lista de archivos seleccionados */}
          {selectedFiles.length > 0 && (
            <div className="mt-6">
              <h4 className="font-medium text-gray-900 mb-3">
                Archivos seleccionados ({selectedFiles.length})
              </h4>
              
              <div className="space-y-3 max-h-60 overflow-y-auto">
                {selectedFiles.map((fileObj) => (
                  <motion.div
                    key={fileObj.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                  >
                    <div className="flex items-center space-x-3">
                      {getFileStatusIcon(fileObj.status)}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {fileObj.name}
                        </p>
                        <div className="flex items-center space-x-2 text-xs text-gray-500">
                          <span>{formatFileSize(fileObj.size)}</span>
                          {fileObj.status === 'uploading' && (
                            <span>• Subiendo... {progress}%</span>
                          )}
                          {fileObj.status === 'completed' && (
                            <span className="text-green-600">• Completado</span>
                          )}
                          {fileObj.status === 'error' && (
                            <span className="text-red-600">• Error: {fileObj.error}</span>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    {fileObj.status === 'pending' && (
                      <button
                        onClick={() => removeFile(fileObj.id)}
                        className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    )}
                  </motion.div>
                ))}
              </div>
            </div>
          )}

          {/* Barra de progreso global */}
          {isUploading && (
            <div className="mt-6">
              <div className="flex justify-between text-sm text-gray-600 mb-2">
                <span>Subiendo archivos...</span>
                <span>{progress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
            </div>
          )}

          {/* Información adicional */}
          <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <div className="flex items-start space-x-2">
              <File className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
              <div className="text-sm">
                <p className="font-medium text-blue-900 mb-1">
                  💡 Solo archivos CSV máximo 50MB cada uno
                </p>
                <ul className="text-blue-700 space-y-1">
                  <li>• Archivos de Azure Advisor recomendados</li>
                  <li>• Se procesarán automáticamente después de subir</li>
                  <li>• Podrás generar reportes inmediatamente</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-gray-200 bg-gray-50">
          <div className="text-sm text-gray-500">
            {selectedFiles.length > 0 && (
              <span>
                {selectedFiles.filter(f => f.status === 'pending').length} archivo(s) listos para subir
              </span>
            )}
          </div>
          
          <div className="flex items-center space-x-3">
            <button
              onClick={onClose}
              disabled={isUploading}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
            >
              {isUploading ? 'Subiendo...' : 'Cancelar'}
            </button>
            
            <button
              onClick={handleUpload}
              disabled={isUploading || selectedFiles.filter(f => f.status === 'pending').length === 0}
              className="px-6 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center"
            >
              {isUploading ? (
                <>
                  <Loader className="w-4 h-4 mr-2 animate-spin" />
                  Subiendo...
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4 mr-2" />
                  Subir {selectedFiles.filter(f => f.status === 'pending').length} Archivo(s)
                </>
              )}
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default FileUpload;