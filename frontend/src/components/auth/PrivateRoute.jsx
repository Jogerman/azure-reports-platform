// frontend/src/components/auth/PrivateRoute.jsx
import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import Loading from '../common/Loading';

const PrivateRoute = ({ children }) => {
  const { isAuthenticated, isLoading, isInitialized } = useAuth();

  // Mostrar loading mientras se verifica la autenticación inicial
  if (isLoading || !isInitialized) {
    return <Loading fullScreen text="Verificando autenticación..." />;
  }

  // Si no está autenticado después de la verificación inicial, redirigir al login
  if (!isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  // Si todo está bien, mostrar el contenido protegido
  return children;
};

export default PrivateRoute;