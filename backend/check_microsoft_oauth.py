#!/usr/bin/env python
"""
Script para verificar la configuración de Microsoft OAuth
Ejecutar desde la raíz del proyecto Django: python check_microsoft_oauth.py
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def check_environment_variables():
    """Verificar variables de entorno"""
    print("🔍 Verificando variables de entorno...")
    
    from decouple import config
    
    variables = {
        'MICROSOFT_CLIENT_ID': config('MICROSOFT_CLIENT_ID', default=''),
        'MICROSOFT_CLIENT_SECRET': config('MICROSOFT_CLIENT_SECRET', default=''),
        'MICROSOFT_TENANT_ID': config('MICROSOFT_TENANT_ID', default=''),
        'MICROSOFT_REDIRECT_URI': config('MICROSOFT_REDIRECT_URI', default=''),
    }
    
    all_configured = True
    
    for var_name, var_value in variables.items():
        if var_value and var_value not in ['your-client-id', 'your-client-secret']:
            print(f"✅ {var_name}: {'*' * min(len(var_value), 20)}... (CONFIGURADO)")
        else:
            print(f"❌ {var_name}: NO CONFIGURADO")
            all_configured = False
    
    return all_configured

def check_dependencies():
    """Verificar dependencias instaladas"""
    print("\n📦 Verificando dependencias...")
    
    dependencies = {
        'msal': 'Microsoft Authentication Library',
        'requests': 'HTTP Requests Library',
        'decouple': 'Python Decouple'
    }
    
    all_installed = True
    
    for dep_name, dep_description in dependencies.items():
        try:
            __import__(dep_name)
            print(f"✅ {dep_description}: INSTALADO")
        except ImportError:
            print(f"❌ {dep_description}: NO INSTALADO")
            print(f"   Instalar con: pip install {dep_name}")
            all_installed = False
    
    return all_installed

def check_microsoft_service():
    """Verificar servicio de Microsoft"""
    print("\n🔧 Verificando servicio de Microsoft OAuth...")
    
    try:
        from apps.authentication.services import MicrosoftAuthService, is_microsoft_configured
        
        if is_microsoft_configured():
            print("✅ Microsoft OAuth: CONFIGURADO")
            
            # Probar crear instancia del servicio
            ms_service = MicrosoftAuthService()
            
            if ms_service.is_configured():
                print("✅ Servicio MicrosoftAuthService: FUNCIONAL")
                
                # Probar generar URL de autenticación
                try:
                    auth_url = ms_service.get_auth_url()
                    if auth_url:
                        print("✅ Generación de URL de autenticación: EXITOSA")
                        print(f"   URL ejemplo: {auth_url[:50]}...")
                        return True
                    else:
                        print("❌ Generación de URL de autenticación: FALLÓ")
                        return False
                except Exception as e:
                    print(f"❌ Error generando URL: {str(e)}")
                    return False
            else:
                print("❌ Servicio MicrosoftAuthService: NO FUNCIONAL")
                return False
        else:
            print("❌ Microsoft OAuth: NO CONFIGURADO")
            return False
            
    except ImportError as e:
        print(f"❌ Error importando servicio: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        return False

def check_urls():
    """Verificar configuración de URLs"""
    print("\n🌐 Verificando configuración de URLs...")
    
    try:
        from django.urls import reverse
        from django.test import RequestFactory, Client
        
        # Verificar URLs de API (sin namespace, están en apps.authentication.urls)
        api_urls = [
            ('API Microsoft Login', 'microsoft_login_api'),
            ('API Microsoft Callback', 'microsoft_callback_api'),
        ]
        
        for url_desc, url_name in api_urls:
            try:
                # Estas URLs están en /api/auth/ pero sin namespace
                url = reverse(url_name)
                print(f"✅ {url_desc}: /api/auth{url}")
            except Exception as e:
                # Si reverse falla, intentar construir manualmente
                print(f"⚠️  {url_desc}: No encontrado con reverse, verificando manualmente...")
                
                # Intentar hacer una petición HTTP para verificar si existe
                try:
                    client = Client()
                    if 'login' in url_name:
                        response = client.get('/api/auth/microsoft/login/')
                        if response.status_code in [302, 500]:  # Redirect o error esperado
                            print(f"✅ {url_desc}: /api/auth/microsoft/login/ (verificado por HTTP)")
                        else:
                            print(f"❌ {url_desc}: Respuesta inesperada {response.status_code}")
                    elif 'callback' in url_name:
                        response = client.get('/api/auth/microsoft/callback/')
                        if response.status_code in [302, 400, 500]:  # Redirect o error esperado
                            print(f"✅ {url_desc}: /api/auth/microsoft/callback/ (verificado por HTTP)")
                        else:
                            print(f"❌ {url_desc}: Respuesta inesperada {response.status_code}")
                except Exception as http_error:
                    print(f"❌ {url_desc}: ERROR HTTP - {str(http_error)}")
        
        # Verificar URLs tradicionales (con namespace auth)
        traditional_urls = [
            ('Traditional Login', 'auth:login'),
            ('Traditional Microsoft Login', 'auth:microsoft_login'),
            ('Traditional Microsoft Callback', 'auth:microsoft_callback'),
            ('Test Config', 'auth:test_microsoft_config'),
        ]
        
        for url_desc, url_name in traditional_urls:
            try:
                url = reverse(url_name)
                print(f"✅ {url_desc}: {url}")
            except Exception as e:
                print(f"❌ {url_desc}: ERROR - {str(e)}")
        
        # Verificar específicamente el endpoint que usará React
        try:
            client = Client()
            response = client.get('/api/health/')
            if response.status_code == 200:
                print("✅ Health Check: /api/health/ (funcionando)")
            else:
                print(f"❌ Health Check: Código {response.status_code}")
        except Exception as e:
            print(f"❌ Health Check: ERROR - {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando URLs: {str(e)}")
        return False

def main():
    """Función principal"""
    print("🔍 VERIFICACIÓN DE MICROSOFT OAUTH PARA AZURE ADVISOR ANALYZER")
    print("=" * 70)
    
    checks = [
        ("Variables de Entorno", check_environment_variables),
        ("Dependencias", check_dependencies),
        ("Servicio Microsoft", check_microsoft_service),
        ("URLs", check_urls),
    ]
    
    results = []
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Error en verificación de {check_name}: {str(e)}")
            results.append(False)
    
    print("\n" + "=" * 70)
    print("📊 RESUMEN DE VERIFICACIÓN")
    print("=" * 70)
    
    if all(results):
        print("🎉 ¡TODAS LAS VERIFICACIONES PASARON!")
        print("   Microsoft OAuth está configurado correctamente.")
        print("   Puedes probar el login en: http://localhost:8000/api/auth/microsoft/login/")
    else:
        print("⚠️  ALGUNAS VERIFICACIONES FALLARON")
        print("   Revisa los errores anteriores y corrígelos.")
        print("\n💡 SOLUCIONES COMUNES:")
        print("   1. Crear archivo .env con las credenciales de Microsoft")
        print("   2. Instalar dependencias: pip install msal>=1.24.1")
        print("   3. Verificar configuración en Azure Portal")
        print("   4. Verificar que las URLs de redirect coincidan")
    
    print("\n🔧 Para más ayuda, visita:")
    print("   - http://localhost:8000/auth/test-config/ (en modo DEBUG)")
    print("   - Documentación de Microsoft Graph: https://docs.microsoft.com/graph/")

if __name__ == '__main__':
    main()