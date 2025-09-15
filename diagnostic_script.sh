#!/bin/bash
# diagnostic_script.sh - Script para diagnosticar problemas de conexión Frontend-Backend

echo "🔍 DIAGNÓSTICO DE CONEXIÓN FRONTEND-BACKEND"
echo "========================================="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para verificar si un comando existe
check_command() {
    if command -v $1 >/dev/null 2>&1; then
        echo -e "${GREEN}✅ $1 está instalado${NC}"
        return 0
    else
        echo -e "${RED}❌ $1 no está instalado${NC}"
        return 1
    fi
}

# Función para verificar puertos
check_port() {
    if nc -z localhost $1 2>/dev/null; then
        echo -e "${GREEN}✅ Puerto $1 está abierto${NC}"
        return 0
    else
        echo -e "${RED}❌ Puerto $1 no está disponible${NC}"
        return 1
    fi
}

# Función para verificar archivos
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✅ $1 existe${NC}"
        return 0
    else
        echo -e "${RED}❌ $1 no existe${NC}"
        return 1
    fi
}

echo -e "${BLUE}📋 1. VERIFICANDO HERRAMIENTAS NECESARIAS${NC}"
echo "----------------------------------------"
check_command "python"
check_command "node"
check_command "npm"
check_command "psql" || echo -e "${YELLOW}⚠️  psql opcional pero recomendado${NC}"

echo -e "\n${BLUE}📁 2. VERIFICANDO ESTRUCTURA DE ARCHIVOS${NC}"
echo "----------------------------------------"
check_file "backend/manage.py"
check_file "backend/config/settings.py"
check_file "backend/config/urls.py"
check_file "frontend/package.json"
check_file "frontend/src/App.jsx"
check_file "frontend/src/services/api.js"

echo -e "\n${BLUE}🔧 3. VERIFICANDO CONFIGURACIÓN BACKEND${NC}"
echo "----------------------------------------"

# Verificar .env backend
if check_file "backend/.env"; then
    echo -e "${BLUE}Contenido de backend/.env:${NC}"
    grep -E "^(SECRET_KEY|DEBUG|DB_|CORS_)" backend/.env 2>/dev/null || echo -e "${YELLOW}⚠️  Variables críticas no encontradas${NC}"
else
    echo -e "${RED}❌ Crear backend/.env con configuración necesaria${NC}"
fi

# Verificar settings.py
echo -e "\n${BLUE}Verificando CORS en settings.py:${NC}"
if grep -q "corsheaders" backend/config/settings.py; then
    echo -e "${GREEN}✅ corsheaders encontrado en settings${NC}"
else
    echo -e "${RED}❌ corsheaders no configurado${NC}"
fi

if grep -q "CORS_ALLOWED_ORIGINS" backend/config/settings.py; then
    echo -e "${GREEN}✅ CORS_ALLOWED_ORIGINS configurado${NC}"
else
    echo -e "${RED}❌ CORS_ALLOWED_ORIGINS no configurado${NC}"
fi

echo -e "\n${BLUE}🎨 4. VERIFICANDO CONFIGURACIÓN FRONTEND${NC}"
echo "----------------------------------------"

# Verificar .env frontend
if check_file "frontend/.env"; then
    echo -e "${BLUE}Contenido de frontend/.env:${NC}"
    cat frontend/.env 2>/dev/null
else
    echo -e "${RED}❌ Crear frontend/.env con VITE_API_BASE_URL${NC}"
fi

# Verificar package.json
if [ -f "frontend/package.json" ]; then
    echo -e "\n${BLUE}Dependencias React críticas:${NC}"
    grep -E "(react|axios|react-router)" frontend/package.json | head -5
fi

echo -e "\n${BLUE}🚀 5. VERIFICANDO SERVICIOS EN EJECUCIÓN${NC}"
echo "----------------------------------------"
check_port 8000  # Django backend
check_port 5173  # Vite frontend
check_port 5432  # PostgreSQL

echo -e "\n${BLUE}🌐 6. PROBANDO CONECTIVIDAD${NC}"
echo "----------------------------------------"

# Probar backend health check
if check_port 8000; then
    echo -e "${BLUE}Probando health check del backend...${NC}"
    if curl -s http://localhost:8000/api/health/ >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend health check OK${NC}"
        curl -s http://localhost:8000/api/health/ | head -2
    else
        echo -e "${RED}❌ Backend health check falló${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Backend no está ejecutándose${NC}"
fi

# Probar frontend
if check_port 5173; then
    echo -e "${BLUE}Probando frontend...${NC}"
    if curl -s http://localhost:5173/ >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Frontend accesible${NC}"
    else
        echo -e "${RED}❌ Frontend no responde${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Frontend no está ejecutándose${NC}"
fi

echo -e "\n${BLUE}🔒 7. VERIFICANDO AUTENTICACIÓN${NC}"
echo "----------------------------------------"

# Verificar modelo User
if [ -f "backend/apps/authentication/models.py" ]; then
    if grep -q "class.*User" backend/apps/authentication/models.py; then
        echo -e "${GREEN}✅ Modelo User encontrado${NC}"
    else
        echo -e "${RED}❌ Modelo User no encontrado${NC}"
    fi
fi

# Verificar JWT settings
if grep -q "SIMPLE_JWT" backend/config/settings.py; then
    echo -e "${GREEN}✅ JWT configurado${NC}"
else
    echo -e "${RED}❌ JWT no configurado${NC}"
fi

echo -e "\n${BLUE}📊 8. RESUMEN Y RECOMENDACIONES${NC}"
echo "================================"

# Crear lista de problemas encontrados
ISSUES=()

[ ! -f "backend/.env" ] && ISSUES+=("Crear backend/.env")
[ ! -f "frontend/.env" ] && ISSUES+=("Crear frontend/.env")
! check_port 8000 >/dev/null 2>&1 && ISSUES+=("Iniciar backend Django")
! check_port 5173 >/dev/null 2>&1 && ISSUES+=("Iniciar frontend React")

if [ ${#ISSUES[@]} -eq 0 ]; then
    echo -e "${GREEN}✅ ¡Todo parece estar configurado correctamente!${NC}"
    echo -e "${GREEN}Si aún tienes problemas, revisa los logs específicos.${NC}"
else
    echo -e "${RED}❌ Problemas encontrados:${NC}"
    for issue in "${ISSUES[@]}"; do
        echo -e "${RED}  - $issue${NC}"
    done
    
    echo -e "\n${YELLOW}💡 PRÓXIMOS PASOS:${NC}"
    echo "1. Resolver los problemas listados arriba"
    echo "2. Ejecutar: python backend/manage.py runserver 8000"
    echo "3. Ejecutar: cd frontend && npm run dev"
    echo "4. Abrir http://localhost:5173 en el navegador"
    echo "5. Revisar logs en consola del navegador"
fi

echo -e "\n${BLUE}🛠️  COMANDOS ÚTILES:${NC}"
echo "cd backend && python manage.py runserver 8000"
echo "cd frontend && npm run dev"
echo "curl http://localhost:8000/api/health/"
echo "curl http://localhost:8000/api/auth/login/ -X POST -H 'Content-Type: application/json' -d '{\"email\":\"test@test.com\",\"password\":\"test\"}'"

echo -e "\n${GREEN}✨ Diagnóstico completado${NC}"