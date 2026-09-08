"""Benchmark harness: runs a fixed toy dataset against a MemoryBackend and
measures real wall-clock latency and recall.

Nothing in this module returns precomputed or invented numbers. Every
field on `BenchmarkResult` is filled in from an actual timed run against
the backend instance passed to `run_benchmark`.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean

from memory_bench.backend import MemoryBackend

DEFAULT_DATASET_PATH = Path(__file__).resolve().parent.parent / "data" / "toy_dataset.json"

DEFAULT_TOP_K = 3


@dataclass
class BenchmarkResult:
    """Real, measured results from one run of `run_benchmark`.

    All latency values are in seconds and come from `time.perf_counter()`
    deltas around the actual backend calls. `recall_at_k` is the fraction
    of dataset entries for which `search(query, top_k)` returned the
    expected key.
    """

    backend_name: str
    num_entries: int
    top_k: int
    store_latencies_s: list[float] = field(default_factory=list)
    retrieve_latencies_s: list[float] = field(default_factory=list)
    search_latencies_s: list[float] = field(default_factory=list)
    recall_hits: int = 0

    @property
    def recall_at_k(self) -> float:
        if self.num_entries == 0:
            return 0.0
        return self.recall_hits / self.num_entries

    @property
    def mean_store_latency_s(self) -> float:
        return mean(self.store_latencies_s) if self.store_latencies_s else 0.0

    @property
    def mean_retrieve_latency_s(self) -> float:
        return mean(self.retrieve_latencies_s) if self.retrieve_latencies_s else 0.0

    @property
    def mean_search_latency_s(self) -> float:
        return mean(self.search_latencies_s) if self.search_latencies_s else 0.0

    def summary(self) -> str:
        return (
            f"BenchmarkResult(backend={self.backend_name!r}, "
            f"entries={self.num_entries}, top_k={self.top_k}, "
            f"recall@{self.top_k}={self.recall_at_k:.3f}, "
            f"mean_store_ms={self.mean_store_latency_s * 1000:.4f}, "
            f"mean_retrieve_ms={self.mean_retrieve_latency_s * 1000:.4f}, "
            f"mean_search_ms={self.mean_search_latency_s * 1000:.4f})"
        )


def load_dataset(path: Path = DEFAULT_DATASET_PATH) -> list[dict]:
    """Load the toy dataset of key/value/query entries from disk."""
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return raw["entries"]


def run_benchmark(
    backend: MemoryBackend,
    dataset: list[dict] | None = None,
    top_k: int = DEFAULT_TOP_K,
    backend_name: str | None = None,
) -> BenchmarkResult:
    """Run the fixed toy benchmark against `backend` and return real results.

    For each entry in `dataset` (each with "key", "value", "query"):
      1. Time a `store(key, value)` call.
      2. Time a `retrieve(key)` call and sanity-check it returns the value.
      3. Time a `search(query, top_k)` call and check whether `key` is
         among the returned results (counts toward recall).

    All timings come from `time.perf_counter()` around the actual calls.
    """
    if dataset is None:
        dataset = load_dataset()

    name = backend_name or type(backend).__name__
    result = BenchmarkResult(backend_name=name, num_entries=len(dataset), top_k=top_k)

    # Phase 1: store everything first, so later searches/retrieves see the
    # full dataset (mirrors how an agent would populate memory over a
    # session before querying it).
    for entry in dataset:
        start = time.perf_counter()
        backend.store(entry["key"], entry["value"])
        result.store_latencies_s.append(time.perf_counter() - start)

    # Phase 2: retrieve + search against the fully populated backend.
    for entry in dataset:
        start = time.perf_counter()
        retrieved = backend.retrieve(entry["key"])
        result.retrieve_latencies_s.append(time.perf_counter() - start)

        if retrieved != entry["value"]:
            raise AssertionError(
                f"retrieve() mismatch for key {entry['key']!r}: "
                f"expected {entry['value']!r}, got {retrieved!r}"
            )

        start = time.perf_counter()
        search_results = backend.search(entry["query"], top_k)
        result.search_latencies_s.append(time.perf_counter() - start)

        if entry["key"] in search_results:
            result.recall_hits += 1

    return result


def _main() -> None:
    """Run the benchmark against InMemoryBackend and print real results.

    This is the only backend day-1 code exercises for a live run --
    SQLiteBackend can be swapped in the same way (see README.md) but is
    not run here automatically to keep this entry point fast and simple.
    """
    from memory_bench.backends.in_memory import InMemoryBackend

    dataset = load_dataset()
    backend = InMemoryBackend()
    result = run_benchmark(backend, dataset)
    print(result.summary())


if __name__ == "__main__":
    _main()
