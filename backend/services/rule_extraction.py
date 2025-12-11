"""Rule extraction heuristics for SmartReco."""
from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd

from models.schemas import RuleCandidate


def correlation_rules(df: pd.DataFrame, column_types: Dict[str, str], threshold: float = 0.7) -> List[RuleCandidate]:
    numeric_cols = [c for c, t in column_types.items() if t == "numeric"]
    rules: List[RuleCandidate] = []
    if len(numeric_cols) < 2:
        return rules

    corr = df[numeric_cols].corr().fillna(0)
    for i, col_a in enumerate(numeric_cols):
        for col_b in numeric_cols[i + 1 :]:
            value = corr.loc[col_a, col_b]
            if abs(value) >= threshold:
                rules.append(
                    RuleCandidate(
                        rule=f"When {col_a} changes, {col_b} moves in tandem (corr={value:.2f})",
                        rationale="Strong correlation suggests a coupled business metric.",
                        severity="high" if abs(value) > 0.85 else "medium",
                    )
                )
    return rules


def dominance_rules(df: pd.DataFrame, column_types: Dict[str, str], ratio_threshold: float = 0.7) -> List[RuleCandidate]:
    rules: List[RuleCandidate] = []
    categorical_cols = [c for c, t in column_types.items() if t == "categorical"]
    for col in categorical_cols:
        counts = df[col].value_counts(dropna=True)
        if counts.empty:
            continue
        top_value = counts.idxmax()
        top_ratio = counts.iloc[0] / max(1, counts.sum())
        if top_ratio >= ratio_threshold:
            rules.append(
                RuleCandidate(
                    rule=f"Category '{top_value}' dominates {col} ({top_ratio:.0%})",
                    rationale="High dominance indicates a potential default behavior or market share.",
                    severity="medium",
                )
            )
    return rules


def outlier_rules(df: pd.DataFrame, column_types: Dict[str, str], z_threshold: float = 3.0) -> List[RuleCandidate]:
    rules: List[RuleCandidate] = []
    for col, dtype in column_types.items():
        if dtype != "numeric":
            continue
        series = pd.to_numeric(df[col], errors="coerce").dropna()
        if series.empty:
            continue
        zscores = (series - series.mean()) / (series.std() + 1e-9)
        outlier_ratio = float((np.abs(zscores) > z_threshold).sum()) / max(len(series), 1)
        if outlier_ratio > 0.02:
            rules.append(
                RuleCandidate(
                    rule=f"{col} shows {outlier_ratio:.1%} outliers beyond z>{z_threshold}",
                    rationale="Outliers may signal quality issues or rare high-impact events.",
                    severity="high" if outlier_ratio > 0.1 else "medium",
                )
            )
    return rules


def extract_rules(df: pd.DataFrame, column_types: Dict[str, str]) -> List[RuleCandidate]:
    """Aggregate rule candidates from multiple heuristics."""
    rules: List[RuleCandidate] = []
    rules.extend(correlation_rules(df, column_types))
    rules.extend(dominance_rules(df, column_types))
    rules.extend(outlier_rules(df, column_types))
    # Deduplicate by rule text
    seen = set()
    unique_rules: List[RuleCandidate] = []
    for rule in rules:
        if rule.rule not in seen:
            unique_rules.append(rule)
            seen.add(rule.rule)
    return unique_rules


