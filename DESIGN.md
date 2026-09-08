# Design

## What this is

`memory-backend-bench` is a small, honest benchmark harness for comparing
memory backends that an AI agent might use to store and recall facts
(key/value memories) during a session. It measures two things against a
fixed toy dataset:

- **Latency** — real wall-clock time (via `time.perf_counter()`) for
  `store`, `retrieve`, and `search` calls.
- **Recall** — whether `search(query, top_k)` returns the expected key
  for each dataset entry's associated query.

## Interface

All backends implement the `MemoryBackend` protocol in
`memory_bench/backend.py`:

```python
store(key: str, value: str) -> None
retrieve(key: str) -> str | None
search(query: str, top_k: int) -> list[str]
```

`search` is not a stub — both backends implement real (if simple)
relevance scoring: keyword-overlap between the query and stored value,
shared via `keyword_overlap_score()` in `backend.py` so the two backends
are ranked with the same logic and are fairly comparable. This is
deliberately not semantic/embedding-based search; that's out of scope
for day 1 (see below).

## Day 1 scope (this build)

Implemented, tested, and actually run in this sandbox:

- `InMemoryBackend` — a plain Python `dict`. No I/O, no persistence.
  Serves as the latency floor.
- `SQLiteBackend` — a real SQLite table via stdlib `sqlite3`, with real
  `INSERT ... ON CONFLICT DO UPDATE`, `SELECT`, and a `LIKE`-based
  candidate shortlist followed by the same keyword-overlap scoring used
  by `InMemoryBackend`. Works with both `:memory:` and real file-backed
  databases.
- `run_benchmark()` in `memory_bench/harness.py` — runs a fixed,
  hand-authored 18-entry toy dataset (`data/toy_dataset.json`) through
  store/retrieve/search and returns a `BenchmarkResult` dataclass
  populated entirely from a live run. No numbers in this repo's code or
  docs are precomputed or invented — every reported number comes from
  actually executing the harness.
- Test suite (`tests/`) covering both backends and the harness.

## Explicitly deferred (not implemented, not claimed as implemented)

- **DynamoDB backend.** Needs real AWS credentials and a live DynamoDB
  table (or a faithful local emulator like DynamoDB Local/LocalStack)
  that this build sandbox does not have. Adding a `DynamoDBBackend`
  class that merely wraps `boto3` calls without ever exercising them
  against a real or emulated table would violate this project's
  no-fabrication rule, so it is left out entirely rather than stubbed.
- **Vector-store / embeddings-based backend.** Needs a real embeddings
  model or API to compute vector similarity. No such client is
  configured/available in this sandbox, so this is deferred rather than
  faked with random vectors or hardcoded similarity scores.
- **Cross-backend comparison CLI/report.** Comparing `InMemoryBackend`
  and `SQLiteBackend` side-by-side numerically is meaningful, but doing
  it properly (a small CLI or report generator, run for real, with real
  output committed) is scoped to day 2 so it can be built as a consumer
  of the day-1 package rather than developed in parallel with it.

## Non-goals for day 1

- Semantic/embedding search (see vector-store backend above).
- Concurrency / thread-safety guarantees for either backend.
- Any performance tuning beyond "correct and simple." The point of day 1
  is a working, honest baseline to compare later backends against.
