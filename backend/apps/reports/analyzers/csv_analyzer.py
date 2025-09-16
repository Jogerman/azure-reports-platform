# apps/reports/analyzers/csv_analyzer.py - Analyzer JSON-safe
import pandas as pd
import numpy as np
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Dict, Any, List, Union
import logging
import re

logger = logging.getLogger(__name__)

def convert_numpy_types(obj):
    """
    Convierte recursivamente tipos de numpy y pandas a tipos serializables en JSON
    """
    if isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(item) for item in obj)
    elif isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    elif pd.isna(obj):
        return None
    else:
        return obj

class EnhancedCSVAnalyzer:
    """
    Analizador mejorado para archivos CSV con conversión automática a JSON
    """
    
    def __init__(self, csv_data: pd.DataFrame):
        self.df = csv_data.copy()
        self.insights = {}
        logger.info(f"Iniciando análisis de {len(self.df)} filas y {len(self.df.columns)} columnas")
    
    def analyze(self) -> Dict[str, Any]:
        """Realizar análisis completo y detallado"""
        try:
            logger.info("Iniciando análisis completo")
            
            # Limpiar datos de forma segura
            self._safe_clean_data()
            
            # Realizar todos los análisis
            analysis_results = {
                'basic_stats': self._get_basic_stats(),
                'data_quality': self._assess_data_quality(),
                'column_analysis': self._analyze_columns(),
                'categories': self._analyze_categories(),
                'business_impact': self._analyze_business_impact(),
                'resource_types': self._analyze_resource_types(),
                'cost_analysis': self._analyze_cost_optimization(),
                'security_analysis': self._analyze_security_recommendations(),
                'recommendations': self._generate_recommendations(),
                'analysis_completed': True,
                'analysis_timestamp': datetime.now().isoformat(),
            }
            
            # Convertir todos los tipos numpy a tipos JSON serializables
            analysis_results = convert_numpy_types(analysis_results)
            
            logger.info("Análisis completado exitosamente")
            return analysis_results
            
        except Exception as e:
            logger.error(f"Error en análisis: {str(e)}")
            return convert_numpy_types({
                'error': str(e),
                'analysis_completed': False,
                'basic_stats': self._get_basic_stats() if not self.df.empty else {},
            })
    
    def _safe_clean_data(self):
        """Limpiar datos de forma super segura"""
        try:
            logger.info("Iniciando limpieza de datos")
            
            # Identificar y limpiar columnas problemáticas
            for col in self.df.columns:
                try:
                    # Limpiar espacios en blanco en columnas de texto
                    if self.df[col].dtype == 'object':
                        self.df[col] = self.df[col].astype(str).str.strip()
                        
                    # Convertir valores vacíos a NaN
                    self.df[col] = self.df[col].replace(['', 'null', 'NULL', 'None'], np.nan)
                except Exception as e:
                    logger.warning(f"Error limpiando columna '{col}': {e}")
                    continue
                   
            logger.info("Limpieza de datos completada")
            
        except Exception as e:
            logger.warning(f"Error en limpieza de datos: {e}")
    
    def _get_basic_stats(self) -> Dict[str, Any]:
        """Estadísticas básicas del DataFrame"""
        try:
            return {
                'total_rows': int(len(self.df)),
                'total_columns': int(len(self.df.columns)),
                'memory_usage_bytes': int(self.df.memory_usage(deep=True).sum()),
                'column_names': list(self.df.columns),
                'shape': list(self.df.shape),
                'empty_dataframe': bool(self.df.empty)
            }
        except Exception as e:
            logger.error(f"Error en estadísticas básicas: {e}")
            return {'error': str(e)}
    
    def _assess_data_quality(self) -> Dict[str, Any]:
        """Evaluar la calidad de los datos"""
        try:
            total_cells = int(self.df.size)
            null_cells = int(self.df.isnull().sum().sum())
            
            return {
                'completeness_score': round(((total_cells - null_cells) / total_cells) * 100, 2) if total_cells > 0 else 0,
                'total_null_values': null_cells,
                'duplicate_rows': int(self.df.duplicated().sum()),
                'consistency_issues': self._check_consistency(),
                'data_types_summary': self._analyze_data_types(),
            }
        except Exception as e:
            logger.error(f"Error evaluando calidad de datos: {e}")
            return {'error': str(e)}
    
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
                    'sample_values': self.df[col].dropna().head(3).astype(str).tolist(),
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
            if len(series) == 0:
                return {'numeric_analysis': 'no_data'}
                
            return {
                'min_value': float(series.min()),
                'max_value': float(series.max()),
                'mean_value': round(float(series.mean()), 2),
                'median_value': float(series.median()),
                'std_value': round(float(series.std()), 2) if len(series) > 1 else 0,
                'zero_values': int((series == 0).sum()),
                'negative_values': int((series < 0).sum()),
            }
        except Exception as e:
            return {'numeric_analysis_error': str(e)}
    
    def _analyze_text_column(self, col: str) -> Dict[str, Any]:
        """Análisis específico para columnas de texto"""
        try:
            series = self.df[col].dropna().astype(str)
            if len(series) == 0:
                return {'text_analysis': 'no_data'}
                
            most_common = series.value_counts().head(3).to_dict()
            
            return {
                'avg_length': round(series.str.len().mean(), 1),
                'min_length': int(series.str.len().min()),
                'max_length': int(series.str.len().max()),
                'most_common': {str(k): int(v) for k, v in most_common.items()},
                'contains_urls': int(series.str.contains(r'http[s]?://', regex=True, na=False).sum()),
                'contains_emails': int(series.str.contains(r'\S+@\S+', regex=True, na=False).sum()),
            }
        except Exception as e:
            return {'text_analysis_error': str(e)}
    
    def _check_consistency(self) -> List[str]:
        """Verificar consistencia de datos"""
        issues = []
        
        try:
            # Verificar duplicados
            duplicates = int(self.df.duplicated().sum())
            if duplicates > 0:
                issues.append(f"Se encontraron {duplicates} filas duplicadas")
            
            # Verificar valores atípicos básicos en columnas numéricas
            numeric_cols = self.df.select_dtypes(include=[np.number]).columns
            for col in numeric_cols[:3]:  # Solo las primeras 3 para no sobrecargar
                try:
                    series = self.df[col].dropna()
                    if len(series) > 10:  # Solo si hay suficientes datos
                        Q1 = series.quantile(0.25)
                        Q3 = series.quantile(0.75)
                        IQR = Q3 - Q1
                        if IQR > 0:  # Evitar división por cero
                            outliers = int(len(series[(series < (Q1 - 1.5 * IQR)) | 
                                                     (series > (Q3 + 1.5 * IQR))]))
                            if outliers > 0:
                                issues.append(f"Se encontraron {outliers} valores atípicos en '{col}'")
                except Exception:
                    continue
        
        except Exception as e:
            logger.warning(f"Error verificando consistencia: {e}")
            issues.append("Error en verificación de consistencia")
        
        return issues
    
    def _analyze_data_types(self) -> Dict[str, int]:
        """Resumen de tipos de datos"""
        try:
            type_counts = defaultdict(int)
            for dtype in self.df.dtypes:
                type_counts[str(dtype)] += 1
            return dict(type_counts)
        except Exception as e:
            return {'error': str(e)}
    
    # ===== ANÁLISIS ESPECÍFICOS PARA AZURE ADVISOR =====
    
    def _analyze_categories(self) -> Dict[str, Any]:
        """Análisis por categorías"""
        try:
            if 'Category' not in self.df.columns:
                return {'message': 'Columna Category no encontrada'}
            
            categories = self.df['Category'].value_counts()
            return {
                'total_categories': int(len(categories)),
                'category_distribution': {str(k): int(v) for k, v in categories.head(10).items()},
                'most_common_category': str(categories.index[0]) if len(categories) > 0 else None,
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _analyze_business_impact(self) -> Dict[str, Any]:
        """Análisis de impacto de negocio"""
        try:
            if 'Business Impact' not in self.df.columns:
                return {'message': 'Columna Business Impact no encontrada'}
            
            impact = self.df['Business Impact'].value_counts()
            return {
                'impact_distribution': {str(k): int(v) for k, v in impact.items()},
                'high_impact_count': int(self.df[self.df['Business Impact'] == 'High'].shape[0]),
                'medium_impact_count': int(self.df[self.df['Business Impact'] == 'Medium'].shape[0]),
                'low_impact_count': int(self.df[self.df['Business Impact'] == 'Low'].shape[0]),
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _analyze_resource_types(self) -> Dict[str, Any]:
        """Análisis de tipos de recursos"""
        try:
            if 'Resource Type' not in self.df.columns:
                return {'message': 'Columna Resource Type no encontrada'}
            
            resources = self.df['Resource Type'].value_counts()
            return {
                'total_resource_types': int(len(resources)),
                'resource_distribution': {str(k): int(v) for k, v in resources.head(10).items()},
                'most_common_resource': str(resources.index[0]) if len(resources) > 0 else None,
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _analyze_cost_optimization(self) -> Dict[str, Any]:
        """Análisis de optimización de costos"""
        try:
            cost_related = self.df[self.df['Category'].str.contains('Cost', case=False, na=False)]
            
            return {
                'total_cost_recommendations': int(len(cost_related)),
                'cost_percentage': round((len(cost_related) / len(self.df)) * 100, 1),
                'has_cost_analysis': len(cost_related) > 0,
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _analyze_security_recommendations(self) -> Dict[str, Any]:
        """Análisis de recomendaciones de seguridad"""
        try:
            security_related = self.df[self.df['Category'].str.contains('Security', case=False, na=False)]
            
            return {
                'total_security_recommendations': int(len(security_related)),
                'security_percentage': round((len(security_related) / len(self.df)) * 100, 1),
                'has_security_analysis': len(security_related) > 0,
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _generate_recommendations(self) -> List[Dict[str, Any]]:
        """Generar recomendaciones basadas en el análisis"""
        recommendations = []
        
        try:
            # Recomendación sobre calidad de datos
            data_quality = self._assess_data_quality()
            if isinstance(data_quality, dict) and 'completeness_score' in data_quality:
                if data_quality['completeness_score'] < 95:
                    recommendations.append({
                        'type': 'data_quality',
                        'priority': 'medium',
                        'title': 'Mejorar calidad de datos',
                        'description': f"La completitud de datos es del {data_quality['completeness_score']}%. Considera limpiar valores faltantes.",
                    })
            
            # Recomendación sobre duplicados
            if data_quality.get('duplicate_rows', 0) > 0:
                recommendations.append({
                    'type': 'data_cleanup',
                    'priority': 'low',
                    'title': 'Eliminar filas duplicadas',
                    'description': f"Se encontraron {data_quality['duplicate_rows']} filas duplicadas que podrían eliminarse.",
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generando recomendaciones: {e}")
            return [{'error': str(e)}]