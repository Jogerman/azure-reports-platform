#!/usr/bin/env python
"""
Test simple de URLs para Microsoft OAuth
Ejecutar: python simple_url_test.py
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def test_urls():
    """Probar URLs directamente con el cliente de Django"""
    from django.test import Client
    from django.urls import reverse
    
    print("🧪 TESTING URLs for Microsoft OAuth...")
    print("=" * 50)
    
    client = Client()
    
    # URLs a probar
    urls_to_test = [
        ('/api/health/', 'Health Check'),
        ('/api/auth/microsoft/login/', 'Microsoft Login API'),
        ('/api/auth/microsoft/callback/', 'Microsoft Callback API'),
        ('/auth/test-config/', 'Test Config (DEBUG only)'),
    ]
    
    for url, description in urls_to_test:
        try:
            print(f"\n🔗 Testing {description}: {url}")
            response = client.get(url)
            
            if url == '/api/health/':
                if response.status_code == 200:
                    print(f"✅ {description}: OK (200)")
                else:
                    print(f"❌ {description}: ERROR ({response.status_code})")
                    
            elif 'microsoft/login' in url:
                # Microsoft login debería redirigir (302) o dar error 500 si no está configurado
                if response.status_code in [302, 500]:
                    print(f"✅ {description}: FOUND ({response.status_code})")
                    if response.status_code == 302:
                        print(f"   → Redirects to: {response.get('Location', 'Unknown')}")
                    elif response.status_code == 500:
                        print("   → Internal Server Error (check Microsoft config)")
                else:
                    print(f"❌ {description}: UNEXPECTED ({response.status_code})")
                    
            elif 'microsoft/callback' in url:
                # Callback sin parámetros debería dar error 400 o redirect
                if response.status_code in [302, 400, 500]:
                    print(f"✅ {description}: FOUND ({response.status_code})")
                else:
                    print(f"❌ {description}: UNEXPECTED ({response.status_code})")
                    
            elif 'test-config' in url:
                # Test config depende si DEBUG está activado
                if response.status_code in [200, 404]:
                    if response.status_code == 200:
                        print(f"✅ {description}: AVAILABLE (DEBUG=True)")
                    else:
                        print(f"ℹ️  {description}: NOT AVAILABLE (DEBUG=False or missing)")
                else:
                    print(f"❌ {description}: ERROR ({response.status_code})")
                    
        except Exception as e:
            print(f"❌ {description}: EXCEPTION - {str(e)}")
    
    print("\n" + "=" * 50)
    print("📋 SUMMARY:")
    print("✅ = URL exists and responds as expected")
    print("❌ = URL has problems")
    print("ℹ️  = URL not available (normal in some cases)")
    
    print(f"\n🎯 FRONTEND SHOULD USE:")
    print(f"   Microsoft Login: http://localhost:8000/api/auth/microsoft/login/")
    print(f"   Health Check: http://localhost:8000/api/health/")

def test_reverse_urls():
    """Probar reverse de URLs con nombres"""
    print(f"\n🔄 TESTING URL NAMES (reverse lookup)...")
    print("-" * 30)
    
    from django.urls import reverse, NoReverseMatch
    
    # URLs con nombres a probar
    named_urls = [
        ('microsoft_login_api', 'Microsoft Login API'),
        ('microsoft_callback_api', 'Microsoft Callback API'),
        ('auth:test_microsoft_config', 'Test Config'),
        ('health-check', 'Health Check'),
    ]
    
    for url_name, description in named_urls:
        try:
            url = reverse(url_name)
            print(f"✅ {description} ({url_name}): {url}")
        except NoReverseMatch:
            print(f"❌ {description} ({url_name}): NO REVERSE MATCH")
        except Exception as e:
            print(f"❌ {description} ({url_name}): ERROR - {str(e)}")

if __name__ == '__main__':
    test_urls()
    test_reverse_urls()