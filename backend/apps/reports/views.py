# apps/reports/views.py
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
        # USAR SOLO CAMPOS QUE EXISTEN - revisar tu modelo
        fields = ['id', 'title', 'description', 'report_type', 'status', 'created_at', 'user']
        read_only_fields = ['id', 'created_at', 'user']


class ReportViewSet(ModelViewSet):
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # FIX: NO aplicar limit antes de order_by
        queryset = Report.objects.filter(user=self.request.user)
        
        # Aplicar ordering ANTES que limit
        ordering = self.request.query_params.get('ordering', '-created_at')
        if ordering:
            queryset = queryset.order_by(ordering)
            
        # Aplicar limit DESPUÉS del ordering
        limit = self.request.query_params.get('limit')
        if limit:
            try:
                queryset = queryset[:int(limit)]
            except ValueError:
                pass
                
        return queryset
    
    def perform_create(self, serializer):
        """Asegurar que el reporte se asigne al usuario actual"""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'])
    def generate(self, request):
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
            
            # FIX: Crear reporte CON relación a csv_file si existe en el modelo
            report_data = {
                'user': request.user,
                'title': request.data.get('title', 'Reporte sin título'),
                'description': request.data.get('description', ''),
                'report_type': request.data.get('report_type', 'comprehensive'),
                'status': 'completed',
            }
            
            # Si tu modelo Report tiene csv_file_id, agregarlo:
            # report_data['csv_file'] = csv_file  # Descomenta si existe
            
            report = Report.objects.create(**report_data)
            
            logger.info(f"Reporte creado: {report.id}")
            
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
                content_type='text/html'
            )
    
    def generate_report_html(self, report):
        """Generar HTML del reporte"""
        try:
            # Obtener el archivo CSV asociado
            csv_file = None
            if hasattr(report, 'source_filename'):
                csv_file = CSVFile.objects.filter(
                    user=report.user, 
                    original_filename=report.source_filename
                ).first()
            
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
                        margin: 15px 10px;
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
                    .status-completed {{ color: #38a169; font-weight: bold; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>📊 {report.title}</h1>
                    <p><strong>Generado:</strong> {report.created_at.strftime('%d/%m/%Y %H:%M')}</p>
                    <p><strong>Archivo fuente:</strong> {report.source_filename or 'N/A'}</p>
                    <p><strong>Estado:</strong> <span class="status-completed">{report.status.upper()}</span></p>
                </div>
                
                <div class="section">
                    <h2>📈 Resumen Ejecutivo</h2>
                    <div>
            """
            
            # Agregar métricas si están disponibles
            if report.analysis_summary:
                summary = report.analysis_summary
                
                html_template += f"""
                        <div class="metric-card">
                            <div class="metric-value success">{summary.get('total_recommendations', 0)}</div>
                            <div class="metric-label">Recomendaciones Totales</div>
                        </div>
                        
                        <div class="metric-card">
                            <div class="metric-value warning">{summary.get('security_issues_found', 0)}</div>
                            <div class="metric-label">Problemas de Seguridad</div>
                        </div>
                        
                        <div class="metric-card">
                            <div class="metric-value success">${summary.get('estimated_monthly_savings', 0):,.0f}</div>
                            <div class="metric-label">Ahorros Estimados/Mes</div>
                        </div>
                        
                        <div class="metric-card">
                            <div class="metric-value">{summary.get('performance_improvements', 0)}</div>
                            <div class="metric-label">Mejoras de Rendimiento</div>
                        </div>
                """
            
            html_template += """
                    </div>
                </div>
                
                <div class="section">
                    <h2>📋 Detalles del Reporte</h2>
                    <p><strong>Tipo de análisis:</strong> """ + report.report_type.title() + """</p>
                    <p><strong>Descripción:</strong> """ + (report.description or 'Sin descripción') + """</p>
            """
            
            if report.generation_time_seconds:
                html_template += f"<p><strong>Tiempo de generación:</strong> {report.generation_time_seconds} segundos</p>"
            
            if csv_file:
                html_template += f"""
                    <p><strong>Filas procesadas:</strong> {csv_file.rows_count or 'N/A'}</p>
                    <p><strong>Columnas analizadas:</strong> {csv_file.columns_count or 'N/A'}</p>
                """
            
            html_template += """
                </div>
                
                <div class="section">
                    <h2>🚀 Próximos Pasos</h2>
                    <ol>
                        <li><strong class="error">Priorizar problemas de seguridad</strong> - Implementar las recomendaciones de seguridad inmediatamente</li>
                        <li><strong class="warning">Optimizar costos</strong> - Evaluar y aplicar las optimizaciones de costo identificadas</li>
                        <li><strong class="success">Mejorar rendimiento</strong> - Implementar mejoras de rendimiento en orden de impacto</li>
                        <li><strong>Programar seguimiento</strong> - Establecer revisiones regulares para validar mejoras</li>
                    </ol>
                </div>
                
                <div class="section">
                    <h2>💡 Recomendaciones Clave</h2>
                    <ul>
                        <li>Revisar todas las recomendaciones de <strong class="error">alta prioridad</strong></li>
                        <li>Implementar cambios en ventanas de mantenimiento programadas</li>
                        <li>Documentar todos los cambios realizados</li>
                        <li>Monitorear el impacto de las optimizaciones implementadas</li>
                        <li>Generar un nuevo reporte en 30 días para validar mejoras</li>
                    </ul>
                </div>
                
                <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #e2e8f0; text-align: center; color: #718096;">
                    <p><strong>Azure Reports</strong> • Generado el """ + report.created_at.strftime('%d/%m/%Y %H:%M') + """</p>
                    <p>ID del reporte: """ + str(report.id) + """</p>
                    <p>Usuario: """ + report.user.username + """</p>
                </footer>
            </body>
            </html>
            """
            
            return html_template
            
        except Exception as e:
            logger.error(f"Error generando HTML: {str(e)}")
            return f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h1>Error generando reporte</h1>
                <p>No se pudo generar la visualización del reporte.</p>
                <p><strong>Error:</strong> {str(e)}</p>
                <p><strong>ID del reporte:</strong> {report.id}</p>
            </body>
            </html>
            """
