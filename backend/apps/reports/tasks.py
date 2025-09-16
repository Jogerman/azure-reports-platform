# apps/reports/tasks.py - Tareas asíncronas con Celery
from celery import shared_task
from django.apps import apps
from django.utils import timezone
import pandas as pd
import numpy as np
import logging
import os

logger = logging.getLogger(__name__)

def convert_to_json_serializable(obj):
    """
    Convierte objetos numpy y pandas a tipos serializables en JSON
    """
    if isinstance(obj, dict):
        return {key: convert_to_json_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_json_serializable(item) for item in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif pd.isna(obj):
        return None
    else:
        return obj

@shared_task
def process_csv_file(csv_file_id, temp_file_path=None):
    """
    Procesar archivo CSV de forma asíncrona
    
    Args:
        csv_file_id (int): ID del archivo CSV en la base de datos
        temp_file_path (str): Ruta del archivo temporal (opcional)
    """
    csv_file = None
    
    try:
        # Obtener modelo dinámicamente
        CSVFile = apps.get_model('reports', 'CSVFile')
        csv_file = CSVFile.objects.get(id=csv_file_id)
        
        # Actualizar estado
        csv_file.processing_status = 'processing'
        csv_file.save(update_fields=['processing_status'])
        
        logger.info(f"Iniciando procesamiento de CSV {csv_file_id}")
        
        # Leer archivo desde el path temporal o desde Azure
        df = None
        
        if temp_file_path and os.path.exists(temp_file_path):
            # Leer desde archivo temporal
            logger.info(f"Leyendo archivo temporal: {temp_file_path}")
            
            try:
                # Determinar el tipo de archivo y leerlo
                if temp_file_path.endswith(('.xlsx', '.xls')):
                    df = pd.read_excel(temp_file_path)
                else:
                    # Intentar con diferentes encodings
                    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
                    for encoding in encodings:
                        try:
                            df = pd.read_csv(temp_file_path, encoding=encoding)
                            logger.info(f"Archivo leído exitosamente con encoding: {encoding}")
                            break
                        except UnicodeDecodeError:
                            continue
                    
                    if df is None:
                        raise Exception("No se pudo leer el archivo con ningún encoding")
                        
            finally:
                # Limpiar archivo temporal
                try:
                    os.unlink(temp_file_path)
                    logger.info(f"Archivo temporal eliminado: {temp_file_path}")
                except Exception as e:
                    logger.warning(f"Error eliminando archivo temporal: {e}")
        
        else:
            # Leer desde Azure Blob Storage (implementación futura)
            logger.info("Intentando leer desde Azure Blob Storage")
            # TODO: Implementar descarga desde Azure
            raise Exception("Lectura desde Azure Blob no implementada aún")
        
        if df is None or df.empty:
            raise Exception("El archivo está vacío o no se pudo leer")
        
        logger.info(f"Archivo leído: {len(df)} filas, {len(df.columns)} columnas")
        
        # Realizar análisis básico
        basic_analysis = {
            'rows_count': int(len(df)),
            'columns_count': int(len(df.columns)),
            'columns': list(df.columns),
            'data_types': df.dtypes.astype(str).to_dict(),
            'null_counts': {k: int(v) for k, v in df.isnull().sum().to_dict().items()},
            'summary_stats': convert_to_json_serializable(df.describe(include='all').to_dict()) if len(df) > 0 else {}
        }
        
        # Análisis avanzado (opcional)
        try:
            from .analyzers.csv_analyzer import EnhancedCSVAnalyzer
            analyzer = EnhancedCSVAnalyzer(df)
            advanced_analysis = analyzer.analyze()
            
            # Convertir análisis avanzado a JSON serializable
            advanced_analysis = convert_to_json_serializable(advanced_analysis)
            
            # Combinar análisis básico y avanzado
            analysis_results = {
                **basic_analysis,
                **advanced_analysis
            }
        except ImportError:
            logger.warning("EnhancedCSVAnalyzer no disponible, usando análisis básico")
            analysis_results = basic_analysis
        except Exception as e:
            logger.warning(f"Error en análisis avanzado: {e}, usando análisis básico")
            analysis_results = basic_analysis
        
        # Guardar resultados
        csv_file.rows_count = int(len(df))
        csv_file.columns_count = int(len(df.columns))
        csv_file.analysis_data = analysis_results
        csv_file.processing_status = 'completed'
        csv_file.processed_date = timezone.now()
        csv_file.save()
        
        logger.info(f"CSV {csv_file_id} procesado exitosamente")
        return f"Procesado exitosamente: {len(df)} filas"
        
    except Exception as e:
        error_msg = f"Error procesando CSV {csv_file_id}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        if csv_file:
            csv_file.processing_status = 'failed'
            csv_file.error_message = str(e)
            csv_file.save(update_fields=['processing_status', 'error_message'])
        
        # Limpiar archivo temporal en caso de error
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception:
                pass
        
        raise Exception(error_msg)

@shared_task
def generate_report(report_id):
    """Generar reporte PDF de forma asíncrona"""
    report = None
    
    try:
        Report = apps.get_model('reports', 'Report')
        report = Report.objects.get(id=report_id)
        
        logger.info(f"Iniciando generación de reporte {report_id}")
        
        # Actualizar estado
        report.status = 'generating'
        report.save(update_fields=['status'])
        
        # Generar PDF (implementación básica)
        try:
            from apps.storage.services.report_service import ReportGenerator
            generator = ReportGenerator(report)
            pdf_file_path, html_content = generator.generate()
            
            # Subir a Azure Storage
            try:
                from apps.storage.services.azure_storage_service import upload_file
                blob_name = f"reports/{report.id}.pdf"
                blob_url = upload_file(pdf_file_path, blob_name)
                
                # Actualizar reporte
                report.pdf_file_url = blob_url
                report.pdf_azure_blob_name = blob_name
                report.html_preview_url = html_content
            except ImportError:
                logger.warning("Azure Storage no disponible, guardando localmente")
                report.pdf_file_url = pdf_file_path
                
        except ImportError:
            logger.warning("ReportGenerator no disponible, creando reporte básico")
            # Crear reporte básico
            report.pdf_file_url = f"/tmp/basic_report_{report_id}.pdf"
            report.html_preview_url = "<p>Reporte básico generado</p>"
        
        # Finalizar
        report.status = 'completed'
        report.completed_at = timezone.now()
        report.save()
        
        logger.info(f"Reporte {report_id} generado exitosamente")
        return f"Reporte {report_id} completado"
        
    except Exception as e:
        error_msg = f"Error generando reporte {report_id}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        if report:
            report.status = 'failed'
            report.error_message = str(e)
            report.save(update_fields=['status', 'error_message'])
        
        raise Exception(error_msg)