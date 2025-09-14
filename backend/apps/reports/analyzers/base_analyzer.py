# apps/reports/analyzers/base_analyzer.py
import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class BaseAnalyzer(ABC):
    """Clase base para todos los analizadores"""
    
    def __init__(self, data: pd.DataFrame):
        self.df = data.copy() if data is not None else pd.DataFrame()
        self.insights = {}
        
    @abstractmethod
    def analyze(self) -> Dict[str, Any]:
        """Método abstracto para realizar el análisis"""
        pass
    
    def _get_basic_stats(self) -> Dict[str, Any]:
        """Estadísticas básicas del dataset"""
        return {
            'total_rows': len(self.df),
            'total_columns': len(self.df.columns),
            'memory_usage_mb': round(self.df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
            'data_types': self.df.dtypes.astype(str).to_dict(),
            'null_counts': self.df.isnull().sum().to_dict(),
            'duplicate_rows': self.df.duplicated().sum(),
        }