"""Utilities for offline experimentation and benchmarking."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional

import json

from loguru import logger
from sklearn.metrics import roc_auc_score, confusion_matrix

from ..config import settings
from ..modeling import ModelTrainingService
from ..storage import storage_manager


@dataclass
class ExperimentResult:
    """Capture outcome of a single experiment run."""

    experiment_name: str
    dataset_id: str
    metrics: Dict[str, Any]
    model_versions: Dict[str, str]
    artifacts_path: Path


class ExperimentRunner:
    """Provides a structured way to run experiments and log outcomes."""

    def __init__(self, experiments_dir: Optional[Path] = None) -> None:
        self.experiments_dir = experiments_dir or (settings.DATA_DIR / settings.EXPERIMENTS_SUBDIR)
        self.experiments_dir.mkdir(parents=True, exist_ok=True)
        self.training_service = ModelTrainingService()

    def run_supervised_benchmark(self, dataset_id: str) -> ExperimentResult:
        logger.info(f"Running supervised benchmark experiment for dataset {dataset_id}")
        dataset = storage_manager.load_dataframe(dataset_id, subdir=settings.NORMALIZED_DATA_SUBDIR)
        target = dataset[settings.TARGET_COLUMN]

        baseline_score = dataset["priority_score"] if "priority_score" in dataset.columns else None
        artifacts = self.training_service.train_supervised_models(dataset)

        metrics = {"baseline": {}}
        if baseline_score is not None:
            metrics["baseline"]["roc_auc_vs_target"] = roc_auc_score(
                target.apply(lambda x: 1 if x == settings.POSITIVE_CLASS_LABEL else 0),
                baseline_score,
            )

        for name, artifact in artifacts.items():
            metrics[name] = artifact.metrics

        confusion = confusion_matrix(
            target.apply(lambda x: 1 if x == settings.POSITIVE_CLASS_LABEL else 0),
            (dataset["priority_score"] > 0).astype(int) if "priority_score" in dataset.columns else target.apply(lambda x: 1 if x == settings.POSITIVE_CLASS_LABEL else 0),
        )
        metrics["rules_confusion_matrix"] = confusion.tolist()

        result_file = self.experiments_dir / f"experiment_{dataset_id}.json"
        result_file.write_text(json.dumps(metrics, indent=2))

        model_versions = {name: artifact.version for name, artifact in artifacts.items()}
        logger.info(f"Experiment completed for dataset {dataset_id}", metrics=metrics, models=model_versions)

        return ExperimentResult(
            experiment_name="supervised_benchmark",
            dataset_id=dataset_id,
            metrics=metrics,
            model_versions=model_versions,
            artifacts_path=result_file,
        )


