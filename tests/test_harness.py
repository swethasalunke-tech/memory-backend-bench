"""Real test that run_benchmark produces a sane BenchmarkResult using
InMemoryBackend against the actual toy dataset shipped in data/toy_dataset.json.

This does not assert any specific recall or latency VALUE (those come
from a real run and can vary slightly by machine) -- it asserts the
result's fields are well-formed and internally consistent, which is what
we can guarantee statically.
"""

from __future__ import annotations

from memory_bench.backends.in_memory import InMemoryBackend
from memory_bench.harness import BenchmarkResult, load_dataset, run_benchmark


def test_run_benchmark_returns_sane_result() -> None:
    dataset = load_dataset()
    backend = InMemoryBackend()

    result = run_benchmark(backend, dataset, top_k=3)

    assert isinstance(result, BenchmarkResult)
    assert result.backend_name == "InMemoryBackend"
    assert result.num_entries == len(dataset)
    assert result.top_k == 3

    assert len(result.store_latencies_s) == len(dataset)
    assert len(result.retrieve_latencies_s) == len(dataset)
    assert len(result.search_latencies_s) == len(dataset)
    assert all(latency >= 0 for latency in result.store_latencies_s)
    assert all(latency >= 0 for latency in result.retrieve_latencies_s)
    assert all(latency >= 0 for latency in result.search_latencies_s)

    assert result.mean_store_latency_s >= 0
    assert result.mean_retrieve_latency_s >= 0
    assert result.mean_search_latency_s >= 0

    assert 0 <= result.recall_hits <= result.num_entries
    assert 0.0 <= result.recall_at_k <= 1.0


def test_run_benchmark_recall_is_reasonably_high_on_toy_dataset() -> None:
    """The toy dataset is small and hand-authored so that each query's
    keywords overlap heavily with its own entry's value -- recall should
    be well above chance (not asserting a specific fabricated number,
    just a sanity floor for a working keyword-overlap search)."""
    dataset = load_dataset()
    backend = InMemoryBackend()

    result = run_benchmark(backend, dataset, top_k=3)

    assert result.recall_at_k > 0.5


def test_run_benchmark_dataset_has_expected_shape() -> None:
    dataset = load_dataset()
    assert 15 <= len(dataset) <= 20
    for entry in dataset:
        assert set(entry.keys()) == {"key", "value", "query"}
        assert isinstance(entry["key"], str) and entry["key"]
        assert isinstance(entry["value"], str) and entry["value"]
        assert isinstance(entry["query"], str) and entry["query"]
