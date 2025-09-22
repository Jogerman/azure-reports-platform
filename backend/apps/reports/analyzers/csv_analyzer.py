# backend/apps/reports/services/csv_analyzer.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from django.utils import timezone
import logging
import json
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class AzureAdvisorCSVAnalyzer:
    """
    Analizador especializado para archivos CSV de Azure Advisor
    Reemplaza los datos estáticos con análisis real de las recomendaciones
    """
    
    def __init__(self, csv_content: str):
        """
        Inicializar el analizador con el contenido del CSV
        
        Args:
            csv_content (str): Contenido del archivo CSV como string
        """
        self.csv_content = csv_content
        self.df = None
        self.analysis_results = {}
        
    def analyze(self) -> Dict[str, Any]:
        """
        Realizar análisis completo del CSV de Azure Advisor
        
        Returns:
            Dict con todas las métricas y análisis calculados
        """
        try:
            # Cargar CSV en DataFrame
            from io import StringIO
            self.df = pd.read_csv(StringIO(self.csv_content))
            
            logger.info(f"CSV cargado: {len(self.df)} filas, {len(self.df.columns)} columnas")
            
            # Limpiar datos
            self._clean_data()
            
            # Ejecutar todos los análisis
            self.analysis_results = {
                'basic_metrics': self._calculate_basic_metrics(),
                'category_analysis': self._analyze_by_category(),
                'impact_analysis': self._analyze_by_impact(),
                'resource_analysis': self._analyze_resources(),
                'cost_analysis': self._analyze_costs(),
                'time_analysis': self._calculate_working_hours(),
                'dashboard_metrics': self._generate_dashboard_metrics(),
                'charts_data': self._generate_charts_data(),
                'metadata': self._generate_metadata()
            }
            
            logger.info("Análisis completado exitosamente")
            return self.analysis_results
            
        except Exception as e:
            logger.error(f"Error en análisis CSV: {str(e)}")
            raise e
    
    def _clean_data(self):
        """Limpiar y preparar los datos"""
        # Eliminar filas vacías o sin categoría
        self.df = self.df.dropna(subset=['Category'])
        
        # Normalizar valores de Business Impact
        impact_mapping = {
            'High': 'High',
            'Medium': 'Medium', 
            'Low': 'Low',
            'high': 'High',
            'medium': 'Medium',
            'low': 'Low'
        }
        self.df['Business Impact'] = self.df['Business Impact'].map(impact_mapping).fillna('Medium')
        
        # Limpiar columnas de costos
        cost_columns = ['Potential Annual Cost Savings']
        for col in cost_columns:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
                
        logger.info(f"Datos limpiados: {len(self.df)} filas válidas")
    
    def _calculate_basic_metrics(self) -> Dict[str, Any]:
        """Calcular métricas básicas"""
        return {
            'total_recommendations': len(self.df),
            'total_columns': len(self.df.columns),
            'data_quality_score': self._calculate_data_quality_score(),
            'last_updated': timezone.now().isoformat()
        }
    
    def _analyze_by_category(self) -> Dict[str, Any]:
        """Análisis por categoría de Azure Advisor"""
        category_counts = self.df.groupby('Category').size().to_dict()
        
        # Calcular porcentajes
        total = sum(category_counts.values())
        category_percentages = {
            cat: round((count / total) * 100, 1) 
            for cat, count in category_counts.items()
        }
        
        return {
            'counts': category_counts,
            'percentages': category_percentages,
            'top_category': max(category_counts, key=category_counts.get),
            'distribution': self._generate_category_distribution(category_counts)
        }
    
    def _analyze_by_impact(self) -> Dict[str, Any]:
        """Análisis por impacto de negocio"""
        impact_counts = self.df.groupby('Business Impact').size().to_dict()
        
        return {
            'counts': impact_counts,
            'high_impact_percentage': round((impact_counts.get('High', 0) / len(self.df)) * 100, 1),
            'priority_score': self._calculate_priority_score(impact_counts)
        }
    
    def _analyze_resources(self) -> Dict[str, Any]:
        """Análisis de recursos Azure"""
        type_counts = self.df.groupby('Type').size().sort_values(ascending=False)
        
        # Top 10 tipos de recursos
        top_types = type_counts.head(10).to_dict()
        
        # Análisis de grupos de recursos
        resource_groups = self.df['Resource Group'].value_counts().head(10).to_dict()
        
        return {
            'top_resource_types': top_types,
            'total_resource_types': len(type_counts),
            'top_resource_groups': resource_groups,
            'resources_diversity_index': self._calculate_diversity_index(type_counts)
        }
    
    def _analyze_costs(self) -> Dict[str, Any]:
        """Análisis de costos y ahorros potenciales"""
        cost_column = 'Potential Annual Cost Savings'
        
        if cost_column in self.df.columns:
            cost_data = self.df[cost_column].dropna()
            
            if len(cost_data) > 0:
                total_annual_savings = cost_data.sum()
                monthly_savings = total_annual_savings / 12
                
                return {
                    'has_cost_data': True,
                    'recommendations_with_cost_data': len(cost_data),
                    'total_annual_savings': float(total_annual_savings),
                    'estimated_monthly_savings': float(monthly_savings),
                    'average_saving_per_recommendation': float(cost_data.mean()),
                    'cost_categories': self._analyze_cost_by_category()
                }
        
        # Si no hay datos de costo, estimamos basado en el número de recomendaciones
        estimated_annual_savings = len(self.df) * 150  # $150 por recomendación (conservador)
        
        return {
            'has_cost_data': False,
            'estimated_annual_savings': estimated_annual_savings,
            'estimated_monthly_savings': estimated_annual_savings / 12,
            'estimation_method': 'conservative_per_recommendation'
        }
    
    def _calculate_working_hours(self) -> Dict[str, Any]:
        """Calcular horas de trabajo estimadas"""
        hours_mapping = {
            'High': 2.0,    # 2 horas por recomendación de alto impacto
            'Medium': 1.0,  # 1 hora por recomendación de medio impacto  
            'Low': 0.5      # 30 minutos por recomendación de bajo impacto
        }
        
        total_hours = 0
        hours_by_impact = {}
        
        for impact, group in self.df.groupby('Business Impact'):
            hours = len(group) * hours_mapping.get(impact, 1.0)
            hours_by_impact[impact] = hours
            total_hours += hours
        
        return {
            'total_working_hours': round(total_hours, 1),
            'hours_by_impact': hours_by_impact,
            'estimated_days': round(total_hours / 8, 1),  # 8 horas por día laboral
            'estimated_weeks': round(total_hours / 40, 1)  # 40 horas por semana
        }
    
    def _generate_dashboard_metrics(self) -> Dict[str, Any]:
        """Generar métricas específicas para el dashboard"""
        category_analysis = self.analysis_results.get('category_analysis', self._analyze_by_category())
        impact_analysis = self.analysis_results.get('impact_analysis', self._analyze_by_impact())
        cost_analysis = self.analysis_results.get('cost_analysis', self._analyze_costs())
        time_analysis = self.analysis_results.get('time_analysis', self._calculate_working_hours())
        
        return {
            # Métricas principales para cards del dashboard
            'total_actions': len(self.df),
            'estimated_monthly_optimization': cost_analysis.get('estimated_monthly_savings', 0),
            'working_hours': time_analysis.get('total_working_hours', 0),
            'high_impact_count': impact_analysis['counts'].get('High', 0),
            
            # Métricas por categoría (para los gráficos de secciones)
            'cost_optimization': {
                'actions': category_analysis['counts'].get('Cost', 0),
                'estimated_monthly_savings': self._calculate_category_savings('Cost'),
                'working_hours': self._calculate_category_hours('Cost')
            },
            'reliability_optimization': {
                'actions': category_analysis['counts'].get('Reliability', 0),
                'monthly_investment': self._estimate_implementation_cost('Reliability'),
                'working_hours': self._calculate_category_hours('Reliability')
            },
            'security_optimization': {
                'actions': category_analysis['counts'].get('Security', 0),
                'monthly_investment': self._estimate_implementation_cost('Security'),
                'working_hours': self._calculate_category_hours('Security')
            },
            'operational_optimization': {
                'actions': category_analysis['counts'].get('Operational excellence', 0),
                'monthly_investment': self._estimate_implementation_cost('Operational excellence'),
                'working_hours': self._calculate_category_hours('Operational excellence')
            }
        }
    
    def _generate_charts_data(self) -> Dict[str, Any]:
        """Generar datos para gráficos del frontend"""
        return {
            'category_pie_chart': self._generate_category_pie_data(),
            'impact_bar_chart': self._generate_impact_bar_data(),
            'resource_types_chart': self._generate_resource_types_data(),
            'timeline_chart': self._generate_timeline_data(),
            'cost_savings_chart': self._generate_cost_savings_data()
        }
    
    def _generate_metadata(self) -> Dict[str, Any]:
        """Generar metadata del análisis"""
        return {
            'analysis_date': timezone.now().isoformat(),
            'csv_filename': 'azure_advisor_recommendations',
            'total_rows_processed': len(self.df),
            'columns_analyzed': list(self.df.columns),
            'analysis_version': '1.0',
            'quality_checks_passed': self._run_quality_checks()
        }
    
    # Métodos auxiliares
    def _calculate_data_quality_score(self) -> float:
        """Calcular puntaje de calidad de datos"""
        required_columns = ['Category', 'Business Impact', 'Recommendation']
        present_columns = sum(1 for col in required_columns if col in self.df.columns)
        completeness = self.df[required_columns].notna().all(axis=1).mean()
        
        return round((present_columns / len(required_columns)) * completeness * 100, 1)
    
    def _calculate_priority_score(self, impact_counts: Dict) -> float:
        """Calcular puntaje de prioridad basado en impacto"""
        weights = {'High': 3, 'Medium': 2, 'Low': 1}
        total_weighted = sum(count * weights.get(impact, 1) for impact, count in impact_counts.items())
        total_items = sum(impact_counts.values())
        
        return round(total_weighted / total_items if total_items > 0 else 0, 2)
    
    def _calculate_diversity_index(self, type_counts: pd.Series) -> float:
        """Calcular índice de diversidad de recursos"""
        total = type_counts.sum()
        if total == 0:
            return 0
        
        # Índice de Shannon
        proportions = type_counts / total
        shannon_index = -(proportions * np.log(proportions)).sum()
        
        return round(shannon_index, 2)
    
    def _analyze_cost_by_category(self) -> Dict[str, float]:
        """Analizar costos por categoría"""
        cost_column = 'Potential Annual Cost Savings'
        if cost_column not in self.df.columns:
            return {}
        
        category_costs = self.df.groupby('Category')[cost_column].sum().to_dict()
        return {cat: float(cost) for cat, cost in category_costs.items() if not pd.isna(cost)}
    
    def _calculate_category_savings(self, category: str) -> float:
        """Calcular ahorros estimados por categoría"""
        category_df = self.df[self.df['Category'] == category]
        if len(category_df) == 0:
            return 0
        
        # Estimación conservadora basada en el número de recomendaciones de costo
        if category == 'Cost':
            return len(category_df) * 200  # $200 por recomendación de costo
        
        return len(category_df) * 100  # $100 para otras categorías
    
    def _calculate_category_hours(self, category: str) -> float:
        """Calcular horas de trabajo por categoría"""
        category_df = self.df[self.df['Category'] == category]
        if len(category_df) == 0:
            return 0
        
        hours_mapping = {'High': 2.0, 'Medium': 1.0, 'Low': 0.5}
        total_hours = 0
        
        for _, row in category_df.iterrows():
            impact = row.get('Business Impact', 'Medium')
            total_hours += hours_mapping.get(impact, 1.0)
        
        return round(total_hours, 1)
    
    def _estimate_implementation_cost(self, category: str) -> float:
        """Estimar costo de implementación por categoría"""
        hours = self._calculate_category_hours(category)
        hourly_rate = 75  # $75 por hora para servicios especializados de Azure
        return round(hours * hourly_rate, 0)
    
    def _generate_category_pie_data(self) -> List[Dict]:
        """Datos para gráfico circular de categorías"""
        category_counts = self.df.groupby('Category').size()
        
        return [
            {'name': category, 'value': int(count)}
            for category, count in category_counts.items()
        ]
    
    def _generate_impact_bar_data(self) -> List[Dict]:
        """Datos para gráfico de barras de impacto"""
        impact_counts = self.df.groupby('Business Impact').size()
        
        return [
            {'impact': impact, 'count': int(count)}
            for impact, count in impact_counts.items()
        ]
    
    def _generate_resource_types_data(self) -> List[Dict]:
        """Datos para gráfico de tipos de recursos"""
        type_counts = self.df.groupby('Type').size().sort_values(ascending=False).head(10)
        
        return [
            {'type': resource_type, 'count': int(count)}
            for resource_type, count in type_counts.items()
        ]
    
    def _generate_timeline_data(self) -> List[Dict]:
        """Generar datos de timeline (simulado para demostración)"""
        # Simular progreso mensual basado en los datos
        months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun']
        total = len(self.df)
        
        return [
            {
                'month': month,
                'implemented': min(int(total * (i + 1) / len(months) * 0.7), total),
                'pending': max(total - int(total * (i + 1) / len(months) * 0.7), 0)
            }
            for i, month in enumerate(months)
        ]
    
    def _generate_cost_savings_data(self) -> Dict[str, Any]:
        """Generar datos de ahorro de costos"""
        cost_analysis = self._analyze_costs()
        
        return {
            'monthly_savings': cost_analysis.get('estimated_monthly_savings', 0),
            'annual_savings': cost_analysis.get('estimated_annual_savings', 0),
            'implementation_cost': self._calculate_total_implementation_cost(),
            'roi_months': self._calculate_roi_months(cost_analysis)
        }
    
    def _calculate_total_implementation_cost(self) -> float:
        """Calcular costo total de implementación"""
        time_analysis = self._calculate_working_hours()
        hourly_rate = 75
        
        return round(time_analysis['total_working_hours'] * hourly_rate, 0)
    
    def _calculate_roi_months(self, cost_analysis: Dict) -> float:
        """Calcular meses para retorno de inversión"""
        monthly_savings = cost_analysis.get('estimated_monthly_savings', 0)
        implementation_cost = self._calculate_total_implementation_cost()
        
        if monthly_savings > 0:
            return round(implementation_cost / monthly_savings, 1)
        
        return 0
    
    def _generate_category_distribution(self, category_counts: Dict) -> List[Dict]:
        """Generar distribución de categorías para gráficos"""
        colors = {
            'Cost': '#4CAF50',
            'Reliability': '#2196F3',
            'Security': '#FF9800',
            'Operational excellence': '#9C27B0',
            'Performance': '#F44336'
        }
        
        total = sum(category_counts.values())
        
        return [
            {
                'category': category,
                'count': count,
                'percentage': round((count / total) * 100, 1),
                'color': colors.get(category, '#757575')
            }
            for category, count in category_counts.items()
        ]
    
    def _run_quality_checks(self) -> List[str]:
        """Ejecutar verificaciones de calidad de datos"""
        checks_passed = []
        
        # Verificar columnas requeridas
        required_columns = ['Category', 'Business Impact', 'Recommendation']
        if all(col in self.df.columns for col in required_columns):
            checks_passed.append('required_columns_present')
        
        # Verificar completitud de datos
        completeness = self.df[required_columns].notna().all(axis=1).mean()
        if completeness > 0.9:
            checks_passed.append('high_data_completeness')
        
        # Verificar diversidad de categorías
        if len(self.df['Category'].unique()) >= 3:
            checks_passed.append('category_diversity')
        
        return checks_passed


def analyze_csv_content(csv_content: str) -> Dict[str, Any]:
    """
    Función principal para analizar contenido CSV
    
    Args:
        csv_content (str): Contenido del archivo CSV
        
    Returns:
        Dict con análisis completo
    """
    analyzer = AzureAdvisorCSVAnalyzer(csv_content)
    return analyzer.analyze()