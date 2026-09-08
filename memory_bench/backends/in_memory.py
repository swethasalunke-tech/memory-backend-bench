"""A trivial in-process memory backend backed by a Python dict.

This is the baseline backend: no persistence, no I/O, just a dict lookup.
It exists as a lower bound for latency comparisons against backends that
do real I/O (e.g. SQLite).
"""

from __future__ import annotations

from memory_bench.backend import MemoryBackendBase, keyword_overlap_score


class InMemoryBackend(MemoryBackendBase):
    """Stores key/value pairs in a plain Python dict."""

    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    def store(self, key: str, value: str) -> None:
        self._store[key] = value

    def retrieve(self, key: str) -> str | None:
        return self._store.get(key)

    def search(self, query: str, top_k: int) -> list[str]:
        if top_k <= 0:
            return []

        scored: list[tuple[float, str]] = []
        for key, value in self._store.items():
            score = keyword_overlap_score(query, value)
            if score > 0:
                scored.append((score, key))

        # Sort by score descending, then by key for stable/deterministic
        # ordering when scores tie.
        scored.sort(key=lambda pair: (-pair[0], pair[1]))
        return [key for _, key in scored[:top_k]]
