/* eslint-disable no-unused-vars */
// src/components/reports/ReportsList.jsx
import React from 'react';
import { Link } from 'react-router-dom';
import { 
  FileText, 
  Download, 
  Eye, 
  MoreHorizontal,
  Calendar,
  Clock,
  User,
  BarChart3
} from 'lucide-react';
import { formatRelativeTime, formatReportType } from '../../utils/formatters';
import { getStatusColor, getStatusIcon } from '../../utils/formatters';
import { downloadFile } from '../../utils/helpers';
import { reportService } from '../../services/reportsService';
import toast from 'react-hot-toast';

const ReportsList = ({ reports = [] }) => {
  const handleDownload = async (report) => {
    try {
      const blob = await reportService.downloadReport(report.id);
      downloadFile(blob, `${report.title}.pdf`);
      toast.success('Reporte descargado exitosamente');
    } catch (_error) {
      toast.error('Error al descargar el reporte');
    }
  };

  const handlePreview = async (report) => {
    try {
      const preview = await reportService.getReportPreview(report.id);
      // Abrir en nueva ventana o modal
      const newWindow = window.open('', '_blank');
      newWindow.document.write(preview.html_content || preview.preview_url);
    } catch (_error) {
      toast.error('Error al obtener preview');
    }
  };

  if (reports.length === 0) {
    return (
      <div className="text-center py-12">
        <BarChart3 className="w-16 h-16 text-gray-300 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          No hay reportes aún
        </h3>
        <p className="text-gray-600 mb-6">
          Genera tu primer reporte a partir de un archivo CSV
        </p>
        <Link to="/app/reports" className="btn-primary">
          Crear Reporte
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {reports.map((report, index) => (
        <motion.div
          key={report.id}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.1 }}
          className="bg-white rounded-xl shadow-soft border border-gray-200 p-6 hover:shadow-medium transition-shadow"
        >
          <div className="flex items-center justify-between">
            {/* Información del reporte */}
            <div className="flex items-center space-x-4 flex-1 min-w-0">
              <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl flex items-center justify-center">
                <FileText className="w-6 h-6 text-white" />
              </div>
              
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2 mb-1">
                  <h3 className="font-semibold text-gray-900 truncate">
                    {report.title}
                  </h3>
                  <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(report.status)}`}>
                    <span className="mr-1">{getStatusIcon(report.status)}</span>
                    {report.status}
                  </span>
                </div>
                
                <div className="flex items-center space-x-4 text-sm text-gray-500">
                  <div className="flex items-center">
                    <User className="w-4 h-4 mr-1" />
                    <span>{report.user_name || 'Usuario'}</span>
                  </div>
                  <div className="flex items-center">
                    <Calendar className="w-4 h-4 mr-1" />
                    <span>{formatRelativeTime(report.created_at)}</span>
                  </div>
                  <div className="flex items-center">
                    <BarChart3 className="w-4 h-4 mr-1" />
                    <span>{formatReportType(report.report_type)}</span>
                  </div>
                  {report.generation_time_seconds && (
                    <div className="flex items-center">
                      <Clock className="w-4 h-4 mr-1" />
                      <span>{report.generation_time_seconds}s</span>
                    </div>
                  )}
                </div>

                {report.description && (
                  <p className="text-sm text-gray-600 mt-2 truncate">
                    {report.description}
                  </p>
                )}

                {/* Análisis summary */}
                {report.analysis_summary && (
                  <div className="flex items-center space-x-4 mt-3 text-xs">
                    <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                      {report.analysis_summary.total_recommendations} recomendaciones
                    </span>
                    {report.analysis_summary.cost_savings_identified && (
                      <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full">
                        Ahorros identificados
                      </span>
                    )}
                    {report.analysis_summary.security_issues_found > 0 && (
                      <span className="bg-orange-100 text-orange-800 px-2 py-1 rounded-full">
                        {report.analysis_summary.security_issues_found} problemas de seguridad
                      </span>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Acciones */}
            <div className="flex items-center space-x-2 ml-4">
              {report.status === 'completed' && (
                <>
                  <button
                    onClick={() => handlePreview(report)}
                    className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
                    title="Vista previa"
                  >
                    <Eye className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDownload(report)}
                    className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
                    title="Descargar PDF"
                  >
                    <Download className="w-4 h-4" />
                  </button>
                </>
              )}
              
              {report.status === 'generating' && (
                <div className="flex items-center space-x-2 text-sm text-blue-600">
                  <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                  <span>Generando...</span>
                </div>
              )}
              
              <button className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100">
                <MoreHorizontal className="w-4 h-4" />
              </button>
            </div>
          </div>
        </motion.div>
      ))}
    </div>
  );
};

export default ReportsList;