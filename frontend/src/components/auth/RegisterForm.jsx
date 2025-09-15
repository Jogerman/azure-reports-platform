// src/components/auth/RegisterForm.jsx
import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Eye, EyeOff, Mail, Lock, User, Briefcase, Loader2 } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const RegisterForm = () => {
  const { register: registerUser, loading } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm();

  const password = watch('password');

  const onSubmit = async (data) => {
    try {
      await registerUser(data);
    } catch (_error) {
      // Error ya manejado en el contexto
    }
  };

  return (
    <motion.form
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      onSubmit={handleSubmit(onSubmit)}
      className="space-y-6"
    >
      {/* Nombre y Apellido */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="first_name" className="block text-sm font-medium text-gray-700 mb-2">
            Nombre
          </label>
          <input
            id="first_name"
            type="text"
            className={`input-field ${errors.first_name ? 'border-red-500' : ''}`}
            placeholder="Juan"
            {...register('first_name', {
              required: 'El nombre es requerido'
            })}
          />
          {errors.first_name && (
            <p className="mt-1 text-sm text-red-600">{errors.first_name.message}</p>
          )}
        </div>
        
        <div>
          <label htmlFor="last_name" className="block text-sm font-medium text-gray-700 mb-2">
            Apellido
          </label>
          <input
            id="last_name"
            type="text"
            className={`input-field ${errors.last_name ? 'border-red-500' : ''}`}
            placeholder="Pérez"
            {...register('last_name', {
              required: 'El apellido es requerido'
            })}
          />
          {errors.last_name && (
            <p className="mt-1 text-sm text-red-600">{errors.last_name.message}</p>
          )}
        </div>
      </div>

      {/* Username */}
      <div>
        <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-2">
          Nombre de Usuario
        </label>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <User className="h-5 w-5 text-gray-400" />
          </div>
          <input
            id="username"
            type="text"
            className={`input-field pl-10 ${errors.username ? 'border-red-500' : ''}`}
            placeholder="juanperez"
            {...register('username', {
              required: 'El nombre de usuario es requerido',
              minLength: {
                value: 3,
                message: 'Debe tener al menos 3 caracteres'
              }
            })}
          />
        </div>
        {errors.username && (
          <p className="mt-1 text-sm text-red-600">{errors.username.message}</p>
        )}
      </div>

      {/* Email */}
      <div>
        <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
          Correo Electrónico
        </label>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Mail className="h-5 w-5 text-gray-400" />
          </div>
          <input
            id="email"
            type="email"
            autoComplete="email"
            className={`input-field pl-10 ${errors.email ? 'border-red-500' : ''}`}
            placeholder="juan@empresa.com"
            {...register('email', {
              required: 'El email es requerido',
              pattern: {
                value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                message: 'Email inválido'
              }
            })}
          />
        </div>
        {errors.email && (
          <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>
        )}
      </div>

      {/* Departamento y Cargo */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="department" className="block text-sm font-medium text-gray-700 mb-2">
            Departamento
          </label>
          <input
            id="department"
            type="text"
            className="input-field"
            placeholder="IT"
            {...register('department')}
          />
        </div>
        
        <div>
          <label htmlFor="job_title" className="block text-sm font-medium text-gray-700 mb-2">
            Cargo
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Briefcase className="h-5 w-5 text-gray-400" />
            </div>
            <input
              id="job_title"
              type="text"
              className="input-field pl-10"
              placeholder="Analista"
              {...register('job_title')}
            />
          </div>
        </div>
      </div>

      {/* Password */}
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
            type={showPassword ? 'text' : 'password'}
            autoComplete="new-password"
            className={`input-field pl-10 pr-10 ${errors.password ? 'border-red-500' : ''}`}
            placeholder="••••••••"
            {...register('password', {
              required: 'La contraseña es requerida',
              minLength: {
                value: 8,
                message: 'Debe tener al menos 8 caracteres'
              },
              pattern: {
                value: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
                message: 'Debe contener al menos una mayúscula, una minúscula y un número'
              }
            })}
          />
          <button
            type="button"
            className="absolute inset-y-0 right-0 pr-3 flex items-center"
            onClick={() => setShowPassword(!showPassword)}
          >
            {showPassword ? (
              <EyeOff className="h-5 w-5 text-gray-400 hover:text-gray-600" />
            ) : (
              <Eye className="h-5 w-5 text-gray-400 hover:text-gray-600" />
            )}
          </button>
        </div>
        {errors.password && (
          <p className="mt-1 text-sm text-red-600">{errors.password.message}</p>
        )}
      </div>

      {/* Confirm Password */}
      <div>
        <label htmlFor="password_confirm" className="block text-sm font-medium text-gray-700 mb-2">
          Confirmar Contraseña
        </label>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Lock className="h-5 w-5 text-gray-400" />
          </div>
          <input
            id="password_confirm"
            type={showConfirmPassword ? 'text' : 'password'}
            autoComplete="new-password"
            className={`input-field pl-10 pr-10 ${errors.password_confirm ? 'border-red-500' : ''}`}
            placeholder="••••••••"
            {...register('password_confirm', {
              required: 'Confirma tu contraseña',
              validate: value =>
                value === password || 'Las contraseñas no coinciden'
            })}
          />
          <button
            type="button"
            className="absolute inset-y-0 right-0 pr-3 flex items-center"
            onClick={() => setShowConfirmPassword(!showConfirmPassword)}
          >
            {showConfirmPassword ? (
              <EyeOff className="h-5 w-5 text-gray-400 hover:text-gray-600" />
            ) : (
              <Eye className="h-5 w-5 text-gray-400 hover:text-gray-600" />
            )}
          </button>
        </div>
        {errors.password_confirm && (
          <p className="mt-1 text-sm text-red-600">{errors.password_confirm.message}</p>
        )}
      </div>

      {/* Términos y condiciones */}
      <div className="flex items-center">
        <input
          id="accept-terms"
          name="accept-terms"
          type="checkbox"
          className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
          {...register('accept_terms', {
            required: 'Debes aceptar los términos y condiciones'
          })}
        />
        <label htmlFor="accept-terms" className="ml-2 block text-sm text-gray-700">
          Acepto los{' '}
          <a href="#" className="text-primary-600 hover:text-primary-500 font-medium">
            términos y condiciones
          </a>{' '}
          y la{' '}
          <a href="#" className="text-primary-600 hover:text-primary-500 font-medium">
            política de privacidad
          </a>
        </label>
      </div>
      {errors.accept_terms && (
        <p className="mt-1 text-sm text-red-600">{errors.accept_terms.message}</p>
      )}

      {/* Submit Button */}
      <motion.button
        type="submit"
        disabled={loading}
        whileHover={{ scale: loading ? 1 : 1.02 }}
        whileTap={{ scale: loading ? 1 : 0.98 }}
        className="w-full btn-primary flex items-center justify-center space-x-2"
      >
        {loading && <Loader2 className="w-4 h-4 animate-spin" />}
        <span>{loading ? 'Creando cuenta...' : 'Crear Cuenta'}</span>
      </motion.button>

      {/* Divider */}
      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-gray-300" />
        </div>
        <div className="relative flex justify-center text-sm">
          <span className="px-2 bg-white text-gray-500">O regístrate con</span>
        </div>
      </div>

      {/* Microsoft SSO */}
      <button
        type="button"
        className="w-full btn-secondary flex items-center justify-center space-x-2"
        onClick={() => {
          // Implementar Microsoft SSO aquí
          console.log('Microsoft SSO registration');
        }}
      >
        <svg className="w-5 h-5" viewBox="0 0 24 24">
          <path
            fill="#00BCF2"
            d="M0 0h11.377v11.372H0V0zm12.623 0H24v11.372H12.623V0zM0 12.623h11.377V24H0V12.623zm12.623 0H24V24H12.623V12.623z"
          />
        </svg>
        <span>Microsoft</span>
      </button>
    </motion.form>
  );
};

export default RegisterForm