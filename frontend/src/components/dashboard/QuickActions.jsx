// src/components/dashboard/QuickActions.jsx
import React from 'react';
import { Link } from 'react-router-dom';
import { Upload, FileText, BarChart3, Settings, Plus } from 'lucide-react';

const QuickActions = () => {
  const actions = [
    {
      title: 'Subir CSV',
      description: 'Analizar nuevos datos',
      icon: Upload,
      href: '/app/reports',
      color: 'bg-blue-500 hover:bg-blue-600',
    },
    {
      title: 'Crear Reporte',
      description: 'Generar nuevo reporte',
      icon: FileText,
      href: '/app/reports',
      color: 'bg-green-500 hover:bg-green-600',
    },
    {
      title: 'Ver Analytics',
      description: 'Dashboard de métricas',
      icon: BarChart3,
      href: '/app/analytics',
      color: 'bg-purple-500 hover:bg-purple-600',
    },
    {
      title: 'Configuración',
      description: 'Ajustar preferencias',
      icon: Settings,
      href: '/app/settings',
      color: 'bg-gray-500 hover:bg-gray-600',
    },
  ];

  return (
    <div className="bg-white rounded-xl shadow-soft border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">
          Acciones Rápidas
        </h3>
        <Plus className="h-5 w-5 text-gray-400" />
      </div>
      
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {actions.map((action, index) => (
          <motion.div
            key={action.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <Link
              to={action.href}
              className="block p-4 rounded-lg border border-gray-200 hover:border-gray-300 transition-colors group"
            >
              <div className={`w-10 h-10 rounded-lg ${action.color} flex items-center justify-center mb-3 transition-colors`}>
                <action.icon className="w-5 h-5 text-white" />
              </div>
              <h4 className="font-medium text-gray-900 group-hover:text-gray-700">
                {action.title}
              </h4>
              <p className="text-sm text-gray-500 mt-1">
                {action.description}
              </p>
            </Link>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

export default QuickActions;