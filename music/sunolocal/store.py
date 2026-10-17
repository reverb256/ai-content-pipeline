"""
SQLite job store for sunolocal.

The DB path is resolved per call so tests can point SUNOLOCAL_DB at a
temporary file.
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from .spec import SunoGenerateRequest

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    request TEXT NOT NULL,
    status TEXT NOT NULL,
    result TEXT,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);
"""


def _db_path() -> Path:
    default = Path.home() / ".local" / "share" / "sunolocal" / "jobs.sqlite3"
    return Path(os.environ.get("SUNOLOCAL_DB", str(default)))


def _get_conn() -> sqlite3.Connection:
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _get_conn() as conn:
        conn.executescript(SCHEMA)


def _to_jsonable(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_jsonable(v) for v in obj]
    if hasattr(obj, "__dataclass_fields__"):
        return {k: _to_jsonable(getattr(obj, k)) for k in obj.__dataclass_fields__}
    return obj


def create_job(request: SunoGenerateRequest) -> str:
    job_id = uuid.uuid4().hex
    now = time.time()
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO jobs (job_id, request, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (job_id, json.dumps(_to_jsonable(request)), "pending", now, now),
        )
    return job_id


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    with _get_conn() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
    return dict(row) if row is not None else None


def update_job_status(job_id: str, status: str, result: Optional[Any] = None) -> None:
    now = time.time()
    with _get_conn() as conn:
        if result is None:
            conn.execute(
                "UPDATE jobs SET status = ?, updated_at = ? WHERE job_id = ?",
                (status, now, job_id),
            )
        else:
            conn.execute(
                "UPDATE jobs SET status = ?, result = ?, updated_at = ? WHERE job_id = ?",
                (status, json.dumps(_to_jsonable(result)), now, job_id),
            )


def list_jobs(limit: int = 100) -> List[Dict[str, Any]]:
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT job_id, status, created_at, updated_at FROM jobs ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def delete_old_jobs(older_than_seconds: int = 86400) -> None:
    cutoff = time.time() - older_than_seconds
    with _get_conn() as conn:
        conn.execute("DELETE FROM jobs WHERE updated_at < ?", (cutoff,))
