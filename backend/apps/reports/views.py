# apps/reports/views.py
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
import logging

from .models import CSVFile, Report
from .serializers import (
    CSVFileSerializer, CSVFileUploadSerializer, 
    ReportSerializer, ReportCreateSerializer
)

logger = logging.getLogger(__name__)

class CSVFileViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de archivos CSV"""
    serializer_class = CSVFileSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['processing_status']
    
    def get_queryset(self):
        """Solo archivos del usuario actual"""
        return CSVFile.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        """Usar serializer específico para upload"""
        if self.action == 'create':
            return CSVFileUploadSerializer
        return CSVFileSerializer
    
    def get_parsers(self):
        """Usar MultiPartParser para uploads"""
        if self.action == 'create':
            return [MultiPartParser(), FormParser()]
        return super().get_parsers()
    
    @action(detail=True, methods=['post'])
    def reprocess(self, request, pk=None):
        """Re-procesar un archivo CSV"""
        csv_file = self.get_object()
        
        if csv_file.processing_status == 'processing':
            return Response(
                {'error': 'El archivo ya se está procesando'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Reiniciar procesamiento
        csv_file.processing_status = 'pending'
        csv_file.analysis_data = {}
        csv_file.save()
        
        from .tasks import process_csv_file
        process_csv_file.delay(csv_file.id)
        
        return Response({'message': 'Reprocesamiento iniciado'})
    
    @action(detail=True, methods=['get'])
    def analysis_details(self, request, pk=None):
        """Obtener detalles completos del análisis"""
        csv_file = self.get_object()
        
        if not csv_file.analysis_data:
            return Response(
                {'error': 'El archivo no ha sido analizado aún'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(csv_file.analysis_data)

class ReportViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de reportes"""
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'report_type']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Solo reportes del usuario actual"""
        return Report.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        """Usar serializer específico para creación"""
        if self.action == 'create':
            return ReportCreateSerializer
        return ReportSerializer
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Descargar reporte PDF"""
        report = self.get_object()
        
        if report.status != 'completed' or not report.pdf_file_url:
            return Response(
                {'error': 'El reporte no está disponible para descarga'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Incrementar contador de descargas
        report.download_count += 1
        report.last_downloaded_at = timezone.now()
        report.save(update_fields=['download_count', 'last_downloaded_at'])
        
        # Devolver URL de descarga o archivo directo
        try:
            from apps.storage.services.azure_storage_service import get_azure_file_url
            file_content = get_azure_file_url(report.pdf_file_url)
            
            response = FileResponse(
                file_content,
                content_type='application/pdf',
                filename=f"{report.title}.pdf"
            )
            return response
        except Exception as e:
            logger.error(f"Error descargando reporte {pk}: {e}")
            return Response(
                {'error': 'Error descargando el archivo'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def preview(self, request, pk=None):
        """Obtener preview HTML del reporte"""
        report = self.get_object()
        
        if report.status != 'completed':
            return Response(
                {'error': 'El reporte no está completado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Generar preview si no existe
        if not report.html_preview_url:
            from apps.storage.services.report_service import generate_html_preview
            html_content = generate_html_preview(report)
            return Response({'html_content': html_content})
        
        return Response({'preview_url': report.html_preview_url})
    
    @action(detail=True, methods=['post'])
    def regenerate(self, request, pk=None):
        """Regenerar un reporte"""
        report = self.get_object()
        
        if report.status == 'generating':
            return Response(
                {'error': 'El reporte ya se está generando'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Reiniciar generación
        report.status = 'generating'
        report.completed_at = None
        report.save()
        
        from .tasks import generate_report
        generate_report.delay(report.id)
        
        return Response({'message': 'Regeneración iniciada'})
