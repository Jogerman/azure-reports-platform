# apps/reports/views.py
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from django.http import FileResponse, Http404, HttpResponse
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404
from django.utils import timezone
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
        if hasattr(self, 'action') and self.action == 'create':
            return CSVFileUploadSerializer
        return CSVFileSerializer
    
    def get_parsers(self):
        """Usar el parser correcto basado en la acción"""
        # Verificar si existe el atributo action antes de usarlo
        if hasattr(self, 'action') and self.action == 'create':
            return [MultiPartParser(), FormParser()]
        # Verificar el método HTTP como alternativa
        elif hasattr(self.request, 'method') and self.request.method == 'POST':
            return [MultiPartParser(), FormParser()]
        return super().get_parsers()
    
    def perform_create(self, serializer):
        """Personalizar la creación del archivo CSV"""
        serializer.save(user=self.request.user)
    
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
        
        # Importar aquí para evitar problemas de importación circular
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
        if hasattr(self, 'action') and self.action == 'create':
            return ReportCreateSerializer
        return ReportSerializer
    
    def perform_create(self, serializer):
        """Personalizar la creación del reporte"""
        serializer.save(user=self.request.user)
    
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
        
        # Devolver URL de descarga
        return Response({
            'download_url': report.pdf_file_url,
            'filename': f'{report.title}.pdf'
        })
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
                content_type='text/html'
            )

    def generate_report_html(self, report):
        """Generar HTML del reporte"""
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{report.title}</title>
            <meta charset="utf-8">
            <style>
                body {{ 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{ 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 10px;
                    margin-bottom: 30px;
                }}
                .metric-card {{ 
                    background: #f8fafc;
                    border: 1px solid #e2e8f0;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 15px 0;
                    display: inline-block;
                    min-width: 200px;
                    text-align: center;
                }}
                .metric-value {{ 
                    font-size: 2em;
                    font-weight: bold;
                    color: #2d3748;
                }}
                .metric-label {{ 
                    color: #718096;
                    font-size: 0.9em;
                    margin-top: 5px;
                }}
                .section {{ 
                    margin: 30px 0;
                    padding: 20px;
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                }}
                .success {{ color: #38a169; }}
                .warning {{ color: #d69e2e; }}
                .error {{ color: #e53e3e; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{report.title}</h1>
                <p>Generado el: {report.created_at.strftime('%d/%m/%Y %H:%M')}</p>
                <p>Estado: {report.status}</p>
            </div>
            
            <div class="section">
                <h2>📊 Información del Reporte</h2>
                <p><strong>Tipo:</strong> {getattr(report, 'report_type', 'No especificado')}</p>
                <p><strong>Descripción:</strong> {getattr(report, 'description', 'Sin descripción')}</p>
                <p><strong>Usuario:</strong> {report.user.username if hasattr(report, 'user') else 'N/A'}</p>
            </div>
            
            <div class="section">
                <h2>📈 Análisis de Azure Advisor</h2>
                <p>Este reporte contiene el análisis de las recomendaciones de Azure Advisor.</p>
                <div class="metric-card">
                    <div class="metric-value success">✅</div>
                    <div class="metric-label">Reporte Completado</div>
                </div>
            </div>
            
            <div class="section">
                <h2>🚀 Próximos Pasos</h2>
                <ol>
                    <li>Revisar las recomendaciones específicas</li>
                    <li>Priorizar implementaciones según impacto</li>
                    <li>Programar seguimiento regular</li>
                    <li>Validar mejoras implementadas</li>
                </ol>
            </div>
            
            <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #e2e8f0; text-align: center; color: #718096;">
                <p>Azure Reports • Generado el {report.created_at.strftime('%d/%m/%Y %H:%M')}</p>
                <p>ID del reporte: {report.id}</p>
            </footer>
        </body>
        </html>
        """
        
        return html_template