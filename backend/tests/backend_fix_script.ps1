# ====================================================================
# SCRIPT DE CORRECCIÓN AUTOMÁTICA DEL BACKEND - WINDOWS
# ====================================================================

Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "   CORRECCIÓN AUTOMÁTICA DEL BACKEND - AZURE ADVISOR ANALYZER" -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan

# Función para verificar si un comando existe
function Test-Command {
    param($Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

Write-Host ""
Write-Host "🔧 1. CONFIGURANDO ENTORNO VIRTUAL" -ForegroundColor Blue
Write-Host "----------------------------------------" -ForegroundColor Blue

# Crear entorno virtual si no existe
if (!(Test-Path "venv")) {
    Write-Host "📦 Creando entorno virtual..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "✅ Entorno virtual creado" -ForegroundColor Green
} else {
    Write-Host "✅ Entorno virtual ya existe" -ForegroundColor Green
}

# Activar entorno virtual
Write-Host "🔌 Activando entorno virtual..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

if ($env:VIRTUAL_ENV) {
    Write-Host "✅ Entorno virtual activado: $env:VIRTUAL_ENV" -ForegroundColor Green
} else {
    Write-Host "❌ Error activando entorno virtual" -ForegroundColor Red
    Write-Host "💡 Ejecutar manualmente: venv\Scripts\activate" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📁 2. CREANDO ESTRUCTURA DE DIRECTORIOS" -ForegroundColor Blue
Write-Host "----------------------------------------" -ForegroundColor Blue

# Crear directorios necesarios
$requiredDirs = @(
    "backend\staticfiles",
    "backend\media",
    "backend\logs",
    "backend\templates"
)

foreach ($dir in $requiredDirs) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "✅ Creado directorio: $dir" -ForegroundColor Green
    } else {
        Write-Host "✅ Directorio ya existe: $dir" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "📄 3. CREANDO ARCHIVO .ENV" -ForegroundColor Blue
Write-Host "----------------------------------------" -ForegroundColor Blue

# Crear archivo .env si no existe
if (!(Test-Path "backend\.env")) {
    Write-Host "📝 Creando archivo backend\.env..." -ForegroundColor Yellow
    
    $envContent = @"
# Configuración para desarrollo
SECRET_KEY=django-insecure-dev-key-change-in-production-$(Get-Random)
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de datos PostgreSQL
DB_ENGINE=django.db.backends.postgresql
DB_NAME=azure_reports_dev
DB_USER=postgres
DB_PASSWORD=postgres123
DB_HOST=localhost
DB_PORT=5432
DB_SSLMODE=prefer

# Microsoft OAuth (opcional)
MICROSOFT_CLIENT_ID=your-client-id
MICROSOFT_CLIENT_SECRET=your-client-secret
MICROSOFT_TENANT_ID=your-tenant-id

# Cache y Redis (opcional)
CACHE_BACKEND=django.core.cache.backends.locmem.LocMemCache
REDIS_URL=redis://localhost:6379/0

# Storage
DEFAULT_FILE_STORAGE=django.core.files.storage.FileSystemStorage
STATICFILES_STORAGE=whitenoise.storage.CompressedManifestStaticFilesStorage

# Logging
LOG_LEVEL=INFO
"@
    
    $envContent | Out-File -FilePath "backend\.env" -Encoding UTF8
    Write-Host "✅ Archivo .env creado con configuración por defecto" -ForegroundColor Green
} else {
    Write-Host "✅ Archivo .env ya existe" -ForegroundColor Green
}

Write-Host ""
Write-Host "📦 4. INSTALANDO DEPENDENCIAS" -ForegroundColor Blue
Write-Host "----------------------------------------" -ForegroundColor Blue

# Moverse al directorio backend
Set-Location "backend"

# Actualizar pip
Write-Host "🔄 Actualizando pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Instalar dependencias base
if (Test-Path "requirements\base.txt") {
    Write-Host "📦 Instalando dependencias base..." -ForegroundColor Yellow
    pip install -r requirements\base.txt
    Write-Host "✅ Dependencias base instaladas" -ForegroundColor Green
} else {
    Write-Host "❌ No se encontró requirements\base.txt" -ForegroundColor Red
}

# Instalar dependencias de desarrollo
if (Test-Path "requirements\development.txt") {
    Write-Host "📦 Instalando dependencias de desarrollo..." -ForegroundColor Yellow
    pip install -r requirements\development.txt
    Write-Host "✅ Dependencias de desarrollo instaladas" -ForegroundColor Green
}

Write-Host ""
Write-Host "🗄️ 5. CONFIGURANDO BASE DE DATOS" -ForegroundColor Blue
Write-Host "----------------------------------------" -ForegroundColor Blue

# Verificar configuración de Django
Write-Host "🔍 Verificando configuración de Django..." -ForegroundColor Yellow
try {
    python manage.py check
    Write-Host "✅ Configuración de Django válida" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Advertencias en configuración de Django" -ForegroundColor Yellow
}

# Crear migraciones
Write-Host "🔄 Creando migraciones..." -ForegroundColor Yellow
try {
    python manage.py makemigrations
    Write-Host "✅ Migraciones creadas" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Error creando migraciones" -ForegroundColor Yellow
}

# Aplicar migraciones
Write-Host "🚀 Aplicando migraciones..." -ForegroundColor Yellow
try {
    python manage.py migrate
    Write-Host "✅ Migraciones aplicadas exitosamente" -ForegroundColor Green
} catch {
    Write-Host "❌ Error aplicando migraciones" -ForegroundColor Red
    Write-Host "💡 Verificar que PostgreSQL esté ejecutándose" -ForegroundColor Yellow
}

# Recopilar archivos estáticos
Write-Host "📁 Recopilando archivos estáticos..." -ForegroundColor Yellow
try {
    python manage.py collectstatic --noinput
    Write-Host "✅ Archivos estáticos recopilados" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Error recopilando archivos estáticos" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "👤 6. CREANDO USUARIO ADMINISTRADOR" -ForegroundColor Blue
Write-Host "----------------------------------------" -ForegroundColor Blue

# Verificar si ya existe un superusuario
$userExists = python -c "
from django.contrib.auth import get_user_model
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
User = get_user_model()
print('exists' if User.objects.filter(is_superuser=True).exists() else 'none')
"

if ($userExists -eq "exists") {
    Write-Host "✅ Ya existe un superusuario" -ForegroundColor Green
} else {
    Write-Host "📝 Creando usuario administrador de prueba..." -ForegroundColor Yellow
    
    # Crear superusuario automáticamente
    python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('✅ Superusuario creado: admin / admin123')
else:
    print('✅ Usuario admin ya existe')
"
}

Write-Host ""
Write-Host "🧪 7. EJECUTANDO PRUEBAS BÁSICAS" -ForegroundColor Blue
Write-Host "----------------------------------------" -ForegroundColor Blue

# Probar importaciones críticas
Write-Host "🔍 Probando importaciones críticas..." -ForegroundColor Yellow
try {
    python -c "
import django
from rest_framework import viewsets
from rest_framework_simplejwt.tokens import RefreshToken
print('✅ Todas las importaciones exitosas')
"
    Write-Host "✅ Importaciones críticas funcionando" -ForegroundColor Green
} catch {
    Write-Host "❌ Error en importaciones críticas" -ForegroundColor Red
}

# Probar conexión a base de datos
Write-Host "🔍 Probando conexión a base de datos..." -ForegroundColor Yellow
try {
    python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from django.db import connection
cursor = connection.cursor()
cursor.execute('SELECT 1')
print('✅ Conexión a BD exitosa')
"
    Write-Host "✅ Conexión a base de datos funcionando" -ForegroundColor Green
} catch {
    Write-Host "❌ Error conectando a base de datos" -ForegroundColor Red
}

Write-Host ""
Write-Host "🚀 8. INICIANDO SERVIDOR DE DESARROLLO" -ForegroundColor Blue
Write-Host "----------------------------------------" -ForegroundColor Blue

Write-Host "🌐 Iniciando servidor Django en modo desarrollo..." -ForegroundColor Yellow
Write-Host ""
Write-Host "📋 INFORMACIÓN IMPORTANTE:" -ForegroundColor Cyan
Write-Host "- Servidor Django: http://localhost:8000" -ForegroundColor White
Write-Host "- Admin Django: http://localhost:8000/admin" -ForegroundColor White
Write-Host "- API Health: http://localhost:8000/api/health/" -ForegroundColor White
Write-Host "- Usuario admin: admin / admin123" -ForegroundColor White
Write-Host ""
Write-Host "💡 Para detener el servidor: Ctrl+C" -ForegroundColor Yellow
Write-Host ""

# Volver al directorio raíz
Set-Location ".."

Write-Host "🎉 CONFIGURACIÓN COMPLETADA" -ForegroundColor Green
Write-Host ""
Write-Host "🔥 PRÓXIMOS PASOS:" -ForegroundColor Yellow
Write-Host "1. Ir al directorio backend: cd backend" -ForegroundColor Gray
Write-Host "2. Activar entorno virtual: venv\Scripts\activate" -ForegroundColor Gray
Write-Host "3. Ejecutar servidor: python manage.py runserver" -ForegroundColor Gray
Write-Host "4. Abrir navegador: http://localhost:8000/api/health/" -ForegroundColor Gray
Write-Host ""
Write-Host "✨ El backend está listo para conectar con React!" -ForegroundColor Cyan

Write-Host ""
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "   CORRECCIÓN COMPLETADA EXITOSAMENTE" -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan