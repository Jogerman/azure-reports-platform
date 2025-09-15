// src/components/reports/FileUpload.jsx
import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { AnimatePresence } from 'framer-motion';
import { 
  Upload, 
  FileText, 
  AlertCircle, 
  CheckCircle, 
  X,
  Loader2 
} from 'lucide-react';
import { useUploadCSV } from '../../hooks/useReports';
import { formatFileSize } from '../../utils/helpers';
import toast from 'react-hot-toast';

const FileUpload = ({ onFileUploaded }) => {
  const [uploadProgress, setUploadProgress] = useState(0);
  const [dragActive, setDragActive] = useState(false);
  
  const uploadMutation = useUploadCSV();

  const onDrop = useCallback(async (acceptedFiles, rejectedFiles) => {
    if (rejectedFiles.length > 0) {
      const error = rejectedFiles[0].errors[0];
      toast.error(`Error: ${error.message}`);
      return;
    }

    const file = acceptedFiles[0];
    if (!file) return;

    try {
      const result = await uploadMutation.mutateAsync({
        file,
        onProgress: setUploadProgress
      });
      
      if (onFileUploaded) {
        onFileUploaded(result);
      }
      setUploadProgress(0);
    } catch (_error) {
      setUploadProgress(0);
      console.error('Upload error:', error);
    }
  }, [uploadMutation, onFileUploaded]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    onDragEnter: () => setDragActive(true),
    onDragLeave: () => setDragActive(false),
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
    },
    maxFiles: 1,
    maxSize: 50 * 1024 * 1024, // 50MB
    disabled: uploadMutation.isLoading,
  });

  return (
    <div className="space-y-6">
      {/* Upload Area */}
      <div className="bg-white rounded-xl shadow-soft border border-gray-200 p-8">
        <motion.div
          {...getRootProps()}
          className={`relative border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all duration-300 ${
            isDragActive || dragActive
              ? 'border-primary-400 bg-primary-50'
              : uploadMutation.isLoading
              ? 'border-gray-200 bg-gray-50 cursor-not-allowed'
              : 'border-gray-300 hover:border-primary-400 hover:bg-primary-50'
          }`}
          whileHover={!uploadMutation.isLoading ? { scale: 1.02 } : {}}
          whileTap={!uploadMutation.isLoading ? { scale: 0.98 } : {}}
        >
          <input {...getInputProps()} />
          
          <AnimatePresence mode="wait">
            {uploadMutation.isLoading ? (
              <motion.div
                key="uploading"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="space-y-4"
              >
                <Loader2 className="w-12 h-12 text-primary-500 mx-auto animate-spin" />
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    Subiendo archivo...
                  </h3>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-primary-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                  <p className="text-sm text-gray-600 mt-2">{uploadProgress}% completado</p>
                </div>
              </motion.div>
            ) : (
              <motion.div
                key="idle"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="space-y-4"
              >
                <div className={`w-16 h-16 rounded-full flex items-center justify-center mx-auto ${
                  isDragActive || dragActive ? 'bg-primary-100' : 'bg-gray-100'
                }`}>
                  <Upload className={`w-8 h-8 ${
                    isDragActive || dragActive ? 'text-primary-600' : 'text-gray-400'
                  }`} />
                </div>
                
                <div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">
                    {isDragActive ? '¡Suelta tu archivo aquí!' : 'Sube tu archivo CSV'}
                  </h3>
                  <p className="text-gray-600 mb-4">
                    Arrastra y suelta o haz clic para seleccionar un archivo
                  </p>
                  
                  <div className="flex items-center justify-center space-x-6 text-sm text-gray-500">
                    <span>CSV, XLS, XLSX</span>
                    <span>•</span>
                    <span>Máximo 50MB</span>
                    <span>•</span>
                    <span>Análisis automático</span>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </div>

      {/* Tips */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-blue-50 rounded-xl p-6 border border-blue-200">
          <div className="flex items-start space-x-3">
            <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
              <FileText className="w-4 h-4 text-blue-600" />
            </div>
            <div>
              <h4 className="font-semibold text-blue-900 mb-2">Formato Recomendado</h4>
              <p className="text-blue-700 text-sm">
                Usa archivos CSV con headers claros para obtener mejores resultados de análisis.
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-green-50 rounded-xl p-6 border border-green-200">
          <div className="flex items-start space-x-3">
            <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center flex-shrink-0">
              <CheckCircle className="w-4 h-4 text-green-600" />
            </div>
            <div>
              <h4 className="font-semibold text-green-900 mb-2">Datos Seguros</h4>
              <p className="text-green-700 text-sm">
                Tus archivos se almacenan de forma segura en Azure Cloud con encriptación.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FileUpload;
