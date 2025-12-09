"""Data ingestion pipeline orchestrating validation, enrichment, and persistence."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, Any, Optional

import pandas as pd
from loguru import logger

from .config import settings
from .data_models import BankMarketingRecord
from .data_quality import validate_dataframe
from .storage import storage_manager
from .chunk_processor import chunk_processor
from .schema_detection import schema_detector
from .ai_agent import ai_agent


class DataIngestionService:
    """End-to-end ingestion service from raw CSV to normalized dataset."""

    def ingest(self, 
              df: pd.DataFrame, 
              source_filename: str,
              use_chunks: bool = True,
              chunk_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Ingest dataset with automatic chunking for large files.
        
        Args:
            df: Input DataFrame
            source_filename: Source file name
            use_chunks: Whether to process in chunks for large datasets
            chunk_size: Optional chunk size override
        """
        logger.info(f"Ingesting dataset from {source_filename} ({len(df)} rows, {len(df.columns)} columns)")
        
        # Estimate memory usage
        memory_info = chunk_processor.estimate_memory_usage(df)
        logger.info(f"Dataset memory usage: {memory_info['total_memory_mb']:.2f} MB")
        
        # Use chunking for large datasets (>100MB or >100k rows)
        if use_chunks and (memory_info['total_memory_mb'] > 100 or len(df) > 100000):
            logger.info("Processing dataset in chunks")
            return self._ingest_chunked(df, source_filename, chunk_size)
        else:
            return self._ingest_single(df, source_filename)

    def _ingest_single(self, df: pd.DataFrame, source_filename: str) -> Dict[str, Any]:
        """Ingest dataset as single batch."""
        # Use flexible validation (accepts any CSV structure)
        cleaned_df, quality_report = validate_dataframe(df, strict_schema=False)
        dataset_id = uuid.uuid4().hex
        
        logger.info(
            "Data validation complete",
            dataset_id=dataset_id,
            records_valid=quality_report.records_valid,
            records_invalid=quality_report.records_invalid,
        )

        enriched_df = self._enrich(cleaned_df, dataset_id)

        # Detect schema for metadata
        schema = schema_detector.detect_schema(enriched_df, sample_size=min(1000, len(enriched_df)))
        
        # AI Agent analysis (if enabled)
        ai_analysis = None
        if settings.AI_AGENT_ENABLED:
            try:
                logger.info("Running AI agent analysis...")
                ai_analysis = ai_agent.analyze_dataset(enriched_df, sample_size=min(5000, len(enriched_df)))
                
                # Apply AI-suggested transformations
                if ai_analysis.get("transformation_plan"):
                    logger.info("Applying AI-suggested transformations...")
                    enriched_df = ai_agent.apply_transformations(enriched_df, ai_analysis["transformation_plan"])
                    logger.info("AI transformations applied successfully")
            except Exception as e:
                logger.warning(f"AI agent analysis failed: {e}. Continuing without AI recommendations.")

        metadata = {
            "dataset_id": dataset_id,
            "source_filename": source_filename,
            "ingestion_timestamp": datetime.utcnow().isoformat(),
            "quality_report": quality_report.to_dict(),
            "columns": enriched_df.columns.tolist(),
            "schema": schema,
            "row_count": len(enriched_df),
            "column_count": len(enriched_df.columns),
            "ai_analysis": ai_analysis,
        }
        
        storage_manager.save_dataframe(
            enriched_df,
            artifact_name=dataset_id,
            subdir=settings.NORMALIZED_DATA_SUBDIR,
            format="parquet",
            metadata=metadata,
        )

        return metadata

    def _ingest_chunked(self, 
                       df: pd.DataFrame, 
                       source_filename: str,
                       chunk_size: Optional[int] = None) -> Dict[str, Any]:
        """Ingest dataset in chunks."""
        dataset_id = uuid.uuid4().hex
        chunk_size = chunk_size or 10000
        
        all_chunks = []
        total_valid = 0
        total_invalid = 0
        
        # Process in chunks
        for chunk in chunk_processor.process_dataframe_chunks(df, chunk_size):
            cleaned_chunk, quality_report = validate_dataframe(chunk, strict_schema=False)
            enriched_chunk = self._enrich(cleaned_chunk, dataset_id)
            all_chunks.append(enriched_chunk)
            total_valid += quality_report.records_valid
            total_invalid += quality_report.records_invalid
        
        # Combine all chunks
        enriched_df = pd.concat(all_chunks, ignore_index=True)
        logger.info(f"Combined {len(all_chunks)} chunks into {len(enriched_df)} rows")
        
        # Detect schema
        schema = schema_detector.detect_schema(enriched_df, sample_size=min(1000, len(enriched_df)))
        
        # AI Agent analysis (if enabled)
        ai_analysis = None
        if settings.AI_AGENT_ENABLED:
            try:
                logger.info("Running AI agent analysis on chunked dataset...")
                ai_analysis = ai_agent.analyze_dataset(enriched_df, sample_size=min(5000, len(enriched_df)))
                
                # Apply AI-suggested transformations
                if ai_analysis.get("transformation_plan"):
                    logger.info("Applying AI-suggested transformations...")
                    enriched_df = ai_agent.apply_transformations(enriched_df, ai_analysis["transformation_plan"])
                    logger.info("AI transformations applied successfully")
            except Exception as e:
                logger.warning(f"AI agent analysis failed: {e}. Continuing without AI recommendations.")
        
        quality_report_dict = {
            "timestamp": datetime.utcnow().isoformat(),
            "records_total": len(df),
            "records_valid": total_valid,
            "records_invalid": total_invalid,
            "invalid_indices": [],
            "anomalies": {},
        }
        
        metadata = {
            "dataset_id": dataset_id,
            "source_filename": source_filename,
            "ingestion_timestamp": datetime.utcnow().isoformat(),
            "quality_report": quality_report_dict,
            "columns": enriched_df.columns.tolist(),
            "schema": schema,
            "row_count": len(enriched_df),
            "column_count": len(enriched_df.columns),
            "processed_in_chunks": True,
            "chunk_count": len(all_chunks),
            "ai_analysis": ai_analysis,
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
        """Enrich dataset with metadata columns."""
        logger.info("Enriching dataset with normalized columns")
        df = df.copy()
        df["dataset_id"] = dataset_id
        df["ingestion_timestamp"] = datetime.utcnow()
        
        # Only apply legacy enrichments if columns exist (backward compatibility)
        if "contact" in df.columns:
            df["normalized_contact"] = df["contact"].replace({"unknown": "cellular"})
        
        if "pdays" in df.columns:
            df["is_contact_recent"] = df["pdays"].apply(lambda x: x <= 7 and x != -1 if pd.notna(x) else False)
        
        if "balance" in df.columns and "age" in df.columns:
            df["balance_to_age_ratio"] = df.apply(
                lambda row: (row["balance"] / row["age"]) if row["age"] and row["age"] != 0 else None,
                axis=1,
            )
            df["age_balance_interaction"] = df["age"] * (df["balance"].abs() + 1) ** 0.5
        
        if "contact" in df.columns and "campaign" in df.columns:
            contact_freq = df.groupby("contact")["campaign"].transform("count")
            df["contact_frequency_score"] = contact_freq / contact_freq.max() if contact_freq.max() > 0 else 0.0
        
        # Rename target column if exists
        if "y" in df.columns and settings.TARGET_COLUMN != "y":
            df.rename(columns={"y": settings.TARGET_COLUMN}, inplace=True)
        
        logger.info("Dataset enrichment complete", rows=len(df))
        return df


data_ingestion_service = DataIngestionService()









