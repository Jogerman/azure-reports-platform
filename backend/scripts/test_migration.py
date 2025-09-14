# scripts/test_migration.py
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from apps.reports.models import CSVFile, Report
from apps.reports.analyzers.csv_analyzer import EnhancedCSVAnalyzer
import pandas as pd

User = get_user_model()

def test_user_creation():
    """Probar creación de usuarios"""
    print("🧪 Probando creación de usuarios...")
    
    user, created = User.objects.get_or_create(
        email='test@example.com',
        defaults={
            'username': 'testuser',
            'first_name': 'Usuario',
            'last_name': 'Prueba',
            'department': 'IT',
            'job_title': 'Desarrollador'
        }
    )
    
    if created:
        user.set_password('password123')
        user.save()
        print("✅ Usuario creado exitosamente")
    else:
        print("ℹ️ Usuario ya existe")
    
    return user

def test_csv_analyzer():
    """Probar el analizador de CSV"""
    print("\n🧪 Probando analizador de CSV...")
    
    # Crear datos de prueba
    data = {
        'Category': ['Cost Optimization', 'Security', 'Reliability'] * 10,
        'Impact': ['High', 'Medium', 'Low'] * 10,
        'Resource Type': ['VM', 'Storage', 'Network'] * 10,
        'Potential Savings': [100, 200, 300] * 10,
        'Date': pd.date_range('2024-01-01', periods=30, freq='D')
    }
    
    df = pd.DataFrame(data)
    
    # Analizar
    analyzer = EnhancedCSVAnalyzer(df)
    results = analyzer.analyze()
    
    print("✅ Análisis completado")
    print(f"  - Filas analizadas: {results['basic_stats']['total_rows']}")
    print(f"  - Columnas analizadas: {results['basic_stats']['total_columns']}")
    print(f"  - Calidad de datos: {results['data_quality']['completeness_score']}%")
    print(f"  - Recomendaciones: {len(results['recommendations'])}")
    
    return results

def test_models():
    """Probar modelos de Django"""
    print("\n🧪 Probando modelos...")
    
    user = User.objects.first()
    if not user:
        user = test_user_creation()
    
    # Crear archivo CSV de prueba
    csv_file = CSVFile.objects.create(
        user=user,
        original_filename='test_data.csv',
        file_size=1024,
        processing_status='completed',
        rows_count=30,
        columns_count=5,
        analysis_data={'test': 'data'}
    )
    print("✅ Archivo CSV creado")
    
    # Crear reporte de prueba
    report = Report.objects.create(
        user=user,
        csv_file=csv_file,
        title='Reporte de Prueba',
        description='Este es un reporte de prueba',
        report_type='executive',
        status='completed'
    )
    print("✅ Reporte creado")
    
    return csv_file, report

if __name__ == '__main__':
    print("🚀 Iniciando pruebas de migración...\n")
    
    try:
        # Probar componentes
        user = test_user_creation()
        analysis_results = test_csv_analyzer()
        csv_file, report = test_models()
        
        print("\n✅ Todas las pruebas pasaron exitosamente!")
        print("\n📊 Resumen:")
        print(f"  - Usuario: {user.email}")
        print(f"  - CSV File ID: {csv_file.id}")
        print(f"  - Report ID: {report.id}")
        print(f"  - Insights generados: {len(analysis_results.get('recommendations', []))}")
        
    except Exception as e:
        print(f"\n❌ Error en las pruebas: {e}")
        import traceback
        traceback.print_exc()