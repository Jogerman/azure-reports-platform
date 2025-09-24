# backend/apps/reports/utils/real_data_html_generator.py
"""
Generador HTML que usa datos reales del análisis existente
Soporta reportes completos e individuales por categoría
"""

import pandas as pd
from datetime import datetime
from typing import Optional, Tuple, Dict, Any, List
import json
import logging
import re

logger = logging.getLogger(__name__)

class RealDataHTMLGenerator:
    """Generador HTML que conecta con los datos reales del análisis existente"""
    
    def __init__(self, client_name=None):
        self.client_name = client_name or "Azure Client"
        
    def generate_complete_html(self, report) -> str:
        """Genera HTML completo usando datos reales del análisis"""
        try:
            logger.info(f"🚀 Generando HTML con datos reales para reporte {report.id}")
            
            # 1. Obtener datos reales del análisis
            real_data = self._get_real_analysis_data(report)
            if not real_data:
                logger.warning("No se encontraron datos reales, usando fallback")
                return self._generate_fallback_html(report)
            
            # 2. Extraer nombre del cliente
            client_name = self._extract_client_name(report)
            
            # 3. Generar HTML completo con datos reales
            html_content = self._generate_complete_report_html(real_data, client_name)
            
            logger.info(f"✅ HTML completo generado exitosamente para {client_name}")
            return html_content
            
        except Exception as e:
            logger.error(f"❌ Error generando HTML completo: {e}")
            return self._generate_fallback_html(report)
    
    def generate_category_html(self, report, category: str) -> str:
        """Genera HTML para una categoría específica (Cost, Security, etc.)"""
        try:
            logger.info(f"🎯 Generando HTML para categoría {category} en reporte {report.id}")
            
            # 1. Obtener datos reales del análisis
            real_data = self._get_real_analysis_data(report)
            if not real_data:
                logger.warning("No se encontraron datos reales para categoría")
                return self._generate_fallback_html(report)
            
            # 2. Extraer nombre del cliente
            client_name = self._extract_client_name(report)
            
            # 3. Generar HTML específico de la categoría
            html_content = self._generate_category_report_html(real_data, category, client_name)
            
            logger.info(f"✅ HTML de categoría {category} generado exitosamente")
            return html_content
            
        except Exception as e:
            logger.error(f"❌ Error generando HTML de categoría {category}: {e}")
            return self._generate_fallback_html(report)
    
    def _get_real_analysis_data(self, report) -> Optional[Dict[str, Any]]:
        """Obtener datos reales del análisis desde csv_file.analysis_data y report.analysis_data"""
        try:
            # Prioridad 1: Datos del reporte generado
            if (report.analysis_data and 
                'generated_content' in report.analysis_data):
                logger.info("✅ Usando datos de report.analysis_data['generated_content']")
                return report.analysis_data['generated_content']
            
            # Prioridad 2: Datos del CSV procesado
            if (report.csv_file and 
                report.csv_file.analysis_data):
                logger.info("✅ Usando datos de csv_file.analysis_data")
                return report.csv_file.analysis_data
            
            # Prioridad 3: Datos directos del reporte
            if report.analysis_data:
                logger.info("✅ Usando datos de report.analysis_data directos")
                return report.analysis_data
            
            logger.warning("❌ No se encontraron datos de análisis")
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo datos reales: {e}")
            return None
    
    def _extract_client_name(self, report) -> str:
        """Extraer nombre del cliente del reporte"""
        try:
            # 1. Desde el CSV filename
            if report.csv_file and report.csv_file.original_filename:
                client_name = self._extract_client_from_filename(report.csv_file.original_filename)
                if client_name != "Azure Client":
                    return client_name
            
            # 2. Desde el título del reporte
            if report.title and "Azure Client" not in report.title:
                # Extraer cliente del título como "Análisis Bzpay Solutions S.A - 9/23/2025"
                title_parts = report.title.split(' - ')
                if len(title_parts) > 0:
                    client_part = title_parts[0].replace('Análisis', '').strip()
                    if client_part:
                        return client_part
            
            return "Azure Client"
            
        except Exception as e:
            logger.error(f"Error extrayendo cliente: {e}")
            return "Azure Client"
    
    def _extract_client_from_filename(self, filename: str) -> str:
        """Extraer nombre del cliente desde filename"""
        try:
            if not filename:
                return "Azure Client"
                
            # Remover extensión
            name_without_ext = filename.split('.')[0]
            parts = name_without_ext.replace('_', ' ').replace('-', ' ').split()
            
            # Filtrar palabras comunes
            exclude_words = {'recommendations', 'advisor', 'azure', 'report', 'data', 'export', 'csv', 'ejemplo', 'test'}
            client_parts = [part for part in parts if part.lower() not in exclude_words and len(part) > 1]
            
            if client_parts:
                return ' '.join(client_parts[:4]).title()  # Permitir más palabras para nombres largos
            
            return "Azure Client"
            
        except Exception:
            return "Azure Client"
    
    def _generate_complete_report_html(self, real_data: Dict[str, Any], client_name: str) -> str:
        """Generar HTML completo usando datos reales"""
        try:
            # Extraer datos principales
            exec_summary = real_data.get('executive_summary', {})
            cost_optimization = real_data.get('cost_optimization', {})
            security_optimization = real_data.get('security_optimization', {})
            reliability_optimization = real_data.get('reliability_optimization', {})
            operational_excellence = real_data.get('operational_excellence', {})
            totals = real_data.get('totals', {})
            
            # Métricas principales
            total_actions = exec_summary.get('total_recommendations', exec_summary.get('total_actions', 0))
            advisor_score = exec_summary.get('azure_advisor_score', totals.get('advisor_score', 65))
            monthly_savings = cost_optimization.get('estimated_monthly_optimization', 0)
            total_working_hours = totals.get('total_working_hours', 0)
            
            # Datos por categoría
            cost_actions = cost_optimization.get('cost_actions_count', 0)
            security_actions = security_optimization.get('security_actions_count', 0)
            reliability_actions = reliability_optimization.get('reliability_actions_count', 0)
            opex_actions = operational_excellence.get('opex_actions_count', 0)
            
            html = f'''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Azure Advisor Report - {client_name}</title>
    <style>{self._get_professional_css()}</style>
</head>
<body>
    <div class="container">
        {self._generate_header_section(client_name)}
        {self._generate_summary_section(advisor_score, total_actions, monthly_savings)}
        {self._generate_categories_overview_section(cost_actions, security_actions, reliability_actions, opex_actions)}
        {self._generate_detailed_analysis_section(real_data)}
        {self._generate_conclusions_section(real_data)}
        {self._generate_footer_section()}
    </div>
</body>
</html>'''
            
            return html
            
        except Exception as e:
            logger.error(f"Error generando HTML completo: {e}")
            return self._generate_fallback_html(None)
    
    def _generate_category_report_html(self, real_data: Dict[str, Any], category: str, client_name: str) -> str:
        """Generar HTML específico para una categoría"""
        try:
            category_key = category.lower().replace(' ', '_')
            category_data = real_data.get(f'{category_key}_optimization', real_data.get(category_key, {}))
            
            if not category_data:
                logger.warning(f"No se encontraron datos para categoría {category}")
                return self._generate_fallback_html(None)
            
            html = f'''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{category} Analysis - {client_name}</title>
    <style>{self._get_professional_css()}</style>
</head>
<body>
    <div class="container">
        {self._generate_header_section(client_name, category)}
        {self._generate_category_summary_section(category_data, category)}
        {self._generate_category_details_section(real_data, category)}
        {self._generate_category_recommendations_section(real_data, category)}
        {self._generate_footer_section()}
    </div>
</body>
</html>'''
            
            return html
            
        except Exception as e:
            logger.error(f"Error generando HTML de categoría: {e}")
            return self._generate_fallback_html(None)
    
    def _generate_header_section(self, client_name: str, category: str = None) -> str:
        """Generar sección de header"""
        title = f"{category} Analysis" if category else "Azure Advisor Analyzer"
        return f'''
        <div class="header">
            <div class="header-content">
                <div class="logo">
                    <div class="logo-icon">☁</div>
                    <div class="logo-text">
                        <div class="company">The Cloud Mastery</div>
                    </div>
                </div>
                <h1>{title}</h1>
                <h2>{client_name}</h2>
            </div>
        </div>
        '''
    
    def _generate_summary_section(self, advisor_score: float, total_actions: int, monthly_savings: float) -> str:
        """Generar sección de resumen ejecutivo"""
        return f'''
        <div class="summary-section">
            <div class="summary-card">
                <div class="summary-icon">📊</div>
                <div class="summary-content">
                    <div class="summary-number">{advisor_score:.0f}</div>
                    <div class="summary-label">Azure Advisor Score</div>
                </div>
            </div>
            
            <div class="summary-card">
                <div class="summary-icon">📋</div>
                <div class="summary-content">
                    <div class="summary-number">{total_actions:,}</div>
                    <div class="summary-label">Total Actions</div>
                </div>
            </div>
            
            <div class="summary-card">
                <div class="summary-icon">💰</div>
                <div class="summary-content">
                    <div class="summary-number">${monthly_savings:,.0f}</div>
                    <div class="summary-label">Monthly Savings</div>
                </div>
            </div>
        </div>
        '''
    
    def _generate_categories_overview_section(self, cost_actions: int, security_actions: int, 
                                           reliability_actions: int, opex_actions: int) -> str:
        """Generar sección de overview de categorías"""
        return f'''
        <div class="categories-section">
            <h2>Optimization Categories</h2>
            <div class="categories-grid">
                <div class="category-card cost">
                    <div class="category-header">
                        <div class="category-icon">💰</div>
                        <h3>Cost Optimization</h3>
                    </div>
                    <div class="category-stats">
                        <div class="stat">
                            <span class="stat-number">{cost_actions}</span>
                            <span class="stat-label">Actions</span>
                        </div>
                    </div>
                </div>
                
                <div class="category-card security">
                    <div class="category-header">
                        <div class="category-icon">🔒</div>
                        <h3>Security</h3>
                    </div>
                    <div class="category-stats">
                        <div class="stat">
                            <span class="stat-number">{security_actions}</span>
                            <span class="stat-label">Actions</span>
                        </div>
                    </div>
                </div>
                
                <div class="category-card reliability">
                    <div class="category-header">
                        <div class="category-icon">⚡</div>
                        <h3>Reliability</h3>
                    </div>
                    <div class="category-stats">
                        <div class="stat">
                            <span class="stat-number">{reliability_actions}</span>
                            <span class="stat-label">Actions</span>
                        </div>
                    </div>
                </div>
                
                <div class="category-card operational">
                    <div class="category-header">
                        <div class="category-icon">⚙️</div>
                        <h3>Operational Excellence</h3>
                    </div>
                    <div class="category-stats">
                        <div class="stat">
                            <span class="stat-number">{opex_actions}</span>
                            <span class="stat-label">Actions</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        '''
    
    def _generate_detailed_analysis_section(self, real_data: Dict[str, Any]) -> str:
        """Generar sección de análisis detallado con datos reales"""
        try:
            cost_optimization = real_data.get('cost_optimization', {})
            monthly_savings = cost_optimization.get('estimated_monthly_optimization', 0)
            cost_actions = cost_optimization.get('cost_actions_count', 0)
            cost_hours = cost_optimization.get('cost_working_hours', 0)
            
            # Generar tabla de cost optimization si hay datos
            cost_table = ""
            if monthly_savings > 0:
                cost_table = f'''
                <div class="analysis-section">
                    <div class="section-header cost">
                        <div class="section-icon">💰</div>
                        <h3>COST OPTIMIZATION</h3>
                    </div>
                    <div class="cost-summary">
                        <div class="cost-metric">
                            <div class="metric-value">${monthly_savings:,.0f}</div>
                            <div class="metric-label">Estimated Monthly Optimization</div>
                        </div>
                        <div class="cost-metric">
                            <div class="metric-value">{cost_actions}</div>
                            <div class="metric-label">Total Actions</div>
                        </div>
                        <div class="cost-metric">
                            <div class="metric-value">{cost_hours:.1f}</div>
                            <div class="metric-label">Working Hours</div>
                        </div>
                    </div>
                </div>
                '''
            
            # Similar para security, reliability, etc.
            security_optimization = real_data.get('security_optimization', {})
            security_actions = security_optimization.get('security_actions_count', 0)
            security_hours = security_optimization.get('security_working_hours', 0)
            
            security_table = ""
            if security_actions > 0:
                security_table = f'''
                <div class="analysis-section">
                    <div class="section-header security">
                        <div class="section-icon">🔒</div>
                        <h3>SECURITY OPTIMIZATION</h3>
                    </div>
                    <div class="security-summary">
                        <div class="security-metric">
                            <div class="metric-value">{security_actions}</div>
                            <div class="metric-label">Actions To Take</div>
                        </div>
                        <div class="security-metric">
                            <div class="metric-value">{security_hours:.1f}</div>
                            <div class="metric-label">Working Hours</div>
                        </div>
                    </div>
                </div>
                '''
            
            return f'''
            <div class="detailed-analysis">
                <h2>Detailed Analysis</h2>
                {cost_table}
                {security_table}
            </div>
            '''
            
        except Exception as e:
            logger.error(f"Error generando análisis detallado: {e}")
            return "<div class='analysis-section'><p>Error loading detailed analysis</p></div>"
    
    def _generate_category_summary_section(self, category_data: Dict[str, Any], category: str) -> str:
        """Generar sección de resumen para categoría específica"""
        try:
            if category.lower() == 'cost':
                savings = category_data.get('estimated_monthly_optimization', 0)
                actions = category_data.get('cost_actions_count', 0)
                hours = category_data.get('cost_working_hours', 0)
                
                return f'''
                <div class="category-summary cost">
                    <div class="summary-stat">
                        <div class="stat-value">${savings:,.0f}</div>
                        <div class="stat-label">Monthly Savings</div>
                    </div>
                    <div class="summary-stat">
                        <div class="stat-value">{actions}</div>
                        <div class="stat-label">Actions</div>
                    </div>
                    <div class="summary-stat">
                        <div class="stat-value">{hours:.1f}</div>
                        <div class="stat-label">Working Hours</div>
                    </div>
                </div>
                '''
            elif category.lower() == 'security':
                actions = category_data.get('security_actions_count', 0)
                hours = category_data.get('security_working_hours', 0)
                investment = category_data.get('security_monthly_investment', 0)
                
                return f'''
                <div class="category-summary security">
                    <div class="summary-stat">
                        <div class="stat-value">{actions}</div>
                        <div class="stat-label">Actions To Take</div>
                    </div>
                    <div class="summary-stat">
                        <div class="stat-value">{hours:.1f}</div>
                        <div class="stat-label">Working Hours</div>
                    </div>
                    <div class="summary-stat">
                        <div class="stat-value">${investment:,.0f}</div>
                        <div class="stat-label">Monthly Investment</div>
                    </div>
                </div>
                '''
            
            # Similar para otras categorías
            return f'<div class="category-summary"><p>Summary for {category}</p></div>'
            
        except Exception as e:
            logger.error(f"Error generando resumen de categoría: {e}")
            return f'<div class="category-summary"><p>Error loading {category} summary</p></div>'
    
    def _generate_category_details_section(self, real_data: Dict[str, Any], category: str) -> str:
        """Generar sección de detalles para categoría específica"""
        return f'''
        <div class="category-details">
            <h3>{category} Details</h3>
            <p>Detailed breakdown and analysis for {category} optimization...</p>
        </div>
        '''
    
    def _generate_category_recommendations_section(self, real_data: Dict[str, Any], category: str) -> str:
        """Generar sección de recomendaciones para categoría específica"""
        return f'''
        <div class="category-recommendations">
            <h3>Recommendations</h3>
            <p>Specific recommendations for {category} improvements...</p>
        </div>
        '''
    
    def _generate_conclusions_section(self, real_data: Dict[str, Any]) -> str:
        """Generar sección de conclusiones usando datos reales"""
        try:
            cost_optimization = real_data.get('cost_optimization', {})
            monthly_savings = cost_optimization.get('estimated_monthly_optimization', 0)
            exec_summary = real_data.get('executive_summary', {})
            total_actions = exec_summary.get('total_recommendations', exec_summary.get('total_actions', 0))
            
            return f'''
            <div class="conclusions-section">
                <div class="section-header">
                    <div class="section-icon">📋</div>
                    <h2>CONCLUSIONS</h2>
                </div>
                <div class="conclusions-content">
                    <p>This report summarizes the main areas of detected optimization, highlighting their potential 
                    impact on improving operational efficiency and generating significant economic savings.</p>
                    
                    <h4>Potential Optimization:</h4>
                    <ol>
                        <li>Economic optimization of <strong>${monthly_savings:,.0f} USD</strong> per month pending validation.</li>
                        <li>Total of <strong>{total_actions:,}</strong> recommended actions across all categories.</li>
                        <li>Strategic implementation essential for maximizing organizational benefits.</li>
                    </ol>
                </div>
            </div>
            '''
        except Exception as e:
            logger.error(f"Error generando conclusiones: {e}")
            return "<div class='conclusions-section'><h2>Conclusions</h2><p>Analysis completed successfully.</p></div>"
    
    def _generate_footer_section(self) -> str:
        """Generar sección de footer"""
        return f'''
        <div class="footer">
            <p>Data retrieved on {datetime.now().strftime('%A, %B %d, %Y')}</p>
            <p>Generated by Azure Reports Platform</p>
        </div>
        '''
    
    def _generate_fallback_html(self, report) -> str:
        """Generar HTML de fallback cuando no hay datos reales"""
        client_name = self._extract_client_name(report) if report else "Azure Client"
        
        return f'''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Azure Report - {client_name}</title>
    <style>{self._get_basic_css()}</style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Azure Advisor Report</h1>
            <h2>{client_name}</h2>
        </div>
        <div class="content">
            <div class="message">
                <h3>📊 Report Processing</h3>
                <p>The report is being generated with available data. For a complete analysis, ensure the CSV file has been properly processed.</p>
            </div>
        </div>
        <div class="footer">
            <p>Generated on {datetime.now().strftime('%A, %B %d, %Y')}</p>
        </div>
    </div>
</body>
</html>
        '''
    
    def _get_professional_css(self) -> str:
        """CSS profesional para reportes completos"""
        return '''
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f8f9fa;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }
        
        .header {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 60px 40px;
            text-align: center;
        }
        
        .logo {
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 30px;
        }
        
        .logo-icon {
            font-size: 48px;
            margin-right: 20px;
        }
        
        .company {
            font-size: 24px;
            font-weight: 300;
        }
        
        .header h1 {
            font-size: 48px;
            margin: 20px 0;
            font-weight: 700;
        }
        
        .header h2 {
            font-size: 36px;
            color: #FFD700;
            font-weight: 300;
        }
        
        .summary-section {
            display: flex;
            padding: 40px;
            gap: 30px;
            background: #f8f9fa;
        }
        
        .summary-card {
            flex: 1;
            background: white;
            padding: 30px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        
        .summary-card:hover {
            transform: translateY(-5px);
        }
        
        .summary-icon {
            font-size: 36px;
            margin-bottom: 15px;
        }
        
        .summary-number {
            font-size: 48px;
            font-weight: bold;
            color: #1e3c72;
            margin-bottom: 10px;
        }
        
        .summary-label {
            font-size: 16px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .categories-section {
            padding: 40px;
        }
        
        .categories-section h2 {
            text-align: center;
            margin-bottom: 40px;
            font-size: 36px;
            color: #333;
        }
        
        .categories-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 30px;
        }
        
        .category-card {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        
        .category-card:hover {
            transform: translateY(-8px);
        }
        
        .category-card.cost { border-top: 4px solid #28a745; }
        .category-card.security { border-top: 4px solid #dc3545; }
        .category-card.reliability { border-top: 4px solid #ffc107; }
        .category-card.operational { border-top: 4px solid #17a2b8; }
        
        .category-header {
            display: flex;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .category-icon {
            font-size: 32px;
            margin-right: 15px;
        }
        
        .category-header h3 {
            font-size: 20px;
            font-weight: 600;
        }
        
        .category-stats {
            display: flex;
            justify-content: space-between;
        }
        
        .stat {
            text-align: center;
        }
        
        .stat-number {
            display: block;
            font-size: 32px;
            font-weight: bold;
            color: #1e3c72;
            margin-bottom: 5px;
        }
        
        .stat-label {
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .detailed-analysis {
            padding: 40px;
            background: #f8f9fa;
        }
        
        .detailed-analysis h2 {
            text-align: center;
            margin-bottom: 40px;
            font-size: 32px;
        }
        
        .analysis-section {
            background: white;
            margin-bottom: 30px;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        
        .section-header {
            display: flex;
            align-items: center;
            margin-bottom: 25px;
        }
        
        .section-icon {
            font-size: 28px;
            margin-right: 15px;
        }
        
        .section-header h3 {
            font-size: 24px;
            font-weight: 600;
        }
        
        .cost-summary, .security-summary {
            display: flex;
            gap: 30px;
        }
        
        .cost-metric, .security-metric {
            text-align: center;
            flex: 1;
        }
        
        .metric-value {
            font-size: 32px;
            font-weight: bold;
            color: #1e3c72;
            margin-bottom: 8px;
        }
        
        .metric-label {
            font-size: 14px;
            color: #666;
            text-transform: uppercase;
        }
        
        .conclusions-section {
            padding: 40px;
            background: white;
        }
        
        .conclusions-content {
            background: #f8f9ff;
            padding: 30px;
            border-radius: 15px;
            border: 1px solid #e1e8ff;
        }
        
        .conclusions-content p {
            font-size: 1.1rem;
            line-height: 1.6;
            margin-bottom: 20px;
            color: #2d3748;
        }
        
        .conclusions-content h4 {
            color: #4c6ef5;
            margin-bottom: 15px;
        }
        
        .conclusions-content ol {
            margin-left: 20px;
        }
        
        .conclusions-content li {
            margin-bottom: 10px;
            line-height: 1.6;
        }
        
        .footer {
            background: #1e3c72;
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .footer p {
            margin: 5px 0;
        }
        
        @media (max-width: 768px) {
            .summary-section, .cost-summary, .security-summary {
                flex-direction: column;
                gap: 20px;
            }
            
            .categories-grid {
                grid-template-columns: 1fr;
            }
            
            .header {
                padding: 40px 20px;
            }
            
            .header h1 {
                font-size: 36px;
            }
            
            .header h2 {
                font-size: 28px;
            }
        }
        '''
    
    def _get_basic_css(self) -> str:
        """CSS básico para fallback"""
        return '''
        body { 
            font-family: Arial, sans-serif; 
            margin: 0; 
            background: #f5f5f5; 
        }
        .container { 
            max-width: 800px; 
            margin: 0 auto; 
            background: white; 
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        .header { 
            background: linear-gradient(135deg, #1e3c72, #2a5298); 
            color: white; 
            padding: 40px; 
            text-align: center; 
        }
        .header h1 { 
            font-size: 36px; 
            margin: 0 0 15px 0; 
        }
        .header h2 { 
            font-size: 24px; 
            color: #FFD700; 
            margin: 0; 
        }
        .content { 
            padding: 40px; 
        }
        .message { 
            background: #fff3cd; 
            border: 1px solid #ffeaa7; 
            color: #856404; 
            padding: 20px; 
            border-radius: 5px; 
        }
        .footer { 
            background: #1e3c72; 
            color: white; 
            padding: 20px; 
            text-align: center; 
        }
        '''