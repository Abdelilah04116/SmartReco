"""Data quality utilities for ingestion, validation, and anomaly handling."""
from __future__ import annotations

from datetime import datetime
from typing import List, Tuple, Dict

import pandas as pd
from loguru import logger

from .data_models import BankMarketingRawRecord


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
            "invalid_indices": self.invalid_indices,
            "anomalies": self.anomalies,
        }


def validate_dataframe(df: pd.DataFrame) -> Tuple[pd.DataFrame, DataQualityReport]:
    """Validate raw dataframe rows using strict schema definitions."""
    report = DataQualityReport()
    cleaned_records = []
    import numpy as np
    for idx, row in df.iterrows():
        report.records_total += 1
        row_dict = row.to_dict()
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
            record = BankMarketingRawRecord(**row_dict)
        except Exception as exc:
            logger.warning(f"Invalid record at row {idx}: {exc}")
            report.record_invalid(idx, str(exc))
            continue
        cleaned_records.append(record.model_dump())
        report.record_valid()

    cleaned_df = pd.DataFrame(cleaned_records)
    cleaned_df = _handle_missing_values(cleaned_df)
    cleaned_df = _cap_outliers(cleaned_df)

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


