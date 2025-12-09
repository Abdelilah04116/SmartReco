"""Feature engineering utilities."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any, Optional

import numpy as np
import pandas as pd
from loguru import logger
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .config import settings
from .schema_detection import schema_detector


# Legacy columns for backward compatibility
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


def _derive_features(df: pd.DataFrame, 
                    numeric_cols: Optional[List[str]] = None,
                    categorical_cols: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Create domain-driven engineered features dynamically.
    
    Args:
        df: Input DataFrame
        numeric_cols: List of numeric column names
        categorical_cols: List of categorical column names
    """
    df = df.copy()
    
    # Auto-detect columns if not provided
    if numeric_cols is None or categorical_cols is None:
        schema = schema_detector.detect_schema(df, sample_size=1000)
        detected_cols = schema_detector.get_feature_columns(schema)
        numeric_cols = detected_cols.get("numeric", [])
        categorical_cols = detected_cols.get("categorical", [])
    
    # Create interaction features for numeric columns
    if len(numeric_cols) >= 2:
        # Use first two numeric columns for interaction
        col1, col2 = numeric_cols[0], numeric_cols[1]
        if col1 in df.columns and col2 in df.columns:
            with np.errstate(divide="ignore", invalid="ignore"):
                ratio_col = f"{col1}_to_{col2}_ratio"
                df[ratio_col] = (
                    df[col1].replace({0: np.nan}) / df[col2].replace({0: np.nan})
                ).fillna(0.0)
                
                interaction_col = f"{col1}_{col2}_interaction"
                df[interaction_col] = df[col1] * np.log1p(np.abs(df[col2]))
    
    # Create frequency scores for categorical columns
    if categorical_cols:
        for cat_col in categorical_cols[:3]:  # Limit to first 3 to avoid explosion
            if cat_col in df.columns:
                freq_col = f"{cat_col}_frequency_score"
                counts = df.groupby(cat_col)[cat_col].transform("count")
                df[freq_col] = counts / counts.max() if counts.max() > 0 else 0.0
    
    return df


@dataclass
class FeatureEngineer:
    """Encapsulates feature transformations used for modeling."""

    pipeline: Pipeline = field(init=False)
    feature_columns_: List[str] = field(default_factory=list)
    categorical_columns_: List[str] = field(default_factory=list)
    numeric_columns_: List[str] = field(default_factory=list)
    schema_: Optional[Dict[str, Any]] = field(default=None)

    def __post_init__(self) -> None:
        # Pipeline will be initialized in fit() with detected columns
        pass

    def _build_pipeline(self, categorical_cols: List[str], numeric_cols: List[str]) -> None:
        """Build the feature engineering pipeline with detected columns."""
        categorical_transformer = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
            ]
        )
        numeric_transformer = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
            ]
        )
        
        transformers = []
        if categorical_cols:
            transformers.append(("categorical", categorical_transformer, categorical_cols))
        if numeric_cols:
            transformers.append(("numeric", numeric_transformer, numeric_cols))
        
        if not transformers:
            logger.warning("No feature columns detected. Using remainder='passthrough'")
            self.pipeline = ColumnTransformer(
                transformers=[],
                remainder="passthrough",
            )
        else:
            self.pipeline = ColumnTransformer(
                transformers=transformers,
                remainder="drop",
            )

    def fit(self, df: pd.DataFrame, 
            exclude_columns: Optional[List[str]] = None,
            target_column: Optional[str] = None) -> "FeatureEngineer":
        """
        Fit the feature engineering pipeline with automatic schema detection.
        
        Args:
            df: Input DataFrame
            exclude_columns: Columns to exclude from features (e.g., ID, target)
            target_column: Target column name to exclude
        """
        # Detect schema
        self.schema_ = schema_detector.detect_schema(df, sample_size=10000)
        
        # Get feature columns
        exclude = set(exclude_columns or [])
        if target_column:
            exclude.add(target_column)
        
        feature_cols = schema_detector.get_feature_columns(self.schema_, exclude_columns=list(exclude))
        self.categorical_columns_ = feature_cols.get("categorical", [])
        self.numeric_columns_ = feature_cols.get("numeric", [])
        
        # Build pipeline
        self._build_pipeline(self.categorical_columns_, self.numeric_columns_)
        
        # Derive features
        df_processed = _derive_features(df, self.numeric_columns_, self.categorical_columns_)
        
        logger.info(f"Fitting feature engineering pipeline: "
                   f"{len(self.categorical_columns_)} categorical, "
                   f"{len(self.numeric_columns_)} numeric columns")
        
        self.pipeline.fit(df_processed)
        self.feature_columns_ = self.categorical_columns_ + self.numeric_columns_
        
        return self

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        """Transform dataset using fitted pipeline."""
        df_processed = _derive_features(df, self.numeric_columns_, self.categorical_columns_)
        logger.debug("Transforming dataset using feature pipeline")
        return self.pipeline.transform(df_processed)

    def fit_transform(self, df: pd.DataFrame,
                     exclude_columns: Optional[List[str]] = None,
                     target_column: Optional[str] = None) -> np.ndarray:
        """Fit and transform in one step."""
        return self.fit(df, exclude_columns, target_column).transform(df)

    def get_feature_names(self) -> List[str]:
        """Return output feature names, if available."""
        try:
            feature_names = []
            if self.categorical_columns_:
                cat_features = list(
                    self.pipeline.named_transformers_["categorical"]
                    .named_steps["encoder"]
                    .get_feature_names_out(self.categorical_columns_)
                )
                feature_names.extend(cat_features)
            if self.numeric_columns_:
                feature_names.extend(self.numeric_columns_)
            return feature_names
        except (AttributeError, KeyError):  # pragma: no cover
            return self.feature_columns_

    def to_metadata(self) -> Dict[str, Any]:
        return {
            "feature_columns": self.feature_columns_,
            "categorical_columns": self.categorical_columns_,
            "numeric_columns": self.numeric_columns_,
            "schema": self.schema_,
            "settings": {
                "target_column": settings.TARGET_COLUMN,
            },
        }









