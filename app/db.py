from __future__ import annotations

import json
import sqlite3
from threading import RLock
from pathlib import Path
from typing import Any, Optional


class SQLiteStore:
    def __init__(self, db_path: str = "interflow.db") -> None:
        self.path = Path(db_path)
        # Background workflow tasks execute outside the request thread. SQLite
        # permits this when access to the shared connection is serialized.
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._lock = RLock()
        self._init_schema()

    def _init_schema(self) -> None:
        with self._lock:
            self._init_schema_locked()

    def _init_schema_locked(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS records (
              namespace TEXT NOT NULL,
              id TEXT NOT NULL,
              case_id TEXT,
              payload TEXT NOT NULL,
              created_at TEXT DEFAULT CURRENT_TIMESTAMP,
              updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
              PRIMARY KEY(namespace, id)
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
              id TEXT PRIMARY KEY,
              case_id TEXT NOT NULL,
              status TEXT NOT NULL,
              payload TEXT,
              created_at TEXT DEFAULT CURRENT_TIMESTAMP,
              updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.conn.commit()

    def upsert(self, namespace: str, object_id: str, payload: dict[str, Any], case_id: Optional[str] = None) -> None:
        with self._lock:
            self._upsert_locked(namespace, object_id, payload, case_id)

    def _upsert_locked(self, namespace: str, object_id: str, payload: dict[str, Any], case_id: Optional[str]) -> None:
        self.conn.execute(
            """
            INSERT INTO records(namespace, id, case_id, payload, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(namespace, id) DO UPDATE SET
              case_id=excluded.case_id,
              payload=excluded.payload,
              updated_at=CURRENT_TIMESTAMP
            """,
            (namespace, object_id, case_id, json.dumps(payload)),
        )
        self.conn.commit()

    def list_namespace(self, namespace: str, case_id: Optional[str] = None) -> list[dict[str, Any]]:
        with self._lock:
            if case_id:
                rows = self.conn.execute(
                    "SELECT payload FROM records WHERE namespace=? AND case_id=?", (namespace, case_id)
                ).fetchall()
            else:
                rows = self.conn.execute("SELECT payload FROM records WHERE namespace=?", (namespace,)).fetchall()
        return [json.loads(r["payload"]) for r in rows]

    def set_job(self, job_id: str, case_id: str, status: str, payload: Optional[dict[str, Any]] = None) -> None:
        with self._lock:
            self._set_job_locked(job_id, case_id, status, payload)

    def _set_job_locked(self, job_id: str, case_id: str, status: str, payload: Optional[dict[str, Any]]) -> None:
        self.conn.execute(
            """
            INSERT INTO jobs(id, case_id, status, payload, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
              status=excluded.status,
              payload=excluded.payload,
              updated_at=CURRENT_TIMESTAMP
            """,
            (job_id, case_id, status, json.dumps(payload or {})),
        )
        self.conn.commit()

    def get_job(self, job_id: str) -> Optional[dict[str, Any]]:
        with self._lock:
            row = self.conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "case_id": row["case_id"],
            "status": row["status"],
            "payload": json.loads(row["payload"] or "{}"),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
