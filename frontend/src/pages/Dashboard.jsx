// frontend/src/pages/Dashboard.jsx - CORREGIDO
import React, { useState } from 'react';
import { 
  BarChart3, 
  TrendingUp, 
  FileText, 
  Upload,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Info,
  Activity
} from 'lucide-react';
import { 
  useRealDashboardStats, 
  useRealActivity, 
  useHasRealData
} from '../hooks/useRealData';
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
  
  const { data: stats, isLoading: statsLoading, error: statsError, refetch: refetchStats } = useRealDashboardStats();
  const { data: recentActivity, isLoading: activityLoading, refetch: refetchActivity } = useRealActivity(8);
  const { hasRealData, dataSource, lastAnalysisDate, csvFilename, qualityScore } = useHasRealData();

  const handleRefreshDashboard = async () => {
    setRefreshing(true);
    try {
      await Promise.all([refetchStats(), refetchActivity()]);
      toast.success('🔄 Dashboard actualizado con datos reales');
    } catch (error) {
      toast.error('❌ Error al actualizar dashboard');
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
      default:
        console.log('Action:', action);
    }
  };

  const handleFileUploaded = () => {
    setShowUpload(false);
    setTimeout(() => {
      handleRefreshDashboard();
      toast.success('🎉 ¡Datos reales actualizados!');
    }, 2000);
  };

  if (statsLoading) {
    return <Loading message="Cargando análisis real de datos..." />;
  }

  if (statsError) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <div className="flex items-center gap-3">
            <AlertCircle className="h-6 w-6 text-red-600" />
            <div>
              <h3 className="text-lg font-semibold text-red-800">Error Cargando Datos</h3>
              <p className="text-red-600 mt-1">{statsError.message}</p>
              <button
                onClick={handleRefreshDashboard}
                className="mt-3 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                disabled={refreshing}
              >
                {refreshing ? 'Reintentando...' : 'Reintentar'}
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard - Análisis Real</h1>
          <div className="flex items-center gap-4 mt-2">
            {hasRealData ? (
              <div className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-green-600" />
                <span className="text-green-700 font-medium">
                  Datos reales de "{csvFilename}"
                </span>
                <span className="text-sm text-gray-500">
                  (Calidad: {qualityScore}%)
                </span>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <AlertCircle className="h-5 w-5 text-amber-600" />
                <span className="text-amber-700 font-medium">
                  Sin archivos CSV - Mostrando datos de ejemplo
                </span>
                <button
                  onClick={() => setShowUpload(true)}
                  className="ml-2 text-blue-600 hover:text-blue-700 text-sm font-medium"
                >
                  Subir CSV →
                </button>
              </div>
            )}
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          <button
            onClick={handleRefreshDashboard}
            disabled={refreshing}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            {refreshing ? 'Actualizando...' : 'Actualizar'}
          </button>
          
          <button
            onClick={() => setShowUpload(true)}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
          >
            <Upload className="w-4 h-4" />
            Subir CSV
          </button>
        </div>
      </div>

      {/* Métricas principales */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <DashboardCard
          title="Total Recomendaciones"
          value={formatNumber(stats?.total_recommendations || 0)}
          icon={FileText}
          color="blue"
          change={hasRealData ? "Datos reales" : "Esperando CSV"}
          changeType={hasRealData ? "increase" : "decrease"}
        />
        
        <DashboardCard
          title="Optimización Mensual"
          value={formatCurrency(stats?.monthly_optimization || 0)}
          icon={TrendingUp}
          color="green"
          change={hasRealData ? "Análisis real" : "Estimación"}
          changeType={hasRealData ? "increase" : "decrease"}
        />
        
        <DashboardCard
          title="Horas de Trabajo"
          value={formatNumber(stats?.working_hours || 0)}
          icon={Activity}
          color="orange"
          change={hasRealData ? "Calculado" : "Pendiente"}
          changeType={hasRealData ? "increase" : "decrease"}
        />
        
        <DashboardCard
          title="Alto Impacto"
          value={formatNumber(stats?.high_impact_actions || 0)}
          icon={AlertCircle}
          color="red"
          change={hasRealData ? "Identificados" : "N/A"}
          changeType={hasRealData ? "increase" : "decrease"}
        />
      </div>

      {/* Resto del contenido */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-6">
          <QuickActions onAction={handleQuickAction} />
        </div>
        <div className="space-y-6">
          <RecentReports />
        </div>
      </div>

      {/* Info del análisis */}
      {hasRealData && lastAnalysisDate && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <Info className="w-5 h-5 text-blue-600 mt-0.5" />
            <div>
              <h4 className="font-medium text-blue-900">Información del Análisis</h4>
              <p className="text-sm text-blue-700 mt-1">
                Último análisis: {new Date(lastAnalysisDate).toLocaleString('es-ES')}
              </p>
              <p className="text-sm text-blue-700">
                Archivo: {csvFilename} | Calidad: {qualityScore}%
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Modal de upload */}
      {showUpload && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-2xl mx-4">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-semibold text-gray-900">
                Subir Archivo CSV para Análisis Real
              </h3>
              <button
                onClick={() => setShowUpload(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            <FileUpload 
              onFileUploaded={handleFileUploaded}
              acceptedTypes=".csv"
              maxSize={50}
              instructions="Sube tu archivo CSV de Azure Advisor para análisis real."
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;