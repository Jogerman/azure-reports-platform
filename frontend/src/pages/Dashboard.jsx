// src/pages/Dashboard.jsx
import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  FileText, 
  Upload, 
  BarChart3, 
  Shield, 
  TrendingUp, 
  Clock,
  Plus,
  Download,
  Eye,
  AlertCircle
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useDashboardStats, useRecentReports, useRecentActivity } from '../hooks/useReports';
import { useNavigate } from 'react-router-dom';
import Loading from '../components/common/Loading';

// Componente para tarjetas de estadísticas
const StatCard = ({ title, value, icon: Icon, trend, color = "blue" }) => {
  const colorClasses = {
    blue: "from-blue-500 to-blue-600",
    green: "from-green-500 to-green-600", 
    purple: "from-purple-500 to-purple-600",
    orange: "from-orange-500 to-orange-600"
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-xl shadow-soft border border-gray-200 p-6 hover:shadow-medium transition-shadow"
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600 mb-1">{title}</p>
          <p className="text-3xl font-bold text-gray-900">{value}</p>
          {trend && (
            <div className="flex items-center mt-2">
              <TrendingUp className="w-4 h-4 text-green-500 mr-1" />
              <span className="text-sm text-green-600">{trend}</span>
            </div>
          )}
        </div>
        <div className={`w-16 h-16 bg-gradient-to-r ${colorClasses[color]} rounded-xl flex items-center justify-center`}>
          <Icon className="w-8 h-8 text-white" />
        </div>
      </div>
    </motion.div>
  );
};

// Componente para la acción rápida de crear reporte
const QuickActionCard = ({ title, description, icon: Icon, onClick, color = "blue" }) => {
  const colorClasses = {
    blue: "hover:from-blue-50 hover:to-blue-100 hover:border-blue-200",
    green: "hover:from-green-50 hover:to-green-100 hover:border-green-200",
    purple: "hover:from-purple-50 hover:to-purple-100 hover:border-purple-200"
  };

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className={`bg-white rounded-xl shadow-soft border-2 border-gray-200 p-6 cursor-pointer transition-all duration-200 ${colorClasses[color]}`}
    >
      <div className="flex items-start space-x-4">
        <div className="flex-shrink-0">
          <div className="w-12 h-12 bg-gradient-to-r from-primary-500 to-secondary-500 rounded-lg flex items-center justify-center">
            <Icon className="w-6 h-6 text-white" />
          </div>
        </div>
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-1">{title}</h3>
          <p className="text-gray-600">{description}</p>
        </div>
        <Plus className="w-5 h-5 text-gray-400" />
      </div>
    </motion.div>
  );
};

// Componente para lista de reportes recientes
const RecentReportItem = ({ report, onView, onDownload }) => {
  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-100';
      case 'processing': return 'text-yellow-600 bg-yellow-100';
      case 'failed': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'completed': return 'Completado';
      case 'processing': return 'Procesando';
      case 'failed': return 'Error';
      default: return 'Desconocido';
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      className="flex items-center justify-between p-4 hover:bg-gray-50 rounded-lg transition-colors"
    >
      <div className="flex items-center space-x-4 flex-1">
        <div className="w-10 h-10 bg-gradient-to-r from-primary-400 to-secondary-400 rounded-lg flex items-center justify-center">
          <FileText className="w-5 h-5 text-white" />
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-medium text-gray-900 truncate">
            {report.title || `Reporte ${report.id}`}
          </h4>
          <div className="flex items-center space-x-2 mt-1">
            <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${getStatusColor(report.status)}`}>
              {getStatusText(report.status)}
            </span>
            <span className="text-xs text-gray-500">
              {report.client_name || 'Sin cliente'}
            </span>
          </div>
        </div>
      </div>
      
      <div className="flex items-center space-x-2">
        {report.status === 'completed' && (
          <>
            <button
              onClick={() => onView(report)}
              className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
              title="Ver reporte"
            >
              <Eye className="w-4 h-4" />
            </button>
            <button
              onClick={() => onDownload(report)}
              className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
              title="Descargar PDF"
            >
              <Download className="w-4 h-4" />
            </button>
          </>
        )}
        <div className="text-xs text-gray-400">
          {new Date(report.created_at).toLocaleDateString()}
        </div>
      </div>
    </motion.div>
  );
};

const Dashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [selectedTimeRange, setSelectedTimeRange] = useState('7d');

  // Hooks para datos del dashboard
  const { data: stats, isLoading: statsLoading } = useDashboardStats();
  const { data: recentReports, isLoading: reportsLoading } = useRecentReports(5);
  const { data: recentActivity, isLoading: activityLoading } = useRecentActivity(5);

  const handleCreateReport = () => {
    navigate('/reports');
  };

  const handleUploadFile = () => {
    navigate('/reports?tab=upload');
  };

  const handleViewReport = (report) => {
    navigate(`/reports/${report.id}`);
  };

  const handleDownloadReport = (report) => {
    // Implementar descarga de reporte
    console.log('Descargar reporte:', report.id);
  };

  if (statsLoading || reportsLoading || activityLoading) {
    return <Loading fullScreen text="Cargando dashboard..." />;
  }

  return (
    <div className="space-y-8">
      {/* Header de bienvenida */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-r from-primary-600 to-secondary-600 rounded-2xl p-8 text-white"
      >
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">
              ¡Bienvenido, {user?.first_name || user?.username}!
            </h1>
            <p className="text-primary-100 text-lg">
              Analiza tus datos de Azure Advisor y genera reportes inteligentes
            </p>
          </div>
          <div className="hidden md:block">
            <div className="w-20 h-20 bg-white/20 rounded-2xl flex items-center justify-center">
              <BarChart3 className="w-10 h-10" />
            </div>
          </div>
        </div>
      </motion.div>

      {/* Estadísticas principales */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Reportes"
          value={stats?.total_reports || 0}
          icon={FileText}
          trend="+12% este mes"
          color="blue"
        />
        <StatCard
          title="Archivos CSV"
          value={stats?.total_csv_files || 0}
          icon={Upload}
          trend="+5 nuevos"
          color="green"
        />
        <StatCard
          title="Recomendaciones"
          value={stats?.total_recommendations || 0}
          icon={Shield}
          trend="98% implementadas"
          color="purple"
        />
        <StatCard
          title="Ahorro Estimado"
          value={`$${stats?.estimated_savings || 0}`}
          icon={TrendingUp}
          trend="+23% vs mes anterior"
          color="orange"
        />
      </div>

      {/* Acciones rápidas */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <QuickActionCard
          title="Crear Nuevo Reporte"
          description="Genera un reporte de Azure Advisor con análisis inteligente"
          icon={FileText}
          onClick={handleCreateReport}
          color="blue"
        />
        <QuickActionCard
          title="Subir Archivo CSV"
          description="Sube un nuevo archivo CSV para análisis"
          icon={Upload}
          onClick={handleUploadFile}
          color="green"
        />
      </div>

      {/* Contenido principal en dos columnas */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Reportes recientes */}
        <div className="lg:col-span-2">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-white rounded-xl shadow-soft border border-gray-200"
          >
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-gray-900">
                  Reportes Recientes
                </h2>
                <button
                  onClick={() => navigate('/reports/history')}
                  className="text-primary-600 hover:text-primary-700 font-medium text-sm"
                >
                  Ver todos
                </button>
              </div>
            </div>
            
            <div className="p-6">
              {recentReports && recentReports.length > 0 ? (
                <div className="space-y-2">
                  {recentReports.map((report) => (
                    <RecentReportItem
                      key={report.id}
                      report={report}
                      onView={handleViewReport}
                      onDownload={handleDownloadReport}
                    />
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    No hay reportes aún
                  </h3>
                  <p className="text-gray-600 mb-6">
                    Crea tu primer reporte para comenzar
                  </p>
                  <button
                    onClick={handleCreateReport}
                    className="btn-primary"
                  >
                    Crear Reporte
                  </button>
                </div>
              )}
            </div>
          </motion.div>
        </div>

        {/* Panel lateral con actividad */}
        <div className="space-y-6">
          {/* Actividad reciente */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-white rounded-xl shadow-soft border border-gray-200"
          >
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                <Clock className="w-5 h-5 mr-2" />
                Actividad Reciente
              </h3>
            </div>
            
            <div className="p-6">
              {recentActivity && recentActivity.length > 0 ? (
                <div className="space-y-4">
                  {recentActivity.map((activity, index) => (
                    <div key={index} className="flex items-start space-x-3">
                      <div className="w-2 h-2 bg-primary-500 rounded-full mt-2 flex-shrink-0"></div>
                      <div>
                        <p className="text-sm text-gray-900">{activity.description}</p>
                        <p className="text-xs text-gray-500 mt-1">
                          {new Date(activity.timestamp).toLocaleString()}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-sm">No hay actividad reciente</p>
              )}
            </div>
          </motion.div>

          {/* Alertas o notificaciones */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-white rounded-xl shadow-soft border border-gray-200"
          >
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                <AlertCircle className="w-5 h-5 mr-2" />
                Alertas
              </h3>
            </div>
            
            <div className="p-6">
              <div className="space-y-3">
                <div className="flex items-start space-x-3 p-3 bg-yellow-50 rounded-lg">
                  <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-yellow-800">
                      Recomendaciones pendientes
                    </p>
                    <p className="text-xs text-yellow-700 mt-1">
                      Tienes 15 recomendaciones de seguridad sin implementar
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;