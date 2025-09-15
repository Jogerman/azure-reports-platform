// src/pages/Storage.jsx
import React, { useState } from 'react';
import { 
  Database, 
  Search, 
  Filter,
  Download,
  Trash2,
  Eye,
  File,
  Image,
  FileText
} from 'lucide-react';
import { formatRelativeTime } from '../utils/helpers';

const Storage = () => {
  const [_viewMode, _setViewMode] = useState('grid'); // 'grid' or 'list'
  const [_selectedFiles, _setSelectedFiles] = useState([]);
  
  // Mock data - replace with actual API call
  const files = [
    {
      id: 1,
      name: 'ventas_q3_2024.csv',
      type: 'csv',
      size: 2048576,
      url: '#',
      uploadDate: '2024-01-15T10:30:00Z',
      accessCount: 5,
    },
    {
      id: 2,
      name: 'reporte_costos_azure.pdf',
      type: 'pdf',
      size: 5242880,
      url: '#',
      uploadDate: '2024-01-14T15:45:00Z',
      accessCount: 12,
    },
    {
      id: 3,
      name: 'dashboard_screenshot.png',
      type: 'image',
      size: 1048576,
      url: '#',
      uploadDate: '2024-01-13T09:15:00Z',
      accessCount: 3,
    }
  ];

  const getFileIcon = (type) => {
    switch (type) {
      case 'csv':
        return <Database className="w-8 h-8 text-green-600" />;
      case 'pdf':
        return <FileText className="w-8 h-8 text-red-600" />;
      case 'image':
        return <Image className="w-8 h-8 text-blue-600" />;
      default:
        return <File className="w-8 h-8 text-gray-600" />;
    }
  };

  const getFileTypeColor = (type) => {
    switch (type) {
      case 'csv':
        return 'bg-green-100 text-green-800';
      case 'pdf':
        return 'bg-red-100 text-red-800';
      case 'image':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-green-600 to-teal-600 rounded-2xl p-8 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">Almacenamiento</h1>
            <p className="text-green-100 text-lg">
              Gestiona todos tus archivos y documentos de forma segura
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
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {[
          { label: 'Archivos Totales', value: '24', color: 'bg-blue-500' },
          { label: 'Espacio Usado', value: '2.4 GB', color: 'bg-green-500' },
          { label: 'Archivos CSV', value: '12', color: 'bg-purple-500' },
          { label: 'Reportes PDF', value: '8', color: 'bg-orange-500' },
        ].map((stat, index) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="bg-white rounded-xl shadow-soft border border-gray-200 p-6"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">{stat.label}</p>
                <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
              </div>
              <div className={`w-10 h-10 ${stat.color} rounded-xl flex items-center justify-center`}>
                <Database className="w-5 h-5 text-white" />
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Controles */}
      <div className="bg-white rounded-xl shadow-soft border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-gray-900">Mis Archivos</h3>
          <div className="flex items-center space-x-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Buscar archivos..."
                className="input-field pl-10 w-64"
              />
            </div>
            <button className="btn-secondary flex items-center space-x-2">
              <Filter className="w-4 h-4" />
              <span>Filtros</span>
            </button>
          </div>
        </div>

        {/* Lista de archivos */}
        <div className="space-y-4">
          {files.map((file, index) => (
            <motion.div
              key={file.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:border-gray-300 transition-colors"
            >
              <div className="flex items-center space-x-4 flex-1">
                <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
                  {getFileIcon(file.type)}
                </div>
                
                <div className="flex-1 min-w-0">
                  <h4 className="font-medium text-gray-900 truncate">{file.name}</h4>
                  <div className="flex items-center space-x-4 text-sm text-gray-500">
                    <span>{formatFileSize(file.size)}</span>
                    <span>•</span>
                    <span>{formatRelativeTime(file.uploadDate)}</span>
                    <span>•</span>
                    <span>{file.accessCount} accesos</span>
                  </div>
                </div>
                
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getFileTypeColor(file.type)}`}>
                  {file.type.toUpperCase()}
                </span>
              </div>
              
              <div className="flex items-center space-x-2 ml-4">
                <button className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100">
                  <Eye className="w-4 h-4" />
                </button>
                <button className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100">
                  <Download className="w-4 h-4" />
                </button>
                <button className="p-2 text-gray-400 hover:text-red-600 rounded-lg hover:bg-red-50">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Storage;