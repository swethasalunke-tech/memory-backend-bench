"""A memory backend backed by a real SQLite table via stdlib `sqlite3`.

Unlike `InMemoryBackend`, this backend does real disk (or file-mode)
I/O through SQLite, which makes it a meaningful latency comparison point
against the pure-dict baseline. Nothing here is mocked: `store`/`retrieve`
issue real INSERT/SELECT statements, and `search` runs a real SQL LIKE
query to shortlist candidates before scoring them in Python with the same
keyword-overlap scorer used by `InMemoryBackend`.
"""

from __future__ import annotations

import sqlite3

from memory_bench.backend import MemoryBackendBase, keyword_overlap_score


class SQLiteBackend(MemoryBackendBase):
    """Stores key/value pairs in a SQLite table.

    Parameters
    ----------
    db_path:
        Path to the SQLite database file. Use ":memory:" for an
        in-process, non-persistent database (useful in tests).
    """

    def __init__(self, db_path: str = ":memory:") -> None:
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memory (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def store(self, key: str, value: str) -> None:
        self._conn.execute(
            """
            INSERT INTO memory (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, value),
        )
        self._conn.commit()

    def retrieve(self, key: str) -> str | None:
        cursor = self._conn.execute(
            "SELECT value FROM memory WHERE key = ?", (key,)
        )
        row = cursor.fetchone()
        return row[0] if row is not None else None

    def search(self, query: str, top_k: int) -> list[str]:
        if top_k <= 0:
            return []

        query = query.strip()
        if not query:
            return []

        tokens = [t for t in query.lower().split() if t]
        if not tokens:
            return []

        # Shortlist candidate rows with a real SQL LIKE query for any
        # token matching the value, then rank the shortlist in Python
        # with the shared keyword-overlap scorer (same scoring logic as
        # InMemoryBackend, so results are comparable across backends).
        where_clause = " OR ".join(["value LIKE ?"] * len(tokens))
        params = [f"%{t}%" for t in tokens]
        cursor = self._conn.execute(
            f"SELECT key, value FROM memory WHERE {where_clause}", params
        )
        rows = cursor.fetchall()

        scored: list[tuple[float, str]] = []
        for key, value in rows:
            score = keyword_overlap_score(query, value)
            if score > 0:
                scored.append((score, key))

        scored.sort(key=lambda pair: (-pair[0], pair[1]))
        return [key for _, key in scored[:top_k]]

    def close(self) -> None:
        self._conn.close()

    def __del__(self) -> None:
        try:
            self._conn.close()
        except Exception:
            pass
