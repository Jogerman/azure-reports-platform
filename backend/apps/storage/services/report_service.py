# apps/reports/services/report_service.py
from django.template.loader import get_template
from django.conf import settings
import weasyprint
import tempfile
import os
from typing import Tuple
import logging

logger = logging.getLogger(__name__)

class ReportGenerator:
    """Generador de reportes PDF a partir de análisis de datos"""
    
    def __init__(self, report):
        self.report = report
        self.csv_file = report.csv_file
        self.analysis_data = report.csv_file.analysis_data
    
    def generate(self) -> Tuple[str, str]:
        """
        Generar reporte PDF y HTML
        Returns: (pdf_file_path, html_content)
        """
        try:
            # Generar contenido HTML
            html_content = self._generate_html()
            
            # Generar PDF desde HTML
            pdf_file_path = self._generate_pdf(html_content)
            
            return pdf_file_path, html_content
            
        except Exception as e:
            logger.error(f"Error generando reporte {self.report.id}: {e}")
            raise
    
    def _generate_html(self) -> str:
        """Generar contenido HTML del reporte"""
        template_name = f"reports/{self.report.report_type}_template.html"
        
        try:
            template = get_template(template_name)
        except:
            # Fallback a template base
            template = get_template("reports/base_template.html")
        
        context = {
            'report': self.report,
            'csv_file': self.csv_file,
            'analysis': self.analysis_data,
            'basic_stats': self.analysis_data.get('basic_stats', {}),
            'data_quality': self.analysis_data.get('data_quality', {}),
            'recommendations': self.analysis_data.get('recommendations', []),
            'cost_analysis': self.analysis_data.get('cost_analysis', {}),
            'security_analysis': self.analysis_data.get('security_analysis', {}),
            'categories': self.analysis_data.get('categories', {}),
        }
        
        return template.render(context)
    
    def _generate_pdf(self, html_content: str) -> str:
        """Generar PDF desde HTML"""
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            pdf_path = tmp_file.name
        
        try:
            # Configurar WeasyPrint
            base_url = settings.STATIC_URL
            html = weasyprint.HTML(string=html_content, base_url=base_url)
            
            # Generar PDF
            html.write_pdf(pdf_path)
            
            return pdf_path
            
        except Exception as e:
            # Limpiar archivo temporal en caso de error
            if os.path.exists(pdf_path):
                os.unlink(pdf_path)
            raise e

def generate_html_preview(report) -> str:
    """Generar preview HTML de un reporte"""
    generator = ReportGenerator(report)
    return generator._generate_html()
