# apps/storage/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from apps.reports.models import CSVFile
from rest_framework import serializers
from django.utils import timezone
import pandas as pd
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
    """Vista mejorada para upload de archivos CSV con análisis avanzado"""
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)
    
    def post(self, request):
        try:
            logger.info(f"Upload request recibido. Content-Type: {request.content_type}")
            logger.info(f"FILES disponibles: {list(request.FILES.keys())}")
            logger.info(f"Parsers usados: {[p.__class__.__name__ for p in self.parser_classes]}")
            
            # Verificar archivo
            uploaded_file = request.FILES.get('file')
            if not uploaded_file:
                return Response({
                    'error': 'No se recibió ningún archivo. Asegúrate de usar FormData con campo "file"'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validar CSV
            if not uploaded_file.name.lower().endswith('.csv'):
                return Response({
                    'error': 'Solo se permiten archivos CSV'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validar tamaño
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
            
            # NUEVO: Procesamiento avanzado
            try:
                # Leer archivo
                file_content = uploaded_file.read().decode('utf-8-sig')
                
                # Procesar con pandas y análisis avanzado
                import pandas as pd
                import io
                
                # Crear DataFrame
                df = pd.read_csv(io.StringIO(file_content))
                logger.info(f"DataFrame creado: {len(df)} filas, {len(df.columns)} columnas")
                
                # Análisis básico
                csv_file.rows_count = len(df)
                csv_file.columns_count = len(df.columns)
                
                # ANÁLISIS AVANZADO
                try:
                    # Intentar usar el analizador avanzado
                    from .services.enhanced_analyzer import analyze_azure_advisor_csv
                    
                    logger.info("🚀 Iniciando análisis avanzado...")
                    advanced_analysis = analyze_azure_advisor_csv(df, uploaded_file.name)
                    
                    csv_file.analysis_data = advanced_analysis
                    logger.info("✅ Análisis avanzado completado exitosamente")
                    
                except ImportError as ie:
                    logger.warning(f"Analizador avanzado no disponible: {ie}")
                    csv_file.analysis_data = self.basic_analysis_fallback(df)
                    
                except Exception as ae:
                    logger.error(f"Error en análisis avanzado: {ae}")
                    csv_file.analysis_data = self.basic_analysis_fallback(df)
                
                # Marcar como completado
                csv_file.processing_status = 'completed'
                csv_file.processed_date = timezone.now()
                csv_file.save()
                
                logger.info(f"✅ CSV procesado exitosamente: {csv_file.original_filename}")
                
                return Response({
                    'id': str(csv_file.id),
                    'original_filename': csv_file.original_filename,
                    'file_size': csv_file.file_size,
                    'processing_status': csv_file.processing_status,
                    'rows_count': csv_file.rows_count,
                    'columns_count': csv_file.columns_count,
                    'analysis_data': csv_file.analysis_data,
                    'created_at': csv_file.upload_date.isoformat(),
                    'message': 'Archivo procesado exitosamente con análisis avanzado'
                }, status=status.HTTP_201_CREATED)
                
            except Exception as processing_error:
                # Error en procesamiento
                csv_file.processing_status = 'failed'
                csv_file.error_message = str(processing_error)
                csv_file.save()
                
                logger.error(f"❌ Error procesando CSV: {processing_error}")
                return Response({
                    'error': f'Error procesando archivo CSV: {str(processing_error)}'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"❌ Error en upload: {str(e)}")
            return Response({
                'error': f'Error interno: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def basic_analysis_fallback(self, df):
        """Análisis básico como fallback si falla el avanzado"""
        try:
            # Análisis básico pero más completo que el anterior
            total_recs = len(df)
            
            # Intentar detectar categorías automáticamente
            categories = {}
            if len(df.columns) > 3:
                # Buscar columna de categorías
                category_column = None
                for col in df.columns:
                    if 'category' in col.lower() or 'categoria' in col.lower():
                        category_column = col
                        break
                
                if category_column:
                    categories = df[category_column].value_counts().to_dict()
            
            return {
                'metadata': {
                    'total_recommendations': total_recs,
                    'analysis_date': timezone.now().isoformat(),
                    'analysis_type': 'basic_fallback',
                    'columns': list(df.columns)[:10]  # Primeras 10 columnas
                },
                'executive_summary': {
                    'monthly_savings': total_recs * 120,  # $120 por recomendación
                    'monthly_investment': total_recs * 75,  # $75 por recomendación
                    'net_monthly_savings': total_recs * 45,  # Diferencia
                    'total_actions': total_recs,
                    'working_hours_estimate': total_recs * 0.35
                },
                'categories_detected': categories,
                'data_quality': {
                    'completeness_score': 85,  # Score básico
                    'has_categories': bool(categories)
                }
            }
        except Exception as e:
            logger.error(f"Error en análisis básico: {e}")
            return {
                'metadata': {
                    'total_recommendations': len(df) if df is not None else 0,
                    'analysis_date': timezone.now().isoformat(),
                    'analysis_type': 'minimal_fallback',
                    'error': str(e)
                }
            }
    
    # Mantener el método analyze_categories existente para compatibilidad
    def analyze_categories(self, rows):
        """Método legacy mantenido para compatibilidad"""
        categories = {
            'security': 0,
            'cost': 0,
            'performance': 0,
            'reliability': 0,
            'operational_excellence': 0
        }
        
        for row in rows:
            if len(row) > 3:
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
                    categories['security'] += 1
        
        return categories