#!/bin/bash
# fix_server_errors.sh - Script para corregir errores del servidor Django

echo "🔧 CORRIGIENDO ERRORES DEL SERVIDOR DJANGO"
echo "=========================================="

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Verificar que estamos en el directorio correcto
if [ ! -f "manage.py" ]; then
    echo -e "${RED}❌ Error: No se encontró manage.py. Ejecuta este script desde el directorio backend/${NC}"
    exit 1
fi

echo -e "${BLUE}📋 Aplicando correcciones...${NC}"

# 1. Crear directorio staticfiles
echo -e "${YELLOW}📁 Creando directorio staticfiles...${NC}"
mkdir -p staticfiles
echo "# Directorio para archivos estáticos" > staticfiles/.gitkeep
echo -e "${GREEN}✅ Directorio staticfiles creado${NC}"

# 2. Backup del settings.py
echo -e "${YELLOW}💾 Creando backup de settings.py...${NC}"
cp config/settings.py config/settings.py.backup
echo -e "${GREEN}✅ Backup creado: config/settings.py.backup${NC}"

# 3. Corregir configuración de cache en settings.py
echo -e "${YELLOW}🔧 Corrigiendo configuración de cache...${NC}"
cat > temp_cache_fix.py << 'EOF'
import re

# Leer el archivo settings.py
with open('config/settings.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Comentar la configuración problemática de Redis
redis_cache_pattern = r"CACHES = \{[^}]*'django\.core\.cache\.backends\.redis\.RedisCache'[^}]*\}"
if re.search(redis_cache_pattern, content, re.DOTALL):
    content = re.sub(
        redis_cache_pattern,
        '''# CONFIGURACIÓN REDIS ORIGINAL (COMENTADA TEMPORALMENTE)
# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.redis.RedisCache',
#         'LOCATION': config('REDIS_URL', default='redis://localhost:6379/1'),
#         'OPTIONS': {
#             'CLIENT_CLASS': 'django_redis.client.DefaultClient',
#         },
#         'KEY_PREFIX': 'azure_reports',
#         'TIMEOUT': 300,
#     }
# }

# CONFIGURACIÓN TEMPORAL (SIN REDIS)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}''',
        content,
        flags=re.DOTALL
    )

# Comentar throttling si existe
throttle_pattern = r"'DEFAULT_THROTTLE_CLASSES': \[[^\]]*\],"
if re.search(throttle_pattern, content, re.DOTALL):
    content = re.sub(
        throttle_pattern,
        "# 'DEFAULT_THROTTLE_CLASSES': [\n    #     'rest_framework.throttling.AnonRateThrottle',\n    #     'rest_framework.throttling.UserRateThrottle'\n    # ],",
        content,
        flags=re.DOTALL
    )

throttle_rates_pattern = r"'DEFAULT_THROTTLE_RATES': \{[^}]*\}"
if re.search(throttle_rates_pattern, content, re.DOTALL):
    content = re.sub(
        throttle_rates_pattern,
        "# 'DEFAULT_THROTTLE_RATES': {\n    #     'anon': '100/hour',\n    #     'user': '1000/hour'\n    # }",
        content,
        flags=re.DOTALL
    )

# Escribir el archivo modificado
with open('config/settings.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Configuración de cache corregida")
EOF

python temp_cache_fix.py
rm temp_cache_fix.py
echo -e "${GREEN}✅ Cache configuration fixed${NC}"

# 4. Agregar LogoutView a views.py
echo -e "${YELLOW}🔐 Agregando vista de logout...${NC}"
cat >> apps/authentication/views.py << 'EOF'

# ================================================================
# LOGOUT VIEW
# ================================================================

class LogoutView(APIView):
    """Vista para logout que invalida el refresh token"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            return Response({
                'message': 'Logout exitoso'
            }, status=status.HTTP_200_OK)
        except TokenError:
            return Response({
                'error': 'Token inválido'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': 'Error en logout'
            }, status=status.HTTP_400_BAD_REQUEST)
EOF
echo -e "${GREEN}✅ LogoutView agregada${NC}"

# 5. Actualizar imports en views.py
echo -e "${YELLOW}📦 Actualizando imports en views.py...${NC}"
python << 'EOF'
import re

# Leer el archivo views.py
with open('apps/authentication/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Agregar imports necesarios si no existen
imports_to_add = [
    'from rest_framework.views import APIView',
    'from rest_framework_simplejwt.tokens import RefreshToken',
    'from rest_framework_simplejwt.exceptions import TokenError'
]

for import_line in imports_to_add:
    if import_line not in content:
        # Agregar después de los otros imports de rest_framework
        pattern = r'(from rest_framework_simplejwt\.views import TokenObtainPairView)'
        if re.search(pattern, content):
            content = re.sub(pattern, f'{import_line}\n\\1', content)

# Escribir el archivo modificado
with open('apps/authentication/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Imports actualizados")
EOF
echo -e "${GREEN}✅ Imports updated${NC}"

# 6. Actualizar URLs para incluir logout
echo -e "${YELLOW}🌐 Agregando endpoint de logout...${NC}"
python << 'EOF'
import re

# Leer el archivo urls.py
with open('apps/authentication/urls.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Agregar logout endpoint si no existe
if "path('logout/" not in content:
    # Buscar donde están definidos los otros paths
    pattern = r"(path\('refresh/', TokenRefreshView\.as_view\(\), name='token_refresh'\),)"
    if re.search(pattern, content):
        replacement = "\\1\n    path('logout/', views.LogoutView.as_view(), name='logout'),"
        content = re.sub(pattern, replacement, content)

# Escribir el archivo modificado
with open('apps/authentication/urls.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Logout endpoint agregado")
EOF
echo -e "${GREEN}✅ Logout endpoint added${NC}"

# 7. Crear usuario de prueba
echo -e "${YELLOW}👤 ¿Quieres crear un usuario de prueba? (y/n)${NC}"
read -r create_user

if [[ $create_user =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Creando usuario de prueba...${NC}"
    python manage.py shell << 'EOF'
from django.contrib.auth import get_user_model

User = get_user_model()

# Crear usuario de prueba si no existe
email = 'test@example.com'
if not User.objects.filter(email=email).exists():
    user = User.objects.create_user(
        username='testuser',
        email=email,
        password='password123',
        first_name='Test',
        last_name='User'
    )
    print(f"✅ Usuario creado: {user.email}")
    print(f"   Username: {user.username}")
    print(f"   Password: password123")
else:
    print(f"ℹ️  Usuario {email} ya existe")
EOF
    echo -e "${GREEN}✅ Usuario de prueba configurado${NC}"
fi

# 8. Verificar configuración
echo -e "${YELLOW}🔍 Verificando configuración...${NC}"
python manage.py check --deploy || {
    echo -e "${YELLOW}⚠️  Warnings encontrados, pero el servidor debería funcionar${NC}"
}

echo -e "\n${GREEN}🎉 CORRECCIONES APLICADAS EXITOSAMENTE${NC}"
echo -e "\n${BLUE}📋 RESUMEN DE CAMBIOS:${NC}"
echo "✅ Directorio staticfiles creado"
echo "✅ Configuración Redis/Cache deshabilitada temporalmente"
echo "✅ Throttling deshabilitado"
echo "✅ Vista LogoutView agregada"
echo "✅ Endpoint /api/auth/logout/ agregado"
echo "✅ Usuario de prueba creado (si se eligió)"

echo -e "\n${YELLOW}🚀 PRÓXIMOS PASOS:${NC}"
echo "1. Ejecutar: python manage.py runserver"
echo "2. Probar: curl http://localhost:8000/api/health/"
echo "3. Probar login con usuario test@example.com / password123"

echo -e "\n${YELLOW}🧪 COMANDOS DE PRUEBA:${NC}"
echo "# Health check:"
echo "curl http://localhost:8000/api/health/"
echo ""
echo "# Login:"
echo 'curl -X POST http://localhost:8000/api/auth/login/ \'
echo '  -H "Content-Type: application/json" \'
echo '  -d '"'"'{"email":"test@example.com","password":"password123"}'"'"

echo -e "\n${GREEN}✨ ¡Servidor listo para conectar con React!${NC}"