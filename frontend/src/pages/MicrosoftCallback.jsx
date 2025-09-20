import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { CheckCircle, XCircle, Loader2 } from 'lucide-react';

const MicrosoftCallback = () => {
  const [status, setStatus] = useState('processing'); // 'processing', 'success', 'error'
  const [message, setMessage] = useState('Procesando autenticación...');

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Extraer parámetros de la URL actual
        const urlParams = new URLSearchParams(window.location.search);
        const accessToken = urlParams.get('access_token');
        const refreshToken = urlParams.get('refresh_token');
        const userId = urlParams.get('user_id');
        const error = urlParams.get('error');

        // Verificar si hay errores
        if (error) {
          const errorMessages = {
            'access_denied': 'Acceso cancelado por el usuario',
            'invalid_tenant': 'Tu organización no está autorizada para usar esta aplicación',
            'token_error': 'Error al obtener los tokens de acceso',
            'user_info_error': 'Error al obtener la información del usuario',
            'user_creation_error': 'Error al crear la cuenta de usuario',
            'not_configured': 'Microsoft OAuth no está configurado correctamente',
            'msal_not_available': 'Servicio de Microsoft no disponible',
            'server_error': 'Error interno del servidor'
          };

          setStatus('error');
          setMessage(errorMessages[error] || `Error: ${error}`);
          
          // Redirigir al login después de 3 segundos
          setTimeout(() => {
            window.location.href = '/';
          }, 3000);
          return;
        }

        // Verificar que tenemos todos los tokens necesarios
        if (!accessToken || !refreshToken || !userId) {
          setStatus('error');
          setMessage('Tokens de autenticación faltantes');
          setTimeout(() => {
            window.location.href = '/';
          }, 3000);
          return;
        }

        // Guardar tokens en localStorage
        localStorage.setItem('access_token', accessToken);
        localStorage.setItem('refresh_token', refreshToken);
        localStorage.setItem('user_id', userId);

        // Opcionalmente, verificar el token con el backend
        try {
          const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/auth/users/`, {
            headers: {
              'Authorization': `Bearer ${accessToken}`,
              'Content-Type': 'application/json',
            },
          });

          if (response.ok) {
            const userData = await response.json();
            
            // Guardar información del usuario
            localStorage.setItem('user_data', JSON.stringify(userData));
            
            setStatus('success');
            setMessage('Autenticación exitosa. Redirigiendo...');
            
            // Redirigir al dashboard después de 1.5 segundos
            setTimeout(() => {
              window.location.href = '/app';
            }, 1500);
          } else {
            throw new Error('Error verificando usuario');
          }
        } catch (verificationError) {
          console.warn('Error verificando usuario, pero tokens guardados:', verificationError);
          
          // Aún así proceder si tenemos los tokens
          setStatus('success');
          setMessage('Autenticación exitosa. Redirigiendo...');
          
          setTimeout(() => {
            window.location.href = '/app';
          }, 1500);
        }

      } catch (error) {
        console.error('Error en callback de Microsoft:', error);
        setStatus('error');
        setMessage('Error procesando la autenticación');
        
        setTimeout(() => {
          window.location.href = '/';
        }, 3000);
      }
    };

    handleCallback();
  }, []);

  const handleBackToHome = () => {
    window.location.href = '/';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full text-center"
      >
        {/* Icono de estado */}
        <div className="mb-6">
          {status === 'processing' && (
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
              className="mx-auto w-16 h-16"
            >
              <Loader2 className="w-16 h-16 text-blue-500" />
            </motion.div>
          )}
          
          {status === 'success' && (
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: "spring", stiffness: 200, damping: 10 }}
              className="mx-auto w-16 h-16"
            >
              <CheckCircle className="w-16 h-16 text-green-500" />
            </motion.div>
          )}
          
          {status === 'error' && (
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: "spring", stiffness: 200, damping: 10 }}
              className="mx-auto w-16 h-16"
            >
              <XCircle className="w-16 h-16 text-red-500" />
            </motion.div>
          )}
        </div>

        {/* Título */}
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          {status === 'processing' && 'Procesando Autenticación'}
          {status === 'success' && 'Autenticación Exitosa'}
          {status === 'error' && 'Error de Autenticación'}
        </h2>

        {/* Mensaje */}
        <p className="text-gray-600 mb-6">
          {message}
        </p>

        {/* Barra de progreso para éxito */}
        {status === 'success' && (
          <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: '100%' }}
              transition={{ duration: 1.5 }}
              className="bg-gradient-to-r from-blue-500 to-green-500 h-2 rounded-full"
            />
          </div>
        )}

        {/* Botón de acción para errores */}
        {status === 'error' && (
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleBackToHome}
            className="w-full bg-gradient-to-r from-blue-500 to-indigo-600 text-white font-medium py-3 px-4 rounded-lg transition-colors duration-200"
          >
            Volver al Inicio
          </motion.button>
        )}

        {/* Información adicional */}
        <div className="mt-6 text-xs text-gray-500">
          Azure Advisor Analyzer
        </div>
      </motion.div>
    </div>
  );
};

export default MicrosoftCallback;