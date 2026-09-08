"""Defines the common interface every memory backend must implement.

A memory backend is a simple key/value store with an additional `search`
method that lets an agent look up entries by approximate relevance to a
query string, rather than by exact key. This module defines that interface
as a `Protocol` (structural typing) plus an `ABC` base class that concrete
backends may subclass for convenience (neither is required — any object
satisfying the method signatures below works with the harness).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable


@runtime_checkable
class MemoryBackend(Protocol):
    """Structural interface for a memory backend.

    Any object implementing these three methods with these signatures is a
    valid backend, whether or not it subclasses `MemoryBackendBase`.
    """

    def store(self, key: str, value: str) -> None:
        """Persist `value` under `key`, overwriting any existing value."""
        ...

    def retrieve(self, key: str) -> str | None:
        """Return the value stored under `key`, or None if not present."""
        ...

    def search(self, query: str, top_k: int) -> list[str]:
        """Return up to `top_k` keys whose stored values are most relevant
        to `query`, ordered from most to least relevant.
        """
        ...


class MemoryBackendBase(ABC):
    """Optional abstract base class for backends that want inheritance.

    Concrete backends are not required to subclass this — the harness only
    depends on structural conformance to `MemoryBackend` above — but this
    gives implementers a clear abstract contract with type-checked stubs.
    """

    @abstractmethod
    def store(self, key: str, value: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def retrieve(self, key: str) -> str | None:
        raise NotImplementedError

    @abstractmethod
    def search(self, query: str, top_k: int) -> list[str]:
        raise NotImplementedError


def keyword_overlap_score(query: str, text: str) -> float:
    """Simple, dependency-free relevance score used by backends' `search`.

    Scores the fraction of query tokens that appear as substrings of the
    candidate text (case-insensitive), plus a small bonus if the whole
    query string appears verbatim as a substring. This is intentionally
    simple (no embeddings/vector similarity) — it is real, working scoring
    logic, just not semantic search.
    """
    query = query.strip().lower()
    text_lower = text.lower()
    if not query:
        return 0.0

    tokens = [t for t in query.split() if t]
    if not tokens:
        return 0.0

    matches = sum(1 for t in tokens if t in text_lower)
    score = matches / len(tokens)

    if query in text_lower:
        score += 0.5

    return score
