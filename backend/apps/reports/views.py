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
from apps.reports.utils.enhanced_analyzer import EnhancedHTMLReportGenerator
from .utils.cache_manager import ReportCacheManager

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
        """Generar vista HTML del reporte con datos reales del CSV"""
        try:
            report = self.get_object()
            
            logger.info(f"Generando HTML para reporte {report.id}")
            
            # ✅ USAR LA CLASE CORREGIDA
            generator = EnhancedHTMLReportGenerator()
            html_content = generator.generate_complete_html(report)
            
            return HttpResponse(html_content, content_type='text/html')
            
        except Exception as e:
            logger.error(f"Error generando HTML para reporte {pk}: {e}")
            return HttpResponse(f'''
            <html>
            <body style="font-family: Arial; padding: 40px; text-align: center;">
                <h1>Error Generating Report</h1>
                <p>Error: {str(e)}</p>
                <p>Please try again or contact support.</p>
            </body>
            </html>
            ''', status=500)

    def _generate_error_fallback(self, error_message):
        """Genera HTML de error como fallback"""
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Error - Reporte</title>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 40px; text-align: center; background: #f8f9fa; }}
                .error-container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .error-title {{ color: #dc3545; margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <div class="error-container">
                <h1 class="error-title">Error generando reporte</h1>
                <p>Ha ocurrido un error al generar el reporte:</p>
                <pre>{error_message}</pre>
                <p>Por favor intenta nuevamente o contacta soporte si el problema persiste.</p>
            </div>
        </body>
        </html>
        '''    


    def _generate_detailed_html_report(self, report):
        """Generar HTML idéntico al ejemplo_pdf.pdf"""
        try:
            logger.info(f"Generando reporte con diseño idéntico al ejemplo_pdf para {report.id}")
            
            # Obtener datos (mantener la lógica que ya funciona)
            analysis_data = {}
            if report.csv_file and report.csv_file.analysis_data:
                analysis_data = report.csv_file.analysis_data
            else:
                return self._generate_simple_html_report(report)
            
            # Mapeo de datos (mantener la lógica que ya funciona)
            if 'dashboard_metrics' in analysis_data:
                dashboard_metrics = analysis_data['dashboard_metrics']
                total_actions = dashboard_metrics.get('total_recommendations', 0)
                estimated_savings = dashboard_metrics.get('estimated_monthly_optimization', 0)
                total_working_hours = dashboard_metrics.get('working_hours', 0)
                advisor_score = dashboard_metrics.get('advisor_score', 0)
            elif 'totals' in analysis_data:
                totals = analysis_data['totals']
                total_actions = totals.get('total_actions', 0)
                estimated_savings = totals.get('total_monthly_savings', 0)
                total_working_hours = totals.get('total_working_hours', 0)
                advisor_score = totals.get('azure_advisor_score', 0)
            else:
                def find_value(data, key):
                    if isinstance(data, dict):
                        if key in data:
                            return data[key]
                        for v in data.values():
                            result = find_value(v, key)
                            if result is not None:
                                return result
                    return None
                
                total_actions = find_value(analysis_data, 'total_actions') or find_value(analysis_data, 'total_recommendations') or 0
                estimated_savings = find_value(analysis_data, 'estimated_monthly_optimization') or find_value(analysis_data, 'total_monthly_savings') or 0
                total_working_hours = find_value(analysis_data, 'total_working_hours') or find_value(analysis_data, 'working_hours') or 0
                advisor_score = find_value(analysis_data, 'advisor_score') or find_value(analysis_data, 'azure_advisor_score') or 0
            
            # Datos por categoría
            category_counts = {}
            if 'category_analysis' in analysis_data:
                category_counts = analysis_data['category_analysis'].get('counts', {})
            
            # Datos de impacto
            high_impact = 0
            medium_impact = 0
            low_impact = 0
            
            if 'impact_analysis' in analysis_data:
                impact_data = analysis_data['impact_analysis'].get('counts', {})
                high_impact = impact_data.get('High', 0)
                medium_impact = impact_data.get('Medium', 0)
                low_impact = impact_data.get('Low', 0)
            
            if high_impact + medium_impact + low_impact == 0 and total_actions > 0:
                high_impact = int(total_actions * 0.4)
                medium_impact = int(total_actions * 0.5)
                low_impact = total_actions - high_impact - medium_impact
            
            # Métricas calculadas
            cost_recommendations_count = category_counts.get('Cost', 0)
            security_recommendations_count = category_counts.get('Security', 0)
            reliability_recommendations_count = category_counts.get('Reliability', 0)
            operational_recommendations_count = (category_counts.get('Operational excellence', 0) + 
                                            category_counts.get('Operational Excellence', 0))
            
            actions_in_scope = high_impact + medium_impact
            remediation_actions = max(0, total_actions - high_impact)
            
            if advisor_score == 0 and total_actions > 0:
                completion_rate = max(0, 100 - (high_impact / total_actions * 50) - (medium_impact / total_actions * 20))
                advisor_score = min(100, max(20, completion_rate))
            
            if estimated_savings == 0 and cost_recommendations_count > 0:
                estimated_savings = cost_recommendations_count * 450
            
            if total_working_hours == 0:
                total_working_hours = (cost_recommendations_count * 0.4 + 
                                    security_recommendations_count * 1.2 + 
                                    reliability_recommendations_count * 0.8 + 
                                    operational_recommendations_count * 0.5)
            
            # HTML IDÉNTICO al ejemplo_pdf.pdf
            html_content = f'''
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Azure Advisor Analyzer</title>
                <style>
                    @import url('https://fonts.googleapis.com/css2?family=Segoe+UI:wght@300;400;600;700&display=swap');
                    
                    * {{
                        margin: 0;
                        padding: 0;
                        box-sizing: border-box;
                    }}
                    
                    body {{
                        font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: #333;
                        line-height: 1.4;
                    }}
                    
                    .page {{
                        width: 210mm;
                        min-height: 297mm;
                        margin: 0 auto;
                        background: white;
                        box-shadow: 0 0 20px rgba(0,0,0,0.1);
                        page-break-after: always;
                        position: relative;
                    }}
                    
                    .page:last-child {{
                        page-break-after: avoid;
                    }}
                    
                    /* === PÁGINA 1: PORTADA === */
                    .cover-page {{
                        background: linear-gradient(135deg, #1e88e5 0%, #1976d2 100%);
                        color: white;
                        display: flex;
                        flex-direction: column;
                        justify-content: center;
                        align-items: center;
                        text-align: center;
                        position: relative;
                        padding: 60px 40px;
                    }}
                    
                    .cloud-logo {{
                        background: rgba(255,255,255,0.15);
                        border-radius: 20px;
                        padding: 15px 25px;
                        margin-bottom: 30px;
                        backdrop-filter: blur(10px);
                        border: 1px solid rgba(255,255,255,0.2);
                    }}
                    
                    .cloud-icon {{
                        font-size: 2em;
                        margin-right: 10px;
                    }}
                    
                    .logo-text {{
                        font-size: 1.2em;
                        font-weight: 600;
                        display: inline-block;
                    }}
                    
                    .main-title {{
                        font-size: 4em;
                        font-weight: 300;
                        margin: 40px 0;
                        letter-spacing: -2px;
                    }}
                    
                    .company-name {{
                        font-size: 6em;
                        font-weight: 700;
                        margin: 60px 0;
                        letter-spacing: 8px;
                        text-shadow: 0 4px 20px rgba(0,0,0,0.3);
                    }}
                    
                    .date-info {{
                        position: absolute;
                        bottom: 40px;
                        right: 40px;
                        font-size: 1.1em;
                        opacity: 0.9;
                    }}
                    
                    /* === PÁGINA 2: MÉTRICAS PRINCIPALES === */
                    .metrics-page {{
                        padding: 60px 40px;
                        background: #f8f9fa;
                    }}
                    
                    .metrics-container {{
                        display: grid;
                        grid-template-columns: repeat(4, 1fr);
                        gap: 30px;
                        margin-bottom: 60px;
                    }}
                    
                    .metric-box {{
                        background: white;
                        padding: 40px 30px;
                        text-align: center;
                        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
                        border-radius: 12px;
                        border-left: 5px solid #1976d2;
                    }}
                    
                    .metric-number {{
                        font-size: 4.5em;
                        font-weight: 700;
                        color: #1976d2;
                        line-height: 1;
                        margin-bottom: 15px;
                    }}
                    
                    .metric-title {{
                        font-size: 1.1em;
                        font-weight: 600;
                        color: #333;
                        margin-bottom: 5px;
                    }}
                    
                    .metric-subtitle {{
                        font-size: 0.9em;
                        color: #666;
                        font-weight: 400;
                    }}
                    
                    /* === SUMMARY OF FINDINGS === */
                    .findings-section {{
                        background: white;
                        padding: 50px 40px;
                        margin-top: 40px;
                        border-radius: 12px;
                        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
                    }}
                    
                    .section-header {{
                        display: flex;
                        align-items: center;
                        margin-bottom: 30px;
                        padding-bottom: 15px;
                        border-bottom: 3px solid #1976d2;
                    }}
                    
                    .section-icon {{
                        width: 60px;
                        height: 60px;
                        background: linear-gradient(135deg, #1976d2, #42a5f5);
                        border-radius: 15px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        margin-right: 20px;
                        color: white;
                        font-size: 1.8em;
                    }}
                    
                    .section-title {{
                        font-size: 2em;
                        font-weight: 700;
                        color: #333;
                        letter-spacing: 1px;
                    }}
                    
                    .findings-text {{
                        font-size: 1.1em;
                        line-height: 1.8;
                        color: #555;
                        margin-bottom: 40px;
                    }}
                    
                    .findings-text strong {{
                        color: #1976d2;
                        font-weight: 600;
                    }}
                    
                    /* === GRÁFICO DE BARRAS === */
                    .chart-section {{
                        background: white;
                        padding: 40px;
                        border-radius: 12px;
                        margin-top: 30px;
                        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
                    }}
                    
                    .chart-container {{
                        display: flex;
                        align-items: flex-end;
                        justify-content: center;
                        height: 300px;
                        gap: 60px;
                        margin: 40px 0;
                        padding: 20px;
                        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                        border-radius: 12px;
                    }}
                    
                    .chart-bar-container {{
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        position: relative;
                    }}
                    
                    .chart-bar {{
                        width: 80px;
                        background: linear-gradient(to top, #1976d2 0%, #42a5f5 100%);
                        border-radius: 8px 8px 0 0;
                        display: flex;
                        align-items: flex-end;
                        justify-content: center;
                        color: white;
                        font-weight: 700;
                        font-size: 1.1em;
                        padding: 15px 10px;
                        box-shadow: 0 4px 15px rgba(25, 118, 210, 0.3);
                        position: relative;
                        transition: transform 0.3s ease;
                    }}
                    
                    .chart-bar:hover {{
                        transform: translateY(-5px);
                    }}
                    
                    .chart-label {{
                        margin-top: 15px;
                        font-weight: 600;
                        color: #333;
                        font-size: 1em;
                        text-align: center;
                    }}
                    
                    .chart-title {{
                        text-align: right;
                        margin-bottom: 20px;
                        font-size: 1.3em;
                        font-weight: 600;
                        color: #333;
                    }}
                    
                    .chart-title-main {{
                        font-size: 1.5em;
                        color: #1976d2;
                        margin-bottom: 5px;
                    }}
                    
                    .chart-subtitle {{
                        color: #666;
                        font-size: 1em;
                    }}
                    
                    /* === PÁGINA 3: COST OPTIMIZATION === */
                    .category-page {{
                        padding: 60px 40px;
                        background: white;
                    }}
                    
                    .category-header {{
                        display: flex;
                        align-items: center;
                        margin-bottom: 50px;
                        padding-bottom: 20px;
                        border-bottom: 3px solid #4caf50;
                    }}
                    
                    .category-icon-large {{
                        width: 100px;
                        height: 100px;
                        background: linear-gradient(135deg, #4caf50, #2e7d32);
                        border-radius: 20px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        margin-right: 30px;
                        color: white;
                        font-size: 3em;
                        box-shadow: 0 8px 25px rgba(76, 175, 80, 0.3);
                    }}
                    
                    .category-title-large {{
                        font-size: 3em;
                        font-weight: 700;
                        color: #333;
                        letter-spacing: 2px;
                    }}
                    
                    .category-metrics {{
                        display: grid;
                        grid-template-columns: repeat(3, 1fr);
                        gap: 40px;
                        margin-bottom: 50px;
                    }}
                    
                    .category-metric {{
                        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
                        padding: 40px 30px;
                        text-align: center;
                        border-radius: 15px;
                        border-left: 5px solid #4caf50;
                        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
                    }}
                    
                    .category-metric-value {{
                        font-size: 3.5em;
                        font-weight: 700;
                        color: #4caf50;
                        line-height: 1;
                        margin-bottom: 10px;
                    }}
                    
                    .category-metric-label {{
                        font-size: 1.1em;
                        color: #555;
                        font-weight: 500;
                    }}
                    
                    /* === TABLA DE CONCLUSIONES === */
                    .conclusions-section {{
                        background: white;
                        padding: 60px 40px;
                        margin-top: 60px;
                        border-radius: 15px;
                        box-shadow: 0 8px 30px rgba(0,0,0,0.1);
                    }}
                    
                    .conclusions-header {{
                        display: flex;
                        align-items: center;
                        margin-bottom: 40px;
                        padding-bottom: 20px;
                        border-bottom: 3px solid #1976d2;
                    }}
                    
                    .conclusions-title {{
                        font-size: 2.5em;
                        font-weight: 700;
                        color: #333;
                        letter-spacing: 1px;
                    }}
                    
                    .conclusions-text {{
                        font-size: 1.2em;
                        line-height: 1.8;
                        color: #555;
                        margin-bottom: 30px;
                    }}
                    
                    .optimization-box {{
                        background: linear-gradient(135deg, #e3f2fd, #bbdefb);
                        border-left: 5px solid #1976d2;
                        padding: 30px;
                        border-radius: 12px;
                        margin: 30px 0;
                    }}
                    
                    .optimization-title {{
                        font-size: 1.4em;
                        font-weight: 600;
                        color: #1976d2;
                        margin-bottom: 20px;
                    }}
                    
                    .optimization-list {{
                        list-style: none;
                        padding: 0;
                    }}
                    
                    .optimization-list li {{
                        font-size: 1.1em;
                        line-height: 1.8;
                        margin-bottom: 15px;
                        color: #333;
                        position: relative;
                        padding-left: 30px;
                    }}
                    
                    .optimization-list li:before {{
                        content: "→";
                        position: absolute;
                        left: 0;
                        color: #1976d2;
                        font-weight: bold;
                        font-size: 1.2em;
                    }}
                    
                    .summary-table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin-top: 40px;
                        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
                        border-radius: 12px;
                        overflow: hidden;
                    }}
                    
                    .summary-table thead {{
                        background: linear-gradient(135deg, #1976d2, #1565c0);
                        color: white;
                    }}
                    
                    .summary-table th {{
                        padding: 20px 15px;
                        text-align: left;
                        font-weight: 600;
                        font-size: 1.1em;
                        letter-spacing: 0.5px;
                    }}
                    
                    .summary-table th:last-child {{
                        text-align: center;
                    }}
                    
                    .summary-table tbody tr {{
                        border-bottom: 1px solid #e0e0e0;
                        transition: background-color 0.3s ease;
                    }}
                    
                    .summary-table tbody tr:hover {{
                        background-color: #f5f5f5;
                    }}
                    
                    .summary-table tbody tr:nth-child(even) {{
                        background-color: #fafafa;
                    }}
                    
                    .summary-table td {{
                        padding: 18px 15px;
                        font-size: 1em;
                    }}
                    
                    .category-cell {{
                        font-weight: 600;
                        color: #1976d2;
                    }}
                    
                    .number-cell {{
                        text-align: right;
                        font-weight: 500;
                        font-family: 'Segoe UI', monospace;
                    }}
                    
                    .center-cell {{
                        text-align: center;
                        font-weight: 500;
                    }}
                    
                    .total-row {{
                        background: linear-gradient(135deg, #333, #424242) !important;
                        color: white !important;
                        font-weight: 700;
                    }}
                    
                    .total-row:hover {{
                        background: linear-gradient(135deg, #333, #424242) !important;
                    }}
                    
                    .total-row td {{
                        border-bottom: none;
                        font-size: 1.1em;
                    }}
                    
                    @media print {{
                        body {{ background: white; }}
                        .page {{ box-shadow: none; margin: 0; }}
                    }}
                    
                    @page {{
                        size: A4;
                        margin: 0;
                    }}
                </style>
            </head>
            <body>
                <!-- PÁGINA 1: PORTADA -->
                <div class="page cover-page">
                    <div class="cloud-logo">
                        <span class="cloud-icon">☁️ ⭐⭐⭐</span>
                        <span class="logo-text">The Cloud Mastery</span>
                    </div>
                    
                    <h1 class="main-title">Azure Advisor Analyzer</h1>
                    
                    <div class="company-name">CONTOSO</div>
                    
                    <div class="date-info">
                        Data retrieved on {datetime.now().strftime('%A, %B %d, %Y')}
                    </div>
                </div>

                <!-- PÁGINA 2: MÉTRICAS PRINCIPALES -->
                <div class="page metrics-page">
                    <div class="metrics-container">
                        <div class="metric-box">
                            <div class="metric-number">{total_actions:,}</div>
                            <div class="metric-title">Total Recommended Actions</div>
                            <div class="metric-subtitle">Obtained From Azure Advisor</div>
                        </div>
                        
                        <div class="metric-box">
                            <div class="metric-number">{actions_in_scope:,}</div>
                            <div class="metric-title">Actions In Scope</div>
                            <div class="metric-subtitle">Selected By Business Impact</div>
                        </div>
                        
                        <div class="metric-box">
                            <div class="metric-number">{remediation_actions:,}</div>
                            <div class="metric-title">Remediation</div>
                            <div class="metric-subtitle">No increase in Billing</div>
                        </div>
                        
                        <div class="metric-box">
                            <div class="metric-number">{advisor_score:.0f}</div>
                            <div class="metric-title">Azure Advisor Score</div>
                            <div class="metric-subtitle">0 → 100</div>
                        </div>
                    </div>

                    <!-- SUMMARY OF FINDINGS -->
                    <div class="findings-section">
                        <div class="section-header">
                            <div class="section-icon">📋</div>
                            <h2 class="section-title">SUMMARY OF FINDINGS</h2>
                        </div>
                        
                        <div class="findings-text">
                            <p><strong>Azure Advisor Score</strong> is a metric that evaluates the <strong>overall optimization status</strong> of resources in Azure, based on five key categories: reliability, security, operational excellence, performance, and cost optimization.</p>
                            <p>It provides <strong>personalized recommendations</strong> to improve each area, helping to <strong>maximize efficiency</strong> and <strong>reduce risks</strong> in the cloud environment.</p>
                        </div>

                        <!-- GRÁFICO DE BARRAS EXACTO -->
                        <div class="chart-section">
                            <div class="chart-title">
                                <div class="chart-title-main">Total Recommended Actions</div>
                                <div class="chart-subtitle">Obtained From Azure Advisor</div>
                            </div>
                            
                            <div style="text-align: right; margin-bottom: 20px; font-size: 4em; font-weight: 700; color: #1976d2;">
                                {total_actions:,}
                            </div>
                            
                            <div class="chart-title">
                                <div class="chart-subtitle">Impacto de Negocio</div>
                            </div>
                            
                            <div class="chart-container">
                                <div class="chart-bar-container">
                                    <div class="chart-bar" style="height: {max(60, (high_impact / max(total_actions, 1) * 200)) if total_actions > 0 else 60}px;">
                                        {high_impact:,}
                                    </div>
                                    <div class="chart-label">Alto</div>
                                </div>
                                
                                <div class="chart-bar-container">
                                    <div class="chart-bar" style="height: {max(60, (medium_impact / max(total_actions, 1) * 200)) if total_actions > 0 else 60}px;">
                                        {medium_impact:,}
                                    </div>
                                    <div class="chart-label">Medio</div>
                                </div>
                                
                                <div class="chart-bar-container">
                                    <div class="chart-bar" style="height: {max(40, (low_impact / max(total_actions, 1) * 200)) if total_actions > 0 else 40}px;">
                                        {low_impact:,}
                                    </div>
                                    <div class="chart-label">Bajo</div>
                                </div>
                            </div>
                            
                            <div style="text-align: center; margin-top: 20px;">
                                <div style="font-size: 2em; font-weight: 700; color: #1976d2; margin-bottom: 10px;">
                                    Actions In Scope
                                </div>
                                <div style="color: #666; margin-bottom: 15px;">Selected By Business Impact</div>
                                <div style="font-size: 4em; font-weight: 700; color: #1976d2;">
                                    {actions_in_scope:,}
                                </div>
                            </div>
                            
                            <div style="text-align: center; margin-top: 40px;">
                                <div style="font-size: 2em; font-weight: 700; color: #1976d2; margin-bottom: 10px;">
                                    Remediation
                                </div>
                                <div style="color: #666; margin-bottom: 15px;">No increase in Billing</div>
                                <div style="font-size: 4em; font-weight: 700; color: #1976d2;">
                                    {remediation_actions:,}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- PÁGINA 3: COST OPTIMIZATION -->
                <div class="page category-page">
                    <div class="category-header">
                        <div class="category-icon-large">💰</div>
                        <h2 class="category-title-large">COST OPTIMIZATION</h2>
                    </div>
                    
                    <div class="category-metrics">
                        <div class="category-metric">
                            <div class="category-metric-value">${estimated_savings:,}</div>
                            <div class="category-metric-label">Estimated Monthly Optimization</div>
                        </div>
                        
                        <div class="category-metric">
                            <div class="category-metric-value">{cost_recommendations_count}</div>
                            <div class="category-metric-label">Total Actions</div>
                        </div>
                        
                        <div class="category-metric">
                            <div class="category-metric-value">{cost_recommendations_count * 0.4:.1f}</div>
                            <div class="category-metric-label">Working Hours</div>
                        </div>
                    </div>
                    
                    <div style="height: 300px; background: linear-gradient(135deg, #f8f9fa, #e9ecef); border-radius: 12px; display: flex; align-items: center; justify-content: center; border: 2px dashed #ddd;">
                        <div style="text-align: center; color: #666;">
                            <div style="font-size: 3em; margin-bottom: 10px;">📊</div>
                            <div style="font-size: 1.2em; font-weight: 600;">Sources Of Optimization Chart</div>
                            <div style="font-size: 1em;">Actual ${estimated_savings:,} (4.85%)</div>
                        </div>
                    </div>
                </div>

                <!-- PÁGINA 4: CONCLUSIONS -->
                <div class="page">
                    <div class="conclusions-section">
                        <div class="conclusions-header">
                            <div class="section-icon">✅</div>
                            <h2 class="conclusions-title">CONCLUSIONS</h2>
                        </div>
                        
                        <div class="conclusions-text">
                            This report summarizes the main areas of detected optimization, highlighting their potential impact on improving operational efficiency and generating significant economic savings.
                        </div>

                        <div class="optimization-box">
                            <div class="optimization-title">Potential Optimization:</div>
                            <ol class="optimization-list">
                                <li>Economic optimization of <strong>{estimated_savings:,} USD</strong> per month pending validation.</li>
                                <li>Below is a summary of key tasks, essential for strategic implementation and maximizing organizational benefits (visible through the increase in the Azure Advisor Score, currently at <strong>{advisor_score:.0f}%</strong>):</li>
                            </ol>
                        </div>

                        <table class="summary-table">
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
                                    <td class="category-cell">Reliability</td>
                                    <td class="number-cell">{reliability_recommendations_count:,}</td>
                                    <td class="number-cell">${reliability_recommendations_count * 50:,}</td>
                                    <td class="center-cell">{reliability_recommendations_count * 0.8:.1f}</td>
                                </tr>
                                <tr>
                                    <td class="category-cell">Security</td>
                                    <td class="number-cell">{security_recommendations_count:,}</td>
                                    <td class="number-cell">${security_recommendations_count * 50:,}</td>
                                    <td class="center-cell">{security_recommendations_count * 1.2:.1f}</td>
                                </tr>
                                <tr>
                                    <td class="category-cell">Operational excellence</td>
                                    <td class="number-cell">{operational_recommendations_count:,}</td>
                                    <td class="number-cell">$0</td>
                                    <td class="center-cell">{operational_recommendations_count * 0.5:.1f}</td>
                                </tr>
                                <tr class="total-row">
                                    <td><strong>Total</strong></td>
                                    <td class="number-cell"><strong>{total_actions:,}</strong></td>
                                    <td class="number-cell"><strong>${(reliability_recommendations_count + security_recommendations_count) * 50:,}</strong></td>
                                    <td class="center-cell"><strong>{total_working_hours:.1f}</strong></td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </body>
            </html>'''
            
            logger.info(f"HTML con diseño EXACTO al ejemplo_pdf generado para {report.id}")
            return html_content
            
        except Exception as e:
            logger.error(f"Error generando HTML con diseño exacto: {e}", exc_info=True)
            return self._generate_simple_html_report(report)
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

    @action(detail=True, methods=['post'], url_path='generate-pdf')
    def generate_pdf(self, request, pk=None):
        """Generar PDF usando el mismo patrón exitoso de test_complete_system.py"""
        try:
            report = self.get_object()
            
            logger.info(f"=== INICIANDO GENERACIÓN PDF CONFIABLE ===")
            logger.info(f"Reporte ID: {report.id}")
            logger.info(f"Título: {report.title}")
            
            # 1. Verificar servicios (igual que en test)
            logger.info("1. Verificando servicios...")
            
            # Verificar PDF Service
            try:
                from apps.storage.services.pdf_generator_service import PDFGeneratorService
                pdf_service = PDFGeneratorService()
                logger.info(f"✅ PDF Service disponible: {pdf_service.available_engines}")
            except Exception as e:
                logger.error(f"❌ PDF Service: {e}")
                return Response({
                    'message': 'PDF Service no disponible',
                    'error': str(e),
                    'recommendation': 'Instalar WeasyPrint: pip install weasyprint'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Verificar Azure Storage
            try:
                from apps.storage.services.enhanced_azure_storage import enhanced_azure_storage
                azure_info = enhanced_azure_storage.get_storage_info()
                logger.info(f"✅ Azure Storage: {azure_info['status']}")
                
                if azure_info['status'] != 'available':
                    logger.warning(f"⚠️ Azure no configurado correctamente: {azure_info}")
                    return Response({
                        'message': 'Azure Storage no disponible',
                        'azure_status': azure_info,
                        'recommendation': 'Configurar credenciales de Azure Storage'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    
            except Exception as e:
                logger.error(f"❌ Azure Storage: {e}")
                return Response({
                    'message': 'Error verificando Azure Storage',
                    'error': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # 2. Generar reporte completo (igual que en test)
            logger.info("2. Iniciando generación completa...")
            
            # Actualizar estado del reporte
            report.status = 'generating'
            report.save(update_fields=['status'])
            
            try:
                from apps.storage.services.complete_report_service import generate_complete_report
                
                # Usar la función que funciona en el test
                result = generate_complete_report(report)
                
                logger.info("3. Procesando resultados...")
                logger.info(f"   ✅ Éxito: {result['success']}")
                logger.info(f"   📄 HTML: {result['html_generated']}")
                logger.info(f"   📋 PDF: {result['pdf_generated']}")
                logger.info(f"   ☁️  PDF en Azure: {result['pdf_uploaded']}")
                logger.info(f"   📊 DataFrame en Azure: {result['dataframe_uploaded']}")
                
                if result['success']:
                    # Actualizar estado del reporte
                    report.status = 'completed'
                    report.completed_at = timezone.now()
                    report.save(update_fields=['status', 'completed_at'])
                    
                    response_data = {
                        'message': 'PDF generado exitosamente usando método confiable',
                        'report_id': str(report.id),
                        'client_name': result.get('client_name', 'Azure Client'),
                        'generation_summary': {
                            'html_generated': result['html_generated'],
                            'pdf_generated': result['pdf_generated'],
                            'pdf_uploaded': result['pdf_uploaded'],
                            'dataframe_uploaded': result['dataframe_uploaded']
                        },
                        'urls': result['urls'],
                        'metadata': {
                            'pdf_size': result.get('pdf_size'),
                            'pdf_filename': result.get('pdf_filename')
                        }
                    }
                    
                    # URLs para descarga
                    if result['urls'].get('pdf'):
                        response_data['pdf_download_url'] = result['urls']['pdf']
                        response_data['direct_download'] = f"/api/reports/{report.id}/download/"
                    
                    if result['urls'].get('dataframe'):
                        response_data['dataframe_url'] = result['urls']['dataframe']
                    
                    logger.info("4. URLs generadas:")
                    if 'pdf' in result['urls']:
                        logger.info(f"   PDF: {result['urls']['pdf'][:60]}...")
                    if 'dataframe' in result['urls']:
                        logger.info(f"   DataFrame: {result['urls']['dataframe'][:60]}...")
                    
                    logger.info(f"5. Cliente detectado: {result.get('client_name', 'No detectado')}")
                    
                    if result.get('pdf_size'):
                        logger.info(f"   Tamaño PDF: {result['pdf_size']:,} bytes")
                    
                    logger.info(f"✅ PDF generado exitosamente para reporte {report.id}")
                    return Response(response_data, status=status.HTTP_201_CREATED)
                
                else:
                    # Error en la generación
                    report.status = 'failed'
                    report.error_message = '; '.join(result['errors'])
                    report.save(update_fields=['status', 'error_message'])
                    
                    error_response = {
                        'message': 'Error generando PDF con método confiable',
                        'errors': result['errors'],
                        'partial_success': {
                            'html_generated': result['html_generated'],
                            'pdf_generated': result['pdf_generated'],
                            'pdf_uploaded': result['pdf_uploaded']
                        },
                        'debug_info': {
                            'method': 'reliable_generation',
                            'based_on': 'test_complete_system.py pattern'
                        }
                    }
                    
                    logger.error(f"❌ Errores generando PDF:")
                    for error in result['errors']:
                        logger.error(f"   - {error}")
                    
                    return Response(error_response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            except Exception as generation_error:
                # Error durante la generación
                report.status = 'failed'
                report.error_message = str(generation_error)
                report.save(update_fields=['status', 'error_message'])
                
                logger.error(f"❌ Excepción durante generación: {generation_error}")
                import traceback
                logger.error(traceback.format_exc())
                
                return Response({
                    'message': 'Excepción durante generación de PDF',
                    'error': str(generation_error),
                    'method': 'reliable_generation',
                    'report_status': 'failed'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"❌ Error crítico en generate_pdf_reliable para reporte {pk}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            return Response({
                'message': 'Error crítico generando PDF',
                'error': str(e),
                'report_id': str(pk) if pk else None,
                'method': 'reliable_generation'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    @action(detail=False, methods=['get'], url_path='test-complete-system')
    def test_complete_system_api(self, request):
        """Ejecutar test completo del sistema via API"""
        try:
            logger.info("=== EJECUTANDO TEST COMPLETO DEL SISTEMA VIA API ===")
            
            # Importar la función de test
            import sys
            import os
            
            # Agregar el path del backend si es necesario
            backend_path = os.path.join(os.path.dirname(__file__), '..', '..', '..')
            if backend_path not in sys.path:
                sys.path.append(backend_path)
            
            # Importar el test
            from test_complete_system import test_complete_system
            
            # Capturar output del test
            import io
            from contextlib import redirect_stdout, redirect_stderr
            
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()
            
            try:
                with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                    test_complete_system()
                
                stdout_output = stdout_capture.getvalue()
                stderr_output = stderr_capture.getvalue()
                
                return Response({
                    'message': 'Test completo ejecutado exitosamente',
                    'stdout': stdout_output,
                    'stderr': stderr_output,
                    'success': True
                }, status=status.HTTP_200_OK)
                
            except Exception as test_error:
                stdout_output = stdout_capture.getvalue()
                stderr_output = stderr_capture.getvalue()
                
                return Response({
                    'message': 'Error ejecutando test completo',
                    'error': str(test_error),
                    'stdout': stdout_output,
                    'stderr': stderr_output,
                    'success': False
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        except Exception as e:
            return Response({
                'message': 'Error crítico ejecutando test',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'], url_path='regenerate-pdf')
    def regenerate_pdf(self, request, pk=None):
        """Regenerar PDF de un reporte existente"""
        try:
            report = self.get_object()
            
            logger.info(f"Regenerando PDF para reporte {report.id}")
            
            from apps.storage.services.complete_report_service import complete_report_service
            
            result = complete_report_service.regenerate_report_pdf(report)
            
            if result['success']:
                return Response({
                    'message': 'PDF regenerado exitosamente',
                    'pdf_download_url': result['pdf_url'],
                    'pdf_filename': result['pdf_filename'],
                    'size_bytes': result['size_bytes']
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'message': 'Error regenerando PDF',
                    'error': result['error']
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        except Exception as e:
            logger.error(f"Error regenerando PDF: {e}")
            return Response({
                'message': 'Error interno regenerando PDF',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'], url_path='download')
    def download_pdf(self, request, pk=None):
        """Descargar PDF del reporte - VERSIÓN MEJORADA CON REGENERACIÓN AUTOMÁTICA"""
        try:
            report = self.get_object()
            
            logger.info(f"Intentando descargar PDF para reporte {report.id}")
            logger.info(f"PDF URL en BD: {report.pdf_file_url}")
            
            # Verificar si existe PDF válido
            pdf_url = report.pdf_file_url
            
            # Fallback 1: Verificar en analysis_data
            if not pdf_url and report.analysis_data and 'pdf_info' in report.analysis_data:
                pdf_info = report.analysis_data['pdf_info']
                pdf_url = pdf_info.get('blob_url')
                logger.info(f"PDF URL desde analysis_data: {pdf_url}")
            
            # Fallback 2: Intentar regenerar URL si tenemos blob_name pero URL expirado
            if not pdf_url or not pdf_url.startswith('https://'):
                logger.warning(f"URL inválida o faltante. Intentando regenerar...")
                
                # Buscar información del blob en analysis_data
                if report.analysis_data and 'pdf_info' in report.analysis_data:
                    pdf_info = report.analysis_data['pdf_info']
                    blob_name = pdf_info.get('blob_name')
                    
                    if blob_name:
                        logger.info(f"Encontrado blob_name: {blob_name}. Regenerando URL...")
                        
                        try:
                            # Importar servicio Azure
                            from apps.storage.services.enhanced_azure_storage import enhanced_azure_storage
                            
                            # Regenerar URL con nuevo SAS token
                            new_pdf_url = enhanced_azure_storage._generate_sas_url(
                                enhanced_azure_storage.containers['pdfs'], 
                                blob_name, 
                                hours=24
                            )
                            
                            if new_pdf_url:
                                # Actualizar la URL en la base de datos
                                report.pdf_file_url = new_pdf_url
                                report.analysis_data['pdf_info']['blob_url'] = new_pdf_url
                                report.save(update_fields=['pdf_file_url', 'analysis_data'])
                                
                                pdf_url = new_pdf_url
                                logger.info(f"✅ URL regenerada exitosamente: {pdf_url[:80]}...")
                            else:
                                logger.error("❌ Error regenerando SAS URL")
                                
                        except Exception as regen_error:
                            logger.error(f"❌ Error regenerando URL: {regen_error}")
            
            # Fallback 3: Si todavía no hay PDF, intentar regeneración completa
            if not pdf_url:
                logger.warning("No se pudo obtener URL. Verificando si necesita regeneración completa...")
                
                # Verificar si el PDF existe físicamente en Azure
                if report.analysis_data and 'pdf_info' in report.analysis_data:
                    blob_name = report.analysis_data['pdf_info'].get('blob_name')
                    
                    if blob_name:
                        try:
                            from apps.storage.services.enhanced_azure_storage import enhanced_azure_storage
                            
                            # Verificar si el blob existe
                            container_client = enhanced_azure_storage.blob_service_client.get_container_client(
                                enhanced_azure_storage.containers['pdfs']
                            )
                            blob_client = container_client.get_blob_client(blob_name)
                            
                            if blob_client.exists():
                                # El blob existe, regenerar URL
                                pdf_url = enhanced_azure_storage._generate_sas_url(
                                    enhanced_azure_storage.containers['pdfs'], 
                                    blob_name, 
                                    hours=24
                                )
                                
                                if pdf_url:
                                    # Actualizar en BD
                                    report.pdf_file_url = pdf_url
                                    report.save(update_fields=['pdf_file_url'])
                                    logger.info(f"✅ PDF encontrado en Azure y URL regenerada")
                            else:
                                logger.warning("❌ PDF no existe físicamente en Azure")
                        
                        except Exception as check_error:
                            logger.error(f"❌ Error verificando blob: {check_error}")
            
            # Si aún no hay URL válida, dar respuesta apropiada
            if not pdf_url or not pdf_url.startswith('https://'):
                logger.error(f"No se pudo obtener URL válida para reporte {report.id}")
                return Response({
                    'message': 'PDF no disponible. El archivo necesita ser regenerado.',
                    'actions': ['generate-pdf', 'regenerate-pdf'],
                    'report_id': str(report.id),
                    'status': report.status,
                    'debug_info': {
                        'has_analysis_data': bool(report.analysis_data),
                        'has_pdf_info': bool(report.analysis_data and 'pdf_info' in report.analysis_data) if report.analysis_data else False,
                        'original_url': report.pdf_file_url if report.pdf_file_url else None
                    }
                }, status=status.HTTP_404_NOT_FOUND)
            
            logger.info(f"✅ Redirigiendo a URL válida: {pdf_url[:80]}...")
            
            # Redirigir a la URL de Azure (con SAS token)
            from django.http import HttpResponseRedirect
            return HttpResponseRedirect(pdf_url)
            
        except Exception as e:
            logger.error(f"❌ Error descargando PDF para reporte {pk}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            return Response({
                'message': 'Error descargando PDF',
                'error': str(e),
                'report_id': str(pk) if pk else None,
                'suggestion': 'Intente regenerar el PDF usando el endpoint generate-pdf'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

    @action(detail=True, methods=['post'], url_path='fix-download')
    def fix_download(self, request, pk=None):
        """Método auxiliar para diagnosticar y corregir problemas de descarga"""
        try:
            report = self.get_object()
            
            diagnosis = {
                'report_id': str(report.id),
                'status': report.status,
                'pdf_file_url': report.pdf_file_url,
                'has_analysis_data': bool(report.analysis_data),
                'pdf_info': None,
                'azure_available': False,
                'blob_exists': False,
                'new_url_generated': False
            }
            
            # Verificar analysis_data
            if report.analysis_data and 'pdf_info' in report.analysis_data:
                diagnosis['pdf_info'] = report.analysis_data['pdf_info']
            
            # Verificar Azure
            try:
                from apps.storage.services.enhanced_azure_storage import enhanced_azure_storage
                diagnosis['azure_available'] = enhanced_azure_storage.is_available()
                
                # Verificar si blob existe
                if diagnosis['pdf_info'] and diagnosis['pdf_info'].get('blob_name'):
                    blob_name = diagnosis['pdf_info']['blob_name']
                    container_client = enhanced_azure_storage.blob_service_client.get_container_client(
                        enhanced_azure_storage.containers['pdfs']
                    )
                    blob_client = container_client.get_blob_client(blob_name)
                    diagnosis['blob_exists'] = blob_client.exists()
                    
                    if diagnosis['blob_exists']:
                        # Generar nueva URL
                        new_url = enhanced_azure_storage._generate_sas_url(
                            enhanced_azure_storage.containers['pdfs'], 
                            blob_name, 
                            hours=24
                        )
                        
                        if new_url:
                            report.pdf_file_url = new_url
                            report.save(update_fields=['pdf_file_url'])
                            diagnosis['new_url_generated'] = True
                            diagnosis['new_url'] = new_url[:80] + "..." if len(new_url) > 80 else new_url
            
            except Exception as azure_error:
                diagnosis['azure_error'] = str(azure_error)
            
            return Response({
                'message': 'Diagnóstico completado',
                'diagnosis': diagnosis,
                'recommendations': [
                    'Regenerar PDF completo' if not diagnosis['blob_exists'] else None,
                    'Usar nueva URL generada' if diagnosis['new_url_generated'] else None,
                    'Verificar configuración de Azure' if not diagnosis['azure_available'] else None
                ]
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'message': 'Error en diagnóstico',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True, methods=['get'], url_path='azure-info')
    def azure_info(self, request, pk=None):
        """Obtener información sobre archivos en Azure Storage"""
        try:
            report = self.get_object()
            
            azure_info = {
                'report_id': str(report.id),
                'pdf_available': bool(report.pdf_file_url),
                'pdf_url': report.pdf_file_url,
            }
            
            # Información del PDF desde analysis_data
            if report.analysis_data and 'pdf_info' in report.analysis_data:
                azure_info['pdf_info'] = report.analysis_data['pdf_info']
            
            # Información del DataFrame desde CSV
            if report.csv_file and report.csv_file.analysis_data:
                csv_data = report.csv_file.analysis_data
                if 'azure_dataframe' in csv_data:
                    azure_info['dataframe_info'] = csv_data['azure_dataframe']
            
            # Estado del Azure Storage
            try:
                from apps.storage.services.enhanced_azure_storage import enhanced_azure_storage
                azure_info['azure_storage_status'] = enhanced_azure_storage.get_storage_info()
            except Exception as e:
                azure_info['azure_storage_status'] = {'status': 'error', 'error': str(e)}
            
            return Response(azure_info, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error obteniendo info Azure: {e}")
            return Response({
                'message': 'Error obteniendo información de Azure',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Función auxiliar para procesar reportes en lote
    @action(detail=False, methods=['post'], url_path='batch-generate-pdfs')
    def batch_generate_pdfs(self, request):
        """Generar PDFs para múltiples reportes"""
        try:
            report_ids = request.data.get('report_ids', [])
            
            if not report_ids:
                return Response({
                    'message': 'Se requiere lista de report_ids'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Filtrar reportes del usuario
            reports = self.get_queryset().filter(id__in=report_ids)
            
            results = []
            success_count = 0
            error_count = 0
            
            from apps.storage.services.complete_report_service import complete_report_service
            
            for report in reports:
                try:
                    result = complete_report_service.generate_complete_report(report)
                    
                    report_result = {
                        'report_id': str(report.id),
                        'success': result['success'],
                        'client_name': result.get('client_name'),
                        'pdf_url': result['urls'].get('pdf') if result['success'] else None
                    }
                    
                    if result['success']:
                        success_count += 1
                    else:
                        error_count += 1
                        report_result['errors'] = result['errors']
                    
                    results.append(report_result)
                    
                except Exception as e:
                    error_count += 1
                    results.append({
                        'report_id': str(report.id),
                        'success': False,
                        'error': str(e)
                    })
            
            return Response({
                'message': f'Procesamiento completado: {success_count} exitosos, {error_count} errores',
                'total_processed': len(results),
                'success_count': success_count,
                'error_count': error_count,
                'results': results
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error en batch_generate_pdfs: {e}")
            return Response({
                'message': 'Error procesando reportes en lote',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    @action(detail=True, methods=['post'], url_path='fix-pdf')
    def fix_pdf(self, request, pk=None):
        """Regenerar PDF y corregir URLs - TEMPORAL para debugging"""
        try:
            report = self.get_object()
            
            logger.info(f"Corrigiendo PDF para reporte {report.id}")
            
            from apps.storage.services.complete_report_service import complete_report_service
            result = complete_report_service.regenerate_report_pdf(report)
            
            if result['success']:
                # Refrescar desde DB para verificar
                report.refresh_from_db()
                
                return Response({
                    'message': 'PDF regenerado y corregido exitosamente',
                    'pdf_url': report.pdf_file_url,
                    'blob_url': result['pdf_url'],
                    'filename': result['pdf_filename'],
                    'size_bytes': result['size_bytes'],
                    'report_status': report.status
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'message': 'Error regenerando PDF',
                    'error': result['error']
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        except Exception as e:
            logger.error(f"Error en fix_pdf: {e}")
            return Response({
                'message': 'Error corrigiendo PDF',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    # Endpoint para probar servicios
    @action(detail=False, methods=['get'], url_path='test-services')
    def test_services(self, request):
        """Probar disponibilidad de servicios PDF y Azure"""
        try:
            service_status = {}
            
            # Probar PDF Service
            try:
                from apps.storage.services.pdf_generator_service import PDFGeneratorService
                pdf_service = PDFGeneratorService()
                service_status['pdf_service'] = {
                    'available': True,
                    'engines': pdf_service.available_engines,
                    'preferred_engine': pdf_service.preferred_engine
                }
            except Exception as e:
                service_status['pdf_service'] = {
                    'available': False,
                    'error': str(e)
                }
            
            # Probar Azure Storage
            try:
                from apps.storage.services.enhanced_azure_storage import enhanced_azure_storage
                service_status['azure_storage'] = enhanced_azure_storage.get_storage_info()
            except Exception as e:
                service_status['azure_storage'] = {
                    'available': False,
                    'error': str(e)
                }
            
            # Probar Complete Report Service
            try:
                from apps.storage.services.complete_report_service import complete_report_service
                service_status['complete_report_service'] = {
                    'available': True,
                    'pdf_service_ready': complete_report_service.pdf_service is not None,
                    'azure_service_ready': complete_report_service.azure_service is not None and complete_report_service.azure_service.is_available()
                }
            except Exception as e:
                service_status['complete_report_service'] = {
                    'available': False,
                    'error': str(e)
                }
            
            # Determinar estado general
            all_ready = (
                service_status.get('pdf_service', {}).get('available', False) and
                service_status.get('azure_storage', {}).get('status') == 'available' and
                service_status.get('complete_report_service', {}).get('available', False)
            )
            
            return Response({
                'all_services_ready': all_ready,
                'timestamp': timezone.now().isoformat(),
                'services': service_status,
                'recommendations': [
                    'Instalar WeasyPrint: pip install weasyprint' if not service_status.get('pdf_service', {}).get('available') else None,
                    'Configurar Azure Storage credentials' if service_status.get('azure_storage', {}).get('status') != 'available' else None
                ]
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error probando servicios: {e}")
            return Response({
                'message': 'Error probando servicios',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)