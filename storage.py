"""
Storage layer for Mini URL Shortener.
Uses Python's standard library `sqlite3` for zero-dependency, persistent storage.
"""

import sqlite3
import contextlib
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Generator


def _get_utc_now_iso() -> str:
    """Returns the current UTC timestamp formatted as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


class Storage:
    def __init__(self, db_path: str = "urls.db"):
        self.db_path = db_path
        self._init_db()

    @contextlib.contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Provides a managed sqlite3 connection that always closes cleanly on exit."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self) -> None:
        """Initializes the database schema if it doesn't already exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS urls (
                    code TEXT PRIMARY KEY,
                    original_url TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    clicks INTEGER NOT NULL DEFAULT 0,
                    last_accessed TEXT
                )
                """
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_urls_original ON urls(original_url)"
            )
            conn.commit()

    def save_url(self, code: str, original_url: str) -> bool:
        """
        Saves a new short code and original URL mapping.
        Returns True if successful, False if code already exists.
        """
        created_at = _get_utc_now_iso()
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO urls (code, original_url, created_at, clicks, last_accessed)
                    VALUES (?, ?, ?, 0, NULL)
                    """,
                    (code, original_url, created_at),
                )
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False

    def get_url(self, code: str, increment_clicks: bool = True) -> Optional[str]:
        """
        Retrieves original URL for the given short code.
        Optionally increments click count and updates last_accessed timestamp.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT original_url, clicks FROM urls WHERE code = ?", (code,)
            )
            row = cursor.fetchone()
            if not row:
                return None

            if increment_clicks:
                now = _get_utc_now_iso()
                cursor.execute(
                    """
                    UPDATE urls
                    SET clicks = clicks + 1, last_accessed = ?
                    WHERE code = ?
                    """,
                    (now, code),
                )
                conn.commit()

            return row["original_url"]

    def get_stats(self, code: str) -> Optional[Dict[str, Any]]:
        """Retrieves metadata and usage statistics for a given short code."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT code, original_url, created_at, clicks, last_accessed
                FROM urls WHERE code = ?
                """,
                (code,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return dict(row)

    def list_urls(self, sort_by: str = "created_at", descending: bool = True) -> List[Dict[str, Any]]:
        """
        Returns all stored URL mappings.
        Supported sort_by options: 'created_at', 'clicks', 'code'.
        """
        valid_sort_cols = {
            "created_at": "created_at",
            "clicks": "clicks",
            "code": "code",
        }
        order_col = valid_sort_cols.get(sort_by, "created_at")
        direction = "DESC" if descending else "ASC"

        query = f"SELECT code, original_url, created_at, clicks, last_accessed FROM urls ORDER BY {order_col} {direction}"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def find_by_url(self, original_url: str) -> Optional[Dict[str, Any]]:
        """Finds if a URL has already been shortened."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT code, original_url, created_at, clicks, last_accessed FROM urls WHERE original_url = ?",
                (original_url,),
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def code_exists(self, code: str) -> bool:
        """Checks whether a short code exists."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM urls WHERE code = ?", (code,))
            return cursor.fetchone() is not None

    def delete_url(self, code: str) -> bool:
        """Deletes a short code entry. Returns True if found and deleted, False otherwise."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM urls WHERE code = ?", (code,))
            conn.commit()
            return cursor.rowcount > 0
