// src/pages/Reports.jsx
import React, { useState } from 'react';
import { AnimatePresence } from 'framer-motion';
import { Plus, FileText, Upload, Sparkles } from 'lucide-react';
import { useCSVFiles, useReports } from '../hooks/useReports';
import FileUpload from '../components/reports/FileUpload';
import ReportGenerator from '../components/reports/ReportGenerator';
import CSVFilesList from '../components/reports/CSVFilesList';
import ReportsList from '../components/reports/ReportsList';
import Loading from '../components/common/Loading';

const Reports = () => {
  const [activeTab, setActiveTab] = useState('upload');
  const [selectedCSVFile, setSelectedCSVFile] = useState(null);
  
  const { data: csvFiles, isLoading: csvLoading, refetch: refetchCSV } = useCSVFiles();
  const { data: reports, isLoading: reportsLoading, refetch: refetchReports } = useReports();

  const tabs = [
    { id: 'upload', label: 'Subir Archivo', icon: Upload },
    { id: 'generate', label: 'Generar Reporte', icon: Sparkles },
    { id: 'files', label: 'Mis Archivos', icon: FileText },
  ];

  const handleFileUploaded = (file) => {
    refetchCSV();
    setSelectedCSVFile(file);
    setActiveTab('generate');
  };

  const handleReportGenerated = () => {
    refetchReports();
  };

  if (csvLoading || reportsLoading) {
    return <Loading fullScreen text="Cargando reportes..." />;
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 rounded-2xl p-8 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">Centro de Reportes</h1>
            <p className="text-purple-100 text-lg">
              Sube tus datos CSV y genera reportes inteligentes con IA
            </p>
          </div>
          <div className="hidden md:block">
            <div className="w-20 h-20 bg-white/20 rounded-2xl flex items-center justify-center">
              <FileText className="w-10 h-10" />
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white rounded-xl shadow-soft border border-gray-200 p-2">
        <nav className="flex space-x-2">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center space-x-2 px-4 py-3 rounded-lg font-medium transition-all duration-200 ${
                activeTab === tab.id
                  ? 'bg-primary-500 text-white shadow-md'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              }`}
            >
              <tab.icon className="w-5 h-5" />
              <span>{tab.label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.3 }}
        >
          {activeTab === 'upload' && (
            <div className="space-y-6">
              <FileUpload onFileUploaded={handleFileUploaded} />
              
              {/* Stats */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-white rounded-xl shadow-soft border border-gray-200 p-6 text-center">
                  <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center mx-auto mb-4">
                    <Upload className="w-6 h-6 text-blue-600" />
                  </div>
                  <h3 className="font-semibold text-gray-900 mb-2">Formatos Soportados</h3>
                  <p className="text-gray-600 text-sm">CSV, XLS, XLSX</p>
                </div>
                
                <div className="bg-white rounded-xl shadow-soft border border-gray-200 p-6 text-center">
                  <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center mx-auto mb-4">
                    <Sparkles className="w-6 h-6 text-green-600" />
                  </div>
                  <h3 className="font-semibold text-gray-900 mb-2">IA Avanzada</h3>
                  <p className="text-gray-600 text-sm">Análisis automático</p>
                </div>
                
                <div className="bg-white rounded-xl shadow-soft border border-gray-200 p-6 text-center">
                  <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center mx-auto mb-4">
                    <FileText className="w-6 h-6 text-purple-600" />
                  </div>
                  <h3 className="font-semibold text-gray-900 mb-2">PDF Profesional</h3>
                  <p className="text-gray-600 text-sm">Reportes ejecutivos</p>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'generate' && (
            <ReportGenerator 
              csvFiles={csvFiles?.results || []}
              selectedFile={selectedCSVFile}
              onReportGenerated={handleReportGenerated}
            />
          )}

          {activeTab === 'files' && (
            <CSVFilesList 
              csvFiles={csvFiles?.results || []}
              onFileSelect={setSelectedCSVFile}
              onRefresh={refetchCSV}
            />
          )}
        </motion.div>
      </AnimatePresence>

      {/* Recent Reports */}
      <div className="bg-white rounded-xl shadow-soft border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-gray-900">Reportes Recientes</h3>
          <button
            onClick={() => setActiveTab('generate')}
            className="btn-primary flex items-center space-x-2"
          >
            <Plus className="w-4 h-4" />
            <span>Nuevo Reporte</span>
          </button>
        </div>
        
        <ReportsList reports={reports?.results || []} />
      </div>
    </div>
  );
};

export default Reports;