/* eslint-disable no-unused-vars */
// src/pages/Profile.jsx
import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { 
  User, 
  Camera, 
  Save,
  Mail,
  Phone,
  MapPin,
  Briefcase,
  Calendar,
  Shield,
  Award
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { formatDate } from '../utils/helpers';
import toast from 'react-hot-toast';

const Profile = () => {
  const { user, updateProfile, loading } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm({
    defaultValues: {
      first_name: user?.first_name || '',
      last_name: user?.last_name || '',
      email: user?.email || '',
      phone_number: user?.phone_number || '',
      department: user?.department || '',
      job_title: user?.job_title || '',
    }
  });

  const onSubmit = async (data) => {
    try {
      await updateProfile(data);
      setIsEditing(false);
      toast.success('Perfil actualizado exitosamente');
    } catch (_error) {
      toast.error('Error al actualizar el perfil');
    }
  };

  const handleCancel = () => {
    reset();
    setIsEditing(false);
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl p-8 text-white">
        <div className="flex items-center space-x-6">
          <div className="relative">
            {user?.profile_picture ? (
              <img
                src={user.profile_picture}
                alt="Profile"
                className="w-24 h-24 rounded-full object-cover border-4 border-white/20"
              />
            ) : (
              <div className="w-24 h-24 bg-white/20 rounded-full flex items-center justify-center">
                <User className="w-12 h-12" />
              </div>
            )}
            <button className="absolute bottom-0 right-0 w-8 h-8 bg-white text-gray-600 rounded-full flex items-center justify-center hover:bg-gray-100 transition-colors">
              <Camera className="w-4 h-4" />
            </button>
          </div>
          
          <div>
            <h1 className="text-3xl font-bold mb-2">
              {user?.first_name ? `${user.first_name} ${user.last_name}` : user?.username}
            </h1>
            <p className="text-blue-100 text-lg">
              {user?.job_title || 'Usuario'} {user?.department && `• ${user.department}`}
            </p>
            <div className="flex items-center space-x-4 mt-3 text-blue-100">
              <div className="flex items-center">
                <Calendar className="w-4 h-4 mr-1" />
                <span>Miembro desde {formatDate(user?.created_at, 'MMM yyyy')}</span>
              </div>
              {user?.is_azure_user && (
                <div className="flex items-center">
                  <Shield className="w-4 h-4 mr-1" />
                  <span>Azure AD</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Información del perfil */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-xl shadow-soft border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-gray-900">Información Personal</h3>
              {!isEditing ? (
                <button
                  onClick={() => setIsEditing(true)}
                  className="btn-secondary"
                >
                  Editar Perfil
                </button>
              ) : (
                <div className="flex items-center space-x-2">
                  <button
                    onClick={handleCancel}
                    className="btn-ghost"
                  >
                    Cancelar
                  </button>
                  <button
                    onClick={handleSubmit(onSubmit)}
                    disabled={loading}
                    className="btn-primary flex items-center space-x-2"
                  >
                    <Save className="w-4 h-4" />
                    <span>Guardar</span>
                  </button>
                </div>
              )}
            </div>

            {isEditing ? (
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Nombre
                    </label>
                    <input
                      type="text"
                      {...register('first_name', { required: 'El nombre es requerido' })}
                      className={`input-field ${errors.first_name ? 'border-red-500' : ''}`}
                    />
                    {errors.first_name && (
                      <p className="mt-1 text-sm text-red-600">{errors.first_name.message}</p>
                    )}
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Apellido
                    </label>
                    <input
                      type="text"
                      {...register('last_name', { required: 'El apellido es requerido' })}
                      className={`input-field ${errors.last_name ? 'border-red-500' : ''}`}
                    />
                    {errors.last_name && (
                      <p className="mt-1 text-sm text-red-600">{errors.last_name.message}</p>
                    )}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Email
                  </label>
                  <input
                    type="email"
                    {...register('email', { 
                      required: 'El email es requerido',
                      pattern: {
                        value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                        message: 'Email inválido'
                      }
                    })}
                    className={`input-field ${errors.email ? 'border-red-500' : ''}`}
                  />
                  {errors.email && (
                    <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Teléfono
                    </label>
                    <input
                      type="tel"
                      {...register('phone_number')}
                      className="input-field"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Departamento
                    </label>
                    <input
                      type="text"
                      {...register('department')}
                      className="input-field"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Cargo
                  </label>
                  <input
                    type="text"
                    {...register('job_title')}
                    className="input-field"
                  />
                </div>
              </form>
            ) : (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="flex items-center space-x-3">
                    <Mail className="w-5 h-5 text-gray-400" />
                    <div>
                      <p className="text-sm text-gray-500">Email</p>
                      <p className="font-medium text-gray-900">{user?.email}</p>
                    </div>
                  </div>
                  
                  {user?.phone_number && (
                    <div className="flex items-center space-x-3">
                      <Phone className="w-5 h-5 text-gray-400" />
                      <div>
                        <p className="text-sm text-gray-500">Teléfono</p>
                        <p className="font-medium text-gray-900">{user.phone_number}</p>
                      </div>
                    </div>
                  )}
                  
                  {user?.department && (
                    <div className="flex items-center space-x-3">
                      <MapPin className="w-5 h-5 text-gray-400" />
                      <div>
                        <p className="text-sm text-gray-500">Departamento</p>
                        <p className="font-medium text-gray-900">{user.department}</p>
                      </div>
                    </div>
                  )}
                  
                  {user?.job_title && (
                    <div className="flex items-center space-x-3">
                      <Briefcase className="w-5 h-5 text-gray-400" />
                      <div>
                        <p className="text-sm text-gray-500">Cargo</p>
                        <p className="font-medium text-gray-900">{user.job_title}</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Estadísticas y actividad */}
        <div className="space-y-6">
          {/* Estadísticas del usuario */}
          <div className="bg-white rounded-xl shadow-soft border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Estadísticas</h3>
            <div className="space-y-4">
              {[
                { label: 'Reportes Generados', value: '24', icon: Award, color: 'text-blue-600' },
                { label: 'Archivos Subidos', value: '18', icon: User, color: 'text-green-600' },
                { label: 'Tiempo Ahorrado', value: '40h', icon: Calendar, color: 'text-purple-600' },
              ].map((stat) => (
                <div key={stat.label} className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <stat.icon className={`w-5 h-5 ${stat.color}`} />
                    <span className="text-gray-600">{stat.label}</span>
                  </div>
                  <span className="font-semibold text-gray-900">{stat.value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Actividad reciente */}
          <div className="bg-white rounded-xl shadow-soft border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Actividad Reciente</h3>
            <div className="space-y-3">
              {[
                { action: 'Reporte generado', time: 'Hace 2 horas' },
                { action: 'Archivo CSV subido', time: 'Hace 1 día' },
                { action: 'Perfil actualizado', time: 'Hace 3 días' },
              ].map((activity, index) => (
                <div key={index} className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">{activity.action}</span>
                  <span className="text-gray-400">{activity.time}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile;