# validate_real_data_implementation.ps1
# Script de validación para verificar que la migración a datos reales funciona correctamente
# Ejecutar como: PowerShell -ExecutionPolicy Bypass -File validate_real_data_implementation.ps1

param(
    [string]$ProjectPath = ".",
    [string]$CSVTestFile = "ejemplo 2.csv"
)

$ErrorActionPreference = "Continue"

# Colores para output
function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    
    switch ($Color) {
        "Red" { Write-Host $Message -ForegroundColor Red }
        "Green" { Write-Host $Message -ForegroundColor Green }
        "Yellow" { Write-Host $Message -ForegroundColor Yellow }
        "Blue" { Write-Host $Message -ForegroundColor Blue }
        "Cyan" { Write-Host $Message -ForegroundColor Cyan }
        default { Write-Host $Message }
    }
}

function Write-TestResult {
    param([bool]$Passed, [string]$TestName, [string]$Details = "")
    
    if ($Passed) {
        Write-ColorOutput "✅ PASS: $TestName" "Green"
        if ($Details) { Write-ColorOutput "   → $Details" "Gray" }
    } else {
        Write-ColorOutput "❌ FAIL: $TestName" "Red"
        if ($Details) { Write-ColorOutput "   → $Details" "Gray" }
    }
}

function Write-Section {
    param([string]$Title)
    Write-ColorOutput "`n📋 $Title" "Cyan"
    Write-ColorOutput "=" * 60 "Blue"
}

# Función para verificar archivos clave
function Test-KeyFiles {
    Write-Section "Verificando Archivos Clave"
    
    $KeyFiles = @{
        "backend/apps/reports/services/csv_analyzer.py" = "Servicio de análisis CSV"
        "backend/apps/reports/services/__init__.py" = "Init del módulo services"
        "frontend/src/hooks/useRealData.js" = "Hook para datos reales"
        "frontend/src/pages/Dashboard.jsx" = "Dashboard actualizado"
    }
    
    $AllPresent = $true
    
    foreach ($File in $KeyFiles.Keys) {
        $FullPath = Join-Path $ProjectPath $File
        $Description = $KeyFiles[$File]
        
        if (Test-Path $FullPath) {
            $Size = (Get-Item $FullPath).Length
            Write-TestResult $true "Archivo existe: $File" "$Description ($Size bytes)"
        } else {
            Write-TestResult $false "Archivo faltante: $File" $Description
            $AllPresent = $false
        }
    }
    
    return $AllPresent
}

# Función para verificar dependencias Python
function Test-PythonDependencies {
    Write-Section "Verificando Dependencias de Python"
    
    Push-Location (Join-Path $ProjectPath "backend")
    
    # Activar entorno virtual si existe
    if (Test-Path "venv/Scripts/Activate.ps1") {
        & "venv/Scripts/Activate.ps1"
        Write-ColorOutput "Entorno virtual activado" "Blue"
    }
    
    $Dependencies = @("pandas", "numpy", "django")
    $AllInstalled = $true
    
    foreach ($Dep in $Dependencies) {
        try {
            $Result = python -c "import $Dep; print($Dep.__version__)" 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-TestResult $true "Dependencia: $Dep" "Versión: $Result"
            } else {
                Write-TestResult $false "Dependencia: $Dep" "No instalada"
                $AllInstalled = $false
            }
        } catch {
            Write-TestResult $false "Dependencia: $Dep" "Error verificando"
            $AllInstalled = $false
        }
    }
    
    Pop-Location
    return $AllInstalled
}

# Función para probar el analizador CSV
function Test-CSVAnalyzer {
    Write-Section "Probando Analizador CSV"
    
    Push-Location (Join-Path $ProjectPath "backend")
    
    if (Test-Path "venv/Scripts/Activate.ps1") {
        & "venv/Scripts/Activate.ps1"
    }
    
    # Crear script de prueba
    $TestScript = @"
import sys
import os
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from apps.reports.services.csv_analyzer import analyze_csv_content

# CSV de prueba
test_csv = '''Category,Business Impact,Recommendation,Type,Resource Name
Cost,High,Test recommendation 1,Virtual machine,vm-001  
Security,Medium,Test recommendation 2,Storage Account,storage-001
Reliability,High,Test recommendation 3,Virtual machine,vm-002'''

try:
    result = analyze_csv_content(test_csv)
    print('SUCCESS: Análisis completado')
    print(f'Total recomendaciones: {result["basic_metrics"]["total_recommendations"]}')
    print(f'Categorías encontradas: {list(result["category_analysis"]["counts"].keys())}')
    print(f'Calidad de datos: {result["basic_metrics"]["data_quality_score"]}%')
except Exception as e:
    print(f'ERROR: {str(e)}')
    sys.exit(1)
"@
    
    $TestScript | python
    $AnalyzerWorked = $LASTEXITCODE -eq 0
    
    Write-TestResult $AnalyzerWorked "Analizador CSV funciona" $(if ($AnalyzerWorked) { "Análisis de prueba exitoso" } else { "Error en análisis" })
    
    Pop-Location
    return $AnalyzerWorked
}

# Función para verificar dependencias del frontend
function Test-FrontendDependencies {
    Write-Section "Verificando Frontend"
    
    Push-Location (Join-Path $ProjectPath "frontend")
    
    $PackageJsonPath = "package.json"
    $NodeModulesPath = "node_modules"
    
    # Verificar package.json
    if (Test-Path $PackageJsonPath) {
        Write-TestResult $true "package.json existe" "Configuración presente"
        
        # Verificar dependencias específicas
        $PackageContent = Get-Content $PackageJsonPath -Raw
        $HasChartJs = $PackageContent -match "chart\.js"
        $HasReactQuery = $PackageContent -match "@tanstack/react-query"
        
        Write-TestResult $HasChartJs "Chart.js configurado" $(if ($HasChartJs) { "Para visualizaciones" } else { "Falta para gráficos" })
        Write-TestResult $HasReactQuery "React Query configurado" $(if ($HasReactQuery) { "Para manejo de estado" } else { "Para API calls" })
    } else {
        Write-TestResult $false "package.json no encontrado" "Configuración faltante"
        Pop-Location
        return $false
    }
    
    # Verificar node_modules
    if (Test-Path $NodeModulesPath) {
        $ModulesSize = (Get-ChildItem $NodeModulesPath -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
        Write-TestResult $true "node_modules existe" "$([math]::Round($ModulesSize, 1)) MB"
    } else {
        Write-TestResult $false "node_modules faltante" "Ejecutar: npm install"
        Pop-Location
        return $false
    }
    
    Pop-Location
    return $true
}

# Función para probar la API
function Test-APIEndpoints {
    Write-Section "Probando API Endpoints"
    
    # Verificar si el servidor Django está corriendo
    try {
        $Response = Invoke-WebRequest -Uri "http://localhost:8000/api/analytics/stats/" -Method GET -ErrorAction Stop
        $StatusCode = $Response.StatusCode
        
        if ($StatusCode -eq 200) {
            $Content = $Response.Content | ConvertFrom-Json
            $DataSource = $Content.data_source
            
            Write-TestResult $true "API Stats endpoint" "Status: $StatusCode, DataSource: $DataSource"
            
            # Verificar estructura de respuesta
            $HasRequiredFields = $Content.PSObject.Properties.Name -contains "total_recommendations" -and
                                $Content.PSObject.Properties.Name -contains "data_source"
            
            Write-TestResult $HasRequiredFields "Estructura API correcta" $(if ($HasRequiredFields) { "Campos requeridos presentes" } else { "Faltan campos" })
            
            return $true
        }
    } catch {
        Write-TestResult $false "API no responde" "¿Está el servidor Django corriendo en puerto 8000?"
        return $false
    }
}

# Función para probar con CSV real
function Test-RealCSVProcessing {
    Write-Section "Probando Procesamiento CSV Real"
    
    $CSVPath = Join-Path $ProjectPath $CSVTestFile
    
    if (-not (Test-Path $CSVPath)) {
        Write-TestResult $false "CSV de prueba no encontrado" "Archivo: $CSVTestFile"
        return $false
    }
    
    # Verificar contenido del CSV
    $CSVContent = Get-Content $CSVPath -First 5
    $HasHeaders = $CSVContent[0] -match "Category.*Business Impact.*Recommendation"
    
    Write-TestResult $HasHeaders "CSV tiene estructura correcta" $(if ($HasHeaders) { "Headers válidos" } else { "Headers incorrectos" })
    
    if ($HasHeaders) {
        $TotalLines = (Get-Content $CSVPath).Count - 1  # -1 para excluir header
        Write-TestResult $true "CSV contiene datos" "$TotalLines filas de datos"
        
        # Probar análisis del CSV real
        Push-Location (Join-Path $ProjectPath "backend")
        
        if (Test-Path "venv/Scripts/Activate.ps1") {
            & "venv/Scripts/Activate.ps1"
        }
        
        $RealTestScript = @"
import sys
import os
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from apps.reports.services.csv_analyzer import analyze_csv_content

try:
    with open('../$CSVTestFile', 'r', encoding='utf-8-sig') as f:
        csv_content = f.read()
    
    result = analyze_csv_content(csv_content)
    
    print('SUCCESS: CSV real analizado')
    print(f'Total recomendaciones: {result["basic_metrics"]["total_recommendations"]}')
    print(f'Categorías: {", ".join(result["category_analysis"]["counts"].keys())}')
    print(f'Ahorro mensual estimado: {result["dashboard_metrics"]["estimated_monthly_optimization"]}')
    print(f'Horas de trabajo: {result["dashboard_metrics"]["working_hours"]}')
    
except Exception as e:
    print(f'ERROR: {str(e)}')
    sys.exit(1)
"@
        
        $RealTestScript | python
        $RealAnalysisWorked = $LASTEXITCODE -eq 0
        
        Write-TestResult $RealAnalysisWorked "Análisis CSV real" $(if ($RealAnalysisWorked) { "Procesamiento exitoso" } else { "Error en procesamiento" })
        
        Pop-Location
        return $RealAnalysisWorked
    }
    
    return $false
}

# Función para generar reporte de validación
function Generate-ValidationReport {
    param([hashtable]$TestResults)
    
    Write-Section "Reporte de Validación"
    
    $Passed = 0
    $Total = 0
    
    foreach ($Test in $TestResults.Keys) {
        $Total++
        if ($TestResults[$Test]) { $Passed++ }
    }
    
    $SuccessRate = [math]::Round(($Passed / $Total) * 100, 1)
    
    Write-ColorOutput "`n📊 RESUMEN DE VALIDACIÓN:" "Cyan"
    Write-ColorOutput "Total de pruebas: $Total" "White"
    Write-ColorOutput "Pruebas exitosas: $Passed" "Green"
    Write-ColorOutput "Pruebas fallidas: $($Total - $Passed)" "Red"
    Write-ColorOutput "Tasa de éxito: $SuccessRate%" $(if ($SuccessRate -ge 80) { "Green" } else { "Red" })
    
    if ($SuccessRate -ge 90) {
        Write-ColorOutput "`n🎉 ¡IMPLEMENTACIÓN EXITOSA!" "Green"
        Write-ColorOutput "Tu aplicación está lista para usar análisis real de CSV" "Green"
    } elseif ($SuccessRate -ge 70) {
        Write-ColorOutput "`n⚠️  IMPLEMENTACIÓN PARCIAL" "Yellow"
        Write-ColorOutput "La mayoría de funciones están listas, revisa los errores" "Yellow"
    } else {
        Write-ColorOutput "`n❌ IMPLEMENTACIÓN INCOMPLETA" "Red"
        Write-ColorOutput "Hay problemas significativos que resolver" "Red"
    }
    
    # Recomendaciones
    Write-ColorOutput "`n💡 PRÓXIMOS PASOS:" "Cyan"
    
    if (-not $TestResults["KeyFiles"]) {
        Write-ColorOutput "• Ejecuta el script de migración principal" "Yellow"
    }
    
    if (-not $TestResults["PythonDeps"]) {
        Write-ColorOutput "• Instala dependencias Python: pip install pandas numpy" "Yellow"
    }
    
    if (-not $TestResults["CSVAnalyzer"]) {
        Write-ColorOutput "• Verifica configuración Django y path de módulos" "Yellow"
    }
    
    if (-not $TestResults["APIEndpoints"]) {
        Write-ColorOutput "• Inicia el servidor Django: python manage.py runserver" "Yellow"
    }
    
    if ($SuccessRate -ge 90) {
        Write-ColorOutput "• Inicia la aplicación y sube un archivo CSV" "Green"
        Write-ColorOutput "• Verifica que las métricas se actualicen automáticamente" "Green"
    }
}

# FUNCIÓN PRINCIPAL
function Main {
    Write-ColorOutput "🧪 VALIDACIÓN DE IMPLEMENTACIÓN - ANÁLISIS REAL CSV" "Magenta"
    Write-ColorOutput "=" * 80 "Blue"
    Write-ColorOutput "Verificando que la migración a datos reales funciona correctamente..." "White"
    Write-ColorOutput ""
    
    # Ejecutar todas las pruebas
    $TestResults = @{}
    
    $TestResults["KeyFiles"] = Test-KeyFiles
    $TestResults["PythonDeps"] = Test-PythonDependencies
    $TestResults["CSVAnalyzer"] = Test-CSVAnalyzer
    $TestResults["FrontendDeps"] = Test-FrontendDependencies
    $TestResults["APIEndpoints"] = Test-APIEndpoints
    $TestResults["RealCSVProcessing"] = Test-RealCSVProcessing
    
    # Generar reporte final
    Generate-ValidationReport -TestResults $TestResults
    
    Write-ColorOutput "`n📋 Para problemas específicos, revisa los logs de Django y la consola del navegador." "Blue"
    Write-ColorOutput "🔗 Documentación completa en: MIGRACION_DATOS_REALES.md" "Blue"
}

# Ejecutar validación
Main
