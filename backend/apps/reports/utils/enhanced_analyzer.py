import json
import pandas as pd
from datetime import datetime
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class EnhancedAzureHTMLReportGenerator:
    """Generador HTML mejorado para reportes de Azure Advisor"""
    
    def __init__(self):
        self.template_base = self._get_base_template()
        
    def generate_enhanced_report(self, report, csv_data_path=None):
        """
        Genera un reporte HTML completo y mejorado
        
        Args:
            report: Objeto Report de Django
            csv_data_path: Ruta al archivo CSV (opcional)
        
        Returns:
            str: HTML completo del reporte
        """
        try:
            # Obtener datos del CSV
            if csv_data_path:
                df = pd.read_csv(csv_data_path)
            elif hasattr(report, 'csv_file') and report.csv_file:
                # Leer desde el archivo asociado al reporte
                df = pd.read_csv(report.csv_file.file.path)
            else:
                # Datos de ejemplo si no hay CSV
                df = self._generate_sample_data()
            
            # Análisis de datos
            analysis = self._analyze_data(df)
            
            # Generar secciones del reporte
            html_content = self._build_complete_html(report, df, analysis)
            
            logger.info(f"Enhanced HTML report generated successfully for {report.title}")
            return html_content
            
        except Exception as e:
            logger.error(f"Error generating enhanced HTML report: {e}")
            return self._generate_error_html(str(e))
    
    def _analyze_data(self, df):
        """Analiza los datos del CSV para generar métricas"""
        analysis = {
            'total_actions': len(df),
            'categories': {},
            'business_impact': {},
            'resource_types': {},
            'recommendations_by_priority': [],
            'monthly_optimization': 3600,  # Estimado
            'working_hours': 3.2,  # Estimado
            'advisor_score': 20,  # De 0-100
        }
        
        # Análisis por categorías
        if 'Category' in df.columns:
            analysis['categories'] = df['Category'].value_counts().to_dict()
        
        # Análisis por impacto de negocio
        if 'Business Impact' in df.columns:
            analysis['business_impact'] = df['Business Impact'].value_counts().to_dict()
        
        # Análisis por tipo de recurso
        if 'Type' in df.columns:
            analysis['resource_types'] = df['Type'].value_counts().head(10).to_dict()
        
        # Recomendaciones prioritarias (primeras 20)
        if len(df) > 0:
            priority_cols = ['Business Impact', 'Category', 'Recommendation', 'Resource Name', 'Type']
            available_cols = [col for col in priority_cols if col in df.columns]
            analysis['recommendations_by_priority'] = df[available_cols].head(20).to_dict('records')
        
        # Calcular acciones en scope (high + medium impact)
        high_impact = analysis['business_impact'].get('High', 0)
        medium_impact = analysis['business_impact'].get('Medium', 0)
        analysis['actions_in_scope'] = high_impact + medium_impact
        
        # Remediation (acciones que no aumentan billing - estimado)
        cost_category_count = analysis['categories'].get('Cost', 0)
        analysis['remediation_count'] = analysis['total_actions'] - cost_category_count
        
        return analysis
    
    def _build_complete_html(self, report, df, analysis):
        """Construye el HTML completo del reporte"""
        
        # Datos para el template
        context = {
            'report_title': getattr(report, 'title', 'Azure Advisor Report'),
            'client_name': getattr(report, 'client_name', 'Cliente'),
            'current_date': datetime.now().strftime('%B %d, %Y'),
            'analysis': analysis,
            'total_actions': analysis['total_actions'],
            'actions_in_scope': analysis['actions_in_scope'],
            'remediation_count': analysis['remediation_count'],
            'advisor_score': analysis['advisor_score'],
            'monthly_optimization': analysis['monthly_optimization'],
            'working_hours': analysis['working_hours'],
        }
        
        # Generar secciones
        dashboard_section = self._generate_dashboard_section(context)
        summary_section = self._generate_summary_section(context)
        charts_section = self._generate_charts_section(analysis)
        recommendations_table = self._generate_recommendations_table(analysis)
        cost_optimization_section = self._generate_cost_optimization_section(context)
        
        # Template principal
        html_template = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{context['report_title']}</title>
            {self._get_styles()}
        </head>
        <body>
            <div class="container">
                <!-- Header -->
                <header class="report-header">
                    <div class="header-content">
                        <div class="logo-section">
                            <i class="icon-azure"></i>
                            <h1>Azure Advisor Report</h1>
                        </div>
                        <div class="report-info">
                            <h2>{context['client_name']}</h2>
                            <p class="date">Data retrieved on {context['current_date']}</p>
                        </div>
                    </div>
                </header>
                
                <!-- Dashboard Principal -->
                {dashboard_section}
                
                <!-- Summary of Findings -->
                {summary_section}
                
                <!-- Charts and Analytics -->
                {charts_section}
                
                <!-- Cost Optimization -->
                {cost_optimization_section}
                
                <!-- Recommendations Table -->
                {recommendations_table}
                
                <!-- Footer -->
                <footer class="report-footer">
                    <p>Generated by Azure Report Generator on {context['current_date']}</p>
                </footer>
            </div>
            
            {self._get_javascript()}
        </body>
        </html>
        """
        
        return html_template
    
    def _generate_dashboard_section(self, context):
        """Genera la sección del dashboard principal"""
        return f"""
        <section class="dashboard-section">
            <div class="metrics-grid">
                <div class="metric-card main-metric">
                    <div class="metric-number">{context['total_actions']}</div>
                    <div class="metric-label">Total<br>Recommended<br>Actions</div>
                    <div class="metric-subtitle">Obtained From<br>Azure Advisor</div>
                </div>
                
                <div class="metric-card secondary-metric">
                    <div class="metric-number">{context['actions_in_scope']}</div>
                    <div class="metric-label">Actions In<br>Scope</div>
                    <div class="metric-subtitle">Selected By<br>Business Impact</div>
                </div>
                
                <div class="metric-card secondary-metric">
                    <div class="metric-number">{context['remediation_count']}</div>
                    <div class="metric-label">Remediation</div>
                    <div class="metric-subtitle">No increase in<br>Billing</div>
                </div>
                
                <div class="metric-card secondary-metric">
                    <div class="metric-number">{context['advisor_score']}</div>
                    <div class="metric-label">Azure<br>Advisor<br>Score</div>
                    <div class="metric-subtitle">0 – 100</div>
                </div>
            </div>
        </section>
        """
    
    def _generate_summary_section(self, context):
        """Genera la sección de resumen de hallazgos"""
        return f"""
        <section class="summary-section">
            <div class="section-header">
                <div class="section-icon">📊</div>
                <h2>SUMMARY OF FINDINGS</h2>
            </div>
            <div class="summary-content">
                <p><strong>Azure Advisor Score</strong> is a metric that evaluates the <span class="highlight">overall optimization status</span> of resources in Azure, based on <span class="highlight">five key categories</span>: reliability, security, operational excellence, performance, and cost optimization.</p>
                
                <p>It provides <span class="highlight">personalized recommendations</span> to improve each area, helping to <span class="highlight">maximize efficiency</span> and <span class="highlight">reduce risks</span> in the cloud environment.</p>
            </div>
            
            <div class="total-actions-display">
                <h3>Total Recommended Actions</h3>
                <p class="subtitle">Obtained From Azure Advisor</p>
                <div class="large-number">{context['total_actions']}</div>
            </div>
        </section>
        """
    
    def _generate_charts_section(self, analysis):
        """Genera la sección de gráficos y análisis"""
        
        # Preparar datos para gráficos
        categories = analysis.get('categories', {})
        business_impact = analysis.get('business_impact', {})
        
        return f"""
        <section class="charts-section">
            <div class="charts-grid">
                <!-- Business Impact Chart -->
                <div class="chart-container">
                    <h3>Business Impact Distribution</h3>
                    <div class="impact-chart">
                        <div class="impact-bar high" style="height: {business_impact.get('High', 0) * 2}px">
                            <div class="bar-value">{business_impact.get('High', 0)}</div>
                            <div class="bar-label">Alto</div>
                        </div>
                        <div class="impact-bar medium" style="height: {business_impact.get('Medium', 0)}px">
                            <div class="bar-value">{business_impact.get('Medium', 0)}</div>
                            <div class="bar-label">Medio</div>
                        </div>
                        <div class="impact-bar low" style="height: {business_impact.get('Low', 0) * 10}px">
                            <div class="bar-value">{business_impact.get('Low', 0)}</div>
                            <div class="bar-label">Bajo</div>
                        </div>
                    </div>
                </div>
                
                <!-- Category Distribution -->
                <div class="chart-container">
                    <h3>Actions In Scope</h3>
                    <p class="chart-subtitle">Selected By Business Impact</p>
                    <div class="scope-number">{analysis.get('actions_in_scope', 0)}</div>
                    
                    <h3>Remediation</h3>
                    <p class="chart-subtitle">No increase in Billing</p>
                    <div class="remediation-number">{analysis.get('remediation_count', 0)}</div>
                </div>
            </div>
        </section>
        """
    
    def _generate_cost_optimization_section(self, context):
        """Genera la sección de optimización de costos"""
        return f"""
        <section class="cost-optimization-section">
            <div class="section-header cost-header">
                <div class="cost-icon">💰</div>
                <h2>COST OPTIMIZATION</h2>
            </div>
            
            <div class="cost-metrics-grid">
                <div class="cost-metric-card">
                    <div class="cost-amount">${context['monthly_optimization']:,}</div>
                    <div class="cost-label">Estimated Monthly<br>Optimization</div>
                </div>
                
                <div class="cost-metric-card">
                    <div class="cost-number">8</div>
                    <div class="cost-label">Total Actions</div>
                </div>
                
                <div class="cost-metric-card">
                    <div class="cost-number">{context['working_hours']}</div>
                    <div class="cost-label">Working Hours</div>
                </div>
            </div>
            
            <div class="cost-chart-placeholder">
                <p>Sources Of Optimization Chart</p>
                <p class="chart-note">Actual ${context['monthly_optimization']:,} (4.85%)</p>
            </div>
        </section>
        """
    
    def _generate_recommendations_table(self, analysis):
        """Genera la tabla de recomendaciones"""
        recommendations = analysis.get('recommendations_by_priority', [])
        
        if not recommendations:
            return "<section class='recommendations-section'><p>No recommendations data available.</p></section>"
        
        table_rows = ""
        for i, rec in enumerate(recommendations[:20], 1):
            business_impact = rec.get('Business Impact', 'Medium')
            category = rec.get('Category', 'General')
            recommendation = rec.get('Recommendation', 'No recommendation text')
            resource_name = rec.get('Resource Name', 'Unknown')
            resource_type = rec.get('Type', 'Unknown')
            
            # Truncar textos largos
            recommendation_short = recommendation[:80] + "..." if len(recommendation) > 80 else recommendation
            resource_name_short = resource_name[:30] + "..." if len(resource_name) > 30 else resource_name
            
            risk_score = 10 if business_impact == 'High' else (5 if business_impact == 'Medium' else 1)
            risk_class = business_impact.lower()
            
            table_rows += f"""
            <tr>
                <td class="index-cell">{i}</td>
                <td class="recommendation-cell" title="{recommendation}">{recommendation_short}</td>
                <td class="impact-cell">
                    <span class="impact-badge {risk_class}">{business_impact}</span>
                </td>
                <td class="category-cell">{category}</td>
                <td class="resource-cell" title="{resource_name}">{resource_name_short}</td>
                <td class="type-cell">{resource_type}</td>
                <td class="risk-cell">
                    <div class="risk-bar {risk_class}" data-risk="{risk_score}">{risk_score}</div>
                </td>
            </tr>
            """
        
        return f"""
        <section class="recommendations-section">
            <div class="section-header">
                <div class="section-icon">📋</div>
                <h2>LISTING OF ACTIONS IN SCOPE</h2>
            </div>
            
            <div class="table-container">
                <table class="recommendations-table">
                    <thead>
                        <tr>
                            <th>Index</th>
                            <th>Recommendation</th>
                            <th>Business Impact</th>
                            <th>Category</th>
                            <th>Resource Name</th>
                            <th>Resource Type</th>
                            <th>Average of Risk</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
            </div>
            
            <div class="scope-summary">
                <div class="scope-box">
                    <h3>Total Recommended Actions</h3>
                    <h4>Actions In Scope</h4>
                    <div class="scope-icon">📊</div>
                    <div class="scope-number-large">{len(recommendations)}</div>
                </div>
                
                <div class="scope-breakdown">
                    <div class="breakdown-item">
                        <h4>Remediation</h4>
                        <p>No increase in Billing</p>
                        <div class="breakdown-number">{analysis.get('remediation_count', 0)}</div>
                        <div class="breakdown-icon">💡</div>
                    </div>
                    
                    <div class="breakdown-plus">+</div>
                    
                    <div class="breakdown-item">
                        <h4>Optimizations</h4>
                        <p>With billing increase</p>
                        <div class="breakdown-number">{analysis.get('actions_in_scope', 0) - analysis.get('remediation_count', 0)}</div>
                        <div class="breakdown-icon">⚙️</div>
                    </div>
                </div>
            </div>
            
            <div class="explanation-box">
                <h4>Why were these actions chosen?</h4>
                <p>In Azure Advisor, recommendations are prioritized based on their <strong>impact</strong> on improving the environment, with greater emphasis placed on those classified as <strong>high impact</strong>. These recommendations have the potential to generate <strong>significant changes</strong> in critical areas, such as improving <strong>security</strong>, optimizing <strong>costs</strong>, or ensuring the <strong>reliability</strong> of services.</p>
            </div>
        </section>
        """
    
    def _get_styles(self):
        """Retorna los estilos CSS mejorados"""
        return """
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                min-height: 100vh;
            }
            
            /* Header Styles */
            .report-header {
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }
            
            .header-content {
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
            }
            
            .logo-section {
                display: flex;
                align-items: center;
                gap: 15px;
            }
            
            .icon-azure::before {
                content: '☁️';
                font-size: 2.5rem;
            }
            
            .report-header h1 {
                font-size: 2.5rem;
                font-weight: 300;
                margin: 0;
            }
            
            .report-info h2 {
                font-size: 1.8rem;
                margin-bottom: 5px;
            }
            
            .date {
                font-size: 1rem;
                opacity: 0.9;
            }
            
            /* Dashboard Section */
            .dashboard-section {
                padding: 40px 30px;
                background: #f8f9fa;
            }
            
            .metrics-grid {
                display: grid;
                grid-template-columns: 2fr 1fr 1fr 1fr;
                gap: 20px;
                align-items: stretch;
            }
            
            .metric-card {
                background: white;
                border-radius: 10px;
                padding: 25px;
                text-align: center;
                box-shadow: 0 5px 15px rgba(0,0,0,0.08);
                border-left: 5px solid #2196F3;
                transition: transform 0.3s ease;
            }
            
            .metric-card:hover {
                transform: translateY(-5px);
            }
            
            .main-metric {
                border-left-color: #1976D2;
            }
            
            .main-metric .metric-number {
                font-size: 4rem;
                font-weight: bold;
                color: #1976D2;
                margin-bottom: 10px;
            }
            
            .secondary-metric .metric-number {
                font-size: 2.5rem;
                font-weight: bold;
                color: #2196F3;
                margin-bottom: 10px;
            }
            
            .metric-label {
                font-size: 1rem;
                font-weight: 600;
                color: #555;
                margin-bottom: 8px;
                line-height: 1.2;
            }
            
            .metric-subtitle {
                font-size: 0.85rem;
                color: #777;
                line-height: 1.2;
            }
            
            /* Summary Section */
            .summary-section {
                padding: 40px 30px;
                background: white;
            }
            
            .section-header {
                display: flex;
                align-items: center;
                gap: 15px;
                margin-bottom: 25px;
                padding-bottom: 15px;
                border-bottom: 3px solid #2196F3;
            }
            
            .section-icon {
                font-size: 2rem;
            }
            
            .section-header h2 {
                color: #1976D2;
                font-size: 1.8rem;
                font-weight: 600;
            }
            
            .summary-content {
                margin-bottom: 30px;
                font-size: 1.1rem;
                line-height: 1.8;
            }
            
            .highlight {
                color: #2196F3;
                font-weight: 600;
            }
            
            .total-actions-display {
                text-align: center;
                background: #f8f9fa;
                padding: 30px;
                border-radius: 10px;
                border: 2px solid #e3f2fd;
            }
            
            .total-actions-display h3 {
                color: #1976D2;
                font-size: 1.5rem;
                margin-bottom: 5px;
            }
            
            .subtitle {
                color: #666;
                margin-bottom: 15px;
            }
            
            .large-number {
                font-size: 4rem;
                font-weight: bold;
                color: #1976D2;
            }
            
            /* Charts Section */
            .charts-section {
                padding: 40px 30px;
                background: #f8f9fa;
            }
            
            .charts-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 30px;
            }
            
            .chart-container {
                background: white;
                padding: 25px;
                border-radius: 10px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            }
            
            .chart-container h3 {
                color: #1976D2;
                margin-bottom: 20px;
                text-align: center;
            }
            
            .impact-chart {
                display: flex;
                justify-content: center;
                align-items: end;
                gap: 20px;
                height: 200px;
                margin-top: 20px;
            }
            
            .impact-bar {
                width: 60px;
                min-height: 20px;
                border-radius: 5px 5px 0 0;
                display: flex;
                flex-direction: column;
                justify-content: flex-end;
                align-items: center;
                position: relative;
                transition: all 0.3s ease;
            }
            
            .impact-bar.high {
                background: linear-gradient(to top, #d32f2f, #f44336);
            }
            
            .impact-bar.medium {
                background: linear-gradient(to top, #f57c00, #ff9800);
            }
            
            .impact-bar.low {
                background: linear-gradient(to top, #388e3c, #4caf50);
            }
            
            .bar-value {
                color: white;
                font-weight: bold;
                padding: 5px;
                font-size: 1.1rem;
            }
            
            .bar-label {
                position: absolute;
                bottom: -25px;
                font-weight: 600;
                color: #555;
            }
            
            .scope-number, .remediation-number {
                font-size: 3rem;
                font-weight: bold;
                color: #2196F3;
                text-align: center;
                margin: 15px 0;
            }
            
            .chart-subtitle {
                text-align: center;
                color: #666;
                margin-bottom: 10px;
            }
            
            /* Cost Optimization Section */
            .cost-optimization-section {
                padding: 40px 30px;
                background: linear-gradient(135deg, #e8f5e8 0%, #f1f8e9 100%);
            }
            
            .cost-header {
                border-bottom-color: #4caf50;
            }
            
            .cost-header h2 {
                color: #2e7d32;
            }
            
            .cost-icon {
                color: #4caf50;
            }
            
            .cost-metrics-grid {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 20px;
                margin-bottom: 30px;
            }
            
            .cost-metric-card {
                background: white;
                padding: 25px;
                border-radius: 10px;
                text-align: center;
                box-shadow: 0 5px 15px rgba(0,0,0,0.08);
                border-left: 5px solid #4caf50;
            }
            
            .cost-amount {
                font-size: 2.5rem;
                font-weight: bold;
                color: #2e7d32;
                margin-bottom: 10px;
            }
            
            .cost-number {
                font-size: 2.5rem;
                font-weight: bold;
                color: #2e7d32;
                margin-bottom: 10px;
            }
            
            .cost-label {
                color: #555;
                font-weight: 600;
                line-height: 1.2;
            }
            
            .cost-chart-placeholder {
                background: white;
                padding: 40px;
                border-radius: 10px;
                text-align: center;
                box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            }
            
            .chart-note {
                color: #666;
                margin-top: 10px;
            }
            
            /* Recommendations Table */
            .recommendations-section {
                padding: 40px 30px;
                background: white;
            }
            
            .table-container {
                overflow-x: auto;
                margin-bottom: 30px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.08);
                border-radius: 10px;
            }
            
            .recommendations-table {
                width: 100%;
                border-collapse: collapse;
                background: white;
            }
            
            .recommendations-table th {
                background: linear-gradient(135deg, #1976D2, #2196F3);
                color: white;
                padding: 15px 10px;
                text-align: left;
                font-weight: 600;
                font-size: 0.9rem;
                position: sticky;
                top: 0;
                z-index: 10;
            }
            
            .recommendations-table td {
                padding: 12px 10px;
                border-bottom: 1px solid #e0e0e0;
                font-size: 0.85rem;
                vertical-align: top;
            }
            
            .recommendations-table tr:nth-child(even) {
                background: #f8f9fa;
            }
            
            .recommendations-table tr:hover {
                background: #e3f2fd;
                transition: background 0.3s ease;
            }
            
            .index-cell {
                width: 60px;
                text-align: center;
                font-weight: bold;
                color: #1976D2;
            }
            
            .recommendation-cell {
                max-width: 300px;
            }
            
            .impact-badge {
                padding: 4px 8px;
                border-radius: 12px;
                font-size: 0.75rem;
                font-weight: 600;
                text-transform: uppercase;
            }
            
            .impact-badge.high {
                background: #ffebee;
                color: #d32f2f;
                border: 1px solid #f44336;
            }
            
            .impact-badge.medium {
                background: #fff3e0;
                color: #f57c00;
                border: 1px solid #ff9800;
            }
            
            .impact-badge.low {
                background: #e8f5e8;
                color: #2e7d32;
                border: 1px solid #4caf50;
            }
            
            .risk-bar {
                display: inline-block;
                padding: 6px 12px;
                border-radius: 15px;
                color: white;
                font-weight: bold;
                font-size: 0.8rem;
                min-width: 30px;
                text-align: center;
            }
            
            .risk-bar.high {
                background: linear-gradient(45deg, #d32f2f, #f44336);
            }
            
            .risk-bar.medium {
                background: linear-gradient(45deg, #f57c00, #ff9800);
            }
            
            .risk-bar.low {
                background: linear-gradient(45deg, #388e3c, #4caf50);
            }
            
            /* Scope Summary */
            .scope-summary {
                display: grid;
                grid-template-columns: 1fr 2fr;
                gap: 30px;
                margin-bottom: 30px;
            }
            
            .scope-box {
                background: linear-gradient(135deg, #e3f2fd, #bbdefb);
                padding: 30px;
                border-radius: 10px;
                text-align: center;
                border: 2px solid #2196F3;
            }
            
            .scope-box h3 {
                color: #1976D2;
                margin-bottom: 5px;
            }
            
            .scope-box h4 {
                color: #1976D2;
                font-weight: 600;
                margin-bottom: 15px;
            }
            
            .scope-icon {
                font-size: 2rem;
                margin-bottom: 15px;
            }
            
            .scope-number-large {
                font-size: 3.5rem;
                font-weight: bold;
                color: #1976D2;
            }
            
            .scope-breakdown {
                display: flex;
                align-items: center;
                justify-content: space-around;
                gap: 20px;
            }
            
            .breakdown-item {
                background: white;
                padding: 25px;
                border-radius: 10px;
                text-align: center;
                box-shadow: 0 5px 15px rgba(0,0,0,0.08);
                border-left: 5px solid #2196F3;
                flex: 1;
            }
            
            .breakdown-item h4 {
                color: #1976D2;
                margin-bottom: 8px;
            }
            
            .breakdown-item p {
                color: #666;
                font-size: 0.9rem;
                margin-bottom: 15px;
            }
            
            .breakdown-number {
                font-size: 2.5rem;
                font-weight: bold;
                color: #2196F3;
                margin-bottom: 10px;
            }
            
            .breakdown-icon {
                font-size: 1.5rem;
            }
            
            .breakdown-plus {
                font-size: 2rem;
                font-weight: bold;
                color: #2196F3;
            }
            
            /* Explanation Box */
            .explanation-box {
                background: linear-gradient(135deg, #fff3e0, #ffe0b2);
                padding: 25px;
                border-radius: 10px;
                border-left: 5px solid #ff9800;
            }
            
            .explanation-box h4 {
                color: #e65100;
                margin-bottom: 15px;
                font-size: 1.1rem;
            }
            
            .explanation-box p {
                color: #333;
                line-height: 1.6;
            }
            
            /* Footer */
            .report-footer {
                background: #1976D2;
                color: white;
                text-align: center;
                padding: 20px;
                font-size: 0.9rem;
            }
            
            /* Responsive Design */
            @media (max-width: 768px) {
                .container {
                    margin: 0;
                }
                
                .header-content {
                    flex-direction: column;
                    text-align: center;
                    gap: 20px;
                }
                
                .metrics-grid {
                    grid-template-columns: 1fr;
                }
                
                .charts-grid {
                    grid-template-columns: 1fr;
                }
                
                .cost-metrics-grid {
                    grid-template-columns: 1fr;
                }
                
                .scope-summary {
                    grid-template-columns: 1fr;
                }
                
                .scope-breakdown {
                    flex-direction: column;
                }
                
                .breakdown-plus {
                    transform: rotate(90deg);
                }
                
                .recommendations-table {
                    font-size: 0.75rem;
                }
                
                .recommendations-table th,
                .recommendations-table td {
                    padding: 8px 6px;
                }
            }
            
            /* Print Styles */
            @media print {
                body {
                    background: white;
                }
                
                .container {
                    box-shadow: none;
                }
                
                .metric-card:hover,
                .recommendations-table tr:hover {
                    transform: none;
                    background: inherit;
                }
            }
        </style>
        """
    
    def _get_javascript(self):
        """Retorna JavaScript para interactividad"""
        return """
        <script>
            // Animaciones y funcionalidad interactiva
            document.addEventListener('DOMContentLoaded', function() {
                // Animar contadores
                animateCounters();
                
                // Agregar efectos hover a las barras de riesgo
                addRiskBarEffects();
                
                // Tooltip para celdas truncadas
                addTooltips();
            });
            
            function animateCounters() {
                const counters = document.querySelectorAll('.metric-number, .large-number, .scope-number-large, .breakdown-number');
                
                counters.forEach(counter => {
                    const target = parseInt(counter.textContent.replace(/[^0-9]/g, ''));
                    if (isNaN(target)) return;
                    
                    let current = 0;
                    const increment = target / 50;
                    
                    const timer = setInterval(() => {
                        current += increment;
                        if (current >= target) {
                            counter.textContent = counter.textContent.replace(/[0-9,]+/, target.toLocaleString());
                            clearInterval(timer);
                        } else {
                            counter.textContent = counter.textContent.replace(/[0-9,]+/, Math.floor(current).toLocaleString());
                        }
                    }, 30);
                });
            }
            
            function addRiskBarEffects() {
                const riskBars = document.querySelectorAll('.risk-bar');
                
                riskBars.forEach(bar => {
                    bar.addEventListener('mouseenter', function() {
                        this.style.transform = 'scale(1.1)';
                        this.style.transition = 'transform 0.3s ease';
                    });
                    
                    bar.addEventListener('mouseleave', function() {
                        this.style.transform = 'scale(1)';
                    });
                });
            }
            
            function addTooltips() {
                const truncatedCells = document.querySelectorAll('[title]');
                
                truncatedCells.forEach(cell => {
                    cell.style.cursor = 'help';
                });
            }
            
            // Funcionalidad de impresión mejorada
            function printReport() {
                window.print();
            }
            
            // Smooth scroll para anclas
            document.querySelectorAll('a[href^="#"]').forEach(anchor => {
                anchor.addEventListener('click', function (e) {
                    e.preventDefault();
                    
                    const target = document.querySelector(this.getAttribute('href'));
                    if (target) {
                        target.scrollIntoView({
                            behavior: 'smooth',
                            block: 'start'
                        });
                    }
                });
            });
        </script>
        """
    
    def _generate_sample_data(self):
        """Genera datos de ejemplo si no hay CSV disponible"""
        import pandas as pd
        
        sample_data = {
            'Category': ['Security', 'Cost', 'Reliability', 'Security', 'Operational excellence'] * 60,
            'Business Impact': ['High', 'Medium', 'High', 'Medium', 'Low'] * 60,
            'Recommendation': ['Sample recommendation'] * 300,
            'Resource Name': ['sample-resource'] * 300,
            'Type': ['Virtual machine', 'Disk', 'Storage Account'] * 100
        }
        
        return pd.DataFrame(sample_data)
    
    def _generate_error_html(self, error_message):
        """Genera HTML de error"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Error - Report Generation</title>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 40px; text-align: center; background: #f8f9fa; }}
                .error-container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .error-title {{ color: #dc3545; margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <div class="error-container">
                <h1 class="error-title">Error Generating Report</h1>
                <p>An error occurred while generating the report:</p>
                <pre>{error_message}</pre>
                <p>Please try again or contact support if the problem persists.</p>
            </div>
        </body>
        </html>
        """

# Función de integración con Django
def generate_enhanced_html_report(report, csv_file_path=None):
    """
    Función principal para integrar con Django
    
    Usage:
        from .utils.enhanced_html_generator import generate_enhanced_html_report
        
        html_content = generate_enhanced_html_report(report, csv_file_path)
    """
    generator = EnhancedAzureHTMLReportGenerator()
    return generator.generate_enhanced_report(report, csv_file_path)