from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status,viewsets, permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.db.models import Count, Sum,Q
from django.utils import timezone 
from datetime import datetime, timedelta
import logging

from .models import UserActivity
from .serializers import UserActivitySerializer
logger = logging.getLogger(__name__)

class AnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """Vista para analytics y actividades"""
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'], url_path='activity')
    def activity(self, request):
        """Endpoint para obtener actividad reciente del usuario"""
        try:
            limit = int(request.query_params.get('limit', 8))
            
            # Obtener actividades del usuario actual
            activities = UserActivity.objects.filter(
                user=request.user
            ).order_by('-timestamp')[:limit]
            
            # Formatear datos para el frontend
            activity_data = []
            for activity in activities:
                activity_data.append({
                    'id': str(activity.id),
                    'description': activity.description,
                    'timestamp': activity.timestamp.isoformat(),
                    'type': activity.activity_type,
                    'metadata': activity.metadata
                })
            
            logger.info(f"Actividad solicitada por usuario: {request.user.email}, {len(activity_data)} items")
            return Response({'results': activity_data})
            
        except Exception as e:
            logger.error(f"Error obteniendo actividad: {e}")
            return Response(
                {"error": "Error obteniendo actividad de usuario"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """Endpoint para estadísticas del dashboard"""
        try:
            user = request.user
            
            # Calcular estadísticas básicas
            total_activities = UserActivity.objects.filter(user=user).count()
            
            # Actividades por tipo
            activity_counts = UserActivity.objects.filter(
                user=user
            ).values('activity_type').annotate(
                count=Count('activity_type')
            )
            
            # Actividades recientes (últimos 7 días)
            last_week = timezone.now() - timedelta(days=7)
            recent_activities = UserActivity.objects.filter(
                user=user,
                timestamp__gte=last_week
            ).count()
            
            stats_data = {
                'total_files': activity_counts.filter(activity_type='upload_csv').first()['count'] if activity_counts.filter(activity_type='upload_csv').exists() else 0,
                'total_reports': activity_counts.filter(activity_type='generate_report').first()['count'] if activity_counts.filter(activity_type='generate_report').exists() else 0,
                'completed_reports': activity_counts.filter(activity_type='download_report').first()['count'] if activity_counts.filter(activity_type='download_report').exists() else 0,
                'total_recommendations': 0,  # Placeholder
                'potential_savings': 0,  # Placeholder
                'success_rate': 100,  # Placeholder
                'total_activities': total_activities,
                'recent_activities': recent_activities,
                'last_updated': timezone.now().isoformat()
            }
            
            logger.info(f"Stats solicitadas por usuario: {request.user.email}")
            return Response(stats_data)
            
        except Exception as e:
            logger.error(f"Error obteniendo stats: {e}")
            return Response(
                {"error": "Error obteniendo estadísticas"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
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
