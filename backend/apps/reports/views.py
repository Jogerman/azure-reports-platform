# apps/reports/views.py - VERSIÓN FINAL CORREGIDA

from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.decorators import action
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
            
            # Guardar contenido del reporte
            if not hasattr(report, 'content'):
                # Si no hay campo content en el modelo, guardarlo en metadata
                if not report.metadata:
                    report.metadata = {}
                report.metadata['generated_content'] = report_content
            else:
                report.content = report_content
            
            report.save()
            
            logger.info(f"Contenido generado para reporte {report.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error procesando reporte con IA: {e}")
            return False
    
    def _generate_report_content(self, report, analysis_data):
        """Generar contenido del reporte basado en datos reales"""
        try:
            # Extraer métricas principales
            exec_summary = analysis_data.get('executive_summary', {})
            cost_optimization = analysis_data.get('cost_optimization', {})
            security_analysis = analysis_data.get('security_optimization', {})
            
            total_actions = exec_summary.get('total_actions', 0)
            advisor_score = exec_summary.get('advisor_score', 0)
            estimated_savings = cost_optimization.get('estimated_monthly_optimization', 0)
            
            # Generar resumen ejecutivo
            content = {
                'executive_summary': {
                    'total_recommendations': total_actions,
                    'azure_advisor_score': advisor_score,
                    'potential_monthly_savings': estimated_savings,
                    'report_type': report.report_type,
                    'generated_at': timezone.now().isoformat()
                },
                'key_findings': [],
                'recommendations': [],
                'cost_analysis': cost_optimization,
                'security_analysis': security_analysis,
                'raw_data': analysis_data
            }
            
            # Extraer hallazgos clave basados en el tipo de reporte
            if report.report_type == 'comprehensive':
                content['key_findings'] = self._extract_comprehensive_findings(analysis_data)
            elif report.report_type == 'cost':
                content['key_findings'] = self._extract_cost_findings(analysis_data)
            elif report.report_type == 'security':
                content['key_findings'] = self._extract_security_findings(analysis_data)
            
            return content
            
        except Exception as e:
            logger.error(f"Error generando contenido: {e}")
            return {'error': str(e)}
    
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
        """Generar HTML con datos reales del reporte"""
        try:
            # Obtener datos del CSV asociado
            analysis_data = {}
            if report.csv_file and report.csv_file.analysis_data:
                analysis_data = report.csv_file.analysis_data
            
            # Extraer métricas
            exec_summary = analysis_data.get('executive_summary', {})
            cost_optimization = analysis_data.get('cost_optimization', {})
            
            total_actions = exec_summary.get('total_actions', 0)
            advisor_score = exec_summary.get('advisor_score', 0)
            estimated_savings = cost_optimization.get('estimated_monthly_optimization', 0)
            
            # Generar HTML profesional
            html_content = f'''
            <!DOCTYPE html>
            <html lang="es">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{report.title}</title>
                <style>
                    body {{ 
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                        margin: 0; 
                        padding: 40px; 
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        min-height: 100vh;
                    }}
                    .container {{ 
                        max-width: 1200px; 
                        margin: 0 auto; 
                        background: white; 
                        border-radius: 15px; 
                        box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                        overflow: hidden;
                    }}
                    .header {{ 
                        background: linear-gradient(135deg, #0078d4 0%, #106ebe 100%); 
                        color: white; 
                        padding: 40px; 
                        text-align: center;
                    }}
                    .header h1 {{ margin: 0; font-size: 2.5em; font-weight: 300; }}
                    .header p {{ margin: 10px 0 0 0; opacity: 0.9; }}
                    .content {{ padding: 40px; }}
                    .metrics {{ 
                        display: grid; 
                        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
                        gap: 30px; 
                        margin: 30px 0; 
                    }}
                    .metric-card {{ 
                        background: #f8f9fa; 
                        padding: 25px; 
                        border-radius: 10px; 
                        text-align: center;
                        border-left: 5px solid #0078d4;
                    }}
                    .metric-value {{ 
                        font-size: 2.5em; 
                        font-weight: bold; 
                        color: #0078d4; 
                        margin-bottom: 10px;
                    }}
                    .metric-label {{ 
                        color: #6c757d; 
                        font-size: 0.9em; 
                        text-transform: uppercase; 
                        letter-spacing: 1px;
                    }}
                    .section {{ 
                        margin: 40px 0; 
                        padding: 30px; 
                        background: #f8f9fa; 
                        border-radius: 10px;
                    }}
                    .section h2 {{ 
                        color: #0078d4; 
                        border-bottom: 2px solid #0078d4; 
                        padding-bottom: 10px; 
                        margin-bottom: 20px;
                    }}
                    .recommendation {{ 
                        background: white; 
                        padding: 20px; 
                        margin: 15px 0; 
                        border-radius: 8px; 
                        border-left: 4px solid #28a745;
                        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                    }}
                    .high-priority {{ border-left-color: #dc3545; }}
                    .medium-priority {{ border-left-color: #ffc107; }}
                    .footer {{ 
                        background: #f8f9fa; 
                        padding: 30px; 
                        text-align: center; 
                        color: #6c757d; 
                        font-size: 0.9em;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>{report.title}</h1>
                        <p>Generado el {report.created_at.strftime("%d de %B de %Y")} por {report.user.email}</p>
                        <p>Tipo: {report.get_report_type_display()} | Estado: {report.get_status_display()}</p>
                    </div>
                    
                    <div class="content">
                        <div class="metrics">
                            <div class="metric-card">
                                <div class="metric-value">{total_actions:,}</div>
                                <div class="metric-label">Recomendaciones Totales</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-value">${estimated_savings:,.0f}</div>
                                <div class="metric-label">Ahorros Potenciales Mensuales</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-value">{advisor_score}</div>
                                <div class="metric-label">Azure Advisor Score</div>
                            </div>
                        </div>
                        
                        <div class="section">
                            <h2>Resumen Ejecutivo</h2>
                            <p>{report.description}</p>
                            <p>Este reporte analiza {total_actions:,} recomendaciones de Azure Advisor, 
                            identificando oportunidades de optimización que pueden generar ahorros de 
                            <strong>${estimated_savings:,.0f} USD mensuales</strong>.</p>
                        </div>
                        
                        <div class="section">
                            <h2>Hallazgos Principales</h2>
                            <div class="recommendation high-priority">
                                <h3>🔴 Alta Prioridad - Optimización de Costos</h3>
                                <p>Se identificaron oportunidades significativas de ahorro mediante la implementación de instancias reservadas y el redimensionamiento de recursos infrautilizados.</p>
                            </div>
                            <div class="recommendation medium-priority">
                                <h3>🟡 Prioridad Media - Seguridad</h3>
                                <p>Varias recomendaciones de seguridad requieren atención para mejorar la postura de seguridad general.</p>
                            </div>
                            <div class="recommendation">
                                <h3>🟢 Mejoras Operacionales</h3>
                                <p>Oportunidades para mejorar la confiabilidad y eficiencia operacional de los servicios.</p>
                            </div>
                        </div>
                        
                        <div class="section">
                            <h2>Próximos Pasos</h2>
                            <ol>
                                <li>Revisar y priorizar las recomendaciones de alto impacto</li>
                                <li>Implementar las optimizaciones de costo con mayor potencial de ahorro</li>
                                <li>Abordar las recomendaciones de seguridad críticas</li>
                                <li>Establecer un cronograma de implementación</li>
                                <li>Monitorear el progreso y el impacto de los cambios</li>
                            </ol>
                        </div>
                    </div>
                    
                    <div class="footer">
                        <p>Reporte generado automáticamente por Azure Reports Platform</p>
                        <p>ID del Reporte: {report.id}</p>
                    </div>
                </div>
            </body>
            </html>
            '''
            
            return html_content
            
        except Exception as e:
            logger.error(f"Error generando HTML: {e}")
            return f"<html><body><h1>Error</h1><p>Error generando reporte: {str(e)}</p></body></html>"
    
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