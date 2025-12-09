"""Dynamic schema detection for CSV files."""
from __future__ import annotations

from typing import Dict, List, Any, Optional, Union
import pandas as pd
import numpy as np
from loguru import logger


class SchemaDetector:
    """Automatically detects schema and column types from CSV data."""
    
    def __init__(self, 
                 categorical_threshold: int = 50,
                 numeric_precision_threshold: float = 0.1):
        """
        Initialize schema detector.
        
        Args:
            categorical_threshold: Max unique values to consider a column categorical
            numeric_precision_threshold: Threshold for detecting integer vs float
        """
        self.categorical_threshold = categorical_threshold
        self.numeric_precision_threshold = numeric_precision_threshold
    
    def detect_schema(self, df: pd.DataFrame, sample_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Detect schema from DataFrame.
        
        Args:
            df: Input DataFrame
            sample_size: Optional sample size for large datasets
            
        Returns:
            Dictionary with schema information
        """
        # Sample if dataset is large
        if sample_size and len(df) > sample_size:
            sample_df = df.sample(n=min(sample_size, len(df)), random_state=42)
            logger.info(f"Sampling {sample_size} rows for schema detection")
        else:
            sample_df = df
        
        schema = {
            "columns": [],
            "numeric_columns": [],
            "categorical_columns": [],
            "datetime_columns": [],
            "boolean_columns": [],
            "text_columns": [],
            "column_stats": {}
        }
        
        for col in df.columns:
            col_info = self._analyze_column(df, col, sample_df)
            schema["columns"].append(col_info)
            schema["column_stats"][col] = col_info
            
            # Categorize column
            if col_info["type"] == "numeric":
                if col_info["subtype"] == "integer":
                    schema["numeric_columns"].append(col)
                else:
                    schema["numeric_columns"].append(col)
            elif col_info["type"] == "categorical":
                schema["categorical_columns"].append(col)
            elif col_info["type"] == "datetime":
                schema["datetime_columns"].append(col)
            elif col_info["type"] == "boolean":
                schema["boolean_columns"].append(col)
            elif col_info["type"] == "text":
                schema["text_columns"].append(col)
        
        logger.info(f"Detected schema: {len(schema['numeric_columns'])} numeric, "
                   f"{len(schema['categorical_columns'])} categorical, "
                   f"{len(schema['datetime_columns'])} datetime")
        
        return schema
    
    def _analyze_column(self, df: pd.DataFrame, col: str, sample_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze a single column to determine its type and characteristics."""
        col_info = {
            "name": col,
            "type": "unknown",
            "subtype": None,
            "nullable": df[col].isna().any(),
            "null_count": int(df[col].isna().sum()),
            "null_percentage": float(df[col].isna().sum() / len(df) * 100),
            "unique_count": int(df[col].nunique()),
            "unique_percentage": float(df[col].nunique() / len(df) * 100),
        }
        
        # Try to detect datetime
        if self._is_datetime(df[col]):
            col_info["type"] = "datetime"
            col_info["subtype"] = "datetime"
            return col_info
        
        # Try to detect boolean
        if self._is_boolean(df[col]):
            col_info["type"] = "boolean"
            col_info["subtype"] = "boolean"
            return col_info
        
        # Check if numeric
        if pd.api.types.is_numeric_dtype(df[col]):
            col_info["type"] = "numeric"
            if pd.api.types.is_integer_dtype(df[col]):
                col_info["subtype"] = "integer"
            else:
                col_info["subtype"] = "float"
            
            # Add numeric statistics
            col_info["min"] = float(df[col].min()) if not df[col].isna().all() else None
            col_info["max"] = float(df[col].max()) if not df[col].isna().all() else None
            col_info["mean"] = float(df[col].mean()) if not df[col].isna().all() else None
            col_info["median"] = float(df[col].median()) if not df[col].isna().all() else None
            col_info["std"] = float(df[col].std()) if not df[col].isna().all() else None
            
            return col_info
        
        # Check if categorical (low cardinality)
        unique_ratio = df[col].nunique() / len(df)
        if df[col].nunique() <= self.categorical_threshold or unique_ratio < 0.1:
            col_info["type"] = "categorical"
            col_info["subtype"] = "categorical"
            col_info["categories"] = df[col].value_counts().head(20).to_dict()
            return col_info
        
        # Otherwise, treat as text
        col_info["type"] = "text"
        col_info["subtype"] = "text"
        col_info["avg_length"] = float(df[col].astype(str).str.len().mean()) if not df[col].isna().all() else None
        
        return col_info
    
    def _is_datetime(self, series: pd.Series) -> bool:
        """Check if a series contains datetime data."""
        if pd.api.types.is_datetime64_any_dtype(series):
            return True
        
        # Try to parse as datetime
        sample = series.dropna().head(100)
        if len(sample) == 0:
            return False
        
        try:
            pd.to_datetime(sample, errors='raise')
            return True
        except:
            return False
    
    def _is_boolean(self, series: pd.Series) -> bool:
        """Check if a series contains boolean data."""
        if pd.api.types.is_bool_dtype(series):
            return True
        
        # Check for common boolean patterns
        sample = series.dropna().head(100)
        if len(sample) == 0:
            return False
        
        unique_values = set(str(v).lower().strip() for v in sample.unique())
        boolean_patterns = [
            {'true', 'false', '1', '0', 'yes', 'no', 'y', 'n'},
            {'true', 'false'},
            {'yes', 'no'},
            {'y', 'n'},
            {'1', '0'},
        ]
        
        for pattern in boolean_patterns:
            if unique_values.issubset(pattern):
                return True
        
        return False
    
    def get_feature_columns(self, schema: Dict[str, Any], 
                           exclude_columns: Optional[List[str]] = None) -> Dict[str, List[str]]:
        """
        Get feature columns for ML pipeline.
        
        Args:
            schema: Detected schema
            exclude_columns: Columns to exclude (e.g., ID columns, target)
            
        Returns:
            Dictionary with 'categorical' and 'numeric' column lists
        """
        exclude = set(exclude_columns or [])
        
        categorical = [col for col in schema["categorical_columns"] if col not in exclude]
        numeric = [col for col in schema["numeric_columns"] if col not in exclude]
        
        return {
            "categorical": categorical,
            "numeric": numeric
        }


# Global schema detector instance
schema_detector = SchemaDetector()

