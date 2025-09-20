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
    """Vista para analytics y actividades - PRODUCCIÓN REAL"""
    serializer_class = UserActivitySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Retorna actividades del usuario actual"""
        return UserActivity.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'], url_path='activity')
    def activity(self, request):
        """Endpoint para obtener actividad reciente del usuario"""
        try:
            limit = int(request.query_params.get('limit', 8))
            
            # Obtener actividades reales del usuario
            activities = UserActivity.objects.filter(
                user=request.user
            ).order_by('-timestamp')[:limit]
            
            # Serializar las actividades
            serialized_activities = []
            for activity in activities:
                serialized_activities.append({
                    'id': str(activity.id),
                    'description': activity.description,
                    'timestamp': activity.timestamp.isoformat(),
                    'type': activity.activity_type,
                    'metadata': activity.metadata
                })
            
            logger.info(f"Actividad real obtenida para usuario: {request.user.email}, {len(serialized_activities)} items")
            return Response({'results': serialized_activities})
            
        except Exception as e:
            logger.error(f"Error obteniendo actividad: {e}")
            return Response({'results': []})
    
    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """Endpoint para estadísticas del dashboard - DATOS REALES"""
        try:
            from apps.storage.models import StorageFile
            from apps.reports.models import CSVFile, Report
            
            user = request.user
            
            # Obtener archivos reales del usuario
            try:
                storage_files = StorageFile.objects.filter(user=user)
                total_storage_files = storage_files.count()
            except:
                total_storage_files = 0
            
            try:
                csv_files = CSVFile.objects.filter(user=user)
                total_csv_files = csv_files.count()
            except:
                total_csv_files = 0
            
            total_files = total_storage_files + total_csv_files
            
            # Obtener reportes reales
            try:
                user_reports = Report.objects.filter(user=user)
                total_reports = user_reports.count()
                completed_reports = user_reports.filter(status='completed').count()
            except:
                total_reports = 0
                completed_reports = 0
            
            # Calcular recomendaciones y ahorros desde CSVFiles reales
            total_recommendations = 0
            potential_savings = 0
            azure_advisor_score = 0
            
            try:
                # Analizar CSVFiles que tienen analysis_data
                for csv_file in csv_files:
                    if hasattr(csv_file, 'analysis_data') and csv_file.analysis_data:
                        analysis_data = csv_file.analysis_data
                        if isinstance(analysis_data, dict):
                            # Extraer recomendaciones
                            if 'total_recommendations' in analysis_data:
                                total_recommendations += analysis_data['total_recommendations']
                            elif 'executive_summary' in analysis_data:
                                exec_summary = analysis_data['executive_summary']
                                if isinstance(exec_summary, dict):
                                    total_recommendations += exec_summary.get('total_actions', 0)
                            
                            # Extraer ahorros potenciales
                            if 'potential_savings' in analysis_data:
                                potential_savings += analysis_data['potential_savings']
                            elif 'cost_optimization' in analysis_data:
                                cost_opt = analysis_data['cost_optimization']
                                if isinstance(cost_opt, dict):
                                    potential_savings += cost_opt.get('estimated_monthly_optimization', 0)
                            
                            # Extraer Azure Advisor Score
                            if 'azure_advisor_score' in analysis_data:
                                azure_advisor_score = max(azure_advisor_score, analysis_data['azure_advisor_score'])
                            elif 'executive_summary' in analysis_data:
                                exec_summary = analysis_data['executive_summary']
                                if isinstance(exec_summary, dict):
                                    azure_advisor_score = max(azure_advisor_score, exec_summary.get('advisor_score', 0))
            except Exception as analysis_error:
                logger.warning(f"Error analizando datos de CSV: {analysis_error}")
            
            # Obtener actividades del usuario
            total_activities = UserActivity.objects.filter(user=user).count()
            
            # Actividades recientes (últimos 7 días)
            last_week = timezone.now() - timedelta(days=7)
            recent_activities = UserActivity.objects.filter(
                user=user,
                timestamp__gte=last_week
            ).count()
            
            # Calcular tasa de éxito
            success_rate = 100
            if total_reports > 0:
                success_rate = round((completed_reports / total_reports) * 100, 1)
            
            # Compilar estadísticas reales
            stats_data = {
                'total_files': total_files,
                'total_csv_files': total_csv_files,
                'total_storage_files': total_storage_files,
                'total_reports': total_reports,
                'completed_reports': completed_reports,
                'total_recommendations': total_recommendations,
                'potential_savings': potential_savings,
                'azure_advisor_score': azure_advisor_score,
                'success_rate': success_rate,
                'total_activities': total_activities,
                'recent_activities': recent_activities,
                'last_updated': timezone.now().isoformat()
            }
            
            logger.info(f"Stats reales calculadas para usuario: {request.user.email}")
            logger.info(f"Total recommendations: {total_recommendations}, Savings: {potential_savings}")
            
            return Response(stats_data)
            
        except Exception as e:
            logger.error(f"Error obteniendo stats reales: {e}")
            return Response({
                'total_files': 0,
                'total_reports': 0,
                'completed_reports': 0,
                'total_recommendations': 0,
                'potential_savings': 0,
                'success_rate': 100,
                'last_updated': timezone.now().isoformat()
            })
    
    @action(detail=False, methods=['post'], url_path='track')
    def track_activity(self, request):
        """Endpoint para registrar nueva actividad del usuario"""
        try:
            data = request.data
            activity_type = data.get('activity_type')
            description = data.get('description')
            metadata = data.get('metadata', {})
            
            if not activity_type or not description:
                return Response(
                    {'error': 'activity_type y description son requeridos'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Crear nueva actividad
            activity = UserActivity.objects.create(
                user=request.user,
                activity_type=activity_type,
                description=description,
                ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                metadata=metadata
            )
            
            serializer = UserActivitySerializer(activity)
            logger.info(f"Nueva actividad registrada para {request.user.email}: {activity_type}")
            
            return Response({
                'message': 'Actividad registrada exitosamente',
                'activity': serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error registrando actividad: {e}")
            return Response(
                {'error': f'Error registrando actividad: {str(e)}'}, 
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
