# apps/reports/tasks.py - Tareas asíncronas con Celery
from celery import shared_task
from django.apps import apps
import pandas as pd
import logging

logger = logging.getLogger(__name__)

@shared_task
def process_csv_file(csv_file_id, file_content=None):
    """Procesar archivo CSV de forma asíncrona"""
    try:
        CSVFile = apps.get_model('reports', 'CSVFile')
        csv_file = CSVFile.objects.get(id=csv_file_id)
        
        # Actualizar estado
        csv_file.processing_status = 'processing'
        csv_file.save()
        
        # Leer archivo (desde Azure Blob o local)
        if file_content:
            df = pd.read_csv(file_content)
        else:
            from apps.storage.services.reportlab_generator import download_file
            df = download_file(csv_file.azure_blob_name)
        
        # Realizar análisis
        from .analyzers.csv_analyzer import EnhancedCSVAnalyzer
        analyzer = EnhancedCSVAnalyzer(df)
        analysis_results = analyzer.analyze()
        
        # Guardar resultados
        csv_file.rows_count = len(df)
        csv_file.columns_count = len(df.columns)
        csv_file.analysis_data = analysis_results
        csv_file.processing_status = 'completed'
        csv_file.save()
        
        logger.info(f"CSV {csv_file_id} procesado exitosamente")
        
    except Exception as e:
        logger.error(f"Error procesando CSV {csv_file_id}: {e}")
        csv_file.processing_status = 'failed'
        csv_file.error_message = str(e)
        csv_file.save()

@shared_task
def generate_report(report_id):
    """Generar reporte PDF de forma asíncrona"""
    try:
        Report = apps.get_model('reports', 'Report')
        report = Report.objects.get(id=report_id)
        
        # Generar PDF
        from apps.storage.services.report_service import ReportGenerator
        generator = ReportGenerator(report)
        pdf_file_path, html_content = generator.generate()
        
        # Subir a Azure Storage
        from apps.storage.services.azure_storage_service import upload_file
        blob_name = f"reports/{report.id}.pdf"
        blob_url = upload_file(pdf_file_path, blob_name)
        
        # Actualizar reporte
        report.pdf_file_url = blob_url
        report.pdf_azure_blob_name = blob_name
        report.status = 'completed'
        report.save()
        
        logger.info(f"Reporte {report_id} generado exitosamente")
        
    except Exception as e:
        logger.error(f"Error generando reporte {report_id}: {e}")
        report.status = 'failed'
        report.save()
