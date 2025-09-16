# apps/reports/serializers.py
from rest_framework import serializers
from .models import CSVFile, Report
import logging

logger = logging.getLogger(__name__)

class CSVFileSerializer(serializers.ModelSerializer):
    """Serializer para archivos CSV"""
    upload_progress = serializers.ReadOnlyField()
    analysis_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = CSVFile
        fields = [
            'id', 'original_filename', 'file_size', 'processing_status',
            'rows_count', 'columns_count', 'upload_date', 'processed_date',
            'analysis_data', 'azure_blob_url', 'upload_progress', 'analysis_summary'
        ]
        read_only_fields = [
            'id', 'processing_status', 'rows_count', 'columns_count',
            'upload_date', 'processed_date', 'analysis_data', 'azure_blob_url'
        ]
    
    def get_analysis_summary(self, obj):
        """Resumen del análisis para el frontend"""
        if obj.analysis_data:
            return {
                'total_insights': len(obj.analysis_data.get('recommendations', [])),
                'data_quality_score': obj.analysis_data.get('data_quality', {}).get('completeness_score', 0),
                'has_cost_analysis': bool(obj.analysis_data.get('cost_analysis')),
                'has_security_analysis': bool(obj.analysis_data.get('security_analysis')),
            }
        return None

class CSVFileUploadSerializer(serializers.ModelSerializer):
    """Serializer específico para upload de CSV"""
    file = serializers.FileField(write_only=True)
    
    class Meta:
        model = CSVFile
        fields = ['file']
    
    def validate_file(self, value):
        """Validar archivo CSV"""
        # Verificar extensión
        if not value.name.lower().endswith(('.csv', '.xlsx', '.xls')):
            raise serializers.ValidationError(
                "Solo se permiten archivos CSV, XLS o XLSX"
            )
        
        # Verificar tamaño (50MB máximo)
        if value.size > 50 * 1024 * 1024:
            raise serializers.ValidationError(
                "El archivo no puede ser mayor a 50MB"
            )
        
        return value
    
    def create(self, validated_data):
        """Crear instancia y procesar archivo"""
        file = validated_data.pop('file')
        user = self.context['request'].user
        
        try:
            # Crear instancia del CSV
            csv_file = CSVFile.objects.create(
                user=user,
                original_filename=file.name,
                file_size=file.size,
                content_type=file.content_type if hasattr(file, 'content_type') else 'text/csv',
                processing_status='pending'
            )
            
            # Guardar el archivo temporalmente y obtener su path
            # NO pasamos el objeto InMemoryUploadedFile directamente a Celery
            import tempfile
            import os
            
            # Crear archivo temporal
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
                # Escribir el contenido del archivo
                for chunk in file.chunks():
                    tmp_file.write(chunk)
                temp_file_path = tmp_file.name
            
            # Procesar archivo de forma asíncrona con el path del archivo temporal
            from .tasks import process_csv_file
            process_csv_file.delay(csv_file.id, temp_file_path)
            
            logger.info(f"CSV file {csv_file.id} created and queued for processing")
            
            return csv_file
            
        except Exception as e:
            logger.error(f"Error creating CSV file: {str(e)}")
            # Si algo falla, asegurarnos de limpiar
            if 'temp_file_path' in locals():
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
            raise serializers.ValidationError(f"Error procesando archivo: {str(e)}")

class ReportSerializer(serializers.ModelSerializer):
    """Serializer para reportes"""
    csv_file_name = serializers.CharField(source='csv_file.original_filename', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    analysis_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = Report
        fields = [
            'id', 'title', 'description', 'report_type', 'status',
            'csv_file', 'csv_file_name', 'user_name', 'created_at',
            'completed_at', 'pdf_file_url', 'html_preview_url',
            'generation_time_seconds', 'pages_count', 'download_count',
            'analysis_data', 'analysis_summary'
        ]
        read_only_fields = [
            'id', 'status', 'created_at', 'completed_at', 'pdf_file_url',
            'html_preview_url', 'generation_time_seconds', 'pages_count',
            'download_count', 'analysis_data'
        ]
    
    def get_analysis_summary(self, obj):
        """Resumen del análisis para mostrar en el frontend"""
        if obj.analysis_data:
            return {
                'total_recommendations': len(obj.analysis_data.get('recommendations', [])),
                'categories_analyzed': len(obj.analysis_data.get('categories', {})),
                'cost_savings_identified': bool(obj.analysis_data.get('cost_analysis')),
                'security_issues_found': obj.analysis_data.get('security_analysis', {}).get('total_security_recommendations', 0),
            }
        return None

class ReportCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear reportes"""
    
    class Meta:
        model = Report
        fields = [
            'title', 'description', 'report_type', 'csv_file',
            'user_prompt', 'generation_config'
        ]
    
    def validate_csv_file(self, value):
        """Validar que el archivo CSV esté procesado"""
        if value.processing_status != 'completed':
            raise serializers.ValidationError(
                "El archivo CSV debe estar completamente procesado antes de generar un reporte"
            )
        return value
    
    def create(self, validated_data):
        """Crear reporte y iniciar generación"""
        user = self.context['request'].user
        
        report = Report.objects.create(
            user=user,
            status='generating',
            **validated_data
        )
        
        # Iniciar generación asíncrona
        from .tasks import generate_report
        generate_report.delay(report.id)
        
        return report