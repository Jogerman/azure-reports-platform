// src/context/AuthContext.jsx (modificado)
import React, { createContext, useReducer, useEffect } from 'react';
import { authService } from '../services/authService';
import toast from 'react-hot-toast';

// eslint-disable-next-line react-refresh/only-export-components
export const AuthContext = createContext();

const authReducer = (state, action) => {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    case 'LOGIN_SUCCESS':
      return { 
        ...state, 
        loading: false, 
        user: action.payload, 
        isAuthenticated: true,
        error: null 
      };
    case 'LOGIN_ERROR':
      return { 
        ...state, 
        loading: false, 
        error: action.payload,
        isAuthenticated: false,
        user: null 
      };
    case 'LOGOUT':
      return { 
        ...state, 
        user: null, 
        isAuthenticated: false, 
        loading: false,
        error: null 
      };
    case 'UPDATE_USER':
      return { 
        ...state, 
        user: { ...state.user, ...action.payload } 
      };
    case 'CLEAR_ERROR':
      return { ...state, error: null };
    default:
      return state;
  }
};

const initialState = {
  user: null,
  isAuthenticated: false,
  loading: true,
  error: null,
};

export const AuthProvider = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);

  useEffect(() => {
    const initializeAuth = async () => {
      try {
        dispatch({ type: 'SET_LOADING', payload: true });
        
        if (authService.isAuthenticated()) {
          const storedUser = authService.getStoredUser();
          if (storedUser) {
            try {
              const currentUser = await authService.getCurrentUser();
              dispatch({ type: 'LOGIN_SUCCESS', payload: currentUser });
            // eslint-disable-next-line no-unused-vars
            } catch (_error) {
              dispatch({ type: 'LOGIN_SUCCESS', payload: storedUser });
            }
          }
        }
      } catch (_error) {
        console.error('Error initializing auth:', _error);
        await authService.logout();
        dispatch({ type: 'LOGOUT' });
      } finally {
        dispatch({ type: 'SET_LOADING', payload: false });
      }
    };

    initializeAuth();
  }, []);

  const login = async (credentials) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      const { user } = await authService.login(credentials);
      dispatch({ type: 'LOGIN_SUCCESS', payload: user });
      toast.success(`¡Bienvenido, ${user.first_name || user.username}!`);
      return user;
    } catch (error) {
      dispatch({ type: 'LOGIN_ERROR', payload: error.message });
      throw error;
    }
  };

  const register = async (userData) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      const user = await authService.register(userData);
      toast.success('Cuenta creada exitosamente. Por favor, inicia sesión.');
      return user;
    } catch (error) {
      dispatch({ type: 'LOGIN_ERROR', payload: error.message });
      throw error;
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };

  const logout = async () => {
    try {
      await authService.logout();
      dispatch({ type: 'LOGOUT' });
      toast.success('Sesión cerrada exitosamente');
    } catch (_error) {
      console.error('Logout error:', _error);
      dispatch({ type: 'LOGOUT' });
    }
  };

  const updateProfile = async (userData) => {
    try {
      const updatedUser = await authService.updateProfile(userData);
      dispatch({ type: 'UPDATE_USER', payload: updatedUser });
      toast.success('Perfil actualizado exitosamente');
      return updatedUser;
    } catch (_error) {
      toast.error('Error actualizando perfil');
      throw _error;
    }
  };

  const clearError = () => {
    dispatch({ type: 'CLEAR_ERROR' });
  };

  const value = {
    ...state,
    login,
    register,
    logout,
    updateProfile,
    clearError,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};