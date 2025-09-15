// src/pages/Storage.jsx
import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Cloud, FolderOpen, FileText, Download, Search, Filter } from 'lucide-react';
import { useStorageFiles } from '../hooks/useReports';
import Loading from '../components/common/Loading';
import { formatFileSize, formatRelativeTime } from '../utils/helpers';

const Storage = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [fileType, setFileType] = useState('all');
  
  const { data: files, isLoading } = useStorageFiles({
    search: searchTerm,
    type: fileType === 'all' ? undefined : fileType
  });

  const fileTypes = [
    { value: 'all', label: 'Todos los archivos' },
    { value: 'csv', label: 'Archivos CSV' },
    { value: 'pdf', label: 'Reportes PDF' }
  ];

  const getFileIcon = (fileName) => {
    const extension = fileName.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'csv':
        return '📊';
      case 'pdf':
        return '📄';
      default:
        return '📁';
    }
  };

  const getFileTypeColor = (fileName) => {
    const extension = fileName.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'csv':
        return 'bg-green-100 text-green-800';
      case 'pdf':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (isLoading) {
    return <Loading fullScreen text="Cargando archivos..." />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-r from-cyan-600 to-blue-600 rounded-2xl p-8 text-white"
      >
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">Azure Blob Storage</h1>
            <p className="text-cyan-100 text-lg">
              Gestiona tus archivos CSV y reportes generados
            </p>
          </div>
          <div className="hidden md:block">
            <div className="w-20 h-20 bg-white/20 rounded-2xl flex items-center justify-center">
              <Cloud className="w-10 h-10" />
            </div>
          </div>
        </div>
      </motion.div>

      {/* Filtros y búsqueda */}
      <div className="bg-white rounded-xl shadow-soft border border-gray-200 p-6">
        <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
          <div className="flex flex-col sm:flex-row gap-4 flex-1">
            <div className="flex items-center space-x-2 flex-1 max-w-md">
              <Search className="w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Buscar archivos..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="input-field flex-1"
              />
            </div>
            
            <div className="flex items-center space-x-2">
              <Filter className="w-5 h-5 text-gray-400" />
              <select
                value={fileType}
                onChange={(e) => setFileType(e.target.value)}
                className="input-field min-w-0"
              >
                {fileTypes.map(type => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
          
          <div className="text-sm text-gray-500">
            {files?.length || 0} archivos encontrados
          </div>
        </div>
      </div>

      {/* Grid de archivos */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {files && files.length > 0 ? (
          files.map((file, index) => (
            <motion.div
              key={file.name}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className="bg-white rounded-xl shadow-soft border border-gray-200 p-6 hover:shadow-medium transition-all cursor-pointer group"
            >
              <div className="flex flex-col h-full">
                {/* Icono y tipo de archivo */}
                <div className="flex items-start justify-between mb-4">
                  <div className="text-3xl">
                    {getFileIcon(file.name)}
                  </div>
                  <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getFileTypeColor(file.name)}`}>
                    {file.name.split('.').pop()?.toUpperCase()}
                  </span>
                </div>

                {/* Información del archivo */}
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900 mb-2 truncate" title={file.name}>
                    {file.name}
                  </h3>
                  
                  <div className="space-y-1 text-sm text-gray-600">
                    <div className="flex justify-between">
                      <span>Tamaño:</span>
                      <span className="font-medium">{formatFileSize(file.size)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Modificado:</span>
                      <span className="font-medium">{formatRelativeTime(file.last_modified)}</span>
                    </div>
                  </div>
                </div>

                {/* Acciones */}
                <div className="mt-4 pt-4 border-t border-gray-100">
                  <div className="flex items-center justify-between">
                    <button
                      className="flex items-center space-x-1 text-blue-600 hover:text-blue-700 transition-colors"
                      title="Descargar archivo"
                    >
                      <Download className="w-4 h-4" />
                      <span className="text-sm font-medium">Descargar</span>
                    </button>
                    
                    <button
                      className="flex items-center space-x-1 text-gray-500 hover:text-gray-700 transition-colors"
                      title="Ver detalles"
                    >
                      <FolderOpen className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            </motion.div>
          ))
        ) : (
          <div className="col-span-full">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="bg-white rounded-xl shadow-soft border border-gray-200 p-12 text-center"
            >
              <Cloud className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                No hay archivos en el storage
              </h3>
              <p className="text-gray-600 mb-6">
                Los archivos aparecerán aquí cuando subas CSVs o generes reportes
              </p>
              <button className="btn-primary">
                Subir Primer Archivo
              </button>
            </motion.div>
          </div>
        )}
      </div>

      {/* Información de storage */}
      <div className="bg-white rounded-xl shadow-soft border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Información de Almacenamiento
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600 mb-1">
              {files?.filter(f => f.name.includes('.csv')).length || 0}
            </div>
            <div className="text-sm text-gray-600">Archivos CSV</div>
          </div>
          
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-red-600 mb-1">
              {files?.filter(f => f.name.includes('.pdf')).length || 0}
            </div>
            <div className="text-sm text-gray-600">Reportes PDF</div>
          </div>
          
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600 mb-1">
              {files ? formatFileSize(files.reduce((total, file) => total + (file.size || 0), 0)) : '0 B'}
            </div>
            <div className="text-sm text-gray-600">Espacio Usado</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Storage;