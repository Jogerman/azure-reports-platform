# verify_setup.py - Guardar en tu carpeta backend y ejecutar
import sys
import subprocess

def check_module(module_name):
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False

def check_redis_connection():
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.ping()
        return True
    except Exception as e:
        print(f"Error conectando a Redis: {e}")
        return False

def main():
    print("=== Verificando configuración de Celery y Redis ===\n")
    
    # Verificar Celery
    print("1. Verificando Celery...")
    if check_module('celery'):
        import celery
        print(f"✅ Celery instalado - Versión: {celery.__version__}")
    else:
        print("❌ Celery NO instalado")
        print("   Ejecuta: pip install celery[redis]==5.3.0")
    
    # Verificar Redis Python client
    print("\n2. Verificando cliente Redis Python...")
    if check_module('redis'):
        import redis
        print(f"✅ Redis client instalado - Versión: {redis.__version__}")
    else:
        print("❌ Redis client NO instalado")
        print("   Ejecuta: pip install redis")
    
    # Verificar conexión a Redis
    print("\n3. Verificando conexión a servidor Redis...")
    if check_redis_connection():
        print("✅ Conexión a Redis exitosa")
    else:
        print("❌ No se puede conectar a Redis")
        print("   Asegúrate de que Redis esté corriendo en localhost:6379")
    
    # Verificar configuración Django
    print("\n4. Verificando configuración Django...")
    try:
        import os
        import django
        
        # Configurar Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
        django.setup()
        
        from django.conf import settings
        
        if hasattr(settings, 'CELERY_BROKER_URL'):
            print(f"✅ CELERY_BROKER_URL configurado: {settings.CELERY_BROKER_URL}")
        else:
            print("❌ CELERY_BROKER_URL no configurado")
            
        if hasattr(settings, 'CELERY_RESULT_BACKEND'):
            print(f"✅ CELERY_RESULT_BACKEND configurado: {settings.CELERY_RESULT_BACKEND}")
        else:
            print("❌ CELERY_RESULT_BACKEND no configurado")
            
    except Exception as e:
        print(f"❌ Error verificando Django: {e}")
    
    print("\n=== Verificación completada ===")

if __name__ == "__main__":
    main()