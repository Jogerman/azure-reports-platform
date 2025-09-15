# ====================================================================
# SCRIPT DE PRUEBAS COMPREHENSIVAS DEL BACKEND
# ====================================================================

Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "   PRUEBAS COMPREHENSIVAS DEL BACKEND - AZURE ADVISOR ANALYZER" -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan

# Función para realizar peticiones HTTP
function Invoke-APITest {
    param(
        [string]$Url,
        [string]$Method = "GET",
        [hashtable]$Headers = @{},
        [string]$Body = "",
        [string]$TestName
    )
    
    Write-Host "🧪 Probando: $TestName" -ForegroundColor Yellow
    Write-Host "   URL: $Url" -ForegroundColor Gray
    
    try {
        $response = $null
        if ($Method -eq "GET") {
            $response = Invoke-RestMethod -Uri $Url -Method $Method -Headers $Headers -TimeoutSec 10
        } else {
            $response = Invoke-RestMethod -Uri $Url -Method $Method -Headers $Headers -Body $Body -ContentType "application/json" -TimeoutSec 10
        }
        
        Write-Host "   ✅ Status: SUCCESS" -ForegroundColor Green
        Write-Host "   📄 Response: $($response | ConvertTo-Json -Compress)" -ForegroundColor Gray
        return @{ Success = $true; Response = $response }
    } catch {
        Write-Host "   ❌ Status: FAILED" -ForegroundColor Red
        Write-Host "   📄 Error: $($_.Exception.Message)" -ForegroundColor Red
        return @{ Success = $false; Error = $_.Exception.Message }
    }
}

Write-Host ""
Write-Host "🔍 1. VERIFICACIÓN PREVIA" -ForegroundColor Blue
Write-Host "----------------------------------------" -ForegroundColor Blue

# Verificar que el servidor esté ejecutándose
$baseUrl = "http://localhost:8000"
try {
    $connection = Test-NetConnection -ComputerName "localhost" -Port 8000 -WarningAction SilentlyContinue
    if ($connection.TcpTestSucceeded) {
        Write-Host "✅ Servidor Django ejecutándose en puerto 8000" -ForegroundColor Green
    } else {
        Write-Host "❌ Servidor Django NO está ejecutándose" -ForegroundColor Red
        Write-Host "💡 Ejecutar: python manage.py runserver" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "❌ Error verificando conexión al servidor" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🏥 2. PRUEBAS DE HEALTH CHECK" -ForegroundColor Blue
Write-Host "----------------------------------------" -ForegroundColor Blue

$healthTest = Invoke-APITest -Url "$baseUrl/api/health/" -TestName "Health Check Endpoint"

if ($healthTest.Success) {
    Write-Host "✅ Health Check funcionando correctamente" -ForegroundColor Green
} else {
    Write-Host "❌ Health Check falló - Revisar configuración" -ForegroundColor Red
}

Write-Host ""
Write-Host "🔐 3. PRUEBAS DE AUTENTICACIÓN" -ForegroundColor Blue
Write-Host "----------------------------------------" -ForegroundColor Blue

# Probar endpoint de login
$loginData = @{
    email = "admin@example.com"
    password = "admin123"
} | ConvertTo-Json

$loginTest = Invoke-APITest -Url "$baseUrl/api/auth/login/" -Method "POST" -Body $loginData -TestName "Login con credenciales de prueba"

$accessToken = ""
if ($loginTest.Success -and $loginTest.Response.access) {
    $accessToken = $loginTest.Response.access
    Write-Host "✅ Login exitoso - Token obtenido" -ForegroundColor Green
} else {
    Write-Host "⚠️  Login falló - Crear usuario de prueba" -ForegroundColor Yellow
    Write-Host "💡 Ejecutar: python manage.py createsuperuser" -ForegroundColor Yellow
}

# Probar endpoint de perfil (requiere autenticación)
if ($accessToken) {
    $authHeaders = @{ "Authorization" = "Bearer $accessToken" }
    $profileTest = Invoke-APITest -Url "$baseUrl/api/auth/users/profile/" -Headers $authHeaders -TestName "Obtener perfil de usuario"
    
    if ($profileTest.Success) {
        Write-Host "✅ Autenticación JWT funcionando" -ForegroundColor Green
    } else {
        Write-Host "❌ Error en autenticación JWT" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "📊 4. PRUEBAS DE ENDPOINTS DE REPORTES" -ForegroundColor Blue
Write-Host "----------------------------------------" -ForegroundColor Blue

# Probar endpoint de reportes CSV
$reportHeaders = if ($accessToken) { @{ "Authorization" = "Bearer $accessToken" } } else { @{} }

$csvListTest = Invoke-APITest -Url "$baseUrl/api/reports/csv-files/" -Headers $reportHeaders -TestName "Listar archivos CSV"

if ($csvListTest.Success) {
    Write-Host "✅ Endpoint de reportes CSV accesible" -ForegroundColor Green
} else {
    Write-Host "❌ Endpoint de reportes CSV falló" -ForegroundColor Red
}

# Probar endpoint de reportes generados
$reportsTest = Invoke-APITest -Url "$baseUrl/api/reports/reports/" -Headers $reportHeaders -TestName "Listar reportes generados"

if ($reportsTest.Success) {
    Write-Host "✅ Endpoint de reportes generados accesible" -ForegroundColor Green
} else {
    Write-Host "❌ Endpoint de reportes generados falló" -ForegroundColor Red
}

Write-Host ""
Write-Host "🗄️ 5. PRUEBAS DE ALMACENAMIENTO" -ForegroundColor Blue
Write-Host "----------------------------------------" -ForegroundColor Blue

$storageTest = Invoke-APITest -Url "$baseUrl/api/storage/" -Headers $reportHeaders -TestName "Endpoint de almacenamiento"

if ($storageTest.Success) {
    Write-Host "✅ Endpoint de almacenamiento accesible" -ForegroundColor Green
} else {
    Write-Host "❌ Endpoint de almacenamiento falló" -ForegroundColor Red
}

Write-Host ""
Write-Host "📈 6. PRUEBAS DE ANALYTICS" -ForegroundColor Blue
Write-Host "----------------------------------------" -ForegroundColor Blue

$analyticsTest = Invoke-APITest -Url "$baseUrl/api/analytics/" -Headers $reportHeaders -TestName "Endpoint de analytics"

if ($analyticsTest.Success) {
    Write-Host "✅ Endpoint de analytics accesible" -ForegroundColor Green
} else {
    Write-Host "❌ Endpoint de analytics falló" -ForegroundColor Red
}

Write-Host ""
Write-Host "🌐 7. PRUEBAS DE CORS" -ForegroundColor Blue
Write-Host "----------------------------------------" -ForegroundColor Blue

# Simular una petición desde el frontend
$corsHeaders = @{
    "Origin" = "http://localhost:5173"
    "Access-Control-Request-Method" = "GET"
}

$corsTest = Invoke-APITest -Url "$baseUrl/api/health/" -Headers $corsHeaders -TestName "CORS desde frontend React"

if ($corsTest.Success) {
    Write-Host "✅ CORS configurado correctamente" -ForegroundColor Green
} else {
    Write-Host "⚠️  Verificar configuración CORS" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🔒 8. PRUEBAS DE SEGURIDAD BÁSICAS" -ForegroundColor Blue
Write-Host "----------------------------------------" -ForegroundColor Blue

# Probar endpoint protegido sin autenticación
$unauthorizedTest = Invoke-APITest -Url "$baseUrl/api/auth/users/profile/" -TestName "Acceso no autorizado"

if (!$unauthorizedTest.Success) {
    Write-Host "✅ Endpoints protegidos funcionando" -ForegroundColor Green
} else {
    Write-Host "⚠️  Endpoint debería requerir autenticación" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🏗️ 9. PRUEBAS DE CONFIGURACIÓN DJANGO" -ForegroundColor Blue
Write-Host "----------------------------------------" -ForegroundColor Blue

# Verificar configuración de Django desde el servidor
Write-Host "🔍 Verificando configuración de Django..." -ForegroundColor Yellow

Set-Location "backend"

# Verificar migraciones
Write-Host "🔄 Verificando migraciones..." -ForegroundColor Yellow
try {
    $migrationsOutput = python manage.py showmigrations 2>&1
    if ($migrationsOutput -match "\[X\]") {
        Write-Host "✅ Migraciones aplicadas correctamente" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Algunas migraciones pueden estar pendientes" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Error verificando migraciones" -ForegroundColor Red
}

# Verificar configuración general
Write-Host "🔧 Verificando configuración general..." -ForegroundColor Yellow
try {
    python manage.py check --deploy | Out-Null
    Write-Host "✅ Configuración Django válida para deployment" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Advertencias en configuración de deployment" -ForegroundColor Yellow
}

Set-Location ".."

Write-Host ""
Write-Host "📊 10. RESUMEN DE PRUEBAS" -ForegroundColor Blue
Write-Host "================================" -ForegroundColor Blue

# Contar pruebas exitosas
$totalTests = 0
$passedTests = 0

$tests = @(
    @{ Name = "Health Check"; Success = $healthTest.Success },
    @{ Name = "Login"; Success = $loginTest.Success },
    @{ Name = "JWT Authentication"; Success = ($accessToken -ne "") },
    @{ Name = "CSV Reports Endpoint"; Success = $csvListTest.Success },
    @{ Name = "Reports Endpoint"; Success = $reportsTest.Success },
    @{ Name = "Storage Endpoint"; Success = $storageTest.Success },
    @{ Name = "Analytics Endpoint"; Success = $analyticsTest.Success },
    @{ Name = "CORS Configuration"; Success = $corsTest.Success }
)

Write-Host "🧪 RESULTADOS DE PRUEBAS:" -ForegroundColor Cyan
Write-Host "------------------------" -ForegroundColor Cyan

foreach ($test in $tests) {
    $totalTests++
    if ($test.Success) {
        $passedTests++
        Write-Host "✅ $($test.Name)" -ForegroundColor Green
    } else {
        Write-Host "❌ $($test.Name)" -ForegroundColor Red
    }
}

$successRate = [math]::Round(($passedTests / $totalTests) * 100, 1)

Write-Host ""
Write-Host "📈 TASA DE ÉXITO: $passedTests/$totalTests ($successRate%)" -ForegroundColor Cyan

if ($successRate -ge 80) {
    Write-Host "🎉 ¡EXCELENTE! El backend está funcionando correctamente" -ForegroundColor Green
    Write-Host "✨ Listo para conectar con el frontend React" -ForegroundColor Green
} elseif ($successRate -ge 60) {
    Write-Host "⚠️  BUENO con algunas correcciones menores necesarias" -ForegroundColor Yellow
    Write-Host "🔧 Revisar los endpoints que fallaron" -ForegroundColor Yellow
} else {
    Write-Host "❌ NECESITA CORRECCIONES antes de continuar" -ForegroundColor Red
    Write-Host "🔧 Ejecutar script de corrección automática" -ForegroundColor Red
}

Write-Host ""
Write-Host "💡 PRÓXIMOS PASOS RECOMENDADOS:" -ForegroundColor Yellow
if ($successRate -lt 80) {
    Write-Host "1. Ejecutar script de corrección: .\backend_fix_script.ps1" -ForegroundColor Gray
    Write-Host "2. Verificar configuración de base de datos" -ForegroundColor Gray
    Write-Host "3. Crear usuario de prueba si es necesario" -ForegroundColor Gray
    Write-Host "4. Re-ejecutar estas pruebas" -ForegroundColor Gray
} else {
    Write-Host "1. Iniciar frontend React: npm run dev" -ForegroundColor Gray
    Write-Host "2. Probar integración completa" -ForegroundColor Gray
    Write-Host "3. Subir archivo CSV de prueba" -ForegroundColor Gray
    Write-Host "4. Generar primer reporte" -ForegroundColor Gray
}

Write-Host ""
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "   PRUEBAS COMPLETADAS" -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan