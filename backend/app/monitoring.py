"""Model monitoring utilities for production drift and KPI tracking."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, Any

import numpy as np
import pandas as pd
from loguru import logger
from scipy import stats

from .config import settings


def compute_monitoring_metrics(scores: pd.Series, outcomes: pd.Series) -> Dict[str, Any]:
    """Compute monitoring KPIs for the scoring service."""
    metrics = {
        "timestamp": datetime.utcnow().isoformat(),
        "score_mean": float(scores.mean()),
        "score_std": float(scores.std()),
        "score_min": float(scores.min()),
        "score_max": float(scores.max()),
        "conversion_rate": float((outcomes == settings.POSITIVE_CLASS_LABEL).mean()),
        "uplift_estimate": float(_estimate_uplift(scores, outcomes)),
    }
    return metrics


def detect_drift(current_scores: pd.Series, reference_scores: pd.Series) -> Dict[str, Any]:
    """Detect drift using Kolmogorov–Smirnov test."""
    ks_statistic, p_value = stats.ks_2samp(reference_scores, current_scores)
    drift_detected = p_value < settings.DRIFT_THRESHOLD
    logger.info("Drift detection run", ks_statistic=ks_statistic, p_value=p_value, drift=drift_detected)
    return {
        "ks_statistic": float(ks_statistic),
        "p_value": float(p_value),
        "drift_detected": drift_detected,
        "threshold": settings.DRIFT_THRESHOLD,
    }


def _estimate_uplift(scores: pd.Series, outcomes: pd.Series) -> float:
    """Rough uplift estimation using top quantile comparison."""
    threshold = scores.quantile(0.8)
    treated = outcomes[scores >= threshold]
    control = outcomes[scores < threshold]
    treated_rate = (treated == settings.POSITIVE_CLASS_LABEL).mean() if len(treated) else 0.0
    control_rate = (control == settings.POSITIVE_CLASS_LABEL).mean() if len(control) else 0.0
    return treated_rate - control_rate









