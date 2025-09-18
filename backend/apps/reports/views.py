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
        """Generar HTML del reporte con diseño profesional"""
        try:
            # Obtener datos del análisis del CSV
            analysis_data = {}
            if report.csv_file and hasattr(report.csv_file, 'analysis_data'):
                analysis_data = report.csv_file.analysis_data or {}
            
            # NUEVO: Usar generador HTML profesional
            try:
                from ..storage.services.enhanced_html_generator import generate_professional_azure_html
                
                # Extraer nombre del cliente (puedes configurarlo como necesites)
                client_name = getattr(report, 'client_name', 'CONTOSO')
                filename = report.csv_file.original_filename if report.csv_file else ""
                
                # Generar HTML profesional con análisis completo
                html_content = generate_professional_azure_html(
                    analysis_data=analysis_data,
                    client_name=client_name,
                    filename=filename
                )
                
                logger.info(f"✅ HTML profesional generado exitosamente para reporte {report.id}")
                return html_content
                
            except ImportError:
                logger.warning("Generador HTML profesional no disponible, usando básico")
                return self.generate_basic_html(report, analysis_data)
            
            except Exception as e:
                logger.error(f"Error generando HTML profesional: {e}, usando básico")
                return self.generate_basic_html(report, analysis_data)
        
        except Exception as e:
            logger.error(f"Error generando HTML para reporte {report.id}: {str(e)}")
            return self.generate_error_html(report, str(e))

    def generate_basic_html(self, report, analysis_data):
        """Generar HTML básico como fallback"""
        executive = analysis_data.get('executive_summary', {})
        
        return f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>Azure Advisor Report - {report.title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
                .header {{ background: #0066CC; color: white; padding: 30px; text-align: center; border-radius: 8px; }}
                .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }}
                .metric-card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; border-left: 4px solid #0066CC; }}
                .metric-value {{ font-size: 2rem; font-weight: bold; color: #0066CC; }}
                .metric-label {{ color: #666; margin-top: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Azure Advisor Analysis Report</h1>
                <h2>{report.title}</h2>
                <p>Generated on {timezone.now().strftime('%B %d, %Y')}</p>
            </div>
            
            <div class="metrics">
                <div class="metric-card">
                    <div class="metric-value">${executive.get('monthly_savings', 0):,.0f}</div>
                    <div class="metric-label">Monthly Savings</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{executive.get('total_actions', 0)}</div>
                    <div class="metric-label">Total Recommendations</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{executive.get('working_hours_estimate', 0)}</div>
                    <div class="metric-label">Estimated Hours</div>
                </div>
            </div>
            
            <div style="margin-top: 40px; padding: 20px; background: #f8f9fa; border-radius: 8px;">
                <h3>Report Summary</h3>
                <p>This report analyzes your Azure Advisor recommendations and provides actionable insights for optimization.</p>
                <p><strong>File analyzed:</strong> {report.csv_file.original_filename if report.csv_file else 'N/A'}</p>
                <p><strong>Status:</strong> {report.get_status_display()}</p>
            </div>
            
            <div style="text-align: center; margin-top: 40px; color: #666; border-top: 1px solid #ddd; padding-top: 20px;">
                <p>Generated by Azure Reports Platform | {timezone.now().strftime('%Y-%m-%d %H:%M')}</p>
            </div>
        </body>
        </html>
        """

    def generate_error_html(self, report, error_message):
        """Generar HTML de error"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Error - Azure Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .error {{ background: #fee; border: 1px solid #fcc; padding: 20px; border-radius: 8px; }}
            </style>
        </head>
        <body>
            <h1>Azure Advisor Report - {report.title}</h1>
            <div class="error">
                <h3>Error generating detailed report</h3>
                <p>Report ID: {report.id}</p>
                <p>Error: {error_message}</p>
            </div>
            <p>Please contact support if this error persists.</p>
        </body>
        </html>
        """