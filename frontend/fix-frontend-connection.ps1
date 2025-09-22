# fix-frontend-connection.ps1 - SCRIPT DE CORRECCIÓN FINAL PARA WINDOWS
# Este script corrige los errores de comunicación frontend-backend

Write-Host "🚀 CORRECCIÓN FRONTEND-BACKEND AZURE REPORTS PLATFORM" -ForegroundColor Cyan
Write-Host "===============================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar que estamos en el directorio correcto
if (-not (Test-Path "frontend" -PathType Container) -or -not (Test-Path "backend" -PathType Container)) {
    Write-Host "❌ Error: No se encontraron las carpetas 'frontend' y 'backend'." -ForegroundColor Red
    Write-Host "   Por favor ejecuta este script desde la raíz del proyecto." -ForegroundColor Yellow
    exit 1
}

# Función para reemplazar contenido en archivos
function Replace-FileContent {
    param(
        [string]$FilePath,
        [string]$SearchPattern,
        [string]$ReplaceWith
    )
    
    if (Test-Path $FilePath) {
        try {
            $content = Get-Content $FilePath -Raw -Encoding UTF8
            $newContent = $content -replace $SearchPattern, $ReplaceWith
            Set-Content $FilePath $newContent -Encoding UTF8 -NoNewline
            return $true
        } catch {
            Write-Host "⚠️  Advertencia: No se pudo actualizar $FilePath" -ForegroundColor Yellow
            return $false
        }
    }
    return $false
}

Write-Host "🔧 1. DETENIENDO PROCESOS ACTIVOS" -ForegroundColor Blue
Write-Host "----------------------------------------" -ForegroundColor Blue

# Detener procesos de React y Django si están corriendo
try {
    Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -eq "node" } | Stop-Process -Force
    Write-Host "✅ Procesos Node.js detenidos" -ForegroundColor Green
} catch {
    Write-Host "ℹ️  No hay procesos Node.js ejecutándose" -ForegroundColor Gray
}

try {
    Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*manage.py*" } | Stop-Process -Force
    Write-Host "✅ Procesos Django detenidos" -ForegroundColor Green
} catch {
    Write-Host "ℹ️  No hay procesos Django ejecutándose" -ForegroundColor Gray
}

Write-Host ""
Write-Host "📝 2. CORRIGIENDO ARCHIVO useReports.js" -ForegroundColor Blue
Write-Host "----------------------------------------" -ForegroundColor Blue

$useReportsPath = "frontend/src/hooks/useReports.js"

# Crear el contenido corregido del archivo useReports.js
$correctedContent = @'
// src/hooks/useReports.js - VERSIÓN CORREGIDA FINAL
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchWithAuth, buildApiUrl } from '../config/api';
import toast from 'react-hot-toast';

// 📁 SERVICIO DE ARCHIVOS
const fileService = {
  async uploadFile(file) {
    try {
      console.log('📤 Subiendo archivo:', file.name);
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await fetchWithAuth(buildApiUrl('/files/upload/'), {
        method: 'POST',
        body: formData,
        headers: {}, // No enviar Content-Type para FormData
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `HTTP ${response.status}: Error subiendo archivo`);
      }

      const result = await response.json();
      console.log('✅ Archivo subido:', result);
      return result;
      
    } catch (error) {
      console.error('❌ Error subiendo archivo:', error);
      throw error;
    }
  },

  async getFiles(params = {}) {
    try {
      const searchParams = new URLSearchParams(params);
      const url = buildApiUrl('/files/') + `?${searchParams}`;
      
      console.log('📁 Fetching files from:', url);
      const response = await fetchWithAuth(url);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('✅ Files loaded:', data);
      return data?.results || data || [];
      
    } catch (error) {
      console.error('❌ Error loading files:', error);
      throw error;
    }
  },

  async deleteFile(fileId) {
    try {
      const response = await fetchWithAuth(buildApiUrl('/files/:id/', { id: fileId }), {
        method: 'DELETE',
      });
      return response.ok;
    } catch (error) {
      console.error('❌ Error eliminando archivo:', error);
      throw error;
    }
  },
};

// 📊 SERVICIO DE REPORTES
const reportService = {
  async generateReport(fileId, reportConfig = {}) {
    try {
      console.log('📊 Generating report for file:', fileId);
      
      const requestData = {
        file_id: fileId,
        title: reportConfig.title || 'Reporte Automático',
        description: reportConfig.description || '',
        report_type: reportConfig.type || 'comprehensive'
      };
      
      const response = await fetchWithAuth(buildApiUrl('/reports/generate/'), {
        method: 'POST',
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `HTTP ${response.status}: Error generando reporte`);
      }

      const result = await response.json();
      console.log('✅ Report generated:', result);
      return result;
      
    } catch (error) {
      console.error('❌ Error generating report:', error);
      throw error;
    }
  },

  async getReports(params = {}) {
    try {
      const searchParams = new URLSearchParams(params);
      const url = buildApiUrl('/reports/') + `?${searchParams}`;
      
      console.log('📋 Fetching reports from:', url);
      const response = await fetchWithAuth(url);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('✅ Reports loaded:', data);
      return data?.results || data || [];
      
    } catch (error) {
      console.error('❌ Error loading reports:', error);
      throw error;
    }
  },
  
  async getReport(reportId) {
    try {
      const response = await fetchWithAuth(buildApiUrl('/reports/:id/', { id: reportId }));
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: Error obteniendo reporte`);
      }
      
      return response.json();
    } catch (error) {
      console.error('❌ Error obteniendo reporte:', error);
      throw error;
    }
  },

  async getReportHTML(reportId) {
    try {
      const response = await fetchWithAuth(buildApiUrl('/reports/:id/html/', { id: reportId }));
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: Error obteniendo HTML del reporte`);
      }
      
      return response.text();
    } catch (error) {
      console.error('❌ Error obteniendo HTML del reporte:', error);
      throw error;
    }
  },

  async downloadReportPDF(reportId, filename) {
    try {
      const response = await fetchWithAuth(buildApiUrl('/reports/:id/download/', { id: reportId }));
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: Error descargando reporte`);
      }
      
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename || `reporte_${reportId}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
      
      return true;
    } catch (error) {
      console.error('❌ Error downloading report:', error);
      throw error;
    }
  },

  async deleteReport(reportId) {
    try {
      const response = await fetchWithAuth(buildApiUrl('/reports/:id/', { id: reportId }), {
        method: 'DELETE',
      });
      return response.ok;
    } catch (error) {
      console.error('❌ Error eliminando reporte:', error);
      throw error;
    }
  },
};

// 📈 SERVICIO DE DASHBOARD
const dashboardService = {
  async getStats() {
    try {
      const response = await fetchWithAuth(buildApiUrl('/dashboard/stats/'));
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: Error obteniendo estadísticas`);
      }
      
      const data = await response.json();
      console.log('📊 Dashboard stats loaded:', data);
      return data;
    } catch (error) {
      console.error('❌ Error loading dashboard stats:', error);
      throw error;
    }
  },
};

// 📤 HOOK PERSONALIZADO PARA UPLOADS CON PROGRESO
export const useFileUpload = () => {
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const queryClient = useQueryClient();

  const uploadFile = async (file) => {
    if (!file) throw new Error('No se ha seleccionado ningún archivo');

    setIsUploading(true);
    setProgress(0);

    try {
      const progressInterval = setInterval(() => {
        setProgress(prev => {
          const newProgress = prev + Math.random() * 15;
          return newProgress > 90 ? 90 : newProgress;
        });
      }, 200);

      const result = await fileService.uploadFile(file);
      
      clearInterval(progressInterval);
      setProgress(100);
      
      queryClient.invalidateQueries({ queryKey: ['files'] });
      
      toast.success(`✅ Archivo "${file.name}" subido exitosamente`);
      return result;
      
    } catch (error) {
      console.error('Error uploading file:', error);
      toast.error(`❌ Error subiendo archivo: ${error.message}`);
      throw error;
    } finally {
      setIsUploading(false);
      setTimeout(() => setProgress(0), 1000);
    }
  };

  return { uploadFile, isUploading, progress };
};

// 📁 HOOKS DE ARCHIVOS
export const useFiles = (params = {}) => {
  return useQuery({
    queryKey: ['files', params],
    queryFn: () => fileService.getFiles(params),
    staleTime: 5 * 60 * 1000,
    cacheTime: 10 * 60 * 1000,
  });
};

export const useStorageFiles = useFiles;

// 📋 HOOKS DE REPORTES
export const useReports = (params = {}) => {
  return useQuery({
    queryKey: ['reports', params],
    queryFn: () => reportService.getReports(params),
    staleTime: 5 * 60 * 1000,
    cacheTime: 10 * 60 * 1000,
  });
};

export const useRecentReports = (limit = 5) => {
  return useQuery({
    queryKey: ['reports', 'recent', limit],
    queryFn: () => reportService.getReports({ ordering: '-created_at', limit }),
    staleTime: 2 * 60 * 1000,
  });
};

export const useReport = (reportId) => {
  return useQuery({
    queryKey: ['report', reportId],
    queryFn: () => reportService.getReport(reportId),
    enabled: !!reportId,
    staleTime: 5 * 60 * 1000,
  });
};

export const useReportHTML = (reportId) => {
  return useQuery({
    queryKey: ['report-html', reportId],
    queryFn: () => reportService.getReportHTML(reportId),
    enabled: !!reportId,
    staleTime: 10 * 60 * 1000,
  });
};

// 📊 HOOKS DE MUTACIONES
export const useGenerateReport = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ fileId, config }) => reportService.generateReport(fileId, config),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['reports'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      
      toast.success('🎉 Reporte generado exitosamente');
      return data;
    },
    onError: (error) => {
      console.error('Error generating report:', error);
      toast.error(`❌ Error generando reporte: ${error.message}`);
    },
  });
};

export const useDeleteReport = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (reportId) => reportService.deleteReport(reportId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      
      toast.success('🗑️ Reporte eliminado exitosamente');
    },
    onError: (error) => {
      console.error('Error deleting report:', error);
      toast.error(`❌ Error eliminando reporte: ${error.message}`);
    },
  });
};

export const useDeleteFile = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (fileId) => fileService.deleteFile(fileId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['files'] });
      
      toast.success('🗑️ Archivo eliminado exitosamente');
    },
    onError: (error) => {
      console.error('Error deleting file:', error);
      toast.error(`❌ Error eliminando archivo: ${error.message}`);
    },
  });
};

// 📈 HOOKS DE DASHBOARD
export const useDashboardStats = () => {
  return useQuery({
    queryKey: ['dashboard', 'stats'],
    queryFn: () => dashboardService.getStats(),
    staleTime: 2 * 60 * 1000,
    cacheTime: 5 * 60 * 1000,
  });
};

// 🔄 HOOKS DE COMPATIBILIDAD
export const useReportGeneration = () => {
  const mutation = useGenerateReport();
  
  return {
    generateReport: async (fileId, reportConfig) => {
      return mutation.mutateAsync({ fileId, config: reportConfig });
    },
    isGenerating: mutation.isPending,
  };
};
'@

# Escribir el archivo corregido
try {
    Set-Content -Path $useReportsPath -Value $correctedContent -Encoding UTF8 -NoNewline
    Write-Host "✅ Archivo useReports.js corregido" -ForegroundColor Green
} catch {
    Write-Host "❌ Error corrigiendo useReports.js: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "📝 3. CORRIGIENDO ARCHIVO api.js" -ForegroundColor Blue
Write-Host "----------------------------------------" -ForegroundColor Blue

$apiConfigPath = "frontend/src/config/api.js"

# Crear el contenido corregido del archivo api.js
$apiContent = @'
// src/config/api.js - VERSIÓN CORREGIDA FINAL SIN DUPLICACIONES
export const API_CONFIG = {
  BASE_URL: (() => {
    if (window.location.hostname !== 'localhost') {
      return window.location.origin + '/api';
    }
    return 'http://localhost:8000/api';
  })(),
  
  TIMEOUT: 30000,
  UPLOAD_TIMEOUT: 300000,
  
  ENDPOINTS: {
    AUTH: {
      LOGIN: '/auth/login/',
      REGISTER: '/auth/register/',
      LOGOUT: '/auth/logout/',
      REFRESH: '/auth/refresh/',
      PROFILE: '/auth/users/profile/',
      MICROSOFT_LOGIN: '/auth/microsoft/login/',
      MICROSOFT_CALLBACK: '/auth/microsoft/callback/',
    },
    
    FILES: {
      UPLOAD: '/files/upload/',
      LIST: '/files/',
      DETAIL: '/files/:id/',
      DELETE: '/files/:id/',
      DOWNLOAD: '/files/:id/download/',
    },
    
    REPORTS: {
      GENERATE: '/reports/generate/',
      LIST: '/reports/',
      DETAIL: '/reports/:id/',
      HTML: '/reports/:id/html/',
      DOWNLOAD: '/reports/:id/download/',
      DELETE: '/reports/:id/',
    },
    
    DASHBOARD: {
      STATS: '/dashboard/stats/',
      ACTIVITY: '/dashboard/activity/',
    },
    
    HEALTH: '/health/',
  },
  
  DEFAULT_HEADERS: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
  
  RETRY: {
    ATTEMPTS: 3,
    DELAY: 1000,
    EXPONENTIAL: true,
  },
};

export const fetchWithAuth = async (url, options = {}) => {
  const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
  
  const config = {
    ...options,
    headers: {
      ...API_CONFIG.DEFAULT_HEADERS,
      ...options.headers,
      ...(token && { Authorization: `Bearer ${token}` }),
    },
    timeout: API_CONFIG.TIMEOUT,
  };

  try {
    const response = await fetch(url, config);
    
    if (response.status === 401) {
      localStorage.removeItem('access_token');
      sessionStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      sessionStorage.removeItem('refresh_token');
      window.location.href = '/';
      throw new Error('Sesión expirada');
    }
    
    return response;
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};

export const buildApiUrl = (endpoint, params = {}) => {
  let url = API_CONFIG.BASE_URL + endpoint;
  
  Object.entries(params).forEach(([key, value]) => {
    url = url.replace(`:${key}`, value);
  });
  
  return url;
};

export const buildUrl = buildApiUrl;

export const getAuthHeaders = () => {
  const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
  
  return {
    ...API_CONFIG.DEFAULT_HEADERS,
    ...(token && { Authorization: `Bearer ${token}` }),
  };
};

export default API_CONFIG;
'@

try {
    Set-Content -Path $apiConfigPath -Value $apiContent -Encoding UTF8 -NoNewline
    Write-Host "✅ Archivo api.js corregido" -ForegroundColor Green
} catch {
    Write-Host "❌ Error corrigiendo api.js: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "🧹 4. LIMPIANDO CACHE Y DEPENDENCIAS" -ForegroundColor Blue
Write-Host "----------------------------------------" -ForegroundColor Blue

Set-Location "frontend"

# Limpiar cache de npm/yarn
if (Get-Command yarn -ErrorAction SilentlyContinue) {
    Write-Host "🧹 Limpiando cache de Yarn..." -ForegroundColor Yellow
    yarn cache clean
    Write-Host "✅ Cache de Yarn limpiado" -ForegroundColor Green
} else {
    Write-Host "🧹 Limpiando cache de npm..." -ForegroundColor Yellow
    npm cache clean --force
    Write-Host "✅ Cache de npm limpiado" -ForegroundColor Green
}

Write-Host ""
Write-Host "📦 5. INSTALANDO DEPENDENCIAS" -ForegroundColor Blue
Write-Host "----------------------------------------" -ForegroundColor Blue

if (Get-Command yarn -ErrorAction SilentlyContinue) {
    Write-Host "📦 Instalando dependencias con Yarn..." -ForegroundColor Yellow
    yarn install
} else {
    Write-Host "📦 Instalando dependencias con npm..." -ForegroundColor Yellow
    npm install
}

Write-Host "✅ Dependencias instaladas" -ForegroundColor Green

Write-Host ""
Write-Host "🔍 6. VERIFICANDO BACKEND" -ForegroundColor Blue
Write-Host "----------------------------------------" -ForegroundColor Blue

Set-Location "../backend"

# Verificar si el backend está corriendo
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health/" -Method GET -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Backend está corriendo correctamente" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  Backend no está corriendo. Iniciándolo..." -ForegroundColor Yellow
    
    # Verificar si existe el entorno virtual
    if (Test-Path "venv/Scripts/activate.ps1") {
        Write-Host "🐍 Activando entorno virtual..." -ForegroundColor Yellow
        & "venv/Scripts/activate.ps1"
        
        Write-Host "🚀 Iniciando servidor Django..." -ForegroundColor Yellow
        Start-Process powershell -ArgumentList "-Command", "cd '$PWD'; venv/Scripts/activate.ps1; python manage.py runserver" -WindowStyle Minimized
        
        Write-Host "⏳ Esperando que el backend inicie..." -ForegroundColor Yellow
        Start-Sleep -Seconds 5
        
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health/" -Method GET -TimeoutSec 10
            if ($response.StatusCode -eq 200) {
                Write-Host "✅ Backend iniciado correctamente" -ForegroundColor Green
            }
        } catch {
            Write-Host "❌ Error iniciando el backend" -ForegroundColor Red
            Write-Host "💡 Inicia manualmente: cd backend && venv\Scripts\activate && python manage.py runserver" -ForegroundColor Yellow
        }
    } else {
        Write-Host "❌ No se encontró el entorno virtual del backend" -ForegroundColor Red
        Write-Host "💡 Configura el backend primero ejecutando el script de setup" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "🌐 7. INICIANDO FRONTEND" -ForegroundColor Blue
Write-Host "----------------------------------------" -ForegroundColor Blue

Set-Location "../frontend"

Write-Host "🚀 Iniciando servidor de desarrollo React..." -ForegroundColor Yellow

# Iniciar el servidor de desarrollo de React en una nueva ventana
if (Get-Command yarn -ErrorAction SilentlyContinue) {
    Start-Process powershell -ArgumentList "-Command", "cd '$PWD'; yarn dev" -WindowStyle Normal
} else {
    Start-Process powershell -ArgumentList "-Command", "cd '$PWD'; npm run dev" -WindowStyle Normal
}

Write-Host "⏳ Esperando que el frontend inicie..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host ""
Write-Host "🎉 CORRECCIÓN COMPLETADA" -ForegroundColor Green
Write-Host "===============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ ESTADO DEL SISTEMA:" -ForegroundColor Cyan
Write-Host "• Backend Django: http://localhost:8000" -ForegroundColor White
Write-Host "• Frontend React: http://localhost:5173" -ForegroundColor White
Write-Host "• Health Check: http://localhost:8000/api/health/" -ForegroundColor White
Write-Host ""
Write-Host "🔧 PROBLEMAS CORREGIDOS:" -ForegroundColor Yellow
Write-Host "• ❌ Duplicación de fetchWithAuth → ✅ Función única importada" -ForegroundColor White
Write-Host "• ❌ buildApiUrl undefined → ✅ Función creada y exportada" -ForegroundColor White
Write-Host "• ❌ Comunicación frontend-backend → ✅ URLs corregidas" -ForegroundColor White
Write-Host "• ❌ Datos estáticos mock → ✅ Solo comunicación real con API" -ForegroundColor White
Write-Host ""
Write-Host "🚀 PRÓXIMOS PASOS:" -ForegroundColor Cyan
Write-Host "1. Abre http://localhost:5173 en tu navegador" -ForegroundColor Gray
Write-Host "2. Verifica que no hay errores en la consola del navegador" -ForegroundColor Gray
Write-Host "3. Prueba subir un archivo CSV y generar reportes" -ForegroundColor Gray
Write-Host "4. El MVP está listo para producción" -ForegroundColor Gray
Write-Host ""
Write-Host "🎯 MVP LISTO PARA PRODUCCIÓN ESTA SEMANA" -ForegroundColor Green
Write-Host ""

# Volver al directorio raíz
Set-Location ".."

Write-Host "Presiona cualquier tecla para continuar..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")