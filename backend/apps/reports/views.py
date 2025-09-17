# apps/reports/views.py - VERSIÓN FINAL CORREGIDA

from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from django.template.loader import render_to_string
from rest_framework import serializers
from .models import CSVFile, Report
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

# Serializers
class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ['id', 'title', 'description', 'report_type', 'status', 'created_at', 'user', 'csv_file']
        read_only_fields = ['id', 'created_at', 'user']


class ReportViewSet(ModelViewSet):
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Queryset base sin filtros externos"""
        return Report.objects.filter(user=self.request.user)
    
    def filter_queryset(self, queryset):
        """CRITICAL FIX: Override completo del filter_queryset para controlar orden de operaciones"""
        
        # 1. Partir del queryset base
        filtered_queryset = queryset
        
        # 2. Aplicar ordering PRIMERO
        ordering = self.request.query_params.get('ordering', '-created_at')
        if ordering:
            filtered_queryset = filtered_queryset.order_by(ordering)
        
        # 3. Aplicar otros filtros manuales (búsqueda, etc.)
        search = self.request.query_params.get('search')
        if search:
            filtered_queryset = filtered_queryset.filter(
                title__icontains=search
            )
        
        status_filter = self.request.query_params.get('status')
        if status_filter:
            filtered_queryset = filtered_queryset.filter(status=status_filter)
        
        report_type_filter = self.request.query_params.get('report_type')
        if report_type_filter:
            filtered_queryset = filtered_queryset.filter(report_type=report_type_filter)
        
        # 4. Aplicar limit AL FINAL (slice)
        limit = self.request.query_params.get('limit')
        if limit:
            try:
                limit = int(limit)
                filtered_queryset = filtered_queryset[:limit]
            except (ValueError, TypeError):
                pass
        
        return filtered_queryset
    
    def perform_create(self, serializer):
        """Asegurar que el reporte se asigne al usuario actual"""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generar reporte asegurando relación con csv_file"""
        try:
            file_id = request.data.get('file_id')
            
            if not file_id:
                return Response({'error': 'file_id es requerido'}, status=400)
            
            # Buscar CSV file
            try:
                csv_file = CSVFile.objects.get(id=file_id, user=request.user)
            except (CSVFile.DoesNotExist, ValueError) as e:
                logger.error(f"CSV file no encontrado: {file_id}, error: {e}")
                return Response({'error': 'Archivo no encontrado'}, status=404)
            
            # Crear reporte con relación a csv_file
            report_data = {
                'user': request.user,
                'csv_file': csv_file,
                'title': request.data.get('title', f'Análisis - {csv_file.original_filename}'),
                'description': request.data.get('description', ''),
                'report_type': request.data.get('report_type', 'comprehensive'),
                'status': 'completed',
            }
            
            report = Report.objects.create(**report_data)
            
            logger.info(f"Reporte creado exitosamente: {report.id}")
            
            serializer = ReportSerializer(report)
            return Response(serializer.data, status=201)
            
        except Exception as e:
            logger.error(f"Error generando reporte: {str(e)}")
            return Response({'error': str(e)}, status=500)
        
    @action(detail=True, methods=['get'])
    def html(self, request, pk=None):
        """Endpoint para obtener HTML del reporte"""
        try:
            report = self.get_object()
            
            # Generar HTML del reporte
            html_content = self.generate_report_html(report)
            
            return HttpResponse(html_content, content_type='text/html')
            
        except Exception as e:
            logger.error(f"Error generando HTML para reporte {pk}: {str(e)}")
            return HttpResponse(
                f"<html><body><h1>Error</h1><p>No se pudo generar el reporte: {str(e)}</p></body></html>", 
                content_type='text/html',
                status=500
            )
    
    def generate_report_html(self, report):
        """Generar HTML del reporte"""
        context = {
            'report': report,
            'csv_file': report.csv_file,
            'analysis_data': report.csv_file.analysis_data if report.csv_file else {},
            'generated_at': datetime.now(),
        }
        
        try:
            html_content = render_to_string('reports/report_template.html', context)
            return html_content
        except Exception as e:
            logger.error(f"Error renderizando template: {e}")
            return f"""
            <html>
                <body>
                    <h1>Reporte: {report.title}</h1>
                    <p>Estado: {report.status}</p>
                    <p>Archivo: {report.csv_file.original_filename if report.csv_file else 'N/A'}</p>
                    <p>Creado: {report.created_at}</p>
                </body>
            </html>
            """