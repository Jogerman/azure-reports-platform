// src/pages/Dashboard.jsx
import React from 'react';
import { 
  FileText, 
  Upload, 
  TrendingUp, 
  Clock,
  BarChart3,
  Users,
  Database,
  Activity,
  Plus,
  Download,
  Eye,
  AlertCircle
} from 'lucide-react';
import { useReports, useCSVFiles } from '../hooks/useReports';
import { useAuth } from '../context/AuthContext';
import DashboardCard from '../components/dashboard/DashboardCard';
import RecentReports from '../components/dashboard/RecentReports';
import QuickActions from '../components/dashboard/QuickActions';
import AnalyticsChart from '../components/dashboard/AnalyticsChart';
import Loading from '../components/common/Loading';
import { formatRelativeTime } from '../utils/helpers';

const Dashboard = () => {
  const { user } = useAuth();
  const { data: reports, isLoading: reportsLoading } = useReports({ limit: 5 });
  const { data: csvFiles, isLoading: csvLoading } = useCSVFiles({ limit: 5 });

  if (reportsLoading || csvLoading) {
    return <Loading fullScreen text="Cargando dashboard..." />;
  }

  const stats = {
    total_reports: reports?.results?.length || 0,
    total_files: csvFiles?.results?.length || 0,
    avg_generation_time: 45,
    active_users: 1,
  };

  const cardVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: (i) => ({
      opacity: 1,
      y: 0,
      transition: {
        delay: i * 0.1,
        duration: 0.5,
        ease: "easeOut"
      }
    })
  };

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Buenos días';
    if (hour < 18) return 'Buenas tardes';
    return 'Buenas noches';
  };

  return (
    <div className="space-y-8">
      {/* Header de Bienvenida */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-r from-primary-600 to-secondary-600 rounded-2xl p-8 text-white relative overflow-hidden"
      >
        <div className="relative z-10">
          <h1 className="text-3xl font-bold mb-2">
            {getGreeting()}, {user?.first_name || user?.username}! 👋
          </h1>
          <p className="text-primary-100 text-lg">
            Bienvenido a tu centro de análisis de datos inteligente
          </p>
          <div className="mt-6 flex flex-wrap gap-4">
            <div className="bg-white/20 backdrop-blur-sm rounded-lg px-4 py-2">
              <span className="text-sm">Último acceso: {formatRelativeTime(user?.last_login)}</span>
            </div>
            <div className="bg-white/20 backdrop-blur-sm rounded-lg px-4 py-2">
              <span className="text-sm">Reportes generados: {stats.total_reports}</span>
            </div>
          </div>
        </div>
        
        {/* Decoración de fondo */}
        <div className="absolute top-0 right-0 w-64 h-64 opacity-10">
          <BarChart3 className="w-full h-full" />
        </div>
      </motion.div>

      {/* Tarjetas de Estadísticas */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[
          {
            title: 'Reportes Generados',
            value: stats.total_reports,
            icon: FileText,
            color: 'blue',
            change: '+12%',
            changeType: 'increase'
          },
          {
            title: 'Archivos Procesados',
            value: stats.total_files,
            icon: Database,
            color: 'green',
            change: '+8%',
            changeType: 'increase'
          },
          {
            title: 'Tiempo Promedio',
            value: `${stats.avg_generation_time}s`,
            icon: Clock,
            color: 'purple',
            change: '-5%',
            changeType: 'decrease'
          },
          {
            title: 'Usuarios Activos',
            value: stats.active_users,
            icon: Users,
            color: 'orange',
            change: '+3%',
            changeType: 'increase'
          }
        ].map((stat, index) => (
          <motion.div
            key={stat.title}
            custom={index}
            variants={cardVariants}
            initial="hidden"
            animate="visible"
          >
            <DashboardCard {...stat} />
          </motion.div>
        ))}
      </div>

      {/* Acciones Rápidas */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
      >
        <QuickActions />
      </motion.div>

      {/* Contenido Principal */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Gráfico de Analytics */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.6 }}
          className="bg-white rounded-xl shadow-soft border border-gray-200 p-6"
        >
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-gray-900">
              Actividad Reciente
            </h3>
            <BarChart3 className="h-5 w-5 text-gray-400" />
          </div>
          <AnalyticsChart />
        </motion.div>

        {/* Reportes Recientes */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.7 }}
        >
          <RecentReports reports={reports?.results || []} />
        </motion.div>
      </div>

      {/* Activity Feed */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.8 }}
        className="bg-white rounded-xl shadow-soft border border-gray-200"
      >
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center">
            <Activity className="h-5 w-5 text-gray-400 mr-2" />
            <h3 className="text-lg font-semibold text-gray-900">
              Actividad del Sistema
            </h3>
          </div>
        </div>
        <div className="p-6">
          <div className="space-y-4">
            {[
              {
                type: 'upload',
                message: 'Archivo "datos_ventas_q3.csv" procesado exitosamente',
                time: 'Hace 5 minutos',
                icon: Upload,
                color: 'text-green-600'
              },
              {
                type: 'report',
                message: 'Reporte "Análisis de Costos Azure" generado',
                time: 'Hace 15 minutos',
                icon: FileText,
                color: 'text-blue-600'
              },
              {
                type: 'insight',
                message: 'Se identificaron 3 oportunidades de ahorro',
                time: 'Hace 1 hora',
                icon: TrendingUp,
                color: 'text-purple-600'
              },
              {
                type: 'warning',
                message: 'Recomendación de seguridad: Habilitar MFA',
                time: 'Hace 2 horas',
                icon: AlertCircle,
                color: 'text-orange-600'
              }
            ].map((activity, index) => (
              <div key={index} className="flex items-start space-x-3">
                <div className={`p-2 rounded-full bg-gray-100 ${activity.color}`}>
                  <activity.icon className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-900 font-medium">
                    {activity.message}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {activity.time}
                  </p>
                </div>
              </div>
            ))}
          </div>
          
          <div className="mt-6 text-center">
            <button className="text-sm text-primary-600 hover:text-primary-700 font-medium">
              Ver toda la actividad
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default Dashboard;