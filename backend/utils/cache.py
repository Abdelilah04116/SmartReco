"""Lightweight cache for analysis artifacts keyed by file_id."""
from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any, Dict, Optional

CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

_LOCK = threading.Lock()


def _path(file_id: str) -> Path:
    return CACHE_DIR / f"{file_id}.json"


def set_cache(file_id: str, payload: Dict[str, Any]) -> None:
    """Persist cache to disk (JSON-serializable)."""
    with _LOCK:
        _path(file_id).write_text(json.dumps(payload), encoding="utf-8")


def get_cache(file_id: str) -> Optional[Dict[str, Any]]:
    path = _path(file_id)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def invalidate(file_id: str) -> None:
    path = _path(file_id)
    if path.exists():
        try:
            path.unlink()
        except OSError:
            pass


def clear_all() -> None:
    for f in CACHE_DIR.glob("*.json"):
        try:
            f.unlink()
        except OSError:
            continue


