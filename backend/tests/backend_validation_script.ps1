# ====================================================================
# SCRIPT DE VALIDACIÓN DEL BACKEND - VERSIÓN SIMPLIFICADA
# ====================================================================

Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "   VALIDACIÓN DEL BACKEND - AZURE ADVISOR ANALYZER" -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan

# Variables para tracking de problemas
$issues = @()

Write-Host ""
Write-Host "🔍 1. VERIFICANDO PREREQUISITOS" -ForegroundColor Blue
Write-Host "--------------------------------" -ForegroundColor Blue

# Verificar Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python no encontrado" -ForegroundColor Red
    $issues += "Python no instalado"
}

# Verificar pip
try {
    $pipVersion = pip --version 2>&1
    Write-Host "✅ pip: $pipVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ pip no encontrado" -ForegroundColor Red
    $issues += "pip no instalado"
}

Write-Host ""
Write-Host "📁 2. VERIFICANDO ESTRUCTURA" -ForegroundColor Blue
Write-Host "----------------------------" -ForegroundColor Blue

# Directorios principales
$dirs = @("backend", "backend\config", "backend\apps", "backend\requirements")
foreach ($dir in $dirs) {
    if (Test-Path $dir) {
        Write-Host "✅ $dir" -ForegroundColor Green
    } else {
        Write-Host "❌ $dir faltante" -ForegroundColor Red
        $issues += "Directorio $dir faltante"
    }
}

# Archivos críticos
$files = @("backend\manage.py", "backend\config\settings.py", "backend\requirements\base.txt")
foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "✅ $file" -ForegroundColor Green
    } else {
        Write-Host "❌ $file faltante" -ForegroundColor Red
        $issues += "Archivo $file faltante"
    }
}

Write-Host ""
Write-Host "🔧 3. VERIFICANDO CONFIGURACIÓN" -ForegroundColor Blue
Write-Host "-------------------------------" -ForegroundColor Blue

# Verificar .env
if (Test-Path "backend\.env") {
    Write-Host "✅ Archivo .env encontrado" -ForegroundColor Green
    Write-Host "Contenido:" -ForegroundColor Yellow
    Get-Content "backend\.env" | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
} else {
    Write-Host "❌ Archivo .env faltante" -ForegroundColor Red
    $issues += "Archivo .env faltante"
}

Write-Host ""
Write-Host "🐍 4. VERIFICANDO ENTORNO VIRTUAL" -ForegroundColor Blue
Write-Host "--------------------------------" -ForegroundColor Blue

if ($env:VIRTUAL_ENV) {
    Write-Host "✅ Entorno virtual activo: $env:VIRTUAL_ENV" -ForegroundColor Green
} else {
    Write-Host "⚠️  Sin entorno virtual activo" -ForegroundColor Yellow
    $issues += "Entorno virtual no activo"
}

Write-Host ""
Write-Host "📦 5. VERIFICANDO DEPENDENCIAS" -ForegroundColor Blue
Write-Host "------------------------------" -ForegroundColor Blue

if (Test-Path "backend") {
    Set-Location "backend"
    
    try {
        $packages = pip list 2>&1
        
        if ($packages -match "Django") {
            Write-Host "✅ Django instalado" -ForegroundColor Green
        } else {
            Write-Host "❌ Django no instalado" -ForegroundColor Red
            $issues += "Django no instalado"
        }
        
        if ($packages -match "djangorestframework") {
            Write-Host "✅ Django REST Framework instalado" -ForegroundColor Green
        } else {
            Write-Host "❌ DRF no instalado" -ForegroundColor Red
            $issues += "Django REST Framework no instalado"
        }
        
    } catch {
        Write-Host "⚠️  No se pudieron verificar dependencias" -ForegroundColor Yellow
    }
    
    Set-Location ".."
}

Write-Host ""
Write-Host "🗄️ 6. VERIFICANDO BASE DE DATOS" -ForegroundColor Blue
Write-Host "-------------------------------" -ForegroundColor Blue

# Verificar PostgreSQL
try {
    $pgConnection = Test-NetConnection -ComputerName "localhost" -Port 5432 -WarningAction SilentlyContinue
    if ($pgConnection.TcpTestSucceeded) {
        Write-Host "✅ PostgreSQL ejecutándose (puerto 5432)" -ForegroundColor Green
    } else {
        Write-Host "❌ PostgreSQL no accesible" -ForegroundColor Red
        $issues += "PostgreSQL no ejecutándose"
    }
} catch {
    Write-Host "❌ Error verificando PostgreSQL" -ForegroundColor Red
    $issues += "Error verificando PostgreSQL"
}

Write-Host ""
Write-Host "🌐 7. VERIFICANDO SERVICIOS" -ForegroundColor Blue
Write-Host "---------------------------" -ForegroundColor Blue

# Verificar Django server
try {
    $djangoConnection = Test-NetConnection -ComputerName "localhost" -Port 8000 -WarningAction SilentlyContinue
    if ($djangoConnection.TcpTestSucceeded) {
        Write-Host "✅ Django server ejecutándose (puerto 8000)" -ForegroundColor Green
        
        # Probar health check
        try {
            $response = Invoke-RestMethod -Uri "http://localhost:8000/api/health/" -Method GET -TimeoutSec 5
            Write-Host "✅ Health check: $($response.status)" -ForegroundColor Green
        } catch {
            Write-Host "⚠️  Health check falló" -ForegroundColor Yellow
        }
        
    } else {
        Write-Host "❌ Django server no ejecutándose" -ForegroundColor Red
        $issues += "Django server no ejecutándose"
    }
} catch {
    Write-Host "❌ Error verificando Django server" -ForegroundColor Red
    $issues += "Error verificando Django server"
}

# Verificar React frontend
try {
    $reactConnection = Test-NetConnection -ComputerName "localhost" -Port 5173 -WarningAction SilentlyContinue
    if ($reactConnection.TcpTestSucceeded) {
        Write-Host "✅ React frontend ejecutándose (puerto 5173)" -ForegroundColor Green
    } else {
        Write-Host "⚠️  React frontend no ejecutándose" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  React frontend no verificable" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📊 8. RESUMEN" -ForegroundColor Blue
Write-Host "=============" -ForegroundColor Blue

if ($issues.Count -eq 0) {
    Write-Host "🎉 ¡PERFECTO! Backend completamente funcional" -ForegroundColor Green
    Write-Host ""
    Write-Host "✅ Todos los componentes verificados" -ForegroundColor Green
    Write-Host "✅ Servicios ejecutándose correctamente" -ForegroundColor Green
    Write-Host "✅ Listo para desarrollo" -ForegroundColor Green
} else {
    Write-Host "⚠️  PROBLEMAS ENCONTRADOS:" -ForegroundColor Yellow
    foreach ($issue in $issues) {
        Write-Host "  ❌ $issue" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "💡 PRÓXIMOS PASOS:" -ForegroundColor Yellow

if ($issues.Count -gt 0) {
    Write-Host "1. Resolver problemas listados arriba" -ForegroundColor Gray
    
    if ($issues -contains "Archivo .env faltante") {
        Write-Host "2. Crear backend\.env:" -ForegroundColor Gray
        Write-Host "   SECRET_KEY=tu-secret-key" -ForegroundColor Gray
        Write-Host "   DEBUG=True" -ForegroundColor Gray
        Write-Host "   DB_NAME=azure_reports_dev" -ForegroundColor Gray
    }
    
    if ($issues -contains "Entorno virtual no activo") {
        Write-Host "3. Activar entorno virtual: venv\Scripts\activate" -ForegroundColor Gray
    }
    
    if ($issues -contains "Django no instalado") {
        Write-Host "4. Instalar dependencias: pip install -r requirements\base.txt" -ForegroundColor Gray
    }
    
    if ($issues -contains "Django server no ejecutándose") {
        Write-Host "5. Iniciar servidor: python manage.py runserver" -ForegroundColor Gray
    }
} else {
    Write-Host "1. Backend está funcionando ✅" -ForegroundColor Green
    Write-Host "2. Continuar con testing de funcionalidades" -ForegroundColor Gray
    Write-Host "3. Conectar con frontend React" -ForegroundColor Gray
}

Write-Host ""
Write-Host "🧰 COMANDOS ÚTILES:" -ForegroundColor Blue
Write-Host "# Activar entorno virtual:" -ForegroundColor Yellow
Write-Host "venv\Scripts\activate" -ForegroundColor Gray
Write-Host ""
Write-Host "# Navegar al backend:" -ForegroundColor Yellow
Write-Host "cd backend" -ForegroundColor Gray
Write-Host ""
Write-Host "# Instalar dependencias:" -ForegroundColor Yellow
Write-Host "pip install -r requirements\base.txt" -ForegroundColor Gray
Write-Host ""
Write-Host "# Configurar BD:" -ForegroundColor Yellow
Write-Host "python manage.py migrate" -ForegroundColor Gray
Write-Host ""
Write-Host "# Iniciar servidor:" -ForegroundColor Yellow
Write-Host "python manage.py runserver" -ForegroundColor Gray

Write-Host ""
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "   VALIDACIÓN COMPLETADA" -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan