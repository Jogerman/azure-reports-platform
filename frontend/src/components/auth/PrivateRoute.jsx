// frontend/src/components/auth/PrivateRoute.jsx
import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import Loading from '../common/Loading';

const PrivateRoute = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth(); // CAMBIAR: era 'loading'

  if (isLoading) {
    return <Loading fullScreen text="Verificando autenticación..." />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return children;
};

export default PrivateRoute;