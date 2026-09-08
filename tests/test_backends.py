"""Real pytest tests for InMemoryBackend and SQLiteBackend.

Both backends are exercised through the same test bodies (via
parametrize-by-factory) so we know they behave consistently against the
shared MemoryBackend interface.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from memory_bench.backend import MemoryBackend
from memory_bench.backends.in_memory import InMemoryBackend
from memory_bench.backends.sqlite_backend import SQLiteBackend


def _make_in_memory() -> InMemoryBackend:
    return InMemoryBackend()


def _make_sqlite_in_memory_db() -> SQLiteBackend:
    return SQLiteBackend(":memory:")


def _make_sqlite_temp_file_db(tmp_path: Path) -> SQLiteBackend:
    db_file = tmp_path / "test_memory.db"
    return SQLiteBackend(str(db_file))


BACKEND_FACTORIES = {
    "in_memory": lambda tmp_path: _make_in_memory(),
    "sqlite_memory": lambda tmp_path: _make_sqlite_in_memory_db(),
    "sqlite_file": lambda tmp_path: _make_sqlite_temp_file_db(tmp_path),
}


@pytest.fixture(params=list(BACKEND_FACTORIES.keys()))
def backend(request, tmp_path) -> MemoryBackend:
    factory = BACKEND_FACTORIES[request.param]
    return factory(tmp_path)


def test_store_retrieve_round_trip(backend: MemoryBackend) -> None:
    backend.store("greeting", "hello world")
    assert backend.retrieve("greeting") == "hello world"


def test_store_overwrites_existing_key(backend: MemoryBackend) -> None:
    backend.store("k", "first value")
    backend.store("k", "second value")
    assert backend.retrieve("k") == "second value"


def test_missing_key_returns_none(backend: MemoryBackend) -> None:
    assert backend.retrieve("does-not-exist") is None


def test_search_returns_relevant_results_ranked_reasonably(
    backend: MemoryBackend,
) -> None:
    backend.store("color", "The user's favorite color is teal.")
    backend.store("city", "The user lives in Pune.")
    backend.store("pet", "The user has a cat named Miso.")

    results = backend.search("what is the user's favorite color", top_k=3)

    assert isinstance(results, list)
    assert len(results) > 0
    # The entry that actually mentions "favorite color" should rank first
    # since it shares the most query keywords.
    assert results[0] == "color"


def test_search_top_k_limits_result_count(backend: MemoryBackend) -> None:
    for i in range(10):
        backend.store(f"item{i}", f"this is test entry number {i} about apples")

    results = backend.search("apples", top_k=3)
    assert len(results) <= 3


def test_search_with_no_matches_returns_empty_list(backend: MemoryBackend) -> None:
    backend.store("only_entry", "completely unrelated content about oceans")
    results = backend.search("zzznonexistentqueryterm", top_k=5)
    assert results == []


def test_search_top_k_zero_returns_empty_list(backend: MemoryBackend) -> None:
    backend.store("k", "some value here")
    assert backend.search("value", top_k=0) == []


def test_sqlite_backend_persists_to_file(tmp_path: Path) -> None:
    """SQLiteBackend with a real file path should persist across
    separate connections to the same file (unlike ':memory:')."""
    db_file = tmp_path / "persist_test.db"

    backend1 = SQLiteBackend(str(db_file))
    backend1.store("durable_key", "durable_value")
    backend1.close()

    backend2 = SQLiteBackend(str(db_file))
    assert backend2.retrieve("durable_key") == "durable_value"
    backend2.close()


def test_sqlite_memory_db_does_not_persist_across_instances() -> None:
    """Two separate ':memory:' SQLiteBackend instances are independent
    databases -- confirms we're not accidentally sharing state."""
    backend1 = SQLiteBackend(":memory:")
    backend1.store("k", "v")

    backend2 = SQLiteBackend(":memory:")
    assert backend2.retrieve("k") is None
