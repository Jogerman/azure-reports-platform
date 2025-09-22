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
        """Generar vista HTML del reporte - PRODUCCIÓN REAL"""
        try:
            report = self.get_object()
            
            # Generar HTML basado en datos reales
            html_content = self._generate_html_report(report)
            
            # Registrar actividad
            self._track_activity('view_report', f'Reporte HTML visualizado: {report.title}')
            
            return HttpResponse(html_content, content_type='text/html')
            
        except Exception as e:
            logger.error(f"Error generando HTML para reporte {pk}: {e}")
            return HttpResponse(
                f"<html><body><h1>Error</h1><p>Error generando reporte: {str(e)}</p></body></html>", 
                content_type='text/html',
                status=500
            )
    
    def _generate_html_report(self, report):
        """Generar HTML idéntico al ejemplo_pdf"""
        try:
            # Obtener datos del reporte generado
            report_content = {}
            if report.analysis_data and 'generated_content' in report.analysis_data:
                report_content = report.analysis_data['generated_content']
            
            # Obtener datos del CSV asociado (fallback)
            if not report_content and report.csv_file and report.csv_file.analysis_data:
                analysis_data = report.csv_file.analysis_data
                report_content = self._generate_report_content(report, analysis_data)
            
            # Extraer datos principales
            exec_summary = report_content.get('executive_summary', {})
            cost_analysis = report_content.get('cost_analysis', {})
            totals = report_content.get('totals', {})
            charts_data = report_content.get('charts_data', {})
            categories_summary = report_content.get('categories_summary', {})
            
            # Datos principales
            total_actions = exec_summary.get('total_recommendations', 0)
            advisor_score = exec_summary.get('azure_advisor_score', 0)
            estimated_savings = cost_analysis.get('estimated_monthly_savings', 0)
            total_working_hours = totals.get('total_working_hours', 0)
            high_impact = exec_summary.get('high_impact_actions', 0)
            medium_impact = exec_summary.get('medium_impact_actions', 0)
            
            # Calcular métricas como en ejemplo_pdf
            actions_in_scope = high_impact + medium_impact
            remediation_actions = total_actions - high_impact  # Las que no requieren billing
            
            # Información del archivo
            csv_filename = report.csv_file.original_filename if report.csv_file else "archivo.csv"
            client_name = "CONTOSO"
            
            # HTML idéntico al ejemplo_pdf
            html_content = f'''
            <!DOCTYPE html>
            <html lang="es">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Azure Advisor Analyzer - {report.title}</title>
                <style>
                    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
                    
                    body {{ 
                        font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif; 
                        background: white;
                        color: #333;
                        line-height: 1.4;
                    }}
                    
                    .container {{ 
                        max-width: 1200px; 
                        margin: 0 auto; 
                        background: white; 
                    }}
                    
                    /* Header principal - Idéntico al ejemplo_pdf */
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
                        color: white;
                    }}
                    
                    .client-name {{
                        font-size: 5em;
                        font-weight: bold;
                        margin: 40px 0;
                        color: #ffffff;
                        letter-spacing: 2px;
                    }}
                    
                    .header-date {{
                        position: absolute;
                        bottom: 20px;
                        right: 40px;
                        font-size: 1em;
                        opacity: 0.95;
                    }}
                    
                    /* Métricas principales - Layout exacto del ejemplo_pdf */
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
                    
                    .metric-sublabel {{
                        font-size: 0.8em;
                        color: #999;
                        margin-top: 5px;
                    }}
                    
                    /* Summary of findings */
                    .summary-section {{
                        padding: 50px 40px;
                        background: white;
                    }}
                    
                    .section-title {{
                        font-size: 1.4em;
                        font-weight: bold;
                        color: #333;
                        margin-bottom: 20px;
                        padding-bottom: 10px;
                        border-bottom: 2px solid #1976d2;
                    }}
                    
                    .summary-text {{
                        font-size: 1em;
                        line-height: 1.6;
                        color: #555;
                        margin-bottom: 20px;
                    }}
                    
                    /* Hallazgos principales - Exacto al ejemplo_pdf */
                    .findings-section {{
                        padding: 50px 40px;
                        background: #f8f9fa;
                    }}
                    
                    .findings-grid {{
                        display: grid;
                        grid-template-columns: repeat(2, 1fr);
                        gap: 30px;
                        margin-top: 30px;
                    }}
                    
                    .finding-card {{
                        background: white;
                        padding: 25px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                        border-left: 6px solid;
                        position: relative;
                    }}
                    
                    .finding-card.cost {{ border-left-color: #4caf50; }}
                    .finding-card.security {{ border-left-color: #f44336; }}
                    .finding-card.reliability {{ border-left-color: #ff9800; }}
                    .finding-card.operational {{ border-left-color: #9c27b0; }}
                    
                    .finding-icon {{
                        width: 60px;
                        height: 60px;
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        margin-bottom: 15px;
                        font-size: 1.8em;
                        color: white;
                        font-weight: bold;
                    }}
                    
                    .finding-icon.cost {{ background: #4caf50; }}
                    .finding-icon.security {{ background: #f44336; }}
                    .finding-icon.reliability {{ background: #ff9800; }}
                    .finding-icon.operational {{ background: #9c27b0; }}
                    
                    .finding-title {{
                        font-size: 1.1em;
                        font-weight: bold;
                        margin-bottom: 10px;
                        color: #333;
                    }}
                    
                    .finding-description {{
                        color: #666;
                        line-height: 1.5;
                        font-size: 0.95em;
                    }}
                    
                    /* Conclusiones - Tabla exacta al ejemplo_pdf */
                    .conclusions-section {{
                        padding: 50px 40px;
                        background: white;
                    }}
                    
                    .potential-optimization {{
                        background: #f8f9fa;
                        padding: 25px;
                        margin: 25px 0;
                        border-left: 4px solid #1976d2;
                    }}
                    
                    .potential-optimization h3 {{
                        color: #1976d2;
                        font-size: 1.2em;
                        margin-bottom: 15px;
                    }}
                    
                    .potential-optimization ol {{
                        padding-left: 20px;
                    }}
                    
                    .potential-optimization li {{
                        margin-bottom: 8px;
                        line-height: 1.5;
                    }}
                    
                    .conclusions-table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin-top: 25px;
                        font-size: 0.95em;
                    }}
                    
                    .conclusions-table th {{
                        background: #1976d2;
                        color: white;
                        padding: 15px 12px;
                        text-align: left;
                        font-weight: bold;
                    }}
                    
                    .conclusions-table th:last-child {{
                        text-align: center;
                    }}
                    
                    .conclusions-table td {{
                        padding: 12px;
                        border-bottom: 1px solid #ddd;
                    }}
                    
                    .conclusions-table tr:nth-child(even) {{
                        background-color: #f9f9f9;
                    }}
                    
                    .conclusions-table .total-row {{
                        background: #333 !important;
                        color: white;
                        font-weight: bold;
                    }}
                    
                    .category-cost {{ color: #1976d2; font-weight: bold; }}
                    .category-security {{ color: #1976d2; font-weight: bold; }}
                    .category-reliability {{ color: #1976d2; font-weight: bold; }}
                    .category-operational {{ color: #1976d2; font-weight: bold; }}
                    
                    .number {{
                        text-align: right;
                        font-weight: 500;
                    }}
                    
                    .hours {{
                        text-align: center;
                    }}
                    
                    @media (max-width: 768px) {{
                        .metrics-grid {{ grid-template-columns: repeat(2, 1fr); }}
                        .findings-grid {{ grid-template-columns: 1fr; }}
                        .client-name {{ font-size: 3em; }}
                    }}
                    
                    @media print {{
                        .container {{ box-shadow: none; }}
                        body {{ background: white; }}
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <!-- Header Principal - Idéntico al ejemplo_pdf -->
                    <div class="main-header">
                        <div class="header-title-line"></div>
                        <h1 class="header-title">Azure Advisor Analyzer</h1>
                        <div class="client-name">{client_name}</div>
                        <div class="header-date">
                            Data retrieved on {datetime.now().strftime('%A, %B %d, %Y')}
                        </div>
                    </div>

                    <!-- Métricas Principales - Layout exacto -->
                    <div class="metrics-section">
                        <div class="metrics-grid">
                            <div class="metric-card">
                                <div class="metric-value">{total_actions:,}</div>
                                <div class="metric-label">Total Recommended Actions</div>
                                <div class="metric-sublabel">Obtained From Azure Advisor</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-value">{actions_in_scope:,}</div>
                                <div class="metric-label">Actions In Scope</div>
                                <div class="metric-sublabel">Selected By Business Impact</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-value">{remediation_actions:,}</div>
                                <div class="metric-label">Remediation</div>
                                <div class="metric-sublabel">No increase in Billing</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-value">{advisor_score}</div>
                                <div class="metric-label">Azure Advisor Score</div>
                                <div class="metric-sublabel">0 → 100</div>
                            </div>
                        </div>
                    </div>

                    <!-- Summary of Findings -->
                    <div class="summary-section">
                        <h2 class="section-title">SUMMARY OF FINDINGS</h2>
                        <div class="summary-text">
                            <p><strong>Azure Advisor Score</strong> is a metric that evaluates the overall optimization status of resources in Azure, based on five key categories: reliability, security, operational excellence, performance, and cost optimization.</p>
                            <p>It provides personalized recommendations to improve each area, helping to maximize efficiency and reduce risks in the cloud environment.</p>
                        </div>
                    </div>

                    <!-- Hallazgos Principales - Exacto al ejemplo_pdf -->
                    <div class="findings-section">
                        <h2 class="section-title">Hallazgos Principales</h2>
                        <div class="findings-grid">
                            <div class="finding-card cost">
                                <div class="finding-icon cost">$</div>
                                <div class="finding-title">Alta Prioridad - Optimización de Costos</div>
                                <div class="finding-description">
                                    Se identificaron oportunidades significativas de ahorro mediante la implementación de instancias reservadas y el redimensionamiento de recursos infrautilizados. <strong>Ahorro estimado: ${estimated_savings:,} USD mensuales</strong>.
                                </div>
                            </div>
                            
                            <div class="finding-card security">
                                <div class="finding-icon security">🔒</div>
                                <div class="finding-title">Prioridad Media - Seguridad</div>
                                <div class="finding-description">
                                    Varias recomendaciones de seguridad requieren atención para mejorar la postura de seguridad general. <strong>{report_content.get('security_analysis', {}).get('security_actions', 0)} acciones de seguridad</strong> identificadas.
                                </div>
                            </div>

                            <div class="finding-card reliability">
                                <div class="finding-icon reliability">⚡</div>
                                <div class="finding-title">Confiabilidad y Disponibilidad</div>
                                <div class="finding-description">
                                    Recomendaciones para mejorar la resistencia y disponibilidad de los servicios críticos. <strong>{report_content.get('reliability_analysis', {}).get('reliability_actions', 0)} acciones de confiabilidad</strong> identificadas.
                                </div>
                            </div>

                            <div class="finding-card operational">
                                <div class="finding-icon operational">⚙️</div>
                                <div class="finding-title">Excelencia Operacional</div>
                                <div class="finding-description">
                                    Optimización de procesos y eficiencia del sistema para maximizar los beneficios organizacionales. <strong>{report_content.get('operational_excellence', {}).get('opex_actions', 0)} acciones operacionales</strong>.
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Conclusiones - Tabla exacta al ejemplo_pdf -->
                    <div class="conclusions-section">
                        <h2 class="section-title">CONCLUSIONS</h2>
                        <div class="summary-text">
                            <p>This report summarizes the main areas of detected optimization, highlighting their potential impact on improving operational efficiency and generating significant economic savings.</p>
                        </div>

                        <div class="potential-optimization">
                            <h3>Potential Optimization:</h3>
                            <ol>
                                <li>Economic optimization of <strong>${estimated_savings:,} USD</strong> per month pending validation.</li>
                                <li>Below is a summary of key tasks, essential for strategic implementation and maximizing organizational benefits (visible through the increase in the Azure Advisor Score, currently at <strong>{advisor_score}%</strong>):</li>
                            </ol>
                        </div>

                        <table class="conclusions-table">
                            <thead>
                                <tr>
                                    <th>Category</th>
                                    <th>Total Actions</th>
                                    <th>Monthly Investment</th>
                                    <th>Working Hours</th>
                                </tr>
                            </thead>
                            <tbody>'''

            # Agregar filas por categoría - Orden exacto del ejemplo_pdf
            total_actions_sum = 0
            total_investment = 0
            total_hours_sum = 0
            
            # Categorías en el orden exacto del ejemplo_pdf
            category_order = [
                ('Cost', 'Cost Optimization', '#1976d2'),
                ('Security', 'Security', '#1976d2'), 
                ('Reliability', 'Reliability', '#1976d2'),
                ('Operational Excellence', 'Operational excellence', '#1976d2'),
                ('Operational excellence', 'Operational excellence', '#1976d2')
            ]
            
            # Procesar cada categoría
            processed_categories = set()
            for category_key, category_display, color in category_order:
                if category_key in processed_categories:
                    continue
                    
                # Combinar "Operational Excellence" y "Operational excellence" 
                if category_key in ['Operational Excellence', 'Operational excellence']:
                    if 'operational_combined' in processed_categories:
                        continue
                    processed_categories.add('operational_combined')
                    
                    # Sumar ambas variantes
                    opex1 = categories_summary.get('Operational Excellence', {})
                    opex2 = categories_summary.get('Operational excellence', {})
                    
                    actions = opex1.get('count', 0) + opex2.get('count', 0)
                    hours = opex1.get('working_hours', 0) + opex2.get('working_hours', 0)
                    investment = round(hours * 50) if hours > 0 else 0
                    
                    category_display = 'Operational excellence'
                else:
                    processed_categories.add(category_key)
                    details = categories_summary.get(category_key, {})
                    actions = details.get('count', 0)
                    hours = details.get('working_hours', 0)
                    
                    # Calcular inversión según la categoría
                    if category_key == 'Cost':
                        investment = details.get('monthly_savings', 0)  # Para Cost es ahorro
                    else:
                        investment = round(hours * 50) if hours > 0 else 0  # Para otros es inversión
                
                if actions > 0:  # Solo mostrar categorías con acciones
                    total_actions_sum += actions
                    if category_key != 'Cost':  # Solo sumar inversiones, no ahorros
                        total_investment += investment
                    total_hours_sum += hours
                    
                    css_class = f'category-{category_key.lower().replace(" ", "")}'
                    
                    html_content += f'''
                                <tr>
                                    <td class="{css_class}">{category_display}</td>
                                    <td class="number">{actions:,}</td>
                                    <td class="number">${investment:,}</td>
                                    <td class="hours">{hours:.1f}</td>
                                </tr>'''
            
            # Fila total - Exacta al ejemplo_pdf
            html_content += f'''
                                <tr class="total-row">
                                    <td><strong>Total</strong></td>
                                    <td class="number"><strong>{total_actions_sum:,}</strong></td>
                                    <td class="number"><strong>${total_investment:,}</strong></td>
                                    <td class="hours"><strong>{total_hours_sum:.1f}</strong></td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </body>
            </html>'''
            
            logger.info(f"HTML mejorado generado para reporte {report.id}")
            return html_content
            
        except Exception as e:
            logger.error(f"Error generando HTML de reporte: {e}")
            return f'''
            <!DOCTYPE html>
            <html>
            <head><title>Error en el reporte</title></head>
            <body>
                <div style="padding: 40px; text-align: center;">
                    <h1 style="color: #dc3545;">Error generando reporte</h1>
                    <p>Ocurrió un error al generar el contenido del reporte: {str(e)}</p>
                    <p>ID del reporte: {report.id if report else 'N/A'}</p>
                </div>
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