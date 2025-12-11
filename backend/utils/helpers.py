"""Helper utilities for data handling and common operations."""
from __future__ import annotations

import threading
import uuid
from pathlib import Path
from typing import Any, Dict, List, Tuple

import chardet
import csv
import pandas as pd
from fastapi import HTTPException, UploadFile, status
from loguru import logger

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "uploads"
DATA_DIR.mkdir(parents=True, exist_ok=True)

_DATASETS: Dict[str, Dict[str, Any]] = {}
_LAST_FILE_ID: str | None = None
_LOCK = threading.Lock()


def detect_encoding(raw_bytes: bytes) -> str:
    """Detect encoding for incoming file bytes."""
    if not raw_bytes:
        return "utf-8"
    detection = chardet.detect(raw_bytes)
    return detection.get("encoding") or "utf-8"


def sniff_dialect(sample: str) -> tuple[str, bool]:
    """Detect delimiter and header presence using csv.Sniffer."""
    sniffer = csv.Sniffer()
    try:
        dialect = sniffer.sniff(sample)
        has_header = sniffer.has_header(sample)
        return dialect.delimiter or ",", has_header
    except csv.Error:
        return ",", True


def save_upload_file(file: UploadFile) -> Tuple[str, str, str, bool]:
    """Save an uploaded CSV to disk and register metadata plus dialect."""
    try:
        raw_bytes = file.file.read()
        encoding = detect_encoding(raw_bytes)
        sample = raw_bytes[:5000].decode(encoding, errors="ignore")
        delimiter, has_header = sniff_dialect(sample)

        file_id = uuid.uuid4().hex
        target_path = DATA_DIR / f"{file_id}.csv"

        with target_path.open("wb") as f:
            f.write(raw_bytes)

        with _LOCK:
            _DATASETS[file_id] = {
                "path": target_path,
                "encoding": encoding,
                "delimiter": delimiter,
                "has_header": has_header,
                "original_name": file.filename or "dataset.csv",
            }
            global _LAST_FILE_ID
            _LAST_FILE_ID = file_id
            logger.info(f"Dataset upload/save: id={file_id} name={file.filename} encoding={encoding} delimiter={delimiter}")
        return file_id, encoding, delimiter, has_header
    except Exception as exc:
        logger.error(f"Error in save_upload_file: {exc!r}")
        raise


def _register_existing_file(path: Path) -> str | None:
    """Register a CSV already on disk (used after restarts)."""
    try:
        raw_bytes = path.read_bytes()
    except FileNotFoundError:
        return None

    encoding = detect_encoding(raw_bytes)
    file_id = path.stem

    with _LOCK:
        if file_id in _DATASETS:
            return file_id
        _DATASETS[file_id] = {
            "path": path,
            "encoding": encoding,
            "original_name": path.name,
        }
        global _LAST_FILE_ID
        _LAST_FILE_ID = file_id
    return file_id


def bootstrap_from_disk() -> str | None:
    """
    If the in-memory registry is empty (e.g., after a restart), attempt to
    re-register the most recent CSV found on disk so that previously uploaded
    datasets remain usable.
    """
    with _LOCK:
        if _DATASETS:
            return _LAST_FILE_ID

    csv_files = sorted(DATA_DIR.glob("*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
    for path in csv_files:
        registered = _register_existing_file(path)
        if registered:
            return registered
    return None


def _get_metadata(file_id: str) -> Dict[str, Any]:
    """Retrieve metadata, raising 404 if missing."""
    if not _DATASETS:
        bootstrap_from_disk()
    with _LOCK:
        meta = _DATASETS.get(file_id)
    if not meta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found. Please upload again."
        )
    return meta


def load_dataframe(file_id: str) -> pd.DataFrame:
    """Load a dataframe from the registry."""
    logger.info(f"Chargement du dataframe file_id={file_id}")
    meta = _get_metadata(file_id)
    read_kwargs = {
        "encoding": meta.get("encoding", "utf-8"),
        "sep": meta.get("delimiter", ","),
        "header": 0 if meta.get("has_header", True) else None,
    }
    try:
        df = pd.read_csv(meta["path"], **read_kwargs)
        logger.info(f"Lecture dataframe OK: file_id={file_id}, shape={df.shape}")
    except UnicodeDecodeError:
        read_kwargs["encoding"] = "latin-1"
        df = pd.read_csv(meta["path"], **read_kwargs)
        logger.warning(f"UnicodeDecodeError corrigé pour file_id={file_id}, relu en latin-1")
    except Exception as exc:
        logger.error(f"Erreur chargement CSV: file_id={file_id}, erreur={exc!r}, kwargs={read_kwargs}")
        raise
    return df


def get_path(file_id: str) -> Path:
    """Return dataset path."""
    meta = _get_metadata(file_id)
    return meta["path"]


def dataset_exists(file_id: str) -> bool:
    """Check if dataset id is registered."""
    if not _DATASETS:
        bootstrap_from_disk()
    with _LOCK:
        return file_id in _DATASETS


def dataset_count() -> int:
    """Return how many datasets are currently registered."""
    if not _DATASETS:
        bootstrap_from_disk()
    with _LOCK:
        return len(_DATASETS)


def has_any_dataset() -> bool:
    """Shortcut boolean for data availability checks."""
    return dataset_count() > 0


def get_last_file_id() -> str | None:
    """Return the most recently registered dataset id, if any."""
    if not _DATASETS:
        bootstrap_from_disk()
    with _LOCK:
        return _LAST_FILE_ID


def get_preview(df: pd.DataFrame) -> Dict[str, Any]:
    """Return a JSON-friendly preview of a dataframe."""
    try:
        sample_rows = df.head(20)
        rows = sample_rows.replace({pd.NA: None}).to_dict(orient="records")
        dtypes = {col: str(dtype) for col, dtype in df.dtypes.items()}

        columns: List[Dict[str, Any]] = []
        for col in df.columns:
            series = df[col]
            non_nulls = int(series.notna().sum())
            unique_vals = int(series.nunique(dropna=True))
            sample_values = series.dropna().astype(str).head(5).tolist()
            columns.append(
                {
                    "name": col,
                    "dtype": str(series.dtype),
                    "non_nulls": non_nulls,
                    "unique": unique_vals,
                    "sample_values": sample_values,
                }
            )
        logger.info(f"Preview dataframe généré: {len(rows)} lignes, {len(columns)} colonnes.")
        return {"rows": rows, "dtypes": dtypes, "columns": columns}
    except Exception as exc:
        logger.error(f"Erreur preview dataframe: {exc!r}")
        raise


def get_registered_file_name(file_id: str) -> str:
    """Return original filename for a dataset id."""
    return _get_metadata(file_id)["original_name"]





