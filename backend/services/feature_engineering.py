"""Feature engineering utilities."""
from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd

from models.schemas import FeatureSuggestion


def normalize_numeric(df: pd.DataFrame, column: str) -> FeatureSuggestion:
    series = df[column].astype(float)
    norm = (series - series.min()) / (series.max() - series.min() + 1e-9)
    preview = norm.head(5).round(4).tolist()
    return FeatureSuggestion(
        name=f"normalized_{column}",
        description=f"Min-max normalization of {column}",
        columns=[column],
        preview={"values": preview},
    )


def encode_categorical(df: pd.DataFrame, column: str) -> FeatureSuggestion:
    """Encode categorical column using label encoding instead of one-hot encoding."""
    from sklearn.preprocessing import LabelEncoder
    le = LabelEncoder()
    encoded = le.fit_transform(df[column].astype(str))
    preview = encoded[:5].tolist()
    unique_values = df[column].unique()[:10].tolist()
    return FeatureSuggestion(
        name=f"label_encoded_{column}",
        description=f"Label encoding for {column} (replaces one-hot encoding)",
        columns=[column],
        preview={"values": preview, "unique_values": unique_values},
    )


def decompose_datetime(df: pd.DataFrame, column: str) -> FeatureSuggestion:
    dt = pd.to_datetime(df[column], errors="coerce")
    features = {
        f"{column}_year": dt.dt.year,
        f"{column}_month": dt.dt.month,
        f"{column}_day": dt.dt.day,
        f"{column}_weekday": dt.dt.weekday,
    }
    preview = {k: v.dropna().head(5).tolist() for k, v in features.items()}
    return FeatureSuggestion(
        name=f"datetime_parts_{column}",
        description=f"Year, month, day, weekday extracted from {column}",
        columns=[column],
        preview=preview,
    )


def interaction_feature(df: pd.DataFrame, first: str, second: str) -> FeatureSuggestion:
    a = pd.to_numeric(df[first], errors="coerce")
    b = pd.to_numeric(df[second], errors="coerce")
    ratio = (a / (b.replace(0, np.nan))).replace([np.inf, -np.inf], np.nan)
    preview = ratio.dropna().head(5).round(4).tolist()
    return FeatureSuggestion(
        name=f"{first}_over_{second}",
        description=f"Interaction ratio between {first} and {second}",
        columns=[first, second],
        preview={"values": preview},
    )


def suggest_features(df: pd.DataFrame, column_types: Dict[str, str]) -> List[FeatureSuggestion]:
    """Return a list of heuristic feature engineering suggestions."""
    suggestions: List[FeatureSuggestion] = []
    numeric_cols = [c for c, t in column_types.items() if t == "numeric"]
    categorical_cols = [c for c, t in column_types.items() if t == "categorical"]
    datetime_cols = [c for c, t in column_types.items() if t == "datetime"]

    for col in numeric_cols:
        suggestions.append(normalize_numeric(df, col))

    for col in categorical_cols:
        suggestions.append(encode_categorical(df, col))

    for col in datetime_cols:
        suggestions.append(decompose_datetime(df, col))

    if len(numeric_cols) >= 2:
        first, second = numeric_cols[:2]
        suggestions.append(interaction_feature(df, first, second))

    return suggestions


