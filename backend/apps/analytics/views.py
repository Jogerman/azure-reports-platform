from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Sum
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class DashboardStatsView(APIView):
    """Vista para estadísticas del dashboard"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # CORREGIR: Usar los nombres correctos de los modelos
            from apps.storage.models import StorageFile  # ← CORRECTO: StorageFile, no UploadedFile
            from apps.reports.models import CSVFile, Report  # ← AGREGAR CSVFile también
            
            user = request.user
            
            # Obtener archivos del usuario (tanto StorageFile como CSVFile)
            storage_files = StorageFile.objects.filter(user=user)
            csv_files = CSVFile.objects.filter(user=user)
            
            # Si tienes modelo Report, usarlo también
            try:
                user_reports = Report.objects.filter(user=user)
                total_reports = user_reports.count()
                completed_reports = user_reports.filter(status='completed').count()
            except:
                # Si no existe el modelo Report, usar valores por defecto
                total_reports = 0
                completed_reports = 0
            
            # Estadísticas básicas
            total_storage_files = storage_files.count()
            total_csv_files = csv_files.count()
            total_files = total_storage_files + total_csv_files
            
            # Calcular recomendaciones y ahorros desde CSVFile
            total_recommendations = 0
            potential_savings = 0
            
            # Analizar CSVFiles que tienen analysis_data
            for csv_file in csv_files:
                if hasattr(csv_file, 'analysis_data') and csv_file.analysis_data:
                    analysis_data = csv_file.analysis_data
                    if isinstance(analysis_data, dict):
                        total_recommendations += analysis_data.get('total_recommendations', 0)
                        potential_savings += analysis_data.get('estimated_savings', 0)
            
            # También revisar StorageFiles por si tienen datos de análisis
            for storage_file in storage_files:
                # Si el StorageFile es un CSV y tiene datos de análisis
                if storage_file.file_type == 'csv':
                    # Aquí puedes agregar lógica adicional si los StorageFiles también tienen analysis_data
                    pass
            
            # Calcular tasa de éxito
            success_rate = 0
            if total_reports > 0:
                success_rate = round((completed_reports / total_reports) * 100, 1)
            elif total_csv_files > 0:
                # Si no hay reportes, usar CSV files completados
                completed_csv = csv_files.filter(processing_status='completed').count()
                success_rate = round((completed_csv / total_csv_files) * 100, 1)
            
            return Response({
                'total_files': total_files,
                'total_storage_files': total_storage_files,
                'total_csv_files': total_csv_files,
                'total_reports': total_reports,
                'completed_reports': completed_reports,
                'total_recommendations': total_recommendations,
                'potential_savings': round(potential_savings, 2),
                'success_rate': success_rate,
                'last_updated': datetime.now().isoformat()
            })
            
        except ImportError as e:
            logger.error(f"Error importando modelos: {str(e)}")
            # Devolver datos básicos cuando hay problemas de import
            return Response({
                'total_files': 0,
                'total_storage_files': 0,
                'total_csv_files': 0,
                'total_reports': 0,
                'completed_reports': 0,
                'total_recommendations': 0,
                'potential_savings': 0,
                'success_rate': 0,
                'last_updated': datetime.now().isoformat(),
                'error': f'Problema con modelos: {str(e)}'
            })
        except Exception as e:
            logger.error(f"Error en dashboard stats: {str(e)}")
            # Devolver datos básicos en caso de otros errores
            return Response({
                'total_files': 0,
                'total_storage_files': 0,
                'total_csv_files': 0,
                'total_reports': 0,
                'completed_reports': 0,
                'total_recommendations': 0,
                'potential_savings': 0,
                'success_rate': 0,
                'last_updated': datetime.now().isoformat(),
                'error': 'Datos no disponibles temporalmente'
            })
