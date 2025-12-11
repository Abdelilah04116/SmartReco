"""Helper utilities for data handling and common operations."""
from __future__ import annotations

import io
import threading
import uuid
from pathlib import Path
from typing import Any, Dict, List, Tuple

import chardet
import pandas as pd
from fastapi import HTTPException, UploadFile, status

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "uploads"
DATA_DIR.mkdir(parents=True, exist_ok=True)

_DATASETS: Dict[str, Dict[str, Any]] = {}
_LOCK = threading.Lock()


def detect_encoding(raw_bytes: bytes) -> str:
    """Detect encoding for incoming file bytes."""
    if not raw_bytes:
        return "utf-8"
    detection = chardet.detect(raw_bytes)
    return detection.get("encoding") or "utf-8"


def save_upload_file(file: UploadFile) -> Tuple[str, str]:
    """Save an uploaded CSV to disk and register metadata."""
    raw_bytes = file.file.read()
    encoding = detect_encoding(raw_bytes)
    file_id = uuid.uuid4().hex
    target_path = DATA_DIR / f"{file_id}.csv"

    with target_path.open("wb") as f:
        f.write(raw_bytes)

    with _LOCK:
        _DATASETS[file_id] = {
            "path": target_path,
            "encoding": encoding,
            "original_name": file.filename or "dataset.csv",
        }

    return file_id, encoding


def _get_metadata(file_id: str) -> Dict[str, Any]:
    """Retrieve metadata, raising 404 if missing."""
    with _LOCK:
        meta = _DATASETS.get(file_id)
    if not meta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found. Please upload again."
        )
    return meta


def load_dataframe(file_id: str) -> pd.DataFrame:
    """Load a dataframe from the registry."""
    meta = _get_metadata(file_id)
    try:
        df = pd.read_csv(meta["path"], encoding=meta["encoding"])
    except UnicodeDecodeError:
        # fallback with latin-1 if detection failed
        df = pd.read_csv(meta["path"], encoding="latin-1")
    return df


def dataset_exists(file_id: str) -> bool:
    """Check if dataset id is registered."""
    with _LOCK:
        return file_id in _DATASETS


def get_preview(df: pd.DataFrame) -> Dict[str, Any]:
    """Return a JSON-friendly preview of a dataframe."""
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

    return {"rows": rows, "dtypes": dtypes, "columns": columns}


def get_registered_file_name(file_id: str) -> str:
    """Return original filename for a dataset id."""
    return _get_metadata(file_id)["original_name"]



