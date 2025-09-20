// src/pages/LoginPage.jsx
import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Eye, EyeOff, Mail, Lock, LogIn, Loader2 } from 'lucide-react';

const LoginPage = () => {
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [errors, setErrors] = useState({});

  // Manejar autenticación con Microsoft
  const handleMicrosoftLogin = () => {
    setIsLoading(true);
    // Redirigir al endpoint de Microsoft OAuth del backend Django
    const apiUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    window.location.href = `${apiUrl}/auth/microsoft/login/`;
  };

  // Manejar login local
  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setErrors({});

    try {
      // Validaciones básicas
      const newErrors = {};
      if (!formData.email) newErrors.email = 'El email es requerido';
      if (!formData.password) newErrors.password = 'La contraseña es requerida';
      
      if (Object.keys(newErrors).length > 0) {
        setErrors(newErrors);
        setIsLoading(false);
        return;
      }

      // Aquí iría la lógica de login con el backend
      console.log('Login attempt:', formData);
      
      // Simulación de respuesta del backend
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Después del login exitoso, redirigir al dashboard
      // window.location.href = '/dashboard';
      
    } catch (error) {
      console.error('Error en login:', error);
      setErrors({ general: 'Error al iniciar sesión. Verifica tus credenciales.' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // Limpiar error del campo cuando el usuario empiece a escribir
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* Logo y título */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center"
        >
          <div className="mx-auto h-16 w-16 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-2xl flex items-center justify-center mb-6 shadow-lg">
            <div className="text-white text-2xl font-bold">A</div>
          </div>
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            Iniciar Sesión
          </h2>
          <p className="text-gray-600">
            Accede a tu cuenta de Azure Advisor Analyzer
          </p>
        </motion.div>

        {/* Formulario de login */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white rounded-2xl shadow-xl p-8"
        >
          {/* Botón de Microsoft */}
          <div className="mb-6">
            <button
              onClick={handleMicrosoftLogin}
              disabled={isLoading}
              className="w-full flex items-center justify-center px-4 py-3 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg className="w-5 h-5 mr-3" viewBox="0 0 24 24" fill="none">
                <path d="M11.4 2.4H2.4v9h9v-9z" fill="#f25022"/>
                <path d="M21.6 2.4h-9v9h9v-9z" fill="#00a4ef"/>
                <path d="M11.4 12.6H2.4v9h9v-9z" fill="#ffb900"/>
                <path d="M21.6 12.6h-9v9h9v-9z" fill="#7fba00"/>
              </svg>
              Continuar con Microsoft
            </button>
          </div>

          {/* Divisor */}
          <div className="relative mb-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white text-gray-500">O continúa con</span>
            </div>
          </div>

          {/* Mostrar error general */}
          {errors.general && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm"
            >
              {errors.general}
            </motion.div>
          )}

          <div className="space-y-6">
            {/* Campo Email */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                Email
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Mail className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  className={`block w-full pl-10 pr-12 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors duration-200 ${
                    errors.email ? 'border-red-300 bg-red-50' : 'border-gray-300'
                  }`}
                  placeholder="tu@email.com"
                />
                {/* Mostrar error de validación del campo */}
                <div className="absolute right-3 top-3">
                  {errors.email && (
                    <div className="w-5 h-5 bg-red-500 rounded-full flex items-center justify-center">
                      <span className="text-white text-xs font-bold">!</span>
                    </div>
                  )}
                </div>
              </div>
              {errors.email && (
                <p className="mt-1 text-sm text-red-600">{errors.email}</p>
              )}
            </div>

            {/* Campo Contraseña */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                Contraseña
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  value={formData.password}
                  onChange={handleInputChange}
                  className={`block w-full pl-10 pr-12 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors duration-200 ${
                    errors.password ? 'border-red-300 bg-red-50' : 'border-gray-300'
                  }`}
                  placeholder="Tu contraseña"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                >
                  {showPassword ? (
                    <EyeOff className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                  ) : (
                    <Eye className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                  )}
                </button>
              </div>
              {errors.password && (
                <p className="mt-1 text-sm text-red-600">{errors.password}</p>
              )}
            </div>

            {/* Recordar sesión */}
            <div className="flex items-center">
              <input
                id="remember"
                name="remember"
                type="checkbox"
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="remember" className="ml-2 block text-sm text-gray-700">
                Recordar sesión
              </label>
            </div>

            {/* Enlace de olvido de contraseña */}
            <div className="text-right">
              <a 
                href="#" 
                className="text-sm text-blue-600 hover:text-blue-500 transition-colors duration-200"
              >
                ¿Olvidaste tu contraseña?
              </a>
            </div>

            {/* Botón de submit */}
            <button
              onClick={handleSubmit}
              disabled={isLoading}
              className="w-full flex items-center justify-center px-4 py-3 bg-gradient-to-r from-blue-500 to-indigo-600 text-white font-medium rounded-lg hover:from-blue-600 hover:to-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg"
            >
              {isLoading ? (
                <>
                  <Loader2 className="animate-spin h-5 w-5 mr-2" />
                  Iniciando Sesión...
                </>
              ) : (
                <>
                  <LogIn className="h-5 w-5 mr-2" />
                  Iniciar Sesión
                </>
              )}
            </button>
          </div>

          {/* Credenciales de desarrollo (solo para demo) */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg"
          >
            <div className="flex items-center mb-2">
              <span className="text-yellow-600 text-sm font-medium">🔧 Credenciales de desarrollo:</span>
            </div>
            <p className="text-sm text-yellow-700">
              <strong>Email:</strong> admin@azurereports.com<br />
              <strong>Contraseña:</strong> admin123
            </p>
          </motion.div>
        </motion.div>
      </div>
    </div>
  );
};

export default LoginPage;