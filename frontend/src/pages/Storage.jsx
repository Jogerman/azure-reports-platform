// src/pages/Storage.jsx
import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Cloud, 
  FolderOpen, 
  FileText, 
  Download, 
  Search, 
  Filter,
  Upload,
  Trash2,
  Eye,
  RefreshCw,
  MoreVertical,
  File,
  Database,
  HardDrive
} from 'lucide-react';
import { useStorageFiles } from '../hooks/useReports';
import Loading from '../components/common/Loading';
import { formatFileSize, formatRelativeTime } from '../utils/helpers';
import toast from 'react-hot-toast';

const Storage = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [fileType, setFileType] = useState('all');
  const [viewMode, setViewMode] = useState('grid'); // 'grid' o 'list'
  const [selectedFiles, setSelectedFiles] = useState(new Set());
  
  const { data: files, isLoading, refetch } = useStorageFiles({
    search: searchTerm,
    type: fileType === 'all' ? undefined : fileType
  });

  const fileTypes = [
    { value: 'all', label: 'Todos los archivos', count: files?.length || 0 },
    { value: 'csv', label: 'Archivos CSV', count: files?.filter(f => f.original_filename?.endsWith('.csv')).length || 0 },
    { value: 'pdf', label: 'Reportes PDF', count: files?.filter(f => f.original_filename?.endsWith('.pdf')).length || 0 }
  ];

  // Funciones de manejo
  const handleFileSelect = (fileId) => {
    const newSelected = new Set(selectedFiles);
    if (newSelected.has(fileId)) {
      newSelected.delete(fileId);
    } else {
      newSelected.add(fileId);
    }
    setSelectedFiles(newSelected);
  };

  const handleSelectAll = () => {
    if (selectedFiles.size === files?.length) {
      setSelectedFiles(new Set());
    } else {
      setSelectedFiles(new Set(files?.map(f => f.id) || []));
    }
  };

  const handleDownload = (file) => {
    toast.success(`Descargando ${file.original_filename}...`);
    // Simular descarga
    setTimeout(() => {
      toast.success('Descarga completada');
    }, 2000);
  };

  const handleDelete = (file) => {
    if (window.confirm(`¿Estás seguro de eliminar ${file.original_filename}?`)) {
      toast.success('Archivo eliminado');
      refetch();
    }
  };

  const handleBulkDelete = () => {
    if (selectedFiles.size === 0) {
      toast.error('Selecciona archivos para eliminar');
      return;
    }
    
    if (window.confirm(`¿Eliminar ${selectedFiles.size} archivo(s) seleccionado(s)?`)) {
      toast.success(`${selectedFiles.size} archivo(s) eliminado(s)`);
      setSelectedFiles(new Set());
      refetch();
    }
  };

  const handleUpload = () => {
    // Crear input file temporal
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.csv,.pdf';
    input.multiple = true;
    input.onchange = (e) => {
      const files = Array.from(e.target.files);
      if (files.length > 0) {
        toast.success(`Subiendo ${files.length} archivo(s)...`);
        setTimeout(() => {
          toast.success('Archivos subidos exitosamente');
          refetch();
        }, 2000);
      }
    };
    input.click();
  };

  const getFileIcon = (fileName) => {
    const extension = fileName?.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'csv':
        return { icon: '📊', color: 'text-green-600 bg-green-100' };
      case 'pdf':
        return { icon: '📄', color: 'text-red-600 bg-red-100' };
      case 'xlsx':
      case 'xls':
        return { icon: '📈', color: 'text-blue-600 bg-blue-100' };
      default:
        return { icon: '📁', color: 'text-gray-600 bg-gray-100' };
    }
  };

  const getStorageStats = () => {
    if (!files || files.length === 0) {
      return {
        totalFiles: 0,
        totalSize: 0,
        csvFiles: 0,
        pdfFiles: 0,
        averageSize: 0
      };
    }

    const csvFiles = files.filter(f => f.original_filename?.endsWith('.csv')).length;
    const pdfFiles = files.filter(f => f.original_filename?.endsWith('.pdf')).length;
    const totalSize = files.reduce((total, file) => total + (file.file_size || 0), 0);
    const averageSize = files.length > 0 ? totalSize / files.length : 0;

    return {
      totalFiles: files.length,
      totalSize,
      csvFiles,
      pdfFiles,
      averageSize
    };
  };

  if (isLoading) {
    return <Loading fullScreen text="Cargando almacenamiento..." />;
  }

  const stats = getStorageStats();

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-cyan-600 rounded-2xl p-8 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">Almacenamiento</h1>
            <p className="text-blue-100 text-lg">
              Gestiona tus archivos CSV y reportes generados
            </p>
          </div>
          <div className="hidden md:block">
            <div className="w-20 h-20 bg-white/20 rounded-2xl flex items-center justify-center">
              <Database className="w-10 h-10" />
            </div>
          </div>
        </div>
      </div>

      {/* Estadísticas de almacenamiento */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-xl shadow-soft border border-gray-200 p-6"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Archivos</p>
              <p className="text-3xl font-bold text-gray-900">{stats.totalFiles}</p>
            </div>
            <div className="w-12 h-12 bg-blue-500 rounded-xl flex items-center justify-center">
              <File className="w-6 h-6 text-white" />
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white rounded-xl shadow-soft border border-gray-200 p-6"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Espacio Usado</p>
              <p className="text-3xl font-bold text-gray-900">{formatFileSize(stats.totalSize)}</p>
            </div>
            <div className="w-12 h-12 bg-green-500 rounded-xl flex items-center justify-center">
              <HardDrive className="w-6 h-6 text-white" />
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white rounded-xl shadow-soft border border-gray-200 p-6"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Archivos CSV</p>
              <p className="text-3xl font-bold text-gray-900">{stats.csvFiles}</p>
            </div>
            <div className="w-12 h-12 bg-purple-500 rounded-xl flex items-center justify-center">
              <FileText className="w-6 h-6 text-white" />
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-white rounded-xl shadow-soft border border-gray-200 p-6"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Reportes PDF</p>
              <p className="text-3xl font-bold text-gray-900">{stats.pdfFiles}</p>
            </div>
            <div className="w-12 h-12 bg-orange-500 rounded-xl flex items-center justify-center">
              <Download className="w-6 h-6 text-white" />
            </div>
          </div>
        </motion.div>
      </div>

      {/* Controles */}
      <div className="bg-white rounded-xl shadow-soft border border-gray-200 p-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
          {/* Búsqueda y filtros */}
          <div className="flex items-center space-x-4">
            <div className="relative">
              <Search className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
              <input
                type="text"
                placeholder="Buscar archivos..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent w-64"
              />
            </div>
            
            <select
              value={fileType}
              onChange={(e) => setFileType(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              {fileTypes.map(type => (
                <option key={type.value} value={type.value}>
                  {type.label} ({type.count})
                </option>
              ))}
            </select>
          </div>

          {/* Acciones */}
          <div className="flex items-center space-x-3">
            <button
              onClick={handleUpload}
              className="inline-flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
            >
              <Upload className="w-4 h-4 mr-2" />
              Subir Archivos
            </button>
            
            <button
              onClick={() => refetch()}
              className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Actualizar
            </button>

            {selectedFiles.size > 0 && (
              <button
                onClick={handleBulkDelete}
                className="inline-flex items-center px-3 py-2 border border-red-300 rounded-lg text-sm font-medium text-red-700 bg-white hover:bg-red-50 transition-colors"
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Eliminar ({selectedFiles.size})
              </button>
            )}
          </div>
        </div>

        {/* Selección múltiple */}
        {files && files.length > 0 && (
          <div className="mt-4 flex items-center justify-between text-sm text-gray-600">
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={selectedFiles.size === files.length}
                onChange={handleSelectAll}
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <span>
                Seleccionar todos ({selectedFiles.size} de {files.length} seleccionados)
              </span>
            </label>
            
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setViewMode('grid')}
                className={`p-2 rounded-lg ${viewMode === 'grid' ? 'bg-primary-100 text-primary-600' : 'text-gray-400 hover:text-gray-600'}`}
              >
                <div className="w-4 h-4 grid grid-cols-2 gap-0.5">
                  <div className="bg-current rounded-sm"></div>
                  <div className="bg-current rounded-sm"></div>
                  <div className="bg-current rounded-sm"></div>
                  <div className="bg-current rounded-sm"></div>
                </div>
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`p-2 rounded-lg ${viewMode === 'list' ? 'bg-primary-100 text-primary-600' : 'text-gray-400 hover:text-gray-600'}`}
              >
                <div className="w-4 h-4 flex flex-col space-y-1">
                  <div className="h-0.5 bg-current rounded"></div>
                  <div className="h-0.5 bg-current rounded"></div>
                  <div className="h-0.5 bg-current rounded"></div>
                </div>
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Lista/Grid de archivos */}
      <div className="bg-white rounded-xl shadow-soft border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-6">
          Archivos Almacenados
        </h3>

        {files && files.length > 0 ? (
          <div className={viewMode === 'grid' 
            ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
            : "space-y-4"
          }>
            {files.map((file, index) => {
              const fileIcon = getFileIcon(file.original_filename);
              const isSelected = selectedFiles.has(file.id);
              
              return viewMode === 'grid' ? (
                // Vista Grid
                <motion.div
                  key={file.id}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: index * 0.05 }}
                  className={`relative bg-white border-2 rounded-xl p-4 hover:shadow-lg transition-all cursor-pointer ${
                    isSelected ? 'border-primary-500 bg-primary-50' : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => handleFileSelect(file.id)}
                >
                  {/* Checkbox */}
                  <div className="absolute top-3 left-3">
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => handleFileSelect(file.id)}
                      className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                      onClick={(e) => e.stopPropagation()}
                    />
                  </div>

                  {/* Menú acciones */}
                  <div className="absolute top-3 right-3">
                    <button className="p-1 text-gray-400 hover:text-gray-600 rounded">
                      <MoreVertical className="w-4 h-4" />
                    </button>
                  </div>

                  {/* Icono de archivo */}
                  <div className="flex justify-center mb-4 mt-6">
                    <div className={`w-16 h-16 ${fileIcon.color} rounded-2xl flex items-center justify-center text-2xl`}>
                      {fileIcon.icon}
                    </div>
                  </div>

                  {/* Información del archivo */}
                  <div className="text-center space-y-2">
                    <h4 className="font-medium text-gray-900 text-sm truncate">
                      {file.original_filename}
                    </h4>
                    <p className="text-xs text-gray-500">
                      {formatFileSize(file.file_size || 0)}
                    </p>
                    <p className="text-xs text-gray-400">
                      {formatRelativeTime(file.upload_date)}
                    </p>
                  </div>

                  {/* Estado del archivo */}
                  {file.processing_status && (
                    <div className="mt-3 flex justify-center">
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

                  {/* Acciones rápidas */}
                  <div className="mt-4 flex justify-center space-x-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDownload(file);
                      }}
                      className="flex items-center space-x-1 px-3 py-1 text-xs font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                    >
                      <Download className="w-3 h-3" />
                      <span>Descargar</span>
                    </button>
                    
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        toast.success('Abriendo vista previa...');
                      }}
                      className="flex items-center space-x-1 px-3 py-1 text-xs font-medium text-blue-700 bg-blue-100 rounded-lg hover:bg-blue-200 transition-colors"
                    >
                      <Eye className="w-3 h-3" />
                      <span>Ver</span>
                    </button>
                  </div>
                </motion.div>
              ) : (
                // Vista Lista
                <motion.div
                  key={file.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className={`flex items-center p-4 border rounded-xl hover:shadow-md transition-all ${
                    isSelected ? 'border-primary-500 bg-primary-50' : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  {/* Checkbox */}
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => handleFileSelect(file.id)}
                    className="mr-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />

                  {/* Icono */}
                  <div className={`w-10 h-10 ${fileIcon.color} rounded-lg flex items-center justify-center mr-4`}>
                    {fileIcon.icon}
                  </div>

                  {/* Información */}
                  <div className="flex-1 min-w-0">
                    <h4 className="font-medium text-gray-900 truncate">
                      {file.original_filename}
                    </h4>
                    <div className="flex items-center space-x-4 text-sm text-gray-500">
                      <span>{formatFileSize(file.file_size || 0)}</span>
                      <span>{formatRelativeTime(file.upload_date)}</span>
                      {file.rows_count && (
                        <span>{file.rows_count} filas</span>
                      )}
                    </div>
                  </div>

                  {/* Estado */}
                  {file.processing_status && (
                    <div className="mr-4">
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

                  {/* Acciones */}
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => toast.success('Abriendo vista previa...')}
                      className="p-2 text-gray-400 hover:text-blue-600 rounded-lg hover:bg-blue-50 transition-colors"
                      title="Vista previa"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                    
                    <button
                      onClick={() => handleDownload(file)}
                      className="p-2 text-gray-400 hover:text-green-600 rounded-lg hover:bg-green-50 transition-colors"
                      title="Descargar"
                    >
                      <Download className="w-4 h-4" />
                    </button>
                    
                    <button
                      onClick={() => handleDelete(file)}
                      className="p-2 text-gray-400 hover:text-red-600 rounded-lg hover:bg-red-50 transition-colors"
                      title="Eliminar"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>

                    <button className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-50 transition-colors">
                      <MoreVertical className="w-4 h-4" />
                    </button>
                  </div>
                </motion.div>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-12">
            <Cloud className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              {searchTerm || fileType !== 'all' ? 'No se encontraron archivos' : 'No hay archivos en el almacenamiento'}
            </h3>
            <p className="text-gray-600 mb-6">
              {searchTerm || fileType !== 'all' 
                ? 'Intenta cambiar los filtros de búsqueda'
                : 'Los archivos aparecerán aquí cuando subas CSVs o generes reportes'
              }
            </p>
            {!searchTerm && fileType === 'all' && (
              <button onClick={handleUpload} className="btn-primary">
                Subir Primer Archivo
              </button>
            )}
          </div>
        )}
      </div>

      {/* Panel de información de almacenamiento */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Uso por tipo de archivo */}
        <div className="bg-white rounded-xl shadow-soft border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Distribución por Tipo
          </h3>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="w-4 h-4 bg-green-500 rounded"></div>
                <span className="text-sm font-medium">Archivos CSV</span>
              </div>
              <div className="text-right">
                <div className="text-sm font-semibold text-gray-900">{stats.csvFiles}</div>
                <div className="text-xs text-gray-500">
                  {stats.totalFiles > 0 ? Math.round((stats.csvFiles / stats.totalFiles) * 100) : 0}%
                </div>
              </div>
            </div>
            
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="w-4 h-4 bg-red-500 rounded"></div>
                <span className="text-sm font-medium">Reportes PDF</span>
              </div>
              <div className="text-right">
                <div className="text-sm font-semibold text-gray-900">{stats.pdfFiles}</div>
                <div className="text-xs text-gray-500">
                  {stats.totalFiles > 0 ? Math.round((stats.pdfFiles / stats.totalFiles) * 100) : 0}%
                </div>
              </div>
            </div>
          </div>

          {/* Barra de progreso visual */}
          <div className="mt-6">
            <div className="flex rounded-full overflow-hidden h-2 bg-gray-200">
              <div 
                className="bg-green-500 transition-all duration-300"
                style={{ width: `${stats.totalFiles > 0 ? (stats.csvFiles / stats.totalFiles) * 100 : 0}%` }}
              ></div>
              <div 
                className="bg-red-500 transition-all duration-300"
                style={{ width: `${stats.totalFiles > 0 ? (stats.pdfFiles / stats.totalFiles) * 100 : 0}%` }}
              ></div>
            </div>
          </div>
        </div>

        {/* Estadísticas adicionales */}
        <div className="bg-white rounded-xl shadow-soft border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Estadísticas de Storage
          </h3>
          
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Archivo más grande</span>
              <span className="text-sm font-semibold text-gray-900">
                {files && files.length > 0 
                  ? formatFileSize(Math.max(...files.map(f => f.file_size || 0)))
                  : '0 B'
                }
              </span>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Tamaño promedio</span>
              <span className="text-sm font-semibold text-gray-900">
                {formatFileSize(stats.averageSize)}
              </span>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Archivos procesados</span>
              <span className="text-sm font-semibold text-green-600">
                {files?.filter(f => f.processing_status === 'completed').length || 0}
              </span>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Límite de almacenamiento</span>
              <span className="text-sm font-semibold text-blue-600">
                1 GB disponible
              </span>
            </div>
          </div>

          {/* Progreso de uso */}
          <div className="mt-6">
            <div className="flex justify-between text-sm text-gray-600 mb-2">
              <span>Espacio usado</span>
              <span>{Math.round((stats.totalSize / (1024 * 1024 * 1024)) * 100 * 100) / 100}% de 1 GB</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${Math.min((stats.totalSize / (1024 * 1024 * 1024)) * 100, 100)}%` }}
              ></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Storage;