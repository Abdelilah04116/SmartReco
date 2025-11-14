"""Feature engineering utilities."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any

import numpy as np
import pandas as pd
from loguru import logger
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .config import settings


CATEGORICAL_COLUMNS: List[str] = [
    "job",
    "marital",
    "education",
    "contact",
    "month",
    "default",
    "housing",
    "loan",
    "poutcome",
]

NUMERIC_COLUMNS: List[str] = [
    "age",
    "balance",
    "duration",
    "campaign",
    "pdays",
    "previous",
    "contact_frequency_score",
    "age_balance_interaction",
    "balance_to_age_ratio",
]


def _derive_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create domain-driven engineered features."""
    df = df.copy()
    with np.errstate(divide="ignore", invalid="ignore"):
        df["balance_to_age_ratio"] = (
            df["balance"].replace({0: np.nan}) / df["age"].replace({0: np.nan})
        ).fillna(0.0)
    df["age_balance_interaction"] = df["age"] * np.log1p(np.abs(df["balance"]))

    contact_counts = df.groupby("contact")["campaign"].transform("count")
    df["contact_frequency_score"] = contact_counts / contact_counts.max()
    df["is_contact_recent"] = df["pdays"].apply(lambda x: 1 if x <= 7 and x != -1 else 0)

    return df


@dataclass
class FeatureEngineer:
    """Encapsulates feature transformations used for modeling."""

    pipeline: Pipeline = field(init=False)
    feature_columns_: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        categorical_transformer = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("encoder", OneHotEncoder(handle_unknown="ignore")),
            ]
        )
        numeric_transformer = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
            ]
        )
        self.pipeline = ColumnTransformer(
            transformers=[
                ("categorical", categorical_transformer, CATEGORICAL_COLUMNS),
                ("numeric", numeric_transformer, NUMERIC_COLUMNS),
            ],
            remainder="drop",
        )

    def fit(self, df: pd.DataFrame) -> "FeatureEngineer":
        df = _derive_features(df)
        logger.info("Fitting feature engineering pipeline")
        self.pipeline.fit(df)
        self.feature_columns_ = CATEGORICAL_COLUMNS + NUMERIC_COLUMNS
        return self

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        df = _derive_features(df)
        logger.debug("Transforming dataset using feature pipeline")
        return self.pipeline.transform(df)

    def fit_transform(self, df: pd.DataFrame) -> np.ndarray:
        df = _derive_features(df)
        logger.info("Fit-transforming feature pipeline")
        return self.pipeline.fit_transform(df)

    def get_feature_names(self) -> List[str]:
        """Return output feature names, if available."""
        try:
            cat_features = list(self.pipeline.named_transformers_["categorical"].named_steps["encoder"].get_feature_names_out(CATEGORICAL_COLUMNS))
        except AttributeError:  # pragma: no cover - sklearn <1.0
            cat_features = []
        num_features = NUMERIC_COLUMNS
        return cat_features + num_features

    def to_metadata(self) -> Dict[str, Any]:
        return {
            "feature_columns": self.feature_columns_,
            "settings": {
                "target_column": settings.TARGET_COLUMN,
            },
        }



