# Build schedule

## Day 1 (this commit) — 2026-08-24

- `MemoryBackend` protocol/ABC (`memory_bench/backend.py`).
- `InMemoryBackend` (`memory_bench/backends/in_memory.py`).
- `SQLiteBackend` (`memory_bench/backends/sqlite_backend.py`), real
  stdlib `sqlite3`, tested against both `:memory:` and a temp file DB.
- `run_benchmark()` harness (`memory_bench/harness.py`) with a real,
  hand-authored 18-entry toy dataset (`data/toy_dataset.json`).
- Test suite (`tests/test_backends.py`, `tests/test_harness.py`), run
  and passing at time of commit.
- `DESIGN.md`, this file, `README.md`.

No DynamoDB backend, no vector-store backend, no comparison CLI yet —
see "Explicitly deferred" in `DESIGN.md` for why.

## Day 2 (planned) — comparison CLI/report

- A small CLI (likely `memory_bench/compare.py` or `python -m
  memory_bench.compare`) that runs `run_benchmark()` against both
  `InMemoryBackend` and `SQLiteBackend` back-to-back and prints/writes a
  side-by-side comparison table (latency + recall per backend).
- Depends on day 1's package existing and importable, so it's scoped to
  after day 1 rather than attempted in parallel.
- Any numbers included in the day-2 commit (README, docs, or output
  files) will be from an actual run performed on day 2, in this same
  kind of sandbox, immediately before that commit — not backfilled or
  estimated now.

## Day 3 (planned, conditional) — vector-store backend

- Only happens if an embeddings client (local model or API) can be
  genuinely exercised in the build environment at that time — i.e. real
  embedding calls, not mocked/random vectors standing in for them.
- If no such client is available when day 3 starts, this stays deferred
  and gets re-scoped rather than faked; the schedule will be updated to
  reflect reality rather than silently slipping.
- DynamoDB backend is not currently scheduled — it requires real AWS
  credentials/infra this project doesn't assume access to. It will only
  be added once it can be run against a real (or realistically emulated)
  DynamoDB table, with that fact stated plainly in whatever commit adds
  it.
