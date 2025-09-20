// src/pages/Dashboard.jsx
import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  BarChart3, 
  TrendingUp, 
  FileText, 
  Upload,
  ArrowUpRight,
  ArrowDownRight,
  Plus,
  RefreshCw,
  Calendar,
  Activity,
  Users,
  Target,
  Zap,
  Eye,
  Download
} from 'lucide-react';
import { 
  useDashboardStats, 
  useRecentReports, 
  useRecentActivity
} from '../hooks/useReports';
import { useSafeDashboardStats } from '../hooks/useSafeQuery';
import DashboardCard from '../components/dashboard/DashboardCard';
import QuickActions from '../components/dashboard/QuickActions';
import RecentReports from '../components/dashboard/RecentReports';
import Loading from '../components/common/Loading';
import FileUpload from '../components/reports/FileUpload';
import { formatCurrency, formatNumber } from '../utils/helpers';
import toast from 'react-hot-toast';

const Dashboard = () => {
  const [showUpload, setShowUpload] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  
  const { data: stats, isLoading: statsLoading, error: statsError } = useSafeDashboardStats();
  const { data: recentReports, isLoading: reportsLoading } = useRecentReports(5);
  const { data: recentActivity, isLoading: activityLoading } = useRecentActivity(8);

  const handleRefreshDashboard = async () => {
    setRefreshing(true);
    try {
      // Simular actualización
      await new Promise(resolve => setTimeout(resolve, 1500));
      toast.success('Dashboard actualizado');
    } catch (error) {
      toast.error('Error al actualizar');
    } finally {
      setRefreshing(false);
    }
  };

  const handleQuickAction = (action) => {
    switch (action) {
      case 'upload':
        setShowUpload(true);
        break;
      case 'create-report':
        window.location.href = '/app/reports';
        break;
      case 'view-history':
        window.location.href = '/app/history';
        break;
      case 'view-storage':
        window.location.href = '/app/storage';
        break;
      default:
        toast.info(`Acción ${action} en desarrollo`);
    }
  };

  const handleUploadComplete = (uploadedFiles) => {
    setShowUpload(false);
    toast.success(`${uploadedFiles.length} archivo(s) subido(s) exitosamente`);
    // Aquí podrías refrescar las estadísticas
  };

  if (statsLoading) {
    return <Loading fullScreen text="Cargando dashboard..." />;
  }

  // Datos para las tarjetas principales
  const dashboardCards = [
    {
      title: 'Total Reportes',
      value: formatNumber(stats.totalReports),
      icon: FileText,
      trend: { value: 12, isPositive: true, label: 'vs mes anterior' },
      color: 'blue',
      description: 'Reportes generados',
      action: { label: 'Ver todos', onClick: () => handleQuickAction('view-history') }
    },
    {
      title: 'Archivos CSV',
      value: formatNumber(stats.totalFiles),
      icon: Upload,
      trend: { value: 5, isPositive: true, label: 'nuevos esta semana' },
      color: 'green',
      description: 'Archivos almacenados',
      action: { label: 'Ver storage', onClick: () => handleQuickAction('view-storage') }
    },
    {
      title: 'Recomendaciones',
      value: formatNumber(stats.totalRecommendations),
      icon: Target,
      trend: { value: 8, isPositive: true, label: 'implementadas' },
      color: 'purple',
      description: 'Total identificadas',
      action: { label: 'Ver detalles', onClick: () => toast.info('Función en desarrollo') }
    },
    {
      title: 'Ahorro Estimado',
      value: formatCurrency(stats.potentialSavings),
      icon: TrendingUp,
      trend: { value: 23, isPositive: true, label: 'vs proyección anterior' },
      color: 'orange',
      description: 'Potencial mensual',
      action: { label: 'Ver análisis', onClick: () => toast.info('Función en desarrollo') }
    }
  ];

  // Acciones rápidas disponibles
  const quickActions = [
    {
      title: 'Subir CSV',
      description: 'Sube archivos de Azure Advisor',
      icon: Upload,
      color: 'blue',
      action: () => handleQuickAction('upload')
    },
    {
      title: 'Crear Reporte',
      description: 'Genera análisis inteligente',
      icon: BarChart3,
      color: 'purple',
      action: () => handleQuickAction('create-report')
    },
    {
      title: 'Ver Historial',
      description: 'Revisa reportes anteriores',
      icon: Activity,
      color: 'green',
      action: () => handleQuickAction('view-history')
    },
    {
      title: 'Gestionar Archivos',
      description: 'Administra tu almacenamiento',
      icon: FileText,
      color: 'orange',
      action: () => handleQuickAction('view-storage')
    }
  ];

  return (
    <div className="space-y-8">
      {/* Header del Dashboard */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl p-8 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">¡Bienvenido de vuelta!</h1>
            <p className="text-blue-100 text-lg">
              Analiza tus datos de Azure Advisor y genera reportes inteligentes
            </p>
          </div>
          <div className="hidden md:flex items-center space-x-4">
            <button
              onClick={handleRefreshDashboard}
              disabled={refreshing}
              className="p-3 bg-white/20 rounded-xl hover:bg-white/30 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-6 h-6 ${refreshing ? 'animate-spin' : ''}`} />
            </button>
            <div className="w-16 h-16 bg-white/20 rounded-2xl flex items-center justify-center">
              <BarChart3 className="w-8 h-8" />
            </div>
          </div>
        </div>
      </div>

      {/* Tarjetas de estadísticas principales */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {dashboardCards.map((card, index) => (
          <motion.div
            key={card.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <DashboardCard {...card} />
          </motion.div>
        ))}
      </div>

      {/* Acciones rápidas */}
      <div className="bg-white rounded-xl shadow-soft border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
              <Zap className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Acciones Rápidas</h3>
              <p className="text-sm text-gray-500">Tareas frecuentes al alcance de un clic</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {quickActions.map((action, index) => (
            <motion.button
              key={action.title}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.3 + index * 0.1 }}
              onClick={action.action}
              className="p-4 border border-gray-200 rounded-xl hover:shadow-md hover:border-gray-300 transition-all text-left group"
            >
              <div className="flex items-center space-x-3 mb-2">
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                  action.color === 'blue' ? 'bg-blue-100 text-blue-600' :
                  action.color === 'purple' ? 'bg-purple-100 text-purple-600' :
                  action.color === 'green' ? 'bg-green-100 text-green-600' :
                  'bg-orange-100 text-orange-600'
                } group-hover:scale-110 transition-transform`}>
                  <action.icon className="w-4 h-4" />
                </div>
                <ArrowUpRight className="w-4 h-4 text-gray-400 group-hover:text-gray-600 transition-colors" />
              </div>
              <h4 className="font-medium text-gray-900 mb-1">{action.title}</h4>
              <p className="text-sm text-gray-500">{action.description}</p>
            </motion.button>
          ))}
        </div>
      </div>

      {/* Contenido principal en dos columnas */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Reportes recientes */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-xl shadow-soft border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-green-100 rounded-xl flex items-center justify-center">
                  <FileText className="w-5 h-5 text-green-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Reportes Recientes</h3>
                  <p className="text-sm text-gray-500">Tus últimos análisis generados</p>
                </div>
              </div>
              <button
                onClick={() => handleQuickAction('view-history')}
                className="text-sm text-blue-600 hover:text-blue-700 font-medium"
              >
                Ver todos
              </button>
            </div>

            {reportsLoading ? (
              <div className="space-y-4">
                {[1, 2, 3].map(i => (
                  <div key={i} className="animate-pulse">
                    <div className="flex items-center space-x-4 p-4 border border-gray-200 rounded-lg">
                      <div className="w-10 h-10 bg-gray-200 rounded-lg"></div>
                      <div className="flex-1 space-y-2">
                        <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                        <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : recentReports && recentReports.length > 0 ? (
              <div className="space-y-4">
                {recentReports.map((report, index) => (
                  <motion.div
                    key={report.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-center space-x-4">
                      <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                        <FileText className="w-5 h-5 text-blue-600" />
                      </div>
                      <div>
                        <h4 className="font-medium text-gray-900 truncate">
                          {report.title}
                        </h4>
                        <div className="flex items-center space-x-2 text-sm text-gray-500">
                          <span>{report.status === 'completed' ? 'Completado' : 'En proceso'}</span>
                          <span>•</span>
                          <span>hace {Math.floor(Math.random() * 24)} horas</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => toast.success('Abriendo vista previa...')}
                        className="p-2 text-gray-400 hover:text-blue-600 rounded-lg hover:bg-blue-50 transition-colors"
                        title="Vista previa"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => toast.success('Descargando reporte...')}
                        className="p-2 text-gray-400 hover:text-green-600 rounded-lg hover:bg-green-50 transition-colors"
                        title="Descargar"
                      >
                        <Download className="w-4 h-4" />
                      </button>
                    </div>
                  </motion.div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <FileText className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                <h4 className="text-sm font-medium text-gray-900 mb-2">
                  No hay reportes aún
                </h4>
                <p className="text-sm text-gray-500 mb-4">
                  Genera tu primer reporte desde un archivo CSV
                </p>
                <button
                  onClick={() => handleQuickAction('create-report')}
                  className="btn-primary btn-sm"
                >
                  Crear Reporte
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Actividad reciente y estadísticas */}
        <div className="space-y-6">
          {/* Actividad reciente */}
          <div className="bg-white rounded-xl shadow-soft border border-gray-200 p-6">
            <div className="flex items-center space-x-3 mb-6">
              <div className="w-10 h-10 bg-orange-100 rounded-xl flex items-center justify-center">
                <Activity className="w-5 h-5 text-orange-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Actividad Reciente</h3>
                <p className="text-sm text-gray-500">Últimas acciones realizadas</p>
              </div>
            </div>

            {activityLoading ? (
              <div className="space-y-3">
                {[1, 2, 3, 4].map(i => (
                  <div key={i} className="animate-pulse flex items-center space-x-3">
                    <div className="w-8 h-8 bg-gray-200 rounded-full"></div>
                    <div className="flex-1 space-y-1">
                      <div className="h-3 bg-gray-200 rounded w-3/4"></div>
                      <div className="h-2 bg-gray-200 rounded w-1/2"></div>
                    </div>
                  </div>
                ))}
              </div>
            ) : recentActivity && recentActivity.length > 0 ? (
              <div className="space-y-3">
                {recentActivity.map((activity, index) => (
                  <motion.div
                    key={activity.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="flex items-center space-x-3 p-2 rounded-lg hover:bg-gray-50"
                  >
                    <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                      <Activity className="w-4 h-4 text-blue-600" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-900 truncate">
                        {activity.description}
                      </p>
                      <p className="text-xs text-gray-500">
                        {activity.timestamp ? 'Hace ' + Math.floor(Math.random() * 60) + ' min' : 'Ahora'}
                      </p>
                    </div>
                  </motion.div>
                ))}
              </div>
            ) : (
              <div className="text-center py-6">
                <Activity className="w-8 h-8 text-gray-300 mx-auto mb-2" />
                <p className="text-sm text-gray-500">No hay actividad reciente</p>
              </div>
            )}
          </div>

          {/* Resumen de tendencias */}
          <div className="bg-white rounded-xl shadow-soft border border-gray-200 p-6">
            <div className="flex items-center space-x-3 mb-4">
              <div className="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center">
                <TrendingUp className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Tendencias</h3>
                <p className="text-sm text-gray-500">Resumen semanal</p>
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Reportes generados</span>
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-semibold text-gray-900">+{Math.floor(Math.random() * 10) + 1}</span>
                  <ArrowUpRight className="w-4 h-4 text-green-500" />
                </div>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Archivos procesados</span>
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-semibold text-gray-900">+{Math.floor(Math.random() * 5) + 1}</span>
                  <ArrowUpRight className="w-4 h-4 text-green-500" />
                </div>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Recomendaciones</span>
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-semibold text-gray-900">+{Math.floor(Math.random() * 20) + 5}</span>
                  <ArrowUpRight className="w-4 h-4 text-green-500" />
                </div>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Ahorro potencial</span>
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-semibold text-gray-900">+{Math.floor(Math.random() * 15) + 5}%</span>
                  <ArrowUpRight className="w-4 h-4 text-green-500" />
                </div>
              </div>
            </div>
          </div>

          {/* Consejos rápidos */}
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl p-6 border border-blue-200">
            <div className="flex items-center space-x-3 mb-4">
              <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
                <Users className="w-4 h-4 text-white" />
              </div>
              <h3 className="font-semibold text-gray-900">Consejo del Día</h3>
            </div>
            <p className="text-sm text-gray-700 mb-4">
              Para obtener mejores análisis, asegúrate de subir archivos CSV de Azure Advisor 
              actualizados regularmente. Esto mejora la precisión de las recomendaciones.
            </p>
            <button
              onClick={() => handleQuickAction('upload')}
              className="text-sm text-blue-600 hover:text-blue-700 font-medium"
            >
              Subir archivo ahora →
            </button>
          </div>
        </div>
      </div>

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

export default Dashboard;