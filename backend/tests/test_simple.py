#!/usr/bin/env python
# test_simple.py - Script de pruebas simplificado y robusto

import os
import sys
import json
import requests
from time import sleep

# Configuración
API_BASE = 'http://localhost:8000/api'
TEST_USER_EMAIL = 'test@example.com'
TEST_USER_PASSWORD = 'testpass123'

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_colored(text, color):
    print(f"{color}{text}{Colors.END}")

def print_test_result(test_name, success, message=""):
    status = f"{Colors.GREEN}✅ PASS" if success else f"{Colors.RED}❌ FAIL"
    print(f"{status}{Colors.END} {test_name}")
    if message:
        print(f"    {Colors.YELLOW}{message}{Colors.END}")

def test_server_connection():
    """Verificar que el servidor Django esté corriendo"""
    try:
        response = requests.get(f'{API_BASE}/health/', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_test_result("Server Connection", True, f"Status: {data.get('status', 'unknown')}")
            return True
        else:
            print_test_result("Server Connection", False, f"HTTP {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_test_result("Server Connection", False, "No se puede conectar al servidor")
        print_colored("💡 Ejecuta: python manage.py runserver", Colors.YELLOW)
        return False
    except Exception as e:
        print_test_result("Server Connection", False, str(e))
        return False

def test_user_creation():
    """Crear usuario de prueba usando Django ORM"""
    try:
        # Importar Django después de verificar el servidor
        import django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
        django.setup()
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        user, created = User.objects.get_or_create(
            email=TEST_USER_EMAIL,
            defaults={
                'username': 'testuser',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        
        if created:
            user.set_password(TEST_USER_PASSWORD)
            user.save()
        
        status = "Usuario creado" if created else "Usuario existente"
        print_test_result("User Creation", True, f"{status}: {user.email}")
        return True, user
        
    except Exception as e:
        print_test_result("User Creation", False, str(e))
        return False, None

def test_authentication():
    """Probar login y obtener token JWT"""
    try:
        login_data = {
            'email': TEST_USER_EMAIL,
            'password': TEST_USER_PASSWORD
        }
        
        response = requests.post(
            f'{API_BASE}/auth/login/',
            json=login_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access')
            if token:
                print_test_result("Authentication", True, "Token JWT obtenido")
                return True, token
            else:
                print_test_result("Authentication", False, "No se obtuvo token")
                return False, None
        else:
            print_test_result("Authentication", False, f"HTTP {response.status_code}: {response.text}")
            return False, None
            
    except Exception as e:
        print_test_result("Authentication", False, str(e))
        return False, None

def test_file_upload(auth_token):
    """Probar upload de archivo CSV"""
    try:
        # Crear CSV de prueba
        csv_content = """Recommendation,Category,Impact,Resource
Enable encryption,Security,High,Virtual Machine
Optimize costs,Cost,Medium,Storage Account
Update OS,Security,High,Virtual Machine"""
        
        files = {
            'file': ('test_azure_advisor.csv', csv_content, 'text/csv')
        }
        
        headers = {
            'Authorization': f'Bearer {auth_token}'
        }
        
        response = requests.post(
            f'{API_BASE}/files/upload/',
            files=files,
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 201:
            data = response.json()
            file_id = data.get('id')
            filename = data.get('original_filename')
            print_test_result("File Upload", True, f"Archivo subido: {filename}")
            return True, file_id
        else:
            print_test_result("File Upload", False, f"HTTP {response.status_code}: {response.text}")
            return False, None
            
    except Exception as e:
        print_test_result("File Upload", False, str(e))
        return False, None

def test_file_list(auth_token):
    """Probar listado de archivos"""
    try:
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = requests.get(
            f'{API_BASE}/files/',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            count = data.get('count', 0)
            print_test_result("File List", True, f"{count} archivos encontrados")
            return True
        else:
            print_test_result("File List", False, f"HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print_test_result("File List", False, str(e))
        return False

def test_report_generation(auth_token, file_id):
    """Probar generación de reportes"""
    try:
        if not file_id:
            print_test_result("Report Generation", False, "No hay file_id disponible")
            return False
        
        headers = {
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': 'application/json'
        }
        
        report_data = {
            'file_id': file_id,
            'title': 'Reporte de Prueba Automática',
            'description': 'Reporte generado por script de testing',
            'report_type': 'comprehensive'
        }
        
        response = requests.post(
            f'{API_BASE}/reports/generate/',
            json=report_data,
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 201:
            data = response.json()
            report_id = data.get('id')
            title = data.get('title')
            print_test_result("Report Generation", True, f"Reporte creado: {title}")
            return True, report_id
        else:
            print_test_result("Report Generation", False, f"HTTP {response.status_code}: {response.text}")
            return False, None
            
    except Exception as e:
        print_test_result("Report Generation", False, str(e))
        return False, None

def test_report_list_with_ordering(auth_token):
    """Probar listado de reportes con ordering (que causaba error)"""
    try:
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        # Probar con parámetros que causaban el error
        params = {
            'limit': 5,
            'ordering': '-created_at'
        }
        
        response = requests.get(
            f'{API_BASE}/reports/',
            headers=headers,
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else len(data.get('results', []))
            print_test_result("Report List (Ordering Fix)", True, f"{count} reportes listados con ordering")
            return True
        else:
            print_test_result("Report List (Ordering Fix)", False, f"HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print_test_result("Report List (Ordering Fix)", False, str(e))
        return False

def test_dashboard_stats(auth_token):
    """Probar endpoint de estadísticas"""
    try:
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = requests.get(
            f'{API_BASE}/dashboard/stats/',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print_test_result("Dashboard Stats", True, "Estadísticas obtenidas")
            return True
        else:
            print_test_result("Dashboard Stats", False, f"HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print_test_result("Dashboard Stats", False, str(e))
        return False

def main():
    print_colored("🚀 AZURE REPORTS PLATFORM - TESTING SUITE (FIXED)", Colors.CYAN)
    print_colored("=" * 55, Colors.CYAN)
    print()
    
    # Verificar directorio
    if not os.path.exists('manage.py'):
        print_colored("❌ No se encontró manage.py", Colors.RED)
        print_colored("   Ejecuta desde el directorio backend/", Colors.YELLOW)
        sys.exit(1)
    
    results = []
    auth_token = None
    file_id = None
    
    # 1. Test de conexión al servidor
    print_colored("🔍 1. VERIFICANDO SERVIDOR", Colors.BLUE)
    server_ok = test_server_connection()
    results.append(("Server Connection", server_ok))
    
    if not server_ok:
        print_colored("\n❌ Sin conexión al servidor. Tests terminados.", Colors.RED)
        sys.exit(1)
    
    print()
    
    # 2. Crear usuario de prueba
    print_colored("👤 2. CONFIGURANDO USUARIO DE PRUEBA", Colors.BLUE)
    user_ok, user = test_user_creation()
    results.append(("User Creation", user_ok))
    print()
    
    # 3. Test de autenticación
    print_colored("🔐 3. PROBANDO AUTENTICACIÓN", Colors.BLUE)
    auth_ok, auth_token = test_authentication()
    results.append(("Authentication", auth_ok))
    print()
    
    if not auth_ok or not auth_token:
        print_colored("❌ Sin autenticación. Saltando tests que requieren token.", Colors.YELLOW)
    else:
        # 4. Test de upload de archivos
        print_colored("📤 4. PROBANDO UPLOAD DE ARCHIVOS", Colors.BLUE)
        upload_ok, file_id = test_file_upload(auth_token)
        results.append(("File Upload", upload_ok))
        print()
        
        # 5. Test de listado de archivos
        print_colored("📂 5. PROBANDO LISTADO DE ARCHIVOS", Colors.BLUE)
        list_ok = test_file_list(auth_token)
        results.append(("File List", list_ok))
        print()
        
        # 6. Test de generación de reportes
        print_colored("📊 6. PROBANDO GENERACIÓN DE REPORTES", Colors.BLUE)
        report_ok, report_id = test_report_generation(auth_token, file_id)
        results.append(("Report Generation", report_ok))
        print()
        
        # 7. Test de listado con ordering (FIX crítico)
        print_colored("📋 7. PROBANDO LISTADO CON ORDERING", Colors.BLUE)
        ordering_ok = test_report_list_with_ordering(auth_token)
        results.append(("Report List (Ordering)", ordering_ok))
        print()
        
        # 8. Test de dashboard
        print_colored("📈 8. PROBANDO DASHBOARD", Colors.BLUE)
        dashboard_ok = test_dashboard_stats(auth_token)
        results.append(("Dashboard Stats", dashboard_ok))
        print()
    
    # Resumen final
    print_colored("📊 RESUMEN DE PRUEBAS", Colors.CYAN)
    print_colored("=" * 30, Colors.CYAN)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = f"{Colors.GREEN}✅" if success else f"{Colors.RED}❌"
        print(f"{status} {test_name}{Colors.END}")
    
    print()
    percentage = (passed / total * 100) if total > 0 else 0
    print_colored(f"Total: {total}", Colors.CYAN)
    print_colored(f"Pasadas: {passed}", Colors.GREEN if passed == total else Colors.YELLOW)
    print_colored(f"Fallidas: {total - passed}", Colors.RED if total - passed > 0 else Colors.GREEN)
    print_colored(f"Porcentaje: {percentage:.1f}%", Colors.GREEN if percentage == 100 else Colors.YELLOW)
    
    if passed == total:
        print()
        print_colored("🎉 ¡TODAS LAS PRUEBAS PASARON!", Colors.GREEN)
        print_colored("✅ Los errores principales han sido corregidos:", Colors.GREEN)
        print_colored("   - QuerySet ordering/slice error → SOLUCIONADO", Colors.GREEN)
        print_colored("   - File upload content-type error → SOLUCIONADO", Colors.GREEN)
        print_colored("   - Report generation error → SOLUCIONADO", Colors.GREEN)
    else:
        print()
        print_colored(f"⚠️ {total - passed} prueba(s) fallaron", Colors.YELLOW)
        print_colored("Revisa los errores anteriores para más detalles", Colors.YELLOW)

if __name__ == "__main__":
    main()