"""
Persistencia SQLite del puente Pi → EC2 (Fase 7 §7).
"""
import asyncio
import json
import logging
import sqlite3
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)

_MAX_QUEUE_ROWS = 1000

_SCHEMA = """
CREATE TABLE IF NOT EXISTS state_queue (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS telemetry_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS alerts_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS config_cache (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    payload TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class BridgeStore:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._lock = asyncio.Lock()
        self._init_schema()

    def _init_schema(self) -> None:
        conn = sqlite3.connect(self._db_path)
        try:
            conn.executescript(_SCHEMA)
            conn.commit()
        finally:
            conn.close()
        logger.info("BridgeStore: schema inicializado en %s", self._db_path)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    async def enqueue_state(self, zonas: list[dict[str, Any]]) -> None:
        if not zonas:
            return
        payload = json.dumps(zonas)
        async with self._lock:
            await asyncio.to_thread(self._enqueue_state_sync, payload)

    def _enqueue_state_sync(self, payload: str) -> None:
        conn = self._connect()
        try:
            conn.execute(
                "INSERT INTO state_queue (id, payload, created_at, attempts) "
                "VALUES (1, ?, ?, 0) "
                "ON CONFLICT(id) DO UPDATE SET payload=excluded.payload, "
                "created_at=excluded.created_at, attempts=0",
                (payload, _now_iso()),
            )
            conn.commit()
        finally:
            conn.close()

    async def peek_state(self) -> Optional[tuple[list[dict[str, Any]], int]]:
        async with self._lock:
            return await asyncio.to_thread(self._peek_state_sync)

    def _peek_state_sync(self) -> Optional[tuple[list[dict[str, Any]], int]]:
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT payload, attempts FROM state_queue WHERE id = 1"
            ).fetchone()
            if row is None:
                return None
            return json.loads(row["payload"]), row["attempts"]
        finally:
            conn.close()

    async def clear_state(self) -> None:
        async with self._lock:
            await asyncio.to_thread(self._clear_state_sync)

    def _clear_state_sync(self) -> None:
        conn = self._connect()
        try:
            conn.execute("DELETE FROM state_queue WHERE id = 1")
            conn.commit()
        finally:
            conn.close()

    async def bump_state_attempts(self) -> None:
        async with self._lock:
            await asyncio.to_thread(self._bump_state_attempts_sync)

    def _bump_state_attempts_sync(self) -> None:
        conn = self._connect()
        try:
            conn.execute(
                "UPDATE state_queue SET attempts = attempts + 1 WHERE id = 1"
            )
            conn.commit()
        finally:
            conn.close()

    async def set_config_cache(self, payload: dict[str, Any]) -> None:
        body = json.dumps(payload)
        async with self._lock:
            await asyncio.to_thread(self._set_config_cache_sync, body)

    def _set_config_cache_sync(self, body: str) -> None:
        conn = self._connect()
        try:
            conn.execute(
                "INSERT INTO config_cache (id, payload, updated_at) "
                "VALUES (1, ?, ?) "
                "ON CONFLICT(id) DO UPDATE SET payload=excluded.payload, "
                "updated_at=excluded.updated_at",
                (body, _now_iso()),
            )
            conn.commit()
        finally:
            conn.close()

    async def get_config_cache(self) -> Optional[dict[str, Any]]:
        async with self._lock:
            return await asyncio.to_thread(self._get_config_cache_sync)

    def _get_config_cache_sync(self) -> Optional[dict[str, Any]]:
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT payload FROM config_cache WHERE id = 1"
            ).fetchone()
            if row is None:
                return None
            return json.loads(row["payload"])
        finally:
            conn.close()

    async def enqueue_telemetry(self, payload: dict[str, Any]) -> None:
        await self._enqueue_fifo("telemetry_queue", payload)

    async def enqueue_alert(self, payload: dict[str, Any]) -> None:
        await self._enqueue_fifo("alerts_queue", payload)

    async def _enqueue_fifo(self, table: str, payload: dict[str, Any]) -> None:
        body = json.dumps(payload)
        async with self._lock:
            await asyncio.to_thread(self._enqueue_fifo_sync, table, body)

    def _enqueue_fifo_sync(self, table: str, body: str) -> None:
        conn = self._connect()
        try:
            conn.execute(
                f"INSERT INTO {table} (payload, created_at, attempts) "
                f"VALUES (?, ?, 0)",
                (body, _now_iso()),
            )
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            if count > _MAX_QUEUE_ROWS:
                conn.execute(
                    f"DELETE FROM {table} WHERE id IN ("
                    f"SELECT id FROM {table} ORDER BY id ASC LIMIT ?)",
                    (count - _MAX_QUEUE_ROWS,),
                )
            conn.commit()
        finally:
            conn.close()

    async def peek_fifo(self, table: str) -> Optional[tuple[int, dict[str, Any], int]]:
        async with self._lock:
            return await asyncio.to_thread(self._peek_fifo_sync, table)

    def _peek_fifo_sync(self, table: str) -> Optional[tuple[int, dict[str, Any], int]]:
        conn = self._connect()
        try:
            row = conn.execute(
                f"SELECT id, payload, attempts FROM {table} ORDER BY id ASC LIMIT 1"
            ).fetchone()
            if row is None:
                return None
            return row["id"], json.loads(row["payload"]), row["attempts"]
        finally:
            conn.close()

    async def delete_fifo(self, table: str, row_id: int) -> None:
        async with self._lock:
            await asyncio.to_thread(self._delete_fifo_sync, table, row_id)

    def _delete_fifo_sync(self, table: str, row_id: int) -> None:
        conn = self._connect()
        try:
            conn.execute(f"DELETE FROM {table} WHERE id = ?", (row_id,))
            conn.commit()
        finally:
            conn.close()
