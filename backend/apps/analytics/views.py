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
            # Importar modelos según tu estructura
            from apps.storage.models import UploadedFile  # o el modelo que uses para archivos
            from apps.reports.models import Report  # modelo de reportes
            
            user = request.user
            
            # Obtener archivos del usuario
            user_files = UploadedFile.objects.filter(user=user)
            user_reports = Report.objects.filter(user=user)
            
            # Estadísticas básicas
            total_files = user_files.count()
            total_reports = user_reports.count()
            completed_reports = user_reports.filter(status='completed').count()
            
            # Calcular recomendaciones y ahorros
            total_recommendations = 0
            potential_savings = 0
            
            for file in user_files:
                # Ajustar según tu modelo de datos
                if hasattr(file, 'analysis_data') and file.analysis_data:
                    total_recommendations += file.analysis_data.get('total_recommendations', 0)
                    potential_savings += file.analysis_data.get('estimated_savings', 0)
            
            # Calcular tasa de éxito
            success_rate = 0
            if total_reports > 0:
                success_rate = round((completed_reports / total_reports) * 100, 1)
            
            return Response({
                'total_files': total_files,
                'total_reports': total_reports,
                'completed_reports': completed_reports,
                'total_recommendations': total_recommendations,
                'potential_savings': round(potential_savings, 2),
                'success_rate': success_rate,
                'last_updated': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error en dashboard stats: {str(e)}")
            # Devolver datos básicos en caso de error
            return Response({
                'total_files': 0,
                'total_reports': 0,
                'completed_reports': 0,
                'total_recommendations': 0,
                'potential_savings': 0,
                'success_rate': 0,
                'last_updated': datetime.now().isoformat(),
                'error': 'Datos no disponibles temporalmente'
            })
