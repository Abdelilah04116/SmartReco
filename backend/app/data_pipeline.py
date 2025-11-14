"""Data ingestion pipeline orchestrating validation, enrichment, and persistence."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, Any

import pandas as pd
from loguru import logger

from .config import settings
from .data_models import BankMarketingRecord
from .data_quality import validate_dataframe
from .storage import storage_manager


class DataIngestionService:
    """End-to-end ingestion service from raw CSV to normalized dataset."""

    def ingest(self, df: pd.DataFrame, source_filename: str) -> Dict[str, Any]:
        logger.info(f"Ingesting dataset from {source_filename}")
        cleaned_df, quality_report = validate_dataframe(df)
        dataset_id = uuid.uuid4().hex
        logger.info(
            "Data validation complete",
            dataset_id=dataset_id,
            records_valid=quality_report.records_valid,
            records_invalid=quality_report.records_invalid,
        )

        enriched_df = self._enrich(cleaned_df, dataset_id)

        metadata = {
            "dataset_id": dataset_id,
            "source_filename": source_filename,
            "ingestion_timestamp": datetime.utcnow().isoformat(),
            "quality_report": quality_report.to_dict(),
            "columns": enriched_df.columns.tolist(),
        }
        storage_manager.save_dataframe(
            enriched_df,
            artifact_name=dataset_id,
            subdir=settings.NORMALIZED_DATA_SUBDIR,
            format="parquet",
            metadata=metadata,
        )

        return metadata

    def _enrich(self, df: pd.DataFrame, dataset_id: str) -> pd.DataFrame:
        logger.info("Enriching dataset with normalized columns")
        df = df.copy()
        df["dataset_id"] = dataset_id
        df["ingestion_timestamp"] = datetime.utcnow()
        df["normalized_contact"] = df["contact"].replace({"unknown": "cellular"})
        df["is_contact_recent"] = df["pdays"].apply(lambda x: x <= 7 and x != -1)
        df["balance_to_age_ratio"] = df.apply(
            lambda row: (row["balance"] / row["age"]) if row["age"] else None,
            axis=1,
        )
        df["age_balance_interaction"] = df["age"] * (df["balance"].abs() + 1) ** 0.5
        contact_freq = df.groupby("contact")["campaign"].transform("count")
        df["contact_frequency_score"] = contact_freq / contact_freq.max()
        df.rename(columns={"y": settings.TARGET_COLUMN}, inplace=True)

        normalized_records = []
        for record in df.to_dict(orient="records"):
            normalized_records.append(BankMarketingRecord(**record).model_dump(by_alias=True))
        normalized_df = pd.DataFrame(normalized_records)
        logger.info("Dataset enrichment complete", rows=len(normalized_df))
        return normalized_df


data_ingestion_service = DataIngestionService()




