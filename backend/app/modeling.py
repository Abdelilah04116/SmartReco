"""Model training, evaluation, and registry management."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from loguru import logger
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report,
    roc_auc_score,
    roc_curve,
    precision_recall_fscore_support,
)
from sklearn.model_selection import train_test_split

from .config import settings
from .feature_engineering import FeatureEngineer
from .storage import storage_manager, StoredArtifact


@dataclass
class TrainedModelArtifact:
    """Capture metadata around a trained ML model."""

    model_name: str
    version: str
    metrics: Dict[str, Any]
    storage_artifact: StoredArtifact
    feature_metadata_artifact: StoredArtifact


class ModelRegistry:
    """Handles versioned storage and retrieval of trained models."""

    def __init__(self, registry_dir: Optional[Path] = None) -> None:
        self.registry_dir = registry_dir or (settings.DATA_DIR / settings.MODELS_SUBDIR)
        self.registry_dir.mkdir(parents=True, exist_ok=True)

    def _artifact_name(self, model_name: str, version: str) -> str:
        return f"{model_name}_v{version}"

    def register_model(
        self,
        model_name: str,
        model: Any,
        feature_engineer: FeatureEngineer,
        metrics: Dict[str, Any],
    ) -> TrainedModelArtifact:
        version = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        artifact_name = self._artifact_name(model_name, version)

        model_bytes = joblib.dumps(model)
        fe_bytes = joblib.dumps(feature_engineer)

        logger.info(f"Persisting model {model_name} version {version}")
        model_artifact = storage_manager.save_bytes(
            buffer=model_bytes,
            artifact_name=f"{artifact_name}.joblib",
            subdir=settings.MODELS_SUBDIR,
        )
        feature_artifact = storage_manager.save_bytes(
            buffer=fe_bytes,
            artifact_name=f"{artifact_name}_features.joblib",
            subdir=settings.FEATURE_STORE_SUBDIR,
        )

        metadata = {
            "model_name": model_name,
            "version": version,
            "metrics": metrics,
            "stored_at": datetime.utcnow().isoformat(),
        }
        meta_path = self.registry_dir / f"{artifact_name}.json"
        meta_path.write_text(json.dumps(metadata, indent=2))

        self._enforce_retention(model_name)

        return TrainedModelArtifact(
            model_name=model_name,
            version=version,
            metrics=metrics,
            storage_artifact=model_artifact,
            feature_metadata_artifact=feature_artifact,
        )

    def load_latest(self, model_name: str) -> Tuple[Any, FeatureEngineer, Dict[str, Any]]:
        metadata_files = sorted(
            self.registry_dir.glob(f"{model_name}_v*.json"),
            reverse=True,
        )
        if not metadata_files:
            raise FileNotFoundError(f"No model registered under name {model_name}")
        latest_meta_file = metadata_files[0]
        metadata = json.loads(latest_meta_file.read_text())
        version = metadata["version"]
        artifact_name = self._artifact_name(model_name, version)

        model_bytes = storage_manager.load_bytes(
            f"{artifact_name}.joblib",
            subdir=settings.MODELS_SUBDIR,
        )
        feature_bytes = storage_manager.load_bytes(
            f"{artifact_name}_features.joblib",
            subdir=settings.FEATURE_STORE_SUBDIR,
        )
        model = joblib.loads(model_bytes)
        feature_engineer: FeatureEngineer = joblib.loads(feature_bytes)
        return model, feature_engineer, metadata

    def _enforce_retention(self, model_name: str) -> None:
        retention = settings.MODEL_REGISTRY_RETENTION
        metadata_files = sorted(self.registry_dir.glob(f"{model_name}_v*.json"))
        if len(metadata_files) <= retention:
            return
        for file_path in metadata_files[:-retention]:
            logger.info(f"Pruning old model artifact {file_path.name}")
            try:
                version = file_path.stem.split("_v")[-1]
                storage_manager.load_bytes(
                    f"{model_name}_v{version}.joblib",
                    subdir=settings.MODELS_SUBDIR,
                )  # ensure file exists
            except Exception:
                pass
            file_path.unlink(missing_ok=True)


class ModelTrainingService:
    """Encapsulates training pipelines for supervised models."""

    def __init__(self, model_registry: Optional[ModelRegistry] = None) -> None:
        self.registry = model_registry or ModelRegistry()

    def train_supervised_models(self, dataset: pd.DataFrame) -> Dict[str, TrainedModelArtifact]:
        logger.info("Starting supervised model training pipeline")
        X = dataset.drop(columns=[settings.TARGET_COLUMN])
        y = dataset[settings.TARGET_COLUMN].apply(lambda x: 1 if x == settings.POSITIVE_CLASS_LABEL else 0)

        feature_engineer = FeatureEngineer()
        X_transformed = feature_engineer.fit_transform(X)

        X_train, X_test, y_train, y_test = train_test_split(
            X_transformed,
            y,
            test_size=settings.TEST_SIZE,
            random_state=settings.RANDOM_STATE,
            stratify=y,
        )

        artifacts: Dict[str, TrainedModelArtifact] = {}
        metrics_map: Dict[str, Dict[str, Any]] = {}

        logistic = LogisticRegression(max_iter=1000)
        logistic.fit(X_train, y_train)
        metrics_map["logistic_regression"] = self._evaluate_model(logistic, X_test, y_test)
        artifacts["logistic_regression"] = self.registry.register_model(
            "logistic_regression",
            logistic,
            feature_engineer,
            metrics_map["logistic_regression"],
        )

        gbm = GradientBoostingClassifier(random_state=settings.RANDOM_STATE)
        gbm.fit(X_train, y_train)
        calibrated = CalibratedClassifierCV(gbm, method=settings.CALIBRATION_METHOD, cv=3)
        calibrated.fit(X_train, y_train)
        metrics_map["gradient_boosting"] = self._evaluate_model(calibrated, X_test, y_test)
        artifacts["gradient_boosting"] = self.registry.register_model(
            "gradient_boosting",
            calibrated,
            feature_engineer,
            metrics_map["gradient_boosting"],
        )

        logger.info("Model training completed", metrics=metrics_map)
        return artifacts

    @staticmethod
    def _evaluate_model(model: Any, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, Any]:
        predictions = model.predict(X_test)
        probabilities = model.predict_proba(X_test)[:, 1]
        precision, recall, fscore, support = precision_recall_fscore_support(
            y_test, predictions, average="binary", zero_division=0
        )

        metrics = {
            "roc_auc": roc_auc_score(y_test, probabilities),
            "precision": precision,
            "recall": recall,
            "fscore": fscore,
            "support_positive": int(support),
            "classification_report": classification_report(y_test, predictions),
        }
        fpr, tpr, thresholds = roc_curve(y_test, probabilities)
        metrics["roc_curve"] = {
            "false_positive_rate": fpr.tolist(),
            "true_positive_rate": tpr.tolist(),
            "thresholds": thresholds.tolist(),
        }
        return metrics













