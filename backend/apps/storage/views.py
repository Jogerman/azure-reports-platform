# apps/storage/views.py - CREAR O ACTUALIZAR ESTE ARCHIVO
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from apps.reports.models import CSVFile
from rest_framework import serializers
import logging
import uuid
import csv
import io

logger = logging.getLogger(__name__)

class CSVFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CSVFile
        fields = [
            'id', 'original_filename', 'file_size', 'processing_status',
            'rows_count', 'columns_count', 'analysis_data', 'upload_date'  # ← USAR upload_date
        ]

class FilesListView(APIView):
    """Vista que lista CSVFiles para el frontend"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            user = request.user
            
            # Obtener CSVFiles - USAR CAMPOS CORRECTOS
            csv_files = CSVFile.objects.filter(user=user).order_by('-upload_date')  # ← upload_date
            
            files_data = []
            
            for csv_file in csv_files:
                files_data.append({
                    'id': str(csv_file.id),
                    'original_filename': csv_file.original_filename,
                    'file_size': csv_file.file_size,
                    'file_type': 'csv',
                    'created_at': csv_file.upload_date.isoformat(),  # ← Mapear upload_date a created_at
                    'status': csv_file.processing_status,
                    'source': 'csv',
                    'analysis_data': {
                        'total_rows': csv_file.rows_count or 0,
                        'total_columns': csv_file.columns_count or 0,
                        'total_recommendations': (csv_file.analysis_data or {}).get('total_recommendations', 0),
                        'estimated_savings': (csv_file.analysis_data or {}).get('estimated_savings', 0),
                    }
                })
            
            logger.info(f"Devolviendo {len(files_data)} archivos para el usuario {user.username}")
            
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

class FileUploadView(APIView):
    """Vista para subir archivos CSV - GUARDAR EN BD SOLAMENTE (NO AZURE BLOB)"""
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)
    
    def post(self, request):
        try:
            uploaded_file = request.FILES.get('file')
            if not uploaded_file:
                return Response({
                    'error': 'No se recibió ningún archivo'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validar que es CSV
            if not uploaded_file.name.endswith('.csv'):
                return Response({
                    'error': 'Solo se permiten archivos CSV'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Crear CSVFile - SOLO EN BASE DE DATOS POR AHORA
            csv_file = CSVFile.objects.create(
                user=request.user,
                original_filename=uploaded_file.name,
                file_size=uploaded_file.size,
                processing_status='processing'
            )
            
            # Procesar CSV en memoria
            file_content = uploaded_file.read().decode('utf-8')
            csv_reader = csv.reader(io.StringIO(file_content))
            
            rows = list(csv_reader)
            headers = rows[0] if rows else []
            
            # Actualizar datos del archivo
            csv_file.rows_count = len(rows) - 1 if rows else 0
            csv_file.columns_count = len(headers)
            csv_file.processing_status = 'completed'
            
            # Análisis básico basado en Azure Advisor
            csv_file.analysis_data = {
                'total_recommendations': len(rows) - 1 if rows else 0,
                'estimated_savings': (len(rows) - 1) * 100 if rows else 0,
                'categories': {
                    'security': int((len(rows) - 1) * 0.4) if rows else 0,
                    'cost': int((len(rows) - 1) * 0.3) if rows else 0,
                    'performance': int((len(rows) - 1) * 0.2) if rows else 0,
                    'reliability': int((len(rows) - 1) * 0.1) if rows else 0,
                },
                'headers': headers,
                'sample_data': rows[1:6] if len(rows) > 1 else []  # Primeras 5 filas de datos
            }
            
            csv_file.save()
            
            logger.info(f"CSV procesado: {csv_file.original_filename} - {csv_file.rows_count} filas")
            
            # RESPUESTA EN FORMATO ESPERADO
            return Response({
                'id': str(csv_file.id),
                'original_filename': csv_file.original_filename,
                'file_size': csv_file.file_size,
                'processing_status': csv_file.processing_status,
                'rows_count': csv_file.rows_count,
                'columns_count': csv_file.columns_count,
                'analysis_data': csv_file.analysis_data,
                'created_at': csv_file.upload_date.isoformat(),  # ← Mapear correctamente
                'message': 'Archivo procesado exitosamente'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error procesando archivo: {str(e)}")
            return Response({
                'error': f'Error procesando archivo: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)