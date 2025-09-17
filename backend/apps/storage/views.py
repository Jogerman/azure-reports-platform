# apps/storage/views.py
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
            'rows_count', 'columns_count', 'analysis_data', 'upload_date'
        ]

class FilesListView(APIView):
    """Vista que lista CSVFiles para el frontend"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            user = request.user
            
            # Obtener CSVFiles usando el campo correcto
            csv_files = CSVFile.objects.filter(user=user).order_by('-upload_date')
            
            files_data = []
            
            for csv_file in csv_files:
                files_data.append({
                    'id': str(csv_file.id),
                    'original_filename': csv_file.original_filename,
                    'file_size': csv_file.file_size,
                    'file_type': 'csv',
                    'created_at': csv_file.upload_date.isoformat(),
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
    """FIX: Vista corregida para upload de archivos CSV"""
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)  # ← CRÍTICO: Parsers correctos
    
    def post(self, request):
        try:
            logger.info(f"Upload request recibido. Content-Type: {request.content_type}")
            logger.info(f"FILES disponibles: {list(request.FILES.keys())}")
            logger.info(f"Parsers usados: {[p.__class__.__name__ for p in self.parser_classes]}")
            
            # FIX: Verificar que se recibió un archivo
            uploaded_file = request.FILES.get('file')
            if not uploaded_file:
                return Response({
                    'error': 'No se recibió ningún archivo. Asegúrate de usar FormData con campo "file"'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validar que sea CSV
            if not uploaded_file.name.lower().endswith('.csv'):
                return Response({
                    'error': 'Solo se permiten archivos CSV'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validar tamaño (50MB máximo)
            max_size = 50 * 1024 * 1024  # 50MB
            if uploaded_file.size > max_size:
                return Response({
                    'error': 'El archivo debe ser menor a 50MB'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            logger.info(f"Procesando archivo CSV: {uploaded_file.name} ({uploaded_file.size} bytes)")
            
            # Crear CSVFile
            csv_file = CSVFile.objects.create(
                user=request.user,
                original_filename=uploaded_file.name,
                file_size=uploaded_file.size,
                content_type=uploaded_file.content_type or 'text/csv',
                processing_status='processing'
            )
            
            # Procesar CSV
            try:
                # Leer contenido del archivo
                file_content = uploaded_file.read().decode('utf-8-sig')  # utf-8-sig para manejar BOM
                csv_reader = csv.reader(io.StringIO(file_content))
                rows = list(csv_reader)
                headers = rows[0] if rows else []
                
                # Actualizar metadatos
                csv_file.rows_count = len(rows) - 1 if rows else 0  # -1 para excluir header
                csv_file.columns_count = len(headers)
                csv_file.processing_status = 'completed'
                
                # Análisis básico de Azure Advisor CSV
                analysis_data = {
                    'total_recommendations': len(rows) - 1 if rows else 0,
                    'estimated_savings': (len(rows) - 1) * 100 if rows else 0,  # Estimación básica
                    'categories': self.analyze_categories(rows[1:] if len(rows) > 1 else []),
                    'processed_at': csv_file.upload_date.isoformat(),
                    'headers': headers[:10],  # Primeros 10 headers para referencia
                }
                
                csv_file.analysis_data = analysis_data
                csv_file.save()
                
                logger.info(f"CSV procesado exitosamente: {csv_file.original_filename}")
                
                return Response({
                    'id': str(csv_file.id),
                    'original_filename': csv_file.original_filename,
                    'file_size': csv_file.file_size,
                    'processing_status': csv_file.processing_status,
                    'rows_count': csv_file.rows_count,
                    'columns_count': csv_file.columns_count,
                    'analysis_data': csv_file.analysis_data,
                    'created_at': csv_file.upload_date.isoformat(),
                    'message': 'Archivo procesado exitosamente'
                }, status=status.HTTP_201_CREATED)
                
            except Exception as processing_error:
                # Error en procesamiento, marcar como fallido
                csv_file.processing_status = 'failed'
                csv_file.error_message = str(processing_error)
                csv_file.save()
                
                logger.error(f"Error procesando CSV: {processing_error}")
                return Response({
                    'error': f'Error procesando archivo CSV: {str(processing_error)}'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error en upload: {str(e)}")
            return Response({
                'error': f'Error interno: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def analyze_categories(self, rows):
        """Análisis básico de categorías para Azure Advisor"""
        categories = {
            'security': 0,
            'cost': 0,
            'performance': 0,
            'reliability': 0,
            'operational_excellence': 0
        }
        
        for row in rows:
            if len(row) > 3:  # Asumir que hay al menos 4 columnas
                category = str(row[3]).lower() if len(row) > 3 else ''
                
                if 'security' in category:
                    categories['security'] += 1
                elif 'cost' in category:
                    categories['cost'] += 1
                elif 'performance' in category:
                    categories['performance'] += 1
                elif 'reliability' in category:
                    categories['reliability'] += 1
                elif 'operational' in category:
                    categories['operational_excellence'] += 1
                else:
                    # Distribución por defecto si no se reconoce
                    categories['security'] += 1
        
        return categories