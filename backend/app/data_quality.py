"""Data quality utilities for ingestion, validation, and anomaly handling."""
from __future__ import annotations

from datetime import datetime
from typing import List, Tuple, Dict, Optional

import pandas as pd
import numpy as np
from loguru import logger

from .data_models import BankMarketingRawRecord
from .schema_detection import schema_detector


class DataQualityReport:
    """Captures statistics about the quality checks applied to a dataset."""

    def __init__(self) -> None:
        self.records_total: int = 0
        self.records_valid: int = 0
        self.records_invalid: int = 0
        self.invalid_indices: List[int] = []
        self.anomalies: Dict[str, List[str]] = {}

    def record_invalid(self, index: int, reason: str) -> None:
        self.records_invalid += 1
        self.invalid_indices.append(index)
        self.anomalies.setdefault("row", []).append(f"Row {index}: {reason}")

    def record_valid(self) -> None:
        self.records_valid += 1

    def to_dict(self) -> Dict[str, object]:
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "records_total": self.records_total,
            "records_valid": self.records_valid,
            "records_invalid": self.records_invalid,
            "invalid_indices": self.invalid_indices[:100],  # Limit to first 100
            "anomalies": {k: v[:50] for k, v in self.anomalies.items()},  # Limit anomalies
        }


def validate_dataframe(df: pd.DataFrame, 
                      strict_schema: bool = False,
                      schema_model: Optional[type] = None) -> Tuple[pd.DataFrame, DataQualityReport]:
    """
    Validate raw dataframe rows with flexible or strict schema.
    
    Args:
        df: Input DataFrame
        strict_schema: If True, use strict schema validation (backward compatibility)
        schema_model: Optional Pydantic model for strict validation
        
    Returns:
        Tuple of (cleaned DataFrame, quality report)
    """
    report = DataQualityReport()
    report.records_total = len(df)
    
    if strict_schema and schema_model:
        # Legacy strict validation
        return _validate_strict_schema(df, schema_model, report)
    else:
        # Flexible validation - accept any CSV structure
        return _validate_flexible(df, report)


def _validate_strict_schema(df: pd.DataFrame, 
                           schema_model: type,
                           report: DataQualityReport) -> Tuple[pd.DataFrame, DataQualityReport]:
    """Validate using strict Pydantic schema (legacy mode)."""
    cleaned_records = []
    for idx, row in df.iterrows():
        row_dict = row.to_dict()
        # Handle common defaults
        for col, default in [("pdays", -1), ("previous", 0)]:
            x = row_dict.get(col, default)
            try:
                if x is None or (isinstance(x, float) and np.isnan(x)) or str(x).strip() == '':
                    row_dict[col] = default
                elif not isinstance(x, int):
                    row_dict[col] = int(float(x))
                else:
                    row_dict[col] = x
            except Exception:
                row_dict[col] = default
        try:
            record = schema_model(**row_dict)
            cleaned_records.append(record.model_dump())
            report.record_valid()
        except Exception as exc:
            logger.warning(f"Invalid record at row {idx}: {exc}")
            report.record_invalid(idx, str(exc))
            continue

    cleaned_df = pd.DataFrame(cleaned_records)
    cleaned_df = _handle_missing_values(cleaned_df)
    cleaned_df = _cap_outliers(cleaned_df)
    return cleaned_df, report


def _validate_flexible(df: pd.DataFrame, report: DataQualityReport) -> Tuple[pd.DataFrame, DataQualityReport]:
    """
    Flexible validation - clean data but accept any structure.
    
    This mode:
    - Normalizes column names
    - Handles missing values
    - Converts types appropriately
    - Caps outliers for numeric columns
    - But doesn't reject rows based on schema
    """
    cleaned_df = df.copy()
    
    # Normalize column names
    cleaned_df.columns = [col.strip().lower().replace(" ", "_").replace("-", "_") 
                          for col in cleaned_df.columns]
    
    # Detect and convert types
    schema = schema_detector.detect_schema(cleaned_df, sample_size=min(1000, len(cleaned_df)))
    
    # Convert datetime columns
    for col in schema.get("datetime_columns", []):
        if col in cleaned_df.columns:
            try:
                cleaned_df[col] = pd.to_datetime(cleaned_df[col], errors='coerce')
            except Exception:
                pass
    
    # Convert boolean columns
    for col in schema.get("boolean_columns", []):
        if col in cleaned_df.columns:
            try:
                cleaned_df[col] = cleaned_df[col].astype(str).str.lower().str.strip()
                cleaned_df[col] = cleaned_df[col].isin(['true', 'yes', 'y', '1', '1.0']).astype(bool)
            except Exception:
                pass
    
    # Handle missing values
    cleaned_df = _handle_missing_values(cleaned_df)
    
    # Cap outliers for numeric columns
    cleaned_df = _cap_outliers(cleaned_df)
    
    # All rows are considered valid in flexible mode
    report.records_valid = len(cleaned_df)
    report.records_invalid = 0
    
    logger.info(f"Flexible validation complete: {len(cleaned_df)} rows, "
               f"{len(cleaned_df.columns)} columns")
    
    return cleaned_df, report


def _handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Impute or drop missing values according to data policy."""
    numeric_cols = df.select_dtypes(include=["float64", "int64"]).columns
    categorical_cols = df.select_dtypes(include=["object"]).columns

    for column in numeric_cols:
        if df[column].isna().any():
            median = df[column].median()
            df[column].fillna(median, inplace=True)

    for column in categorical_cols:
        if df[column].isna().any():
            df[column].fillna("unknown", inplace=True)

    return df


def _cap_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """Winsorize numeric columns to mitigate aberrations."""
    numeric_cols = df.select_dtypes(include=["float64", "int64"]).columns
    for column in numeric_cols:
        lower = df[column].quantile(0.01)
        upper = df[column].quantile(0.99)
        df[column] = df[column].clip(lower=lower, upper=upper)
    return df


