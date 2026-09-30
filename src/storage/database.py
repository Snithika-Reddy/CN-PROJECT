"""SQLite Database Manager and Connection Engine.

Provides thread-safe connections, WAL journaling, automatic schema provisioning,
and transaction management for authoritative historical telemetry storage.
"""

from contextlib import contextmanager
import logging
import os
from pathlib import Path
import sqlite3
from typing import Any, Generator
import pandas as pd

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages the lifecycle, schema provisioning, and connection pool of the SQLite database."""

    def __init__(self, db_path: str = "database/network_monitor.db", schema_path: str = "database/schema.sql"):
        self.db_path = Path(db_path)
        self.schema_path = Path(schema_path)
        self._ensure_database_initialized()

    def _ensure_database_initialized(self) -> None:
        """Create parent directory and apply DDL schema if tables do not exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.schema_path.exists():
            logger.warning(f"Schema file not found at {self.schema_path}, skipping initial DDL run.")
            return

        with self.get_connection() as conn:
            with open(self.schema_path, "r", encoding="utf-8") as f:
                schema_sql = f.read()
            conn.executescript(schema_sql)
            logger.info(f"Database schema verified/provisioned at {self.db_path}")

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager providing an optimized, thread-safe SQLite connection."""
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=10.0,
            check_same_thread=False
        )
        conn.row_factory = sqlite3.Row
        # Performance and integrity pragmas
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA busy_timeout = 5000;")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def execute_query(self, query: str, params: tuple = ()) -> list[sqlite3.Row]:
        """Execute a SELECT query and return list of sqlite3.Row results."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()

    def execute_non_query(self, query: str, params: tuple = ()) -> int:
        """Execute an INSERT, UPDATE, or DELETE query and return the last row ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.lastrowid or cursor.rowcount

    def execute_many(self, query: str, param_list: list[tuple]) -> int:
        """Batch insert/update for performance."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, param_list)
            return cursor.rowcount

    def query_df(self, query: str, params: tuple = ()) -> pd.DataFrame:
        """Execute query and return results directly as a Pandas DataFrame."""
        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)
