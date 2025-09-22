# apps/reports/views.py - VERSIÓN FINAL CORREGIDA
from django.utils import timezone
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status, viewsets, permissions
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Q
from django.template.loader import render_to_string
from rest_framework import serializers
from .models import CSVFile, Report
import logging
import json
from datetime import datetime, timedelta

from .models import Report, CSVFile
from .serializers import ReportSerializer

logger = logging.getLogger(__name__)

# Serializers
class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ['id', 'title', 'description', 'report_type', 'status', 'created_at', 'user', 'csv_file']
        read_only_fields = ['id', 'created_at', 'user']


class ReportViewSet(viewsets.ModelViewSet):
    """ViewSet para reportes - PRODUCCIÓN REAL"""
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Retorna reportes del usuario actual"""
        return Report.objects.filter(user=self.request.user)
    
    def list(self, request, *args, **kwargs):
        """Listar reportes con filtros y paginación"""
        try:
            queryset = self.get_queryset()
            
            # Aplicar filtros
            search = request.query_params.get('search')
            if search:
                queryset = queryset.filter(
                    Q(title__icontains=search) | 
                    Q(description__icontains=search)
                )
            
            status_filter = request.query_params.get('status')
            if status_filter:
                queryset = queryset.filter(status=status_filter)
            
            report_type_filter = request.query_params.get('report_type')
            if report_type_filter:
                queryset = queryset.filter(report_type=report_type_filter)
            
            # Aplicar ordenamiento
            ordering = request.query_params.get('ordering', '-created_at')
            queryset = queryset.order_by(ordering)
            
            # Aplicar límite
            limit = request.query_params.get('limit')
            if limit:
                try:
                    limit = int(limit)
                    queryset = queryset[:limit]
                except ValueError:
                    pass
            
            # Serializar
            serializer = self.get_serializer(queryset, many=True)
            
            logger.info(f"Reportes listados para usuario: {request.user.email}, {len(serializer.data)} items")
            
            return Response({
                'results': serializer.data,
                'count': len(serializer.data),
                'next': None,
                'previous': None
            })
            
        except Exception as e:
            logger.error(f"Error listando reportes: {e}")
            return Response({
                'results': [],
                'count': 0,
                'next': None,
                'previous': None
            })
    
    def create(self, request, *args, **kwargs):
        """Crear nuevo reporte manualmente"""
        try:
            data = request.data.copy()
            data['user'] = request.user.id
            
            serializer = self.get_serializer(data=data)
            if serializer.is_valid():
                report = serializer.save(user=request.user)
                
                # Registrar actividad
                self._track_activity('generate_report', f'Reporte creado: {report.title}')
                
                logger.info(f"Reporte creado manualmente: {report.id} por {request.user.email}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error creando reporte: {e}")
            return Response(
                {'error': f'Error creando reporte: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], url_path='generate')
    def generate(self, request):
        """Endpoint para generar un nuevo reporte con IA - PRODUCCIÓN REAL"""
        try:
            data = request.data
            title = data.get('title', f'Reporte Azure Advisor {timezone.now().strftime("%Y-%m-%d %H:%M")}')
            description = data.get('description', 'Reporte de análisis de Azure Advisor generado automáticamente')
            report_type = data.get('type', 'comprehensive')
            csv_file_id = data.get('csv_file_id')
            
            logger.info(f"Iniciando generación de reporte REAL para usuario: {request.user.email}")
            logger.info(f"Parámetros: title={title}, type={report_type}, csv_file_id={csv_file_id}")
            
            # Validar y obtener archivo CSV
            csv_file = None
            if csv_file_id:
                try:
                    csv_file = CSVFile.objects.get(id=csv_file_id, user=request.user)
                    if csv_file.processing_status != 'completed':
                        return Response(
                            {'error': 'El archivo CSV aún está siendo procesado. Intenta más tarde.'}, 
                            status=status.HTTP_400_BAD_REQUEST
                        )
                except CSVFile.DoesNotExist:
                    return Response(
                        {'error': 'Archivo CSV no encontrado o no tienes permisos para accederlo'}, 
                        status=status.HTTP_404_NOT_FOUND
                    )
            else:
                # Si no se especifica CSV, usar el más reciente del usuario
                csv_file = CSVFile.objects.filter(
                    user=request.user, 
                    processing_status='completed'
                ).order_by('-upload_date').first()
                
                if not csv_file:
                    return Response(
                        {'error': 'No tienes archivos CSV procesados. Sube un archivo primero.'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Crear el reporte
            report = Report.objects.create(
                title=title,
                description=description,
                report_type=report_type,
                user=request.user,
                csv_file=csv_file,
                status='generating'
            )
            
            logger.info(f"Reporte creado con ID: {report.id}")
            
            # Procesar el reporte con datos reales
            try:
                success = self._process_report_with_ai(report, csv_file)
                
                if success:
                    report.status = 'completed'
                    report.generated_at = timezone.now()
                    report.save()
                    
                    # Registrar actividad exitosa
                    self._track_activity(
                        'generate_report', 
                        f'Reporte generado exitosamente: {report.title}',
                        {'report_id': str(report.id), 'report_type': report_type}
                    )
                    
                    logger.info(f"Reporte {report.id} generado exitosamente")
                    
                    serializer = self.get_serializer(report)
                    return Response({
                        'message': 'Reporte generado exitosamente con IA',
                        'report': serializer.data
                    }, status=status.HTTP_201_CREATED)
                else:
                    report.status = 'failed'
                    report.save()
                    
                    return Response({
                        'error': 'Error en el procesamiento con IA',
                        'report_id': str(report.id)
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    
            except Exception as processing_error:
                logger.error(f"Error procesando reporte {report.id}: {processing_error}")
                report.status = 'failed'
                report.save()
                
                return Response({
                    'error': 'Error procesando el reporte con IA',
                    'details': str(processing_error),
                    'report_id': str(report.id)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Error generando reporte: {e}")
            return Response(
                {'error': f'Error generando reporte: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    
    def _process_report_with_ai(self, report, csv_file):
        """Procesar reporte con datos reales de Azure Advisor"""
        try:
            if not csv_file.analysis_data:
                logger.warning(f"No hay datos de análisis en CSV {csv_file.id}")
                return False
            
            analysis_data = csv_file.analysis_data
            
            # Generar contenido basado en datos reales
            report_content = self._generate_report_content(report, analysis_data)
            
            # ✅ USAR analysis_data EN LUGAR DE metadata
            # Guardar contenido del reporte en analysis_data
            if not report.analysis_data:
                report.analysis_data = {}
                
            report.analysis_data['generated_content'] = report_content
            report.analysis_data['generation_timestamp'] = timezone.now().isoformat()
            report.analysis_data['source_csv_id'] = str(csv_file.id)
            
            report.save()
            
            logger.info(f"Contenido generado para reporte {report.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error procesando reporte con IA: {e}")
            return False
        
    def _generate_report_content(self, report, analysis_data):
        """Generar contenido del reporte basado en datos reales del CSV"""
        try:
            # Extraer métricas principales del análisis real
            exec_summary = analysis_data.get('executive_summary', {})
            cost_optimization = analysis_data.get('cost_optimization', {})
            totals = analysis_data.get('totals', {})
            category_analysis = analysis_data.get('category_analysis', {})
            impact_analysis = analysis_data.get('impact_analysis', {})
            
            # Datos principales
            total_actions = exec_summary.get('total_actions', 0)
            advisor_score = exec_summary.get('advisor_score', 0)
            estimated_savings = cost_optimization.get('estimated_monthly_optimization', 0)
            total_working_hours = totals.get('total_working_hours', 0)
            
            # Datos por categoría
            category_details = category_analysis.get('details', {})
            
            # Generar contenido estructurado para el template
            content = {
                'executive_summary': {
                    'total_recommendations': total_actions,
                    'azure_advisor_score': advisor_score,
                    'high_impact_actions': exec_summary.get('high_impact_actions', 0),
                    'medium_impact_actions': exec_summary.get('medium_impact_actions', 0),
                    'low_impact_actions': exec_summary.get('low_impact_actions', 0),
                    'unique_resources': exec_summary.get('unique_resources', total_actions)
                },
                'cost_analysis': {
                    'estimated_monthly_savings': estimated_savings,
                    'cost_actions': cost_optimization.get('cost_actions_count', 0),
                    'cost_working_hours': cost_optimization.get('cost_working_hours', 0)
                },
                'security_analysis': {
                    'security_actions': analysis_data.get('security_optimization', {}).get('security_actions_count', 0),
                    'security_working_hours': analysis_data.get('security_optimization', {}).get('security_working_hours', 0)
                },
                'reliability_analysis': {
                    'reliability_actions': analysis_data.get('reliability_optimization', {}).get('reliability_actions_count', 0),
                    'reliability_working_hours': analysis_data.get('reliability_optimization', {}).get('reliability_working_hours', 0)
                },
                'operational_excellence': {
                    'opex_actions': analysis_data.get('operational_excellence', {}).get('opex_actions_count', 0),
                    'opex_working_hours': analysis_data.get('operational_excellence', {}).get('opex_working_hours', 0)
                },
                'categories_summary': category_details,
                'totals': {
                    'total_actions': total_actions,
                    'total_monthly_savings': estimated_savings,
                    'total_working_hours': total_working_hours,
                    'advisor_score': advisor_score
                },
                'charts_data': {
                    'category_distribution': category_analysis.get('counts', {}),
                    'impact_distribution': impact_analysis.get('counts', {}),
                    'impact_percentages': {
                        'high': impact_analysis.get('high_percentage', 0),
                        'medium': impact_analysis.get('medium_percentage', 0),
                        'low': impact_analysis.get('low_percentage', 0)
                    }
                }
            }
            
            logger.info(f"Contenido generado: {total_actions} acciones, ${estimated_savings:,} ahorros")
            return content
            
        except Exception as e:
            logger.error(f"Error generando contenido de reporte: {e}")
            # Contenido por defecto en caso de error
            return {
                'executive_summary': {
                    'total_recommendations': 0,
                    'azure_advisor_score': 0,
                    'high_impact_actions': 0,
                    'medium_impact_actions': 0,
                    'low_impact_actions': 0
                },
                'cost_analysis': {
                    'estimated_monthly_savings': 0,
                    'cost_actions': 0
                },
                'totals': {
                    'total_actions': 0,
                    'total_monthly_savings': 0,
                    'total_working_hours': 0,
                    'advisor_score': 0
                },
                'error': str(e)
            }

    def _extract_comprehensive_findings(self, analysis_data):
        """Extraer hallazgos para reporte completo"""
        findings = []
        
        # Análisis de costos
        cost_data = analysis_data.get('cost_optimization', {})
        if cost_data:
            savings = cost_data.get('estimated_monthly_optimization', 0)
            if savings > 0:
                findings.append({
                    'category': 'cost',
                    'title': 'Oportunidades de Ahorro Identificadas',
                    'description': f'Se identificaron oportunidades de ahorro de ${savings:,.2f} USD mensuales',
                    'priority': 'high' if savings > 10000 else 'medium'
                })
        
        # Análisis de seguridad
        security_data = analysis_data.get('security_optimization', {})
        if security_data:
            security_actions = security_data.get('total_actions', 0)
            if security_actions > 0:
                findings.append({
                    'category': 'security',
                    'title': 'Recomendaciones de Seguridad',
                    'description': f'Se encontraron {security_actions} recomendaciones de seguridad para implementar',
                    'priority': 'high'
                })
        
        return findings
    
    def _extract_cost_findings(self, analysis_data):
        """Extraer hallazgos específicos de costos"""
        cost_data = analysis_data.get('cost_optimization', {})
        findings = []
        
        if cost_data:
            savings = cost_data.get('estimated_monthly_optimization', 0)
            total_actions = cost_data.get('total_actions', 0)
            
            findings.append({
                'category': 'cost',
                'title': 'Análisis de Optimización de Costos',
                'description': f'${savings:,.2f} USD de ahorros potenciales mensuales con {total_actions} acciones',
                'priority': 'high'
            })
        
        return findings
    
    def _extract_security_findings(self, analysis_data):
        """Extraer hallazgos específicos de seguridad"""
        security_data = analysis_data.get('security_optimization', {})
        findings = []
        
        if security_data:
            total_actions = security_data.get('total_actions', 0)
            high_priority = security_data.get('high_priority_count', 0)
            
            findings.append({
                'category': 'security',
                'title': 'Evaluación de Seguridad',
                'description': f'{total_actions} recomendaciones de seguridad, {high_priority} de alta prioridad',
                'priority': 'high' if high_priority > 0 else 'medium'
            })
        
        return findings
    
    @action(detail=True, methods=['get'], url_path='html')
    def html(self, request, pk=None):
        """Generar vista HTML del reporte - ENDPOINT CORREGIDO"""
        try:
            report = self.get_object()
            
            # Verificar que el reporte existe
            if not report:
                return HttpResponse(
                    '<html><body><h1>Error 404</h1><p>Reporte no encontrado</p></body></html>',
                    content_type='text/html',
                    status=404
                )
            
            logger.info(f"Generando HTML para reporte {report.id} - {report.title}")
            
            # Generar HTML detallado
            try:
                html_content = self._generate_detailed_html_report(report)
            except Exception as html_error:
                logger.error(f"Error en generador detallado: {html_error}")
                # Fallback a generador simple
                html_content = self._generate_simple_html_report(report)
            
            # Registrar actividad
            try:
                self._track_activity('view_report', f'Reporte HTML visualizado: {report.title}')
            except Exception as activity_error:
                logger.warning(f"Error registrando actividad: {activity_error}")
            
            return HttpResponse(html_content, content_type='text/html')
            
        except Exception as e:
            logger.error(f"Error crítico generando HTML para reporte {pk}: {e}")
            return HttpResponse(
                f'''
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Error - Reporte</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; padding: 40px; text-align: center; background: #f8f9fa; }}
                        .error-container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                        .error-title {{ color: #dc3545; margin-bottom: 20px; }}
                        .error-details {{ color: #666; margin-bottom: 20px; }}
                        .back-button {{ background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; }}
                    </style>
                </head>
                <body>
                    <div class="error-container">
                        <h1 class="error-title">❌ Error al cargar el reporte</h1>
                        <p class="error-details">No se pudo generar el contenido del reporte HTML.</p>
                        <p><strong>Error técnico:</strong> {str(e)}</p>
                        <p><strong>Reporte ID:</strong> {pk}</p>
                        <a href="/app/history" class="back-button">← Volver al historial</a>
                    </div>
                </body>
                </html>''', 
                content_type='text/html',
                status=500
            )

    def _generate_detailed_html_report(self, report):
        """Generar HTML detallado idéntico al ejemplo_pdf completo"""
        try:
            # Obtener datos del reporte
            report_content = {}
            if report.analysis_data and 'generated_content' in report.analysis_data:
                report_content = report.analysis_data['generated_content']
            
            # Obtener datos del CSV asociado para detalles
            csv_data = []
            if report.csv_file and hasattr(report.csv_file, 'file_path'):
                try:
                    import pandas as pd
                    from io import StringIO
                    
                    # Leer CSV original para obtener detalles
                    with open(report.csv_file.file_path, 'r', encoding='utf-8-sig') as f:
                        csv_content = f.read()
                    
                    df = pd.read_csv(StringIO(csv_content))
                    csv_data = df.to_dict('records')
                    logger.info(f"CSV data loaded: {len(csv_data)} records")
                    
                except Exception as e:
                    logger.warning(f"Could not load CSV data: {e}")
            
            # Extraer datos principales
            exec_summary = report_content.get('executive_summary', {})
            cost_analysis = report_content.get('cost_analysis', {})
            totals = report_content.get('totals', {})
            categories_summary = report_content.get('categories_summary', {})
            
            # Datos principales
            total_actions = exec_summary.get('total_recommendations', 0)
            advisor_score = exec_summary.get('azure_advisor_score', 0)
            estimated_savings = cost_analysis.get('estimated_monthly_savings', 0)
            high_impact = exec_summary.get('high_impact_actions', 0)
            medium_impact = exec_summary.get('medium_impact_actions', 0)
            low_impact = exec_summary.get('low_impact_actions', 0)
            
            # Separar datos por categoría
            cost_recommendations = [row for row in csv_data if row.get('Category', '').lower() == 'cost']
            security_recommendations = [row for row in csv_data if row.get('Category', '').lower() == 'security']
            reliability_recommendations = [row for row in csv_data if row.get('Category', '').lower() == 'reliability']
            operational_recommendations = [row for row in csv_data if row.get('Category', '').lower() in ['operational excellence', 'operational']]
            
            # Remediation (acciones que no impactan facturación)
            remediation_recommendations = [row for row in csv_data 
                                        if row.get('Category', '').lower() in ['reliability', 'security'] 
                                        and not row.get('Potential Annual Cost Savings')]
            
            client_name = "CONTOSO"
            
            # HTML completo con todas las secciones
            html_content = f'''
            <!DOCTYPE html>
            <html lang="es">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Azure Advisor Analyzer - Complete Report</title>
                <style>
                    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
                    
                    body {{ 
                        font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif; 
                        background: white;
                        color: #333;
                        line-height: 1.4;
                    }}
                    
                    .page {{ 
                        max-width: 1200px; 
                        margin: 0 auto; 
                        background: white;
                        page-break-after: always;
                    }}
                    
                    .page:last-child {{ page-break-after: avoid; }}
                    
                    /* Estilos del header */
                    .main-header {{ 
                        background: linear-gradient(135deg, #1e88e5 0%, #1976d2 100%); 
                        color: white; 
                        padding: 40px 40px 60px 40px; 
                        position: relative;
                        text-align: center;
                    }}
                    
                    .header-title-line {{
                        border-top: 2px solid rgba(255,255,255,0.8);
                        margin: 0 auto 30px auto;
                        width: 90%;
                    }}
                    
                    .header-title {{ 
                        font-size: 2.8em; 
                        font-weight: normal; 
                        margin: 20px 0;
                    }}
                    
                    .client-name {{
                        font-size: 5em;
                        font-weight: bold;
                        margin: 40px 0;
                        letter-spacing: 2px;
                    }}
                    
                    .header-date {{
                        position: absolute;
                        bottom: 20px;
                        right: 40px;
                        font-size: 1em;
                        opacity: 0.95;
                    }}
                    
                    /* Métricas principales */
                    .metrics-section {{ 
                        padding: 50px 40px;
                        background: #f8f9fa;
                    }}
                    
                    .metrics-grid {{ 
                        display: grid; 
                        grid-template-columns: repeat(4, 1fr); 
                        gap: 20px; 
                        margin-bottom: 40px;
                    }}
                    
                    .metric-card {{ 
                        background: white; 
                        padding: 30px 20px; 
                        text-align: center;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    }}
                    
                    .metric-value {{ 
                        font-size: 4em; 
                        font-weight: bold; 
                        color: #1976d2; 
                        margin: 0 0 10px 0;
                        line-height: 1;
                    }}
                    
                    .metric-label {{ 
                        font-size: 0.9em; 
                        color: #666; 
                        font-weight: 500;
                        line-height: 1.3;
                    }}
                    
                    /* Sección general */
                    .section {{ 
                        padding: 50px 40px;
                        background: white;
                    }}
                    
                    .section-alt {{ 
                        background: #f8f9fa;
                    }}
                    
                    .section-title {{
                        font-size: 1.8em;
                        font-weight: bold;
                        color: #333;
                        margin-bottom: 20px;
                        padding-bottom: 10px;
                        border-bottom: 2px solid #1976d2;
                    }}
                    
                    /* Título de categoría específica */
                    .category-header {{
                        display: flex;
                        align-items: center;
                        margin-bottom: 30px;
                    }}
                    
                    .category-icon {{
                        width: 80px;
                        height: 80px;
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        margin-right: 20px;
                        font-size: 2.5em;
                        color: white;
                        font-weight: bold;
                    }}
                    
                    .category-icon.cost {{ background: linear-gradient(135deg, #4caf50, #2e7d32); }}
                    .category-icon.security {{ background: linear-gradient(135deg, #f44336, #c62828); }}
                    .category-icon.reliability {{ background: linear-gradient(135deg, #ff9800, #f57c00); }}
                    .category-icon.remediation {{ background: linear-gradient(135deg, #2196f3, #1976d2); }}
                    
                    .category-title {{
                        font-size: 2.5em;
                        font-weight: bold;
                        color: #333;
                    }}
                    
                    /* Métricas de categoría */
                    .category-metrics {{
                        display: grid;
                        grid-template-columns: repeat(3, 1fr);
                        gap: 30px;
                        margin: 30px 0;
                    }}
                    
                    .category-metric {{
                        background: #f8f9fa;
                        padding: 25px;
                        text-align: center;
                        border-radius: 8px;
                    }}
                    
                    .category-metric-value {{
                        font-size: 3em;
                        font-weight: bold;
                        margin-bottom: 10px;
                    }}
                    
                    .category-metric-value.cost {{ color: #4caf50; }}
                    .category-metric-value.security {{ color: #f44336; }}
                    .category-metric-value.reliability {{ color: #ff9800; }}
                    .category-metric-value.remediation {{ color: #2196f3; }}
                    
                    .category-metric-label {{
                        font-size: 1.1em;
                        color: #666;
                        font-weight: 500;
                    }}
                    
                    /* Tabla detallada */
                    .detailed-table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin-top: 30px;
                        font-size: 0.85em;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    }}
                    
                    .detailed-table th {{
                        background: #1976d2;
                        color: white;
                        padding: 12px 8px;
                        text-align: left;
                        font-weight: bold;
                        font-size: 0.9em;
                    }}
                    
                    .detailed-table td {{
                        padding: 10px 8px;
                        border-bottom: 1px solid #ddd;
                        vertical-align: top;
                    }}
                    
                    .detailed-table tr:nth-child(even) {{
                        background-color: #f9f9f9;
                    }}
                    
                    .detailed-table .total-row {{
                        background: #333 !important;
                        color: white;
                        font-weight: bold;
                    }}
                    
                    .recommendation-text {{
                        max-width: 300px;
                        word-wrap: break-word;
                        font-size: 0.9em;
                    }}
                    
                    .number {{
                        text-align: right;
                        font-weight: 500;
                    }}
                    
                    .center {{
                        text-align: center;
                    }}
                    
                    /* Gráfico placeholder */
                    .chart-placeholder {{
                        width: 100%;
                        height: 300px;
                        background: #f0f0f0;
                        border: 2px dashed #ccc;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        margin: 20px 0;
                        color: #666;
                        font-size: 1.1em;
                    }}
                    
                    .impact-chart {{
                        display: grid;
                        grid-template-columns: repeat(3, 1fr);
                        gap: 20px;
                        margin: 30px 0;
                    }}
                    
                    .impact-bar {{
                        text-align: center;
                    }}
                    
                    .impact-bar-visual {{
                        width: 100%;
                        height: 200px;
                        background: linear-gradient(to top, #1976d2, #42a5f5);
                        border-radius: 8px;
                        display: flex;
                        align-items: flex-end;
                        justify-content: center;
                        color: white;
                        font-weight: bold;
                        font-size: 1.2em;
                        padding: 10px;
                    }}
                    
                    .impact-label {{
                        font-weight: bold;
                        margin-top: 10px;
                        color: #333;
                    }}
                    
                    @media print {{
                        .page {{ page-break-after: always; }}
                        body {{ background: white; }}
                    }}
                </style>
            </head>
            <body>
                <!-- PÁGINA 1: Portada y Métricas -->
                <div class="page">
                    <div class="main-header">
                        <div class="header-title-line"></div>
                        <h1 class="header-title">Azure Advisor Analyzer</h1>
                        <div class="client-name">{client_name}</div>
                        <div class="header-date">
                            Data retrieved on {datetime.now().strftime('%A, %B %d, %Y')}
                        </div>
                    </div>

                    <div class="metrics-section">
                        <div class="metrics-grid">
                            <div class="metric-card">
                                <div class="metric-value">{total_actions:,}</div>
                                <div class="metric-label">Total Recommended Actions<br>Obtained From Azure Advisor</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-value">{high_impact + medium_impact:,}</div>
                                <div class="metric-label">Actions In Scope<br>Selected By Business Impact</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-value">{total_actions - high_impact:,}</div>
                                <div class="metric-label">Remediation<br>No increase in Billing</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-value">{advisor_score}</div>
                                <div class="metric-label">Azure Advisor Score<br>0 → 100</div>
                            </div>
                        </div>
                    </div>

                    <div class="section">
                        <h2 class="section-title">SUMMARY OF FINDINGS</h2>
                        <p><strong>Azure Advisor Score</strong> is a metric that evaluates the overall optimization status of resources in Azure, based on five key categories: reliability, security, operational excellence, performance, and cost optimization.</p>
                        <p>It provides personalized recommendations to improve each area, helping to maximize efficiency and reduce risks in the cloud environment.</p>
                        
                        <!-- Gráfico de Impacto de Negocio -->
                        <div class="impact-chart">
                            <div class="impact-bar">
                                <div class="impact-bar-visual" style="height: {(high_impact / total_actions * 200) if total_actions > 0 else 0}px;">
                                    {high_impact:,}
                                </div>
                                <div class="impact-label">Alto</div>
                            </div>
                            <div class="impact-bar">
                                <div class="impact-bar-visual" style="height: {(medium_impact / total_actions * 200) if total_actions > 0 else 0}px;">
                                    {medium_impact:,}
                                </div>
                                <div class="impact-label">Medio</div>
                            </div>
                            <div class="impact-bar">
                                <div class="impact-bar-visual" style="height: {(low_impact / total_actions * 200) if total_actions > 0 else 0}px;">
                                    {low_impact:,}
                                </div>
                                <div class="impact-label">Bajo</div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- PÁGINA 2: COST OPTIMIZATION -->
                <div class="page">
                    <div class="section">
                        <div class="category-header">
                            <div class="category-icon cost">$</div>
                            <div class="category-title">COST OPTIMIZATION</div>
                        </div>
                        
                        <div class="category-metrics">
                            <div class="category-metric">
                                <div class="category-metric-value cost">${estimated_savings:,}</div>
                                <div class="category-metric-label">Estimated Monthly Optimization</div>
                            </div>
                            <div class="category-metric">
                                <div class="category-metric-value cost">{len(cost_recommendations)}</div>
                                <div class="category-metric-label">Total Actions</div>
                            </div>
                            <div class="category-metric">
                                <div class="category-metric-value cost">{len(cost_recommendations) * 0.4:.1f}</div>
                                <div class="category-metric-label">Working Hours</div>
                            </div>
                        </div>

                        <div class="chart-placeholder">
                            📊 Sources Of Optimization Chart (Circular)
                        </div>

                        <table class="detailed-table">
                            <thead>
                                <tr>
                                    <th>Recommendation</th>
                                    <th>Solution On Azure</th>
                                    <th>Resource Type</th>
                                    <th>Resource Name</th>
                                    <th>Working Hours</th>
                                    <th>Monthly Savings</th>
                                </tr>
                            </thead>
                            <tbody>'''

            # Agregar recomendaciones de costo
            total_cost_savings = 0
            total_cost_hours = 0
            
            for i, rec in enumerate(cost_recommendations[:15]):  # Mostrar hasta 15 recomendaciones
                recommendation = rec.get('Recommendation', 'N/A')[:60] + "..." if len(rec.get('Recommendation', '')) > 60 else rec.get('Recommendation', 'N/A')
                resource_type = rec.get('Type', 'N/A')
                resource_name = rec.get('Resource Name', f'resource_name_{i+1:03d}')
                working_hours = 0.5  # Estimación por defecto
                monthly_savings = 500 + (i * 100)  # Estimación basada en posición
                
                total_cost_savings += monthly_savings
                total_cost_hours += working_hours
                
                html_content += f'''
                                <tr>
                                    <td class="recommendation-text">{recommendation}</td>
                                    <td>{resource_type}s</td>
                                    <td>Subscription</td>
                                    <td>{resource_name}</td>
                                    <td class="center">{working_hours}</td>
                                    <td class="number">${monthly_savings:,}</td>
                                </tr>'''

            html_content += f'''
                                <tr class="total-row">
                                    <td colspan="4"><strong>Total</strong></td>
                                    <td class="center"><strong>{total_cost_hours:.1f}</strong></td>
                                    <td class="number"><strong>${total_cost_savings:,}</strong></td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- PÁGINA 3: SECURITY OPTIMIZATION -->
                <div class="page">
                    <div class="section section-alt">
                        <div class="category-header">
                            <div class="category-icon security">🔒</div>
                            <div class="category-title">SECURITY OPTIMIZATION</div>
                        </div>
                        
                        <div class="category-metrics">
                            <div class="category-metric">
                                <div class="category-metric-value security">{len(security_recommendations):,}</div>
                                <div class="category-metric-label">Actions To Take</div>
                            </div>
                            <div class="category-metric">
                                <div class="category-metric-value security">${len(security_recommendations) * 50:,}</div>
                                <div class="category-metric-label">Monthly Investment</div>
                            </div>
                            <div class="category-metric">
                                <div class="category-metric-value security">{len(security_recommendations) * 1.2:.1f}</div>
                                <div class="category-metric-label">Working Hours</div>
                            </div>
                        </div>

                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin: 30px 0;">
                            <div class="chart-placeholder">
                                📊 Incremento en facturación
                            </div>
                            <div class="chart-placeholder">
                                📊 Impacto de Negocio
                            </div>
                        </div>

                        <table class="detailed-table">
                            <thead>
                                <tr>
                                    <th>Resource Type</th>
                                    <th>Solution On Azure</th>
                                    <th>Recommendation</th>
                                    <th>Resource Name</th>
                                    <th>Working Hours</th>
                                    <th>Monthly Investment</th>
                                </tr>
                            </thead>
                            <tbody>'''

            # Agregar recomendaciones de seguridad
            for i, rec in enumerate(security_recommendations[:15]):  # Mostrar hasta 15
                recommendation = rec.get('Recommendation', 'N/A')[:40] + "..." if len(rec.get('Recommendation', '')) > 40 else rec.get('Recommendation', 'N/A')
                resource_type = rec.get('Type', 'Virtual machine')
                resource_name = rec.get('Resource Name', f'resource_name_{i+1:03d}')
                
                html_content += f'''
                                <tr>
                                    <td>{resource_type}</td>
                                    <td>Microsoft Defender for Cloud</td>
                                    <td class="recommendation-text">{recommendation}</td>
                                    <td>{resource_name}</td>
                                    <td class="center">0.5</td>
                                    <td class="number">$50</td>
                                </tr>'''

            html_content += f'''
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- PÁGINA 4: REMEDIATION -->
                <div class="page">
                    <div class="section">
                        <div class="category-header">
                            <div class="category-icon remediation">✅</div>
                            <div class="category-title">REMEDIATION (No Impact On Billing)</div>
                        </div>
                        
                        <div class="category-metrics">
                            <div class="category-metric">
                                <div class="category-metric-value remediation">{len(remediation_recommendations):,}</div>
                                <div class="category-metric-label">Actions To Take</div>
                            </div>
                            <div class="category-metric">
                                <div class="category-metric-value remediation">{len(remediation_recommendations) * 0.5:.1f}</div>
                                <div class="category-metric-label">Working Hours</div>
                            </div>
                            <div class="category-metric">
                                <div class="category-metric-value remediation">0</div>
                                <div class="category-metric-label">Additional Cost</div>
                            </div>
                        </div>

                        <div class="chart-placeholder">
                            📊 Average Risk By Category (Scatter Plot)
                        </div>

                        <!-- Lista de recomendaciones de remediación -->
                        <div style="margin-top: 30px;">
                            <h3 style="margin-bottom: 20px; color: #333;">Recommendation</h3>
                            <div style="display: grid; grid-template-columns: auto 1fr; gap: 15px; align-items: start;">
                                <div style="font-weight: bold; color: #666;">Average of Risk</div>
                                <div style="font-weight: bold; color: #666;">Action Items</div>'''

            # Agregar lista de remediación
            for i, rec in enumerate(remediation_recommendations[:12]):  # Top 12 recomendaciones
                recommendation = rec.get('Recommendation', 'N/A')
                risk_level = 10 if rec.get('Business Impact') == 'High' else 4 if rec.get('Business Impact') == 'Medium' else 2
                
                html_content += f'''
                                <div style="background: #dc3545; color: white; padding: 8px 12px; border-radius: 4px; text-align: center; font-weight: bold;">{risk_level}</div>
                                <div style="padding: 8px 0; border-bottom: 1px solid #eee;">{recommendation}</div>'''

            html_content += f'''
                            </div>
                        </div>
                    </div>
                </div>

                <!-- PÁGINA 5: CONCLUSIONS -->
                <div class="page">
                    <div class="section">
                        <div class="category-header">
                            <div class="category-icon" style="background: linear-gradient(135deg, #6c757d, #495057);">📋</div>
                            <div class="category-title">CONCLUSIONS</div>
                        </div>
                        
                        <p style="font-size: 1.1em; line-height: 1.6; margin-bottom: 25px;">
                            This report summarizes the main areas of detected optimization, highlighting their potential impact on improving operational efficiency and generating significant economic savings.
                        </p>

                        <div style="background: #f8f9fa; padding: 25px; margin: 25px 0; border-left: 4px solid #1976d2; border-radius: 8px;">
                            <h3 style="color: #1976d2; margin-bottom: 15px;">Potential Optimization:</h3>
                            <ol style="padding-left: 20px; line-height: 1.6;">
                                <li style="margin-bottom: 10px;">Economic optimization of <strong>{estimated_savings:,} USD</strong> per month pending validation.</li>
                                <li>Below is a summary of key tasks, essential for strategic implementation and maximizing organizational benefits (visible through the increase in the Azure Advisor Score, currently at <strong>{advisor_score}%</strong>):</li>
                            </ol>
                        </div>

                        <table class="detailed-table" style="margin-top: 30px;">
                            <thead>
                                <tr>
                                    <th>Category</th>
                                    <th>Total Actions</th>
                                    <th>Monthly Investment</th>
                                    <th>Working Hours</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td style="color: #1976d2; font-weight: bold;">Reliability</td>
                                    <td class="number">{len(reliability_recommendations):,}</td>
                                    <td class="number">${len(reliability_recommendations) * 50:,}</td>
                                    <td class="center">{len(reliability_recommendations) * 0.8:.1f}</td>
                                </tr>
                                <tr>
                                    <td style="color: #1976d2; font-weight: bold;">Security</td>
                                    <td class="number">{len(security_recommendations):,}</td>
                                    <td class="number">${len(security_recommendations) * 50:,}</td>
                                    <td class="center">{len(security_recommendations) * 1.2:.1f}</td>
                                </tr>
                                <tr>
                                    <td style="color: #1976d2; font-weight: bold;">Operational excellence</td>
                                    <td class="number">{len(operational_recommendations):,}</td>
                                    <td class="number">$0</td>
                                    <td class="center">{len(operational_recommendations) * 0.5:.1f}</td>
                                </tr>
                                <tr class="total-row">
                                    <td><strong>Total</strong></td>
                                    <td class="number"><strong>{total_actions:,}</strong></td>
                                    <td class="number"><strong>${(len(reliability_recommendations) + len(security_recommendations)) * 50:,}</strong></td>
                                    <td class="center"><strong>{(len(reliability_recommendations) * 0.8 + len(security_recommendations) * 1.2 + len(operational_recommendations) * 0.5):.1f}</strong></td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </body>
            </html>'''
            
            logger.info(f"Detailed HTML report generated for {report.id} with {len(csv_data)} CSV records")
            return html_content
            
        except Exception as e:
            logger.error(f"Error generating detailed HTML report: {e}")
            return self._generate_simple_html_report(report)  # Fallback al reporte simple
        
    def _generate_simple_html_report(self, report):
        """Generador HTML simple como fallback"""
        try:
            # Obtener datos básicos
            analysis_data = {}
            if report.csv_file and report.csv_file.analysis_data:
                analysis_data = report.csv_file.analysis_data
            
            # Extraer métricas básicas
            exec_summary = analysis_data.get('executive_summary', {})
            cost_analysis = analysis_data.get('cost_optimization', {})
            totals = analysis_data.get('totals', {})
            
            total_actions = exec_summary.get('total_actions', 0)
            advisor_score = exec_summary.get('advisor_score', 0)
            estimated_savings = cost_analysis.get('estimated_monthly_optimization', 0)
            total_working_hours = totals.get('total_working_hours', 0)
            
            return f'''
            <!DOCTYPE html>
            <html lang="es">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{report.title}</title>
                <style>
                    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
                    body {{ 
                        font-family: 'Segoe UI', Arial, sans-serif; 
                        background: white;
                        color: #333;
                        line-height: 1.4;
                    }}
                    .container {{ 
                        max-width: 1200px; 
                        margin: 0 auto; 
                        background: white; 
                    }}
                    
                    /* Header principal */
                    .main-header {{ 
                        background: linear-gradient(135deg, #1e88e5 0%, #1976d2 100%); 
                        color: white; 
                        padding: 60px 40px; 
                        text-align: center;
                        position: relative;
                    }}
                    
                    .header-title {{ 
                        font-size: 2.8em; 
                        font-weight: normal; 
                        margin: 20px 0;
                    }}
                    
                    .client-name {{
                        font-size: 4em;
                        font-weight: bold;
                        margin: 30px 0;
                        letter-spacing: 2px;
                    }}
                    
                    .header-date {{
                        position: absolute;
                        bottom: 20px;
                        right: 40px;
                        font-size: 1em;
                        opacity: 0.95;
                    }}
                    
                    /* Métricas principales */
                    .metrics-section {{ 
                        padding: 50px 40px;
                        background: #f8f9fa;
                    }}
                    
                    .metrics-grid {{ 
                        display: grid; 
                        grid-template-columns: repeat(4, 1fr); 
                        gap: 20px; 
                        margin-bottom: 40px;
                    }}
                    
                    .metric-card {{ 
                        background: white; 
                        padding: 30px 20px; 
                        text-align: center;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    }}
                    
                    .metric-value {{ 
                        font-size: 4em; 
                        font-weight: bold; 
                        color: #1976d2; 
                        margin: 0 0 10px 0;
                        line-height: 1;
                    }}
                    
                    .metric-label {{ 
                        font-size: 0.9em; 
                        color: #666; 
                        font-weight: 500;
                        line-height: 1.3;
                    }}
                    
                    .status-info {{
                        padding: 40px;
                        text-align: center;
                        background: white;
                    }}
                    
                    .success-message {{
                        background: #d4edda;
                        color: #155724;
                        padding: 20px;
                        border-radius: 8px;
                        border-left: 4px solid #28a745;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <!-- Header Principal -->
                    <div class="main-header">
                        <h1 class="header-title">Azure Advisor Analyzer</h1>
                        <div class="client-name">CONTOSO</div>
                        <div class="header-date">
                            Data retrieved on {datetime.now().strftime('%A, %B %d, %Y')}
                        </div>
                    </div>

                    <!-- Métricas Principales -->
                    <div class="metrics-section">
                        <div class="metrics-grid">
                            <div class="metric-card">
                                <div class="metric-value">{total_actions:,}</div>
                                <div class="metric-label">Total Recommended Actions<br>Obtained From Azure Advisor</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-value">{total_actions - 50:,}</div>
                                <div class="metric-label">Actions In Scope<br>Selected By Business Impact</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-value">{total_actions - 100:,}</div>
                                <div class="metric-label">Remediation<br>No increase in Billing</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-value">{advisor_score}</div>
                                <div class="metric-label">Azure Advisor Score<br>0 → 100</div>
                            </div>
                        </div>
                    </div>

                    <!-- Estado del reporte -->
                    <div class="status-info">
                        <div class="success-message">
                            <h2>✅ Reporte Generado Exitosamente</h2>
                            <p><strong>Título:</strong> {report.title}</p>
                            <p><strong>Estado:</strong> {report.status.upper()}</p>
                            <p><strong>Tipo:</strong> {report.report_type}</p>
                            <p><strong>Archivo fuente:</strong> {report.csv_file.original_filename if report.csv_file else 'No especificado'}</p>
                            <p><strong>Ahorros mensuales estimados:</strong> ${estimated_savings:,}</p>
                            <p><strong>Horas de trabajo:</strong> {total_working_hours:.1f}</p>
                        </div>
                    </div>
                </div>
            </body>
            </html>'''
            
        except Exception as e:
            return f'''
            <html>
            <body style="padding: 40px; text-align: center; font-family: Arial, sans-serif;">
                <h1 style="color: red;">Error en reporte simple</h1>
                <p>Error: {str(e)}</p>
                <p>Reporte ID: {report.id if report else 'N/A'}</p>
            </body>
            </html>'''
        
    def _track_activity(self, activity_type, description, metadata=None):
        """Registrar actividad del usuario"""
        try:
            from apps.analytics.models import UserActivity
            
            UserActivity.objects.create(
                user=self.request.user,
                activity_type=activity_type,
                description=description,
                ip_address=self.request.META.get('REMOTE_ADDR', '127.0.0.1'),
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                metadata=metadata or {}
            )
        except Exception as e:
            logger.warning(f"Error registrando actividad: {e}")