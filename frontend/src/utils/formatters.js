// src/utils/formatters.js
// Formatters específicos para datos de reportes

export const formatAnalysisData = (analysis) => {
  if (!analysis) return null;
  
  return {
    totalRows: analysis.basic_stats?.total_rows || 0,
    totalColumns: analysis.basic_stats?.total_columns || 0,
    dataQualityScore: analysis.data_quality?.completeness_score || 0,
    recommendations: analysis.recommendations || [],
    categories: analysis.categories || {},
    costAnalysis: analysis.cost_analysis || {},
    securityAnalysis: analysis.security_analysis || {},
  };
};

export const getStatusColor = (status) => {
  const statusColors = {
    // CSV Status
    pending: 'text-yellow-600 bg-yellow-100',
    processing: 'text-blue-600 bg-blue-100',
    completed: 'text-green-600 bg-green-100',
    failed: 'text-red-600 bg-red-100',
    
    // Report Status
    generating: 'text-blue-600 bg-blue-100',
    expired: 'text-gray-600 bg-gray-100',
  };
  
  return statusColors[status] || 'text-gray-600 bg-gray-100';
};

export const getStatusIcon = (status) => {
  const statusIcons = {
    pending: '⏳',
    processing: '🔄',
    completed: '✅',
    failed: '❌',
    generating: '🔄',
    expired: '⏰',
  };
  
  return statusIcons[status] || '❓';
};

export const formatReportType = (type) => {
  const types = {
    executive: 'Ejecutivo',
    detailed: 'Detallado',
    summary: 'Resumen',
    custom: 'Personalizado',
  };
  
  return types[type] || type;
};

export const formatCurrency = (amount, currency = 'USD') => {
  if (amount === null || amount === undefined) return '';
  
  return new Intl.NumberFormat('es-ES', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
};

export const formatDataQualityScore = (score) => {
  if (score >= 90) return { color: 'text-green-600', label: 'Excelente' };
  if (score >= 70) return { color: 'text-yellow-600', label: 'Buena' };
  if (score >= 50) return { color: 'text-orange-600', label: 'Regular' };
  return { color: 'text-red-600', label: 'Pobre' };
};
