#!/usr/bin/env python
import os
import sys
import django
from pathlib import Path

# Setup Django
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.storage.services.azure_storage_service import AzureStorageService
from django.conf import settings

def test_azure_storage():
    """Verificar conexión a Azure Blob Storage"""
    print("🔍 Verificando configuración de Azure Storage...")
    
    # Verificar variables de entorno
    account_name = getattr(settings, 'AZURE_STORAGE_ACCOUNT_NAME', None)
    account_key = getattr(settings, 'AZURE_STORAGE_ACCOUNT_KEY', None)
    container_name = getattr(settings, 'AZURE_STORAGE_CONTAINER_NAME', 'azure-reports')
    
    print(f"📋 Account Name: {account_name}")
    print(f"📋 Container Name: {container_name}")
    print(f"📋 Account Key: {'✅ Configurado' if account_key else '❌ No configurado'}")
    
    if not account_name or not account_key:
        print("❌ Faltan credenciales de Azure Storage")
        print("💡 Configura AZURE_STORAGE_ACCOUNT_NAME y AZURE_STORAGE_ACCOUNT_KEY en .env")
        return False
    
    # Probar servicio
    storage = AzureStorageService()
    
    if not storage.is_configured():
        print("❌ Azure Storage Service no está configurado correctamente")
        return False
    
    print("✅ Azure Storage Service configurado correctamente")
    
    # Probar conexión
    try:
        files = storage.list_files()
        print(f"✅ Conexión exitosa. Archivos encontrados: {len(files)}")
        
        # Mostrar algunos archivos
        for file in files[:3]:
            print(f"   📁 {file.get('name', 'Sin nombre')} ({file.get('size', 0)} bytes)")
            
        return True
        
    except Exception as e:
        print(f"❌ Error conectando a Azure Storage: {str(e)}")
        print("💡 Verifica que las credenciales sean correctas y que el container exista")
        return False

if __name__ == "__main__":
    success = test_azure_storage()
    if success:
        print("\n🎉 Azure Storage está funcionando correctamente!")
    else:
        print("\n⚠️ Hay problemas con la configuración de Azure Storage")
        print("📋 Pasos para solucionarlo:")
        print("   1. Verifica las credenciales en Azure Portal")
        print("   2. Asegúrate de que el storage account existe")
        print("   3. Verifica que el container 'azure-reports' existe")
        print("   4. Revisa los permisos de acceso")
