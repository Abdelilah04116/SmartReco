"""Deterministic agent that orchestrates SmartReco pipeline."""
from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

from models.schemas import (
    AnalyzeResponse,
    FeatureResponse,
    PlotResponse,
    RecommendationResponse,
    RuleResponse,
)
from services import feature_engineering, plotting, rule_extraction


class SmartRecoAgent:
    """Rule-based pipeline that analyzes datasets and derives insights."""

    def __init__(self, df: pd.DataFrame, file_id: str) -> None:
        self.df = df
        self.file_id = file_id
        self.column_types = self._detect_column_types()

    def _detect_column_types(self) -> Dict[str, str]:
        types: Dict[str, str] = {}
        for col in self.df.columns:
            series = self.df[col]
            if pd.api.types.is_numeric_dtype(series):
                types[col] = "numeric"
            elif pd.api.types.is_datetime64_any_dtype(series):
                types[col] = "datetime"
            else:
                # attempt parsing to datetime to catch string dates
                parsed = pd.to_datetime(series, errors="coerce")
                if parsed.notna().sum() > 0.6 * len(parsed):
                    types[col] = "datetime"
                else:
                    types[col] = "categorical"
        return types

    def _descriptive_stats(self) -> Dict[str, Any]:
        desc = self.df.describe(include="all").transpose().fillna("").to_dict()
        shape = {"rows": int(self.df.shape[0]), "columns": int(self.df.shape[1])}
        missing = {col: int(self.df[col].isna().sum()) for col in self.df.columns}
        return {"describe": desc, "shape": shape, "missing_values": missing}

    def _correlation_insights(self) -> List[Dict[str, Any]]:
        insights: List[Dict[str, Any]] = []
        numeric_cols = [c for c, t in self.column_types.items() if t == "numeric"]
        if len(numeric_cols) < 2:
            return insights

        corr = self.df[numeric_cols].corr().fillna(0)
        for i, col_a in enumerate(numeric_cols):
            for col_b in numeric_cols[i + 1 :]:
                value = corr.loc[col_a, col_b]
                insights.append(
                    {
                        "pair": [col_a, col_b],
                        "correlation": round(float(value), 3),
                        "strength": "high" if abs(value) > 0.7 else "moderate",
                    }
                )
        insights.sort(key=lambda x: abs(x["correlation"]), reverse=True)
        return insights[:10]

    def analyze(self) -> AnalyzeResponse:
        plots = plotting.propose_plots(self.df, self.column_types)
        return AnalyzeResponse(
            file_id=self.file_id,
            column_types=self.column_types,
            descriptive_stats=self._descriptive_stats(),
            correlation_insights=self._correlation_insights(),
            suggested_plots=plots,
            dataset_overview={
                "row_count": int(self.df.shape[0]),
                "column_count": int(self.df.shape[1]),
                "numeric_columns": [c for c, t in self.column_types.items() if t == "numeric"],
                "categorical_columns": [c for c, t in self.column_types.items() if t == "categorical"],
                "datetime_columns": [c for c, t in self.column_types.items() if t == "datetime"],
            },
        )

    def generate_plots(self, requested_plots: List[Dict[str, Any]]) -> PlotResponse:
        rendered = plotting.generate_plots(self.df, requested_plots)
        return PlotResponse(file_id=self.file_id, plots=rendered)

    def suggest_features(self) -> FeatureResponse:
        suggestions = feature_engineering.suggest_features(self.df, self.column_types)
        return FeatureResponse(file_id=self.file_id, suggestions=suggestions)

    def extract_rules(self) -> RuleResponse:
        rules = rule_extraction.extract_rules(self.df, self.column_types)
        return RuleResponse(file_id=self.file_id, rules=rules)

    def recommend(self) -> RecommendationResponse:
        rules = self.extract_rules().rules
        actions = [
            {
                "title": "Validate dominant categories",
                "description": "Ensure dominant categorical values represent desired default behavior.",
                "priority": "medium",
            },
            {
                "title": "Monitor correlated metrics",
                "description": "Track highly correlated metrics together to avoid unintended effects.",
                "priority": "high",
            },
        ]
        insight_text = (
            "Automatic summary: dataset analyzed for correlations, dominant categories, and outliers. "
            "Recommendations prioritize data quality and business guardrails."
        )
        return RecommendationResponse(
            file_id=self.file_id,
            insights=insight_text,
            business_rules=rules,
            actions=[  # type: ignore[list-item]
                {
                    "title": act["title"],
                    "description": act["description"],
                    "priority": act["priority"],
                }
                for act in actions
            ],
        )


