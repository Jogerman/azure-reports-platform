# apps/storage/views.py - CREAR O ACTUALIZAR ESTE ARCHIVO
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.http import JsonResponse
from .models import StorageFile
from apps.reports.models import CSVFile
from rest_framework import serializers
import logging

logger = logging.getLogger(__name__)

# Serializers
class StorageFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StorageFile
        fields = [
            'id', 'original_filename', 'file_size', 'file_type', 
            'upload_date', 'description', 'tags'
        ]

class CSVFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CSVFile
        fields = [
            'id', 'original_filename', 'file_size', 'processing_status',
            'rows_count', 'columns_count', 'analysis_data', 'created_at'
        ]

# ViewSets
class StorageFileViewSet(ModelViewSet):
    """ViewSet para archivos de storage"""
    serializer_class = StorageFileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return StorageFile.objects.filter(user=self.request.user).order_by('-upload_date')

# Vista para combinar ambos tipos de archivos
class FilesListView(APIView):
    """Vista que combina StorageFiles y CSVFiles para el frontend"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            user = request.user
            
            # Obtener StorageFiles
            storage_files = StorageFile.objects.filter(user=user).order_by('-upload_date')
            csv_files = CSVFile.objects.filter(user=user).order_by('-created_at')
            
            # Convertir StorageFiles a formato común
            files_data = []
            
            for storage_file in storage_files:
                files_data.append({
                    'id': str(storage_file.id),
                    'original_filename': storage_file.original_filename,
                    'file_size': storage_file.file_size,
                    'file_type': storage_file.file_type,
                    'created_at': storage_file.upload_date.isoformat(),
                    'status': 'stored',
                    'source': 'storage',
                    'analysis_data': None
                })
            
            # Convertir CSVFiles a formato común
            for csv_file in csv_files:
                files_data.append({
                    'id': str(csv_file.id),
                    'original_filename': csv_file.original_filename,
                    'file_size': csv_file.file_size,
                    'file_type': 'csv',
                    'created_at': csv_file.created_at.isoformat(),
                    'status': csv_file.processing_status,
                    'source': 'csv',
                    'analysis_data': csv_file.analysis_data or {},
                    'rows_count': csv_file.rows_count,
                    'columns_count': csv_file.columns_count,
                    # Agregar campos que espera el frontend
                    'total_rows': csv_file.rows_count,
                    'total_columns': csv_file.columns_count,
                    'total_recommendations': csv_file.analysis_data.get('total_recommendations', 0) if csv_file.analysis_data else 0,
                    'estimated_savings': csv_file.analysis_data.get('estimated_savings', 0) if csv_file.analysis_data else 0,
                })
            
            # Ordenar por fecha de creación (más reciente primero)
            files_data.sort(key=lambda x: x['created_at'], reverse=True)
            
            # Devolver en formato que espera el frontend
            return Response({
                'results': files_data,
                'count': len(files_data)
            })
            
        except Exception as e:
            logger.error(f"Error obteniendo archivos: {str(e)}")
            return Response({
                'results': [],
                'count': 0,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

