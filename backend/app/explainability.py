"""Explainability utilities combining rule-based reasons with model interpretability."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Optional

import numpy as np
import pandas as pd
from loguru import logger

try:
    import shap  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    shap = None

try:
    from lime.lime_tabular import LimeTabularExplainer  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    LimeTabularExplainer = None


from .config import settings
from .feature_engineering import FeatureEngineer


@dataclass
class ExplanationBundle:
    """Group rule explanations with ML interpretability artifacts."""

    rule_explanations: Dict[str, Any]
    shap_values: Optional[Dict[str, Any]] = None
    lime_values: Optional[Dict[str, Any]] = None


class ExplainabilityService:
    """Provide SHAP/LIME explanations on top of rule-based insights."""

    def __init__(
        self,
        feature_engineer: FeatureEngineer,
        background_data: Optional[np.ndarray] = None,
    ) -> None:
        self.feature_engineer = feature_engineer
        self.background_data = background_data
        self._lime_explainer: Optional[LimeTabularExplainer] = None
        self._shap_explainer: Optional[Any] = None

    def prepare_background(self, dataset: pd.DataFrame) -> None:
        sample_size = min(settings.SHAP_BACKGROUND_SAMPLE_SIZE, len(dataset))
        background_df = dataset.sample(sample_size, random_state=settings.RANDOM_STATE)
        self.background_data = self.feature_engineer.transform(background_df)
        logger.info("Explainability background data prepared", sample_size=sample_size)

    def explain_instance(
        self,
        model: Any,
        record: pd.Series,
        rule_explanations: Dict[str, Any],
    ) -> ExplanationBundle:
        features = self.feature_engineer.transform(pd.DataFrame([record]))
        bundle = ExplanationBundle(rule_explanations=rule_explanations)
        if shap is not None:
            bundle.shap_values = self._compute_shap(model, features)
        if LimeTabularExplainer is not None:
            bundle.lime_values = self._compute_lime(model, features, record.values)
        return bundle

    def _compute_shap(self, model: Any, features: np.ndarray) -> Dict[str, Any]:
        if self._shap_explainer is None:
            if shap is None:
                raise RuntimeError("SHAP is not installed")
            self._shap_explainer = shap.Explainer(model, self.background_data)  # type: ignore[call-arg]
        shap_values = self._shap_explainer(features)
        return {
            "values": shap_values.values.tolist(),
            "base_values": shap_values.base_values.tolist(),
        }

    def _compute_lime(
        self,
        model: Any,
        features: np.ndarray,
        record_values: np.ndarray,
    ) -> Dict[str, Any]:
        if self._lime_explainer is None:
            if LimeTabularExplainer is None:
                raise RuntimeError("LIME is not installed")
            self._lime_explainer = LimeTabularExplainer(
                training_data=self.background_data,
                feature_names=self.feature_engineer.get_feature_names(),
                class_names=[settings.NEGATIVE_CLASS_LABEL, settings.POSITIVE_CLASS_LABEL],
                discretize_continuous=True,
            )
        explanation = self._lime_explainer.explain_instance(
            record_values,
            model.predict_proba,
            num_features=settings.LIME_NUM_FEATURES,
        )
        return {
            "weights": explanation.as_list(),
            "intercept": explanation.intercept,
            "score": explanation.score,
        }













