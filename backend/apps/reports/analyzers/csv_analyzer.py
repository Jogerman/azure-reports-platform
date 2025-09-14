# apps/reports/analyzers/csv_analyzer.py - Migrado y mejorado desde tu código
import pandas as pd
import numpy as np
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Dict, Any, List 
import logging
import re
from .base_analyzer import BaseAnalyzer

logger = logging.getLogger(__name__)

class EnhancedCSVAnalyzer(BaseAnalyzer):
    """
    Analizador mejorado para archivos CSV - Migrado desde código existente
    Incluye toda la funcionalidad de tu DebugAzureAnalyzer y más
    """
    
    def __init__(self, csv_data: pd.DataFrame):
        super().__init__(csv_data)
        logger.info(f"Iniciando análisis de {len(self.df)} filas y {len(self.df.columns)} columnas")
    
    def analyze(self) -> Dict[str, Any]:
        """Realizar análisis completo y detallado"""
        try:
            logger.info("Iniciando análisis completo")
            
            # Limpiar datos de forma segura
            self._safe_clean_data()
            
            # Realizar todos los análisis
            self.insights = {
                'basic_stats': self._get_basic_stats(),
                'data_quality': self._assess_data_quality(),
                'column_analysis': self._analyze_columns(),
                'categories': self._analyze_categories(),
                'business_impact': self._analyze_business_impact(),
                'resource_types': self._analyze_resource_types(),
                'cost_analysis': self._analyze_cost_optimization(),
                'security_analysis': self._analyze_security_recommendations(),
                'reliability_analysis': self._analyze_reliability_recommendations(),
                'temporal_analysis': self._analyze_temporal_patterns(),
                'resource_groups_analysis': self._analyze_resource_groups(),
                'top_recommendations': self._analyze_top_recommendations(),
                'patterns': self._find_patterns(),
                'recommendations': self._generate_recommendations(),
                'analysis_completed': True,
                'analysis_timestamp': datetime.now().isoformat(),
            }
            
            logger.info("Análisis completado exitosamente")
            return self.insights
            
        except Exception as e:
            logger.error(f"Error en análisis: {str(e)}")
            return {
                'error': str(e),
                'analysis_completed': False,
                'basic_stats': self._get_basic_stats() if not self.df.empty else {},
            }
    
    def _safe_clean_data(self):
        """Limpiar datos de forma super segura con debugging"""
        try:
            logger.info("Iniciando limpieza de datos")
            
            # Identificar y limpiar columnas problemáticas
            for col in self.df.columns:
                logger.debug(f"Procesando columna '{col}'")
                
                # Limpiar espacios en blanco
                if self.df[col].dtype == 'object':
                    self.df[col] = self.df[col].astype(str).str.strip()
                    
                # Convertir valores vacíos a NaN
                self.df[col] = self.df[col].replace(['', 'null', 'NULL', 'None'], np.nan)
            
            logger.info("Limpieza de datos completada")
            
        except Exception as e:
            logger.warning(f"Error en limpieza de datos: {e}")
    
    def _assess_data_quality(self) -> Dict[str, Any]:
        """Evaluar la calidad de los datos"""
        total_cells = self.df.size
        null_cells = self.df.isnull().sum().sum()
        
        return {
            'completeness_score': round(((total_cells - null_cells) / total_cells) * 100, 2),
            'total_null_values': int(null_cells),
            'duplicate_rows': int(self.df.duplicated().sum()),
            'consistency_issues': self._check_consistency(),
            'data_types_summary': self._analyze_data_types(),
        }
    
    def _analyze_columns(self) -> Dict[str, Any]:
        """Análisis detallado por columna"""
        column_info = {}
        for col in self.df.columns:
            try:
                column_info[col] = {
                    'type': str(self.df[col].dtype),
                    'null_count': int(self.df[col].isnull().sum()),
                    'null_percentage': round((self.df[col].isnull().sum() / len(self.df)) * 100, 2),
                    'unique_count': int(self.df[col].nunique()),
                    'unique_percentage': round((self.df[col].nunique() / len(self.df)) * 100, 2),
                    'sample_values': self.df[col].dropna().head(5).astype(str).tolist(),
                }
                
                # Análisis específico por tipo
                if self.df[col].dtype in ['int64', 'float64']:
                    column_info[col].update(self._analyze_numeric_column(col))
                elif self.df[col].dtype == 'object':
                    column_info[col].update(self._analyze_text_column(col))
                    
            except Exception as e:
                logger.warning(f"Error analizando columna {col}: {e}")
                column_info[col] = {'error': str(e)}
        
        return column_info
    
    def _analyze_numeric_column(self, col: str) -> Dict[str, Any]:
        """Análisis específico para columnas numéricas"""
        try:
            series = self.df[col].dropna()
            return {
                'min_value': float(series.min()),
                'max_value': float(series.max()),
                'mean_value': float(series.mean()),
                'median_value': float(series.median()),
                'std_value': float(series.std()) if len(series) > 1 else 0,
                'zero_values': int((series == 0).sum()),
                'negative_values': int((series < 0).sum()),
            }
        except Exception as e:
            return {'numeric_analysis_error': str(e)}
    
    def _analyze_text_column(self, col: str) -> Dict[str, Any]:
        """Análisis específico para columnas de texto"""
        try:
            series = self.df[col].dropna().astype(str)
            return {
                'avg_length': round(series.str.len().mean(), 2),
                'min_length': int(series.str.len().min()),
                'max_length': int(series.str.len().max()),
                'most_common': series.value_counts().head(5).to_dict(),
                'contains_urls': int(series.str.contains(r'http[s]?://', regex=True, na=False).sum()),
                'contains_emails': int(series.str.contains(r'\S+@\S+', regex=True, na=False).sum()),
            }
        except Exception as e:
            return {'text_analysis_error': str(e)}
    
    def _check_consistency(self) -> List[str]:
        """Verificar consistencia de datos"""
        issues = []
        
        try:
            # Verificar formatos inconsistentes en columnas de texto
            text_cols = self.df.select_dtypes(include=['object']).columns
            for col in text_cols:
                if col in self.df.columns:
                    unique_formats = self.df[col].astype(str).str.len().nunique()
                    if unique_formats > len(self.df) * 0.8:
                        issues.append(f"Posibles formatos inconsistentes en columna '{col}'")
            
            # Verificar valores atípicos en columnas numéricas
            numeric_cols = self.df.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                if col in self.df.columns:
                    Q1 = self.df[col].quantile(0.25)
                    Q3 = self.df[col].quantile(0.75)
                    IQR = Q3 - Q1
                    outliers = self.df[(self.df[col] < (Q1 - 1.5 * IQR)) | 
                                      (self.df[col] > (Q3 + 1.5 * IQR))][col].count()
                    if outliers > 0:
                        issues.append(f"Se encontraron {outliers} valores atípicos en '{col}'")
        
        except Exception as e:
            logger.warning(f"Error verificando consistencia: {e}")
            issues.append(f"Error en verificación: {str(e)}")
        
        return issues
    
    def _analyze_data_types(self) -> Dict[str, int]:
        """Resumen de tipos de datos"""
        type_counts = defaultdict(int)
        for dtype in self.df.dtypes:
            type_counts[str(dtype)] += 1
        return dict(type_counts)
    
    # ===== MÉTODOS MIGRADOS DESDE TU CÓDIGO ORIGINAL =====
    
    def _analyze_categories(self) -> Dict[str, Any]:
        """Análisis por categorías - Migrado desde tu código"""
        if 'Category' not in self.df.columns:
            return {}
        
        try:
            categories = self.df['Category'].value_counts()
            return {
                'total_categories': len(categories),
                'category_distribution': categories.to_dict(),
                'top_5_categories': categories.head().to_dict(),
                'categories_with_single_item': len(categories[categories == 1])
            }
        except Exception as e:
            logger.warning(f"Error en análisis de categorías: {e}")
            return {}
    
    def _analyze_business_impact(self) -> Dict[str, Any]:
        """Análisis de impacto de negocio - Migrado desde tu código"""
        if 'Impact' not in self.df.columns:
            return {}
        
        try:
            impact_counts = self.df['Impact'].value_counts()
            return {
                'impact_distribution': impact_counts.to_dict(),
                'high_impact_count': impact_counts.get('High', 0),
                'medium_impact_count': impact_counts.get('Medium', 0),
                'low_impact_count': impact_counts.get('Low', 0),
            }
        except Exception as e:
            logger.warning(f"Error en análisis de impacto: {e}")
            return {}
    
    def _analyze_resource_types(self) -> Dict[str, Any]:
        """Análisis de tipos de recursos - Migrado desde tu código"""
        resource_type_cols = [col for col in self.df.columns if 'resource' in col.lower() or 'type' in col.lower()]
        
        if not resource_type_cols:
            return {}
        
        analysis = {}
        for col in resource_type_cols:
            try:
                value_counts = self.df[col].value_counts()
                analysis[col] = {
                    'unique_types': len(value_counts),
                    'top_10_types': value_counts.head(10).to_dict(),
                    'distribution': value_counts.to_dict()
                }
            except Exception as e:
                logger.warning(f"Error analizando {col}: {e}")
        
        return analysis
    
    def _analyze_cost_optimization(self) -> Dict[str, Any]:
        """Análisis de optimización de costos - Migrado desde tu código"""
        cost_cols = [col for col in self.df.columns if any(keyword in col.lower() 
                    for keyword in ['cost', 'saving', 'price', 'money', 'dollar'])]
        
        if not cost_cols:
            return {}
        
        try:
            analysis = {}
            for col in cost_cols:
                if self.df[col].dtype in ['int64', 'float64']:
                    analysis[col] = {
                        'total_savings': float(self.df[col].sum()),
                        'average_savings': float(self.df[col].mean()),
                        'max_savings': float(self.df[col].max()),
                        'min_savings': float(self.df[col].min()),
                    }
            
            return analysis
        except Exception as e:
            logger.warning(f"Error en análisis de costos: {e}")
            return {}
    
    def _analyze_security_recommendations(self) -> Dict[str, Any]:
        """Análisis de recomendaciones de seguridad - Migrado desde tu código"""
        security_keywords = ['security', 'secure', 'auth', 'encryption', 'ssl', 'tls', 'firewall']
        
        try:
            security_recommendations = self.df[
                self.df.apply(lambda row: any(keyword in str(row).lower() 
                             for keyword in security_keywords), axis=1)
            ]
            
            return {
                'total_security_recommendations': len(security_recommendations),
                'security_percentage': round((len(security_recommendations) / len(self.df)) * 100, 2),
                'security_categories': self._get_security_categories(security_recommendations),
            }
        except Exception as e:
            logger.warning(f"Error en análisis de seguridad: {e}")
            return {}
    
    def _get_security_categories(self, security_df: pd.DataFrame) -> Dict[str, int]:
        """Categorizar recomendaciones de seguridad"""
        categories = {
            'authentication': 0,
            'encryption': 0,
            'network': 0,
            'access_control': 0,
            'other': 0
        }
        
        for _, row in security_df.iterrows():
            row_text = str(row).lower()
            if any(keyword in row_text for keyword in ['auth', 'login', 'password']):
                categories['authentication'] += 1
            elif any(keyword in row_text for keyword in ['encrypt', 'ssl', 'tls']):
                categories['encryption'] += 1
            elif any(keyword in row_text for keyword in ['network', 'firewall', 'port']):
                categories['network'] += 1
            elif any(keyword in row_text for keyword in ['access', 'permission', 'role']):
                categories['access_control'] += 1
            else:
                categories['other'] += 1
        
        return categories
    
    def _analyze_reliability_recommendations(self) -> Dict[str, Any]:
        """Análisis de recomendaciones de confiabilidad - Migrado desde tu código"""
        reliability_keywords = ['backup', 'recovery', 'redundancy', 'availability', 'disaster']
        
        try:
            reliability_recommendations = self.df[
                self.df.apply(lambda row: any(keyword in str(row).lower() 
                             for keyword in reliability_keywords), axis=1)
            ]
            
            return {
                'total_reliability_recommendations': len(reliability_recommendations),
                'reliability_percentage': round((len(reliability_recommendations) / len(self.df)) * 100, 2),
            }
        except Exception as e:
            logger.warning(f"Error en análisis de confiabilidad: {e}")
            return {}
    
    def _analyze_temporal_patterns(self) -> Dict[str, Any]:
        """Análisis de patrones temporales - Migrado desde tu código"""
        date_cols = []
        
        # Buscar columnas que podrían contener fechas
        for col in self.df.columns:
            if any(keyword in col.lower() for keyword in ['date', 'time', 'created', 'updated']):
                date_cols.append(col)
        
        if not date_cols:
            return {}
        
        try:
            analysis = {}
            for col in date_cols:
                try:
                    # Intentar convertir a datetime
                    dates = pd.to_datetime(self.df[col], errors='coerce')
                    dates_clean = dates.dropna()
                    
                    if len(dates_clean) > 0:
                        analysis[col] = {
                            'date_range': {
                                'earliest': dates_clean.min().isoformat(),
                                'latest': dates_clean.max().isoformat(),
                            },
                            'total_valid_dates': len(dates_clean),
                            'monthly_distribution': dates_clean.dt.to_period('M').value_counts().to_dict(),
                        }
                except Exception as e:
                    logger.warning(f"Error procesando fecha en {col}: {e}")
            
            return analysis
        except Exception as e:
            logger.warning(f"Error en análisis temporal: {e}")
            return {}
    
    def _analyze_resource_groups(self) -> Dict[str, Any]:
        """Análisis por grupos de recursos - Migrado desde tu código"""
        group_cols = [col for col in self.df.columns if 'group' in col.lower()]
        
        if not group_cols:
            return {}
        
        try:
            analysis = {}
            for col in group_cols:
                groups = self.df[col].value_counts()
                analysis[col] = {
                    'total_groups': len(groups),
                    'top_10_groups': groups.head(10).to_dict(),
                    'groups_with_single_item': len(groups[groups == 1]),
                }
            
            return analysis
        except Exception as e:
            logger.warning(f"Error en análisis de grupos: {e}")
            return {}
    
    def _analyze_top_recommendations(self) -> Dict[str, Any]:
        """Análisis de principales recomendaciones - Migrado desde tu código"""
        recommendation_cols = [col for col in self.df.columns 
                             if any(keyword in col.lower() for keyword in ['recommendation', 'title', 'description'])]
        
        if not recommendation_cols:
            return {}
        
        try:
            analysis = {}
            for col in recommendation_cols:
                value_counts = self.df[col].value_counts()
                analysis[col] = {
                    'total_unique': len(value_counts),
                    'top_10': value_counts.head(10).to_dict(),
                    'most_common': value_counts.iloc[0] if len(value_counts) > 0 else None,
                }
            
            return analysis
        except Exception as e:
            logger.warning(f"Error en análisis de recomendaciones: {e}")
            return {}
    
    def _find_patterns(self) -> Dict[str, Any]:
        """Encontrar patrones en los datos"""
        patterns = {}
        
        try:
            # Patrones en columnas numéricas
            numeric_cols = self.df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                patterns['numeric_patterns'] = {
                    'correlations': self._find_correlations(numeric_cols),
                    'summary_stats': self.df[numeric_cols].describe().to_dict(),
                }
            
            # Patrones en columnas de texto
            text_cols = self.df.select_dtypes(include=['object']).columns
            if len(text_cols) > 0:
                patterns['text_patterns'] = self._find_text_patterns(text_cols)
            
        except Exception as e:
            logger.warning(f"Error encontrando patrones: {e}")
        
        return patterns
    
    def _find_correlations(self, numeric_cols) -> Dict[str, float]:
        """Encontrar correlaciones entre columnas numéricas"""
        try:
            corr_matrix = self.df[numeric_cols].corr()
            correlations = {}
            
            for i, col1 in enumerate(numeric_cols):
                for j, col2 in enumerate(numeric_cols):
                    if i < j:  # Evitar duplicados
                        corr_value = corr_matrix.loc[col1, col2]
                        if not np.isnan(corr_value) and abs(corr_value) > 0.5:
                            correlations[f"{col1}_vs_{col2}"] = round(float(corr_value), 3)
            
            return correlations
        except Exception as e:
            logger.warning(f"Error calculando correlaciones: {e}")
            return {}
    
    def _find_text_patterns(self, text_cols) -> Dict[str, Any]:
        """Encontrar patrones en columnas de texto"""
        patterns = {}
        
        try:
            for col in text_cols[:3]:  # Limitar a 3 columnas para performance
                series = self.df[col].dropna().astype(str)
                patterns[col] = {
                    'common_words': self._get_common_words(series),
                    'length_distribution': {
                        'avg': round(series.str.len().mean(), 2),
                        'min': int(series.str.len().min()),
                        'max': int(series.str.len().max()),
                    }
                }
        except Exception as e:
            logger.warning(f"Error analizando patrones de texto: {e}")
        
        return patterns
    
    def _get_common_words(self, series: pd.Series, top_n: int = 10) -> Dict[str, int]:
        """Obtener palabras más comunes en una serie"""
        try:
            all_words = []
            for text in series.head(1000):  # Limitar para performance
                words = re.findall(r'\b\w+\b', str(text).lower())
                all_words.extend([word for word in words if len(word) > 3])
            
            word_counts = Counter(all_words)
            return dict(word_counts.most_common(top_n))
        except Exception as e:
            logger.warning(f"Error obteniendo palabras comunes: {e}")
            return {}
    
    def _generate_recommendations(self) -> List[str]:
        """Generar recomendaciones basadas en el análisis"""
        recommendations = []
        
        try:
            # Recomendaciones basadas en calidad de datos
            quality = self.insights.get('data_quality', {})
            if quality.get('completeness_score', 100) < 90:
                recommendations.append(
                    f"Mejore la completitud de datos (actual: {quality.get('completeness_score', 0):.1f}%)"
                )
            
            if quality.get('duplicate_rows', 0) > 0:
                recommendations.append(
                    f"Elimine {quality.get('duplicate_rows')} filas duplicadas"
                )
            
            # Recomendaciones basadas en tamaño
            basic_stats = self.insights.get('basic_stats', {})
            if basic_stats.get('total_rows', 0) > 50000:
                recommendations.append(
                    "Dataset grande detectado: considere usar muestreo para análisis más rápidos"
                )
            
            # Recomendaciones basadas en tipos de datos
            if basic_stats.get('total_columns', 0) > 50:
                recommendations.append(
                    "Muchas columnas detectadas: considere agrupar o filtrar datos"
                )
            
            # Recomendaciones específicas del dominio
            if 'cost_analysis' in self.insights and self.insights['cost_analysis']:
                recommendations.append(
                    "Se detectaron oportunidades de optimización de costos"
                )
            
            if 'security_analysis' in self.insights and self.insights['security_analysis'].get('total_security_recommendations', 0) > 0:
                recommendations.append(
                    "Se encontraron recomendaciones de seguridad importantes"
                )
        
        except Exception as e:
            logger.warning(f"Error generando recomendaciones: {e}")
            recommendations.append("Error generando recomendaciones automáticas")
        
        return recommendations if recommendations else ["Datos analizados correctamente"]