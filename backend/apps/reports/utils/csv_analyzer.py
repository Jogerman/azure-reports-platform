# backend/apps/reports/utils/csv_analyzer.py
import pandas as pd
import logging
from typing import Dict, Any
from decimal import Decimal, InvalidOperation
import re

logger = logging.getLogger(__name__)

class AzureCSVAnalyzer:
    """
    Analizador específico para CSV de Azure Advisor
    Mapea las columnas de tu CSV a las variables del nuevo template
    """
    
    def __init__(self):
        self.category_mapping = {
            'Cost': 'cost_optimization',
            'Security': 'security', 
            'Reliability': 'reliability',
            'OperationalExcellence': 'operational_excellence',
            'Performance': 'performance'
        }
        
        self.impact_mapping = {
            'High': 'high',
            'Medium': 'medium', 
            'Low': 'low'
        }

    def analyze_csv_for_template(self, csv_file_path: str) -> Dict[str, Any]:
        """
        Analiza el CSV y devuelve datos formateados para el nuevo template
        
        Tu CSV tiene estas columnas:
        - Category: String  
        - Business Impact: String
        - Recommendation: String
        - Subscription ID: String
        - Subscription Name: String
        - Resource Group: String
        - Resource Name: String
        - Type: String
        - Updated Date: Date
        - Potential benefits: String
        - Potential Annual Cost Savings: String
        - Potential Cost Savings Currency: String
        - Retirement date: String
        - Retiring feature: String
        """
        try:
            # Leer CSV
            df = pd.read_csv(csv_file_path)
            logger.info(f"CSV cargado: {len(df)} filas")
            
            # Análisis básico
            total_recommendations = len(df)
            
            # 1. ANÁLISIS POR CATEGORÍA
            category_analysis = self._analyze_categories(df)
            
            # 2. ANÁLISIS POR IMPACTO DE NEGOCIO  
            impact_analysis = self._analyze_business_impact(df)
            
            # 3. ANÁLISIS DE COSTOS
            cost_analysis = self._analyze_cost_savings(df)
            
            # 4. ANÁLISIS DE RECURSOS
            resource_analysis = self._analyze_resources(df)
            
            # 5. CALCULAR MÉTRICAS PARA EL TEMPLATE
            template_data = self._calculate_template_metrics(
                total_recommendations,
                category_analysis,
                impact_analysis, 
                cost_analysis,
                resource_analysis
            )
            
            logger.info(f"Análisis completado: {template_data['total_recommendations']} recomendaciones")
            return template_data
            
        except Exception as e:
            logger.error(f"Error analizando CSV: {e}")
            return self._get_default_template_data()

    def _analyze_categories(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analizar columna 'Category'"""
        try:
            if 'Category' not in df.columns:
                logger.warning("Columna 'Category' no encontrada")
                return {}
                
            category_counts = df['Category'].value_counts().to_dict()
            
            # Mapear a nombres estándar
            mapped_categories = {}
            for category, count in category_counts.items():
                standard_name = self.category_mapping.get(category, category.lower().replace(' ', '_'))
                mapped_categories[standard_name] = count
            
            logger.info(f"Categorías encontradas: {mapped_categories}")
            return mapped_categories
            
        except Exception as e:
            logger.error(f"Error analizando categorías: {e}")
            return {}

    def _analyze_business_impact(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analizar columna 'Business Impact'"""
        try:
            if 'Business Impact' not in df.columns:
                logger.warning("Columna 'Business Impact' no encontrada")
                return {}
                
            impact_counts = df['Business Impact'].value_counts().to_dict()
            
            # Calcular métricas específicas
            high_priority = impact_counts.get('High', 0)
            medium_priority = impact_counts.get('Medium', 0)
            low_priority = impact_counts.get('Low', 0)
            
            # Calcular porcentajes
            total = high_priority + medium_priority + low_priority
            if total > 0:
                high_percentage = (high_priority / total) * 100
                medium_percentage = (medium_priority / total) * 100
                low_percentage = (low_priority / total) * 100
            else:
                high_percentage = medium_percentage = low_percentage = 0
            
            return {
                'high_priority': high_priority,
                'medium_priority': medium_priority,
                'low_priority': low_priority,
                'high_percentage': round(high_percentage, 1),
                'medium_percentage': round(medium_percentage, 1),
                'low_percentage': round(low_percentage, 1)
            }
            
        except Exception as e:
            logger.error(f"Error analizando impacto de negocio: {e}")
            return {}

    def _analyze_cost_savings(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analizar columna 'Potential Annual Cost Savings'"""
        try:
            if 'Potential Annual Cost Savings' not in df.columns:
                logger.warning("Columna de ahorros no encontrada")
                return {'total_annual_savings': 0, 'total_monthly_savings': 0}
            
            # Limpiar y convertir valores de ahorro
            total_annual_savings = 0
            valid_savings = 0
            
            for savings_str in df['Potential Annual Cost Savings'].fillna('0'):
                try:
                    # Limpiar string: remover símbolos de moneda, comas, etc.
                    cleaned = re.sub(r'[^\d.-]', '', str(savings_str))
                    if cleaned:
                        savings_value = float(cleaned)
                        total_annual_savings += savings_value
                        valid_savings += 1
                except (ValueError, InvalidOperation):
                    continue
            
            # Calcular ahorros mensuales
            total_monthly_savings = total_annual_savings / 12
            
            logger.info(f"Ahorros calculados: ${total_annual_savings:,.2f} anuales, ${total_monthly_savings:,.2f} mensuales")
            
            return {
                'total_annual_savings': round(total_annual_savings, 2),
                'total_monthly_savings': round(total_monthly_savings, 2),
                'rows_with_savings': valid_savings,
                'currency': self._detect_currency(df)
            }
            
        except Exception as e:
            logger.error(f"Error analizando ahorros de costo: {e}")
            return {'total_annual_savings': 0, 'total_monthly_savings': 0}

    def _analyze_resources(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analizar recursos (Resource Name, Type, Resource Group)"""
        try:
            resource_data = {}
            
            # Recursos únicos
            if 'Resource Name' in df.columns:
                unique_resources = df['Resource Name'].nunique()
                resource_data['unique_resources'] = unique_resources
            
            # Tipos de recursos
            if 'Type' in df.columns:
                resource_types = df['Type'].value_counts().to_dict()
                resource_data['resource_types'] = resource_types
                resource_data['unique_types'] = len(resource_types)
            
            # Grupos de recursos
            if 'Resource Group' in df.columns:
                resource_groups = df['Resource Group'].nunique()
                resource_data['unique_resource_groups'] = resource_groups
            
            logger.info(f"Análisis de recursos: {resource_data.get('unique_resources', 0)} recursos únicos")
            return resource_data
            
        except Exception as e:
            logger.error(f"Error analizando recursos: {e}")
            return {}

    def _detect_currency(self, df: pd.DataFrame) -> str:
        """Detectar moneda desde la columna Currency"""
        try:
            if 'Potential Cost Savings Currency' in df.columns:
                currencies = df['Potential Cost Savings Currency'].value_counts()
                if len(currencies) > 0:
                    return currencies.index[0]  # Moneda más común
            return 'USD'  # Default
        except:
            return 'USD'

    def _calculate_template_metrics(self, total_recs: int, categories: Dict, impacts: Dict, 
                                  costs: Dict, resources: Dict) -> Dict[str, Any]:
        """
        Calcular todas las métricas necesarias para el nuevo template profesional
        """
        
        # Extraer datos de categorías
        cost_actions = categories.get('cost_optimization', 0)
        security_actions = categories.get('security', 0) 
        reliability_actions = categories.get('reliability', 0)
        opex_actions = categories.get('operational_excellence', 0)
        performance_actions = categories.get('performance', 0)
        
        # Calcular acciones de alta prioridad por categoría (estimación)
        high_priority_total = impacts.get('high_priority', 0)
        high_priority_ratio = high_priority_total / total_recs if total_recs > 0 else 0
        
        # Calcular Azure Advisor Score (basado en distribución de impacto)
        advisor_score = self._calculate_advisor_score(impacts, total_recs)
        
        # Calcular working hours (estimación: 0.5h por acción security/reliability, 2h por cost)
        reliability_hours = reliability_actions * 0.5
        security_hours = security_actions * 0.4  
        opex_hours = opex_actions * 0.5
        total_working_hours = reliability_hours + security_hours + opex_hours
        
        # Calcular investments (estimación basada en working hours * $50/hora)
        hourly_rate = 50
        reliability_investment = reliability_hours * hourly_rate
        security_investment = security_hours * hourly_rate  
        opex_investment = opex_hours * hourly_rate
        total_investment = reliability_investment + security_investment + opex_investment
        
        # Determinar acciones "in scope" (estimación: 90% del total)
        actions_in_scope = int(total_recs * 0.9)
        
        # Acciones sin incremento en billing (estimación: 85% de las in scope)
        remediation_actions = int(actions_in_scope * 0.85)
        
        return {
            # Métricas principales del dashboard
            'total_recommendations': total_recs,
            'actions_in_scope': actions_in_scope,
            'remediation_actions': remediation_actions,
            'azure_advisor_score': advisor_score,
            
            # Métricas por categoría
            'cost_actions': cost_actions,
            'cost_high_priority': int(cost_actions * high_priority_ratio),
            'security_actions': security_actions,
            'security_high_priority': int(security_actions * high_priority_ratio),
            'reliability_actions': reliability_actions, 
            'reliability_high_priority': int(reliability_actions * high_priority_ratio),
            'opex_actions': opex_actions,
            'opex_high_priority': int(opex_actions * high_priority_ratio),
            'performance_actions': performance_actions,
            'performance_high_priority': int(performance_actions * high_priority_ratio),
            
            # Datos para tabla de conclusiones
            'monthly_savings': f"{costs.get('total_monthly_savings', 0):,.0f}",
            'advisor_score_percentage': advisor_score,
            'reliability_total': reliability_actions,
            'reliability_investment': f"{reliability_investment:,.0f}",
            'reliability_hours': f"{reliability_hours:.1f}",
            'security_total': security_actions,
            'security_investment': f"{security_investment:,.0f}",
            'security_hours': f"{security_hours:.1f}",
            'opex_total': opex_actions,
            'opex_investment': f"{opex_investment:,.0f}",
            'opex_hours': f"{opex_hours:.1f}",
            'total_actions_summary': total_recs,
            'total_investment': f"{total_investment:,.0f}",
            'total_hours': f"{total_working_hours:.1f}",
            
            # Datos adicionales
            'currency': costs.get('currency', 'USD'),
            'unique_resources': resources.get('unique_resources', 0),
            'resource_types': resources.get('unique_types', 0),
            
            # Análisis de impacto 
            'high_impact_percentage': impacts.get('high_percentage', 0),
            'medium_impact_percentage': impacts.get('medium_percentage', 0),
            'low_impact_percentage': impacts.get('low_percentage', 0)
        }

    def _calculate_advisor_score(self, impacts: Dict, total: int) -> int:
        """
        Calcular Azure Advisor Score basado en distribución de impacto
        Score más alto = menos acciones de alta prioridad pendientes
        """
        if total == 0:
            return 50  # Score neutral
            
        high_ratio = impacts.get('high_priority', 0) / total
        medium_ratio = impacts.get('medium_priority', 0) / total
        low_ratio = impacts.get('low_priority', 0) / total
        
        # Fórmula: Score más bajo si hay muchas acciones de alta prioridad
        # 100 = perfecto (sin high priority), 0 = muy malo (todo high priority)
        base_score = 100
        high_penalty = high_ratio * 60  # Penalizar high priority
        medium_penalty = medium_ratio * 20  # Penalizar medium priority
        
        final_score = base_score - high_penalty - medium_penalty
        return max(0, min(100, int(final_score)))

    def _get_default_template_data(self) -> Dict[str, Any]:
        """Datos por defecto si falla el análisis"""
        return {
            'total_recommendations': 0,
            'actions_in_scope': 0, 
            'remediation_actions': 0,
            'azure_advisor_score': 50,
            'cost_actions': 0,
            'cost_high_priority': 0,
            'security_actions': 0,
            'security_high_priority': 0,
            'reliability_actions': 0,
            'reliability_high_priority': 0,
            'opex_actions': 0,
            'opex_high_priority': 0,
            'monthly_savings': '0',
            'advisor_score_percentage': 50,
            'reliability_total': 0,
            'reliability_investment': '0',
            'reliability_hours': '0.0',
            'security_total': 0,
            'security_investment': '0', 
            'security_hours': '0.0',
            'opex_total': 0,
            'opex_investment': '0',
            'opex_hours': '0.0',
            'total_actions_summary': 0,
            'total_investment': '0',
            'total_hours': '0.0'
        }