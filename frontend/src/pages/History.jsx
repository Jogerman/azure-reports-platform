// src/pages/History.jsx
import React, { useState } from 'react';
import { 
  History as HistoryIcon, 
  Search, 
  Filter,
  Calendar,
  Download,
  Trash2
} from 'lucide-react';
import { useReports } from '../hooks/useReports';
import ReportsList from '../components/reports/ReportsList';
import Loading from '../components/common/Loading';
import { REPORT_TYPES, REPORT_STATUS } from '../utils/constants';

const History = () => {
  const [filters, setFilters] = useState({
    search: '',
    status: '',
    report_type: '',
    date_range: '',
  });
  
  const { data: reports, isLoading, refetch } = useReports(filters);

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  if (isLoading) {
    return <Loading fullScreen text="Cargando historial..." />;
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-2xl p-8 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">Historial de Reportes</h1>
            <p className="text-indigo-100 text-lg">
              Revisa, descarga y gestiona todos tus reportes generados
            </p>
          </div>
          <div className="hidden md:block">
            <div className="w-20 h-20 bg-white/20 rounded-2xl flex items-center justify-center">
              <HistoryIcon className="w-10 h-10" />
            </div>
          </div>
        </div>
      </div>

      {/* Filtros y búsqueda */}
      <div className="bg-white rounded-xl shadow-soft border border-gray-200 p-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Búsqueda */}
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="text"
              placeholder="Buscar reportes..."
              className="input-field pl-10"
              value={filters.search}
              onChange={(e) => handleFilterChange('search', e.target.value)}
            />
          </div>

          {/* Filtro por estado */}
          <select
            className="input-field"
            value={filters.status}
            onChange={(e) => handleFilterChange('status', e.target.value)}
          >
            <option value="">Todos los estados</option>
            {Object.entries(REPORT_STATUS).map(([key, label]) => (
              <option key={key} value={key}>{label}</option>
            ))}
          </select>

          {/* Filtro por tipo */}
          <select
            className="input-field"
            value={filters.report_type}
            onChange={(e) => handleFilterChange('report_type', e.target.value)}
          >
            <option value="">Todos los tipos</option>
            {Object.entries(REPORT_TYPES).map(([key, label]) => (
              <option key={key} value={key}>{label}</option>
            ))}
          </select>

          {/* Acciones */}
          <div className="flex items-center space-x-2">
            <button className="btn-secondary flex items-center space-x-2 flex-1">
              <Filter className="w-4 h-4" />
              <span>Filtros</span>
            </button>
            <button
              onClick={refetch}
              className="btn-ghost p-3"
              title="Actualizar"
            >
              <Download className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Estadísticas rápidas */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {[
          {
            label: 'Total Reportes',
            value: reports?.count || 0,
            color: 'bg-blue-500',
          },
          {
            label: 'Completados',
            value: reports?.results?.filter(r => r.status === 'completed').length || 0,
            color: 'bg-green-500',
          },
          {
            label: 'En Proceso',
            value: reports?.results?.filter(r => r.status === 'generating').length || 0,
            color: 'bg-yellow-500',
          },
          {
            label: 'Este Mes',
            value: reports?.results?.filter(r => {
              const reportDate = new Date(r.created_at);
              const now = new Date();
              return reportDate.getMonth() === now.getMonth() && reportDate.getFullYear() === now.getFullYear();
            }).length || 0,
            color: 'bg-purple-500',
          },
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
                <p className="text-3xl font-bold text-gray-900">{stat.value}</p>
              </div>
              <div className={`w-12 h-12 ${stat.color} rounded-xl flex items-center justify-center`}>
                <HistoryIcon className="w-6 h-6 text-white" />
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Lista de reportes */}
      <div className="bg-white rounded-xl shadow-soft border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-gray-900">
            Todos los Reportes ({reports?.count || 0})
          </h3>
        </div>
        
        <ReportsList reports={reports?.results || []} />
        
        {/* Paginación */}
        {reports?.count > 20 && (
          <div className="mt-8 flex items-center justify-center">
            <nav className="flex items-center space-x-2">
              <button className="btn-secondary">Anterior</button>
              <span className="text-sm text-gray-600">Página 1 de {Math.ceil(reports.count / 20)}</span>
              <button className="btn-secondary">Siguiente</button>
            </nav>
          </div>
        )}
      </div>
    </div>
  );
};

export default History;