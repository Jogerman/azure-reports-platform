// frontend/src/context/AuthContext.jsx
import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { authService } from '../services/authService';
import toast from 'react-hot-toast';

// Estados del contexto de autenticación
const initialState = {
  user: null,
  isAuthenticated: false,
  isLoading: true,
  isInitialized: false, // Nuevo estado para saber cuando la verificación inicial terminó
  error: null
};

// Acciones del reducer
const AUTH_ACTIONS = {
  LOADING: 'LOADING',
  LOGIN_SUCCESS: 'LOGIN_SUCCESS',
  LOGOUT: 'LOGOUT',
  SET_ERROR: 'SET_ERROR',
  CLEAR_ERROR: 'CLEAR_ERROR',
  UPDATE_USER: 'UPDATE_USER',
  SET_INITIALIZED: 'SET_INITIALIZED'
};

// Reducer para manejar el estado de autenticación
const authReducer = (state, action) => {
  switch (action.type) {
    case AUTH_ACTIONS.LOADING:
      return {
        ...state,
        isLoading: action.payload
      };
    
    case AUTH_ACTIONS.LOGIN_SUCCESS:
      return {
        ...state,
        user: action.payload.user,
        isAuthenticated: true,
        isLoading: false,
        isInitialized: true,
        error: null
      };
    
    case AUTH_ACTIONS.LOGOUT:
      return {
        ...state,
        user: null,
        isAuthenticated: false,
        isLoading: false,
        isInitialized: true,
        error: null
      };
    
    case AUTH_ACTIONS.SET_ERROR:
      return {
        ...state,
        error: action.payload,
        isLoading: false,
        isInitialized: true
      };
    
    case AUTH_ACTIONS.CLEAR_ERROR:
      return {
        ...state,
        error: null
      };
    
    case AUTH_ACTIONS.UPDATE_USER:
      return {
        ...state,
        user: { ...state.user, ...action.payload },
        isAuthenticated: true,
        isInitialized: true
      };
    
    case AUTH_ACTIONS.SET_INITIALIZED:
      return {
        ...state,
        isInitialized: true,
        isLoading: false
      };
    
    default:
      return state;
  }
};

// Crear el contexto
const AuthContext = createContext(null);

// Provider del contexto de autenticación
export const AuthProvider = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Verificar autenticación al cargar la app
  useEffect(() => {
    checkAuthStatus();
  }, []);

  // Función para verificar si hay tokens válidos
  const hasValidTokens = () => {
    const accessToken = localStorage.getItem('access_token');
    const refreshToken = localStorage.getItem('refresh_token');
    const authTimestamp = localStorage.getItem('auth_timestamp');
    
    if (!accessToken || !refreshToken) {
      return false;
    }

    // Verificar si la autenticación no es muy antigua (7 días)
    if (authTimestamp) {
      const authTime = parseInt(authTimestamp);
      const now = Date.now();
      const sevenDays = 7 * 24 * 60 * 60 * 1000; // 7 días en ms
      
      if (now - authTime > sevenDays) {
        console.log('Autenticación expirada por tiempo');
        return false;
      }
    }

    // Verificar si el token no está expirado
    try {
      const payload = JSON.parse(atob(accessToken.split('.')[1]));
      const now = Date.now() / 1000;
      
      if (payload.exp < now) {
        console.log('Access token expirado');
        // Si el access token está expirado, intentar renovar con refresh token
        return 'refresh_needed';
      }
      
      return true;
    } catch (error) {
      console.error('Error parsing token:', error);
      return false;
    }
  };

  const checkAuthStatus = async () => {
    dispatch({ type: AUTH_ACTIONS.LOADING, payload: true });
    
    try {
      const tokenStatus = hasValidTokens();
      
      if (tokenStatus === false) {
        // No hay tokens válidos, logout
        dispatch({ type: AUTH_ACTIONS.LOGOUT });
        return;
      }

      if (tokenStatus === 'refresh_needed') {
        // Intentar renovar token
        try {
          await authService.refreshToken();
          console.log('Token renovado exitosamente');
        } catch (refreshError) {
          console.error('Error renovando token:', refreshError);
          dispatch({ type: AUTH_ACTIONS.LOGOUT });
          return;
        }
      }

      // Obtener datos del usuario
      const userData = localStorage.getItem('user_data');
      if (userData) {
        const user = JSON.parse(userData);
        console.log('Usuario encontrado en localStorage:', user);
        dispatch({ 
          type: AUTH_ACTIONS.LOGIN_SUCCESS, 
          payload: { user } 
        });
      } else {
        // Si no hay datos del usuario, intentar obtenerlos del backend
        try {
          console.log('Obteniendo datos del usuario del backend...');
          const userData = await authService.getCurrentUser();
          localStorage.setItem('user_data', JSON.stringify(userData));
          dispatch({ 
            type: AUTH_ACTIONS.LOGIN_SUCCESS, 
            payload: { user: userData } 
          });
        } catch (error) {
          console.error('Error obteniendo datos del usuario:', error);
          // Si falla obtener datos del usuario pero hay tokens, usar datos básicos
          const basicUser = {
            id: localStorage.getItem('user_id'),
            email: 'usuario@microsoft.com',
            username: 'Usuario'
          };
          dispatch({ 
            type: AUTH_ACTIONS.LOGIN_SUCCESS, 
            payload: { user: basicUser } 
          });
        }
      }
    } catch (error) {
      console.error('Error verificando autenticación:', error);
      dispatch({ type: AUTH_ACTIONS.LOGOUT });
    }
  };

  const login = async (credentials) => {
    dispatch({ type: AUTH_ACTIONS.LOADING, payload: true });
    dispatch({ type: AUTH_ACTIONS.CLEAR_ERROR });
    
    try {
      const response = await authService.login(credentials);
      
      // Guardar timestamp de autenticación
      localStorage.setItem('auth_timestamp', Date.now().toString());
      localStorage.setItem('auth_method', 'local');
      
      dispatch({ 
        type: AUTH_ACTIONS.LOGIN_SUCCESS, 
        payload: { user: response.user } 
      });
      
      toast.success(`¡Bienvenido, ${response.user?.username || 'usuario'}!`);
      return response;
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 
                          error.response?.data?.error || 
                          error.message ||
                          'Error al iniciar sesión';
      
      dispatch({ type: AUTH_ACTIONS.SET_ERROR, payload: errorMessage });
      toast.error(errorMessage);
      throw error;
    }
  };

  const register = async (userData) => {
    dispatch({ type: AUTH_ACTIONS.LOADING, payload: true });
    dispatch({ type: AUTH_ACTIONS.CLEAR_ERROR });
    
    try {
      const response = await authService.register(userData);
      toast.success('Cuenta creada exitosamente. Por favor inicia sesión.');
      return response;
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 
                          error.response?.data?.error || 
                          error.message ||
                          'Error al crear cuenta';
      
      dispatch({ type: AUTH_ACTIONS.SET_ERROR, payload: errorMessage });
      toast.error(errorMessage);
      throw error;
    } finally {
      dispatch({ type: AUTH_ACTIONS.SET_INITIALIZED });
    }
  };

  const logout = async () => {
    dispatch({ type: AUTH_ACTIONS.LOADING, payload: true });
    
    try {
      await authService.logout();
      
      // Limpiar todos los datos de autenticación
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user_id');
      localStorage.removeItem('user_data');
      localStorage.removeItem('auth_timestamp');
      localStorage.removeItem('auth_method');
      
      toast.success('Sesión cerrada exitosamente');
    } catch (error) {
      console.error('Error al cerrar sesión:', error);
      
      // Limpiar datos localmente aunque haya error en el backend
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user_id');
      localStorage.removeItem('user_data');
      localStorage.removeItem('auth_timestamp');
      localStorage.removeItem('auth_method');
    } finally {
      dispatch({ type: AUTH_ACTIONS.LOGOUT });
    }
  };

  const updateUser = (userData) => {
    console.log('Actualizando usuario en contexto:', userData);
    
    // Actualizar también en localStorage
    const existingUserData = localStorage.getItem('user_data');
    if (existingUserData) {
      const currentUser = JSON.parse(existingUserData);
      const updatedUser = { ...currentUser, ...userData };
      localStorage.setItem('user_data', JSON.stringify(updatedUser));
    } else {
      localStorage.setItem('user_data', JSON.stringify(userData));
    }

    // Actualizar contexto
    dispatch({ type: AUTH_ACTIONS.UPDATE_USER, payload: userData });
  };

  const clearError = () => {
    dispatch({ type: AUTH_ACTIONS.CLEAR_ERROR });
  };

  // Valor del contexto
  const value = {
    ...state,
    login,
    register,
    logout,
    updateUser,
    clearError,
    checkAuthStatus
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// Hook personalizado para usar el contexto de autenticación
// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => {
  const context = useContext(AuthContext);
  
  if (!context) {
    throw new Error('useAuth debe usarse dentro de un AuthProvider');
  }
  
  return context;
};

export default AuthContext;