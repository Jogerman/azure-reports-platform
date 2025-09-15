// src/pages/LandingPage.jsx
import React, { useState } from 'react';
import { Navigate } from 'react-router-dom';
import { 
  BarChart3, 
  Upload, 
  FileText, 
  TrendingUp, 
  Shield, 
  Zap,
  CheckCircle,
  ArrowRight,
  Play,
  Star
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import LoginForm from '../components/auth/LoginForm';
import RegisterForm from '../components/auth/RegisterForm';

const LandingPage = () => {
  const { isAuthenticated } = useAuth();
  const [showLogin, setShowLogin] = useState(true);

  if (isAuthenticated) {
    return <Navigate to="/app" replace />;
  }

  const features = [
    {
      icon: Upload,
      title: 'Carga Rápida',
      description: 'Sube tus archivos CSV de forma simple y segura'
    },
    {
      icon: BarChart3,
      title: 'Análisis Inteligente',
      description: 'IA avanzada para generar insights automáticamente'
    },
    {
      icon: FileText,
      title: 'Reportes Ejecutivos',
      description: 'Documentos profesionales listos para presentar'
    },
    {
      icon: Shield,
      title: 'Seguridad Azure',
      description: 'Tus datos protegidos con la mejor tecnología'
    },
    {
      icon: TrendingUp,
      title: 'Optimización',
      description: 'Identifica oportunidades de mejora y ahorro'
    },
    {
      icon: Zap,
      title: 'Resultados Rápidos',
      description: 'Reportes generados en minutos, no horas'
    }
  ];

  const benefits = [
    'Análisis automatizado con IA',
    'Reportes profesionales en PDF',
    'Integración con Azure AD',
    'Dashboard intuitivo y moderno',
    'Identificación de ahorros de costos',
    'Recomendaciones de seguridad'
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-blue-50">
      {/* Header */}
      <header className="relative z-10 bg-white/80 backdrop-blur-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <div className="w-10 h-10 bg-gradient-to-r from-primary-500 to-secondary-500 rounded-xl flex items-center justify-center">
                <BarChart3 className="w-6 h-6 text-white" />
              </div>
              <span className="ml-3 text-xl font-bold text-gray-900">
                Azure Reports
              </span>
            </div>
            
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setShowLogin(true)}
                className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                  showLogin 
                    ? 'bg-primary-500 text-white' 
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Iniciar Sesión
              </button>
              <button
                onClick={() => setShowLogin(false)}
                className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                  !showLogin 
                    ? 'bg-secondary-500 text-white' 
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Registrarse
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="relative">
        {/* Hero Section */}
        <section className="relative overflow-hidden">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 lg:py-20">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
              {/* Contenido izquierdo */}
              <motion.div
                initial={{ opacity: 0, x: -50 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.8 }}
                className="space-y-8"
              >
                <div>
                  <h1 className="text-4xl lg:text-6xl font-bold text-gray-900 leading-tight">
                    Análisis de Datos{' '}
                    <span className="bg-gradient-to-r from-primary-600 to-secondary-600 bg-clip-text text-transparent">
                      Inteligente
                    </span>
                  </h1>
                  <p className="mt-6 text-xl text-gray-600 leading-relaxed">
                    Transforma tus datos CSV en reportes ejecutivos profesionales 
                    con inteligencia artificial avanzada y insights accionables.
                  </p>
                </div>

                <div className="flex flex-wrap gap-4">
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className="btn-primary flex items-center space-x-2"
                  >
                    <Play className="w-5 h-5" />
                    <span>Ver Demo</span>
                  </motion.button>
                  <button className="btn-secondary flex items-center space-x-2">
                    <span>Conocer Más</span>
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>

                <div className="flex items-center space-x-6 pt-8">
                  <div className="flex items-center space-x-1">
                    {[...Array(5)].map((_, i) => (
                      <Star key={i} className="w-5 h-5 text-yellow-400 fill-current" />
                    ))}
                  </div>
                  <div className="text-gray-600">
                    <span className="font-semibold">4.9/5</span> - Más de 500 usuarios satisfechos
                  </div>
                </div>
              </motion.div>

              {/* Formulario de autenticación */}
              <motion.div
                initial={{ opacity: 0, x: 50 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.8, delay: 0.2 }}
                className="bg-white rounded-2xl shadow-2xl p-8 border border-gray-200"
              >
                <div className="text-center mb-8">
                  <h2 className="text-2xl font-bold text-gray-900">
                    {showLogin ? 'Iniciar Sesión' : 'Crear Cuenta'}
                  </h2>
                  <p className="text-gray-600 mt-2">
                    {showLogin 
                      ? 'Accede a tu dashboard de análisis' 
                      : 'Comienza tu experiencia gratuita'
                    }
                  </p>
                </div>

                {showLogin ? <LoginForm /> : <RegisterForm />}

                <div className="mt-6 text-center">
                  <button
                    onClick={() => setShowLogin(!showLogin)}
                    className="text-primary-600 hover:text-primary-700 font-medium"
                  >
                    {showLogin 
                      ? '¿No tienes cuenta? Regístrate aquí' 
                      : '¿Ya tienes cuenta? Inicia sesión'
                    }
                  </button>
                </div>
              </motion.div>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="py-16 bg-white">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <motion.div
              initial={{ opacity: 0, y: 50 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8 }}
              viewport={{ once: true }}
              className="text-center mb-16"
            >
              <h2 className="text-3xl lg:text-4xl font-bold text-gray-900 mb-6">
                Características Principales
              </h2>
              <p className="text-xl text-gray-600 max-w-3xl mx-auto">
                Herramientas poderosas diseñadas para simplificar tu análisis de datos 
                y generar insights valiosos de forma automática.
              </p>
            </motion.div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {features.map((feature, index) => (
                <motion.div
                  key={feature.title}
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: index * 0.1 }}
                  viewport={{ once: true }}
                  className="bg-gradient-to-br from-gray-50 to-white p-8 rounded-2xl border border-gray-200 hover:shadow-lg transition-shadow"
                >
                  <div className="w-12 h-12 bg-gradient-to-r from-primary-500 to-secondary-500 rounded-xl flex items-center justify-center mb-6">
                    <feature.icon className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-4">
                    {feature.title}
                  </h3>
                  <p className="text-gray-600">
                    {feature.description}
                  </p>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* Benefits Section */}
        <section className="py-16 bg-gradient-to-r from-primary-50 to-secondary-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
              <motion.div
                initial={{ opacity: 0, x: -50 }}
                whileInView={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.8 }}
                viewport={{ once: true }}
              >
                <h2 className="text-3xl lg:text-4xl font-bold text-gray-900 mb-8">
                  ¿Por qué elegir Azure Reports?
                </h2>
                <div className="space-y-4">
                  {benefits.map((benefit, index) => (
                    <motion.div
                      key={benefit}
                      initial={{ opacity: 0, x: -20 }}
                      whileInView={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.5, delay: index * 0.1 }}
                      viewport={{ once: true }}
                      className="flex items-center space-x-3"
                    >
                      <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0" />
                      <span className="text-gray-700">{benefit}</span>
                    </motion.div>
                  ))}
                </div>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, x: 50 }}
                whileInView={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.8 }}
                viewport={{ once: true }}
                className="relative"
              >
                <div className="bg-white rounded-2xl shadow-2xl p-8 border border-gray-200">
                  <div className="text-center">
                    <div className="w-20 h-20 bg-gradient-to-r from-green-400 to-green-600 rounded-full flex items-center justify-center mx-auto mb-6">
                      <TrendingUp className="w-10 h-10 text-white" />
                    </div>
                    <h3 className="text-2xl font-bold text-gray-900 mb-4">
                      Resultados Comprobados
                    </h3>
                    <p className="text-gray-600 mb-6">
                      Nuestros usuarios han ahorrado en promedio 40 horas mensuales 
                      en análisis manual de datos.
                    </p>
                    <div className="grid grid-cols-2 gap-4 text-center">
                      <div>
                        <div className="text-3xl font-bold text-primary-600">40h</div>
                        <div className="text-sm text-gray-500">Tiempo ahorrado</div>
                      </div>
                      <div>
                        <div className="text-3xl font-bold text-secondary-600">95%</div>
                        <div className="text-sm text-gray-500">Precisión</div>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            </div>
          </div>
        </section>
      </div>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <div className="flex items-center justify-center mb-6">
              <div className="w-10 h-10 bg-gradient-to-r from-primary-500 to-secondary-500 rounded-xl flex items-center justify-center">
                <BarChart3 className="w-6 h-6 text-white" />
              </div>
              <span className="ml-3 text-2xl font-bold">Azure Reports</span>
            </div>
            <p className="text-gray-400 mb-8 max-w-2xl mx-auto">
              Plataforma de análisis de datos inteligente que transforma información 
              compleja en insights accionables para tu negocio.
            </p>
            <div className="text-gray-500 text-sm">
              © 2024 Azure Reports Platform. Todos los derechos reservados.
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
