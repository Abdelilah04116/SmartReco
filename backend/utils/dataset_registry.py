"""Persistent dataset registry with metadata and caching helpers."""
from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

REGISTRY_PATH = Path(__file__).resolve().parent.parent / "data" / "metadata"
REGISTRY_PATH.mkdir(parents=True, exist_ok=True)
REGISTRY_FILE = REGISTRY_PATH / "registry.json"

_LOCK = threading.Lock()
_REGISTRY: Dict[str, Dict[str, Any]] = {}


def _load() -> None:
    if REGISTRY_FILE.exists():
        try:
            data = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
        with _LOCK:
            _REGISTRY.clear()
            _REGISTRY.update(data)


def _save() -> None:
    with _LOCK:
        REGISTRY_FILE.write_text(json.dumps(_REGISTRY, indent=2, default=str), encoding="utf-8")


def register_dataset(
    file_id: str,
    *,
    name: str,
    path: str,
    encoding: str,
    rows: int,
    columns: int,
    delimiter: str,
    has_header: bool,
    detected_types: Dict[str, str],
) -> None:
    """Register dataset metadata with timestamp."""
    created_at = datetime.now(timezone.utc).isoformat()
    _load()
    with _LOCK:
        _REGISTRY[file_id] = {
            "file_id": file_id,
            "name": name,
            "path": path,
            "encoding": encoding,
            "rows": rows,
            "columns": columns,
            "delimiter": delimiter,
            "has_header": has_header,
            "detected_types": detected_types,
            "created_at": created_at,
            "updated_at": created_at,
        }
    _save()


def list_datasets() -> List[Dict[str, Any]]:
    """Return all datasets sorted by creation date desc."""
    _load()
    with _LOCK:
        return sorted(_REGISTRY.values(), key=lambda x: x.get("created_at", ""), reverse=True)


def get_dataset(file_id: str) -> Optional[Dict[str, Any]]:
    _load()
    with _LOCK:
        return _REGISTRY.get(file_id)


def update_timestamp(file_id: str) -> None:
    _load()
    with _LOCK:
        if file_id in _REGISTRY:
            _REGISTRY[file_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
            _save()


def dataset_count() -> int:
    _load()
    with _LOCK:
        return len(_REGISTRY)


def last_dataset_id() -> Optional[str]:
    datasets = list_datasets()
    return datasets[0]["file_id"] if datasets else None


