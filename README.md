# memory-backend-bench

A small benchmark harness for comparing memory backends that an AI agent
could use to store and recall facts during a session — measuring recall
accuracy and latency against a fixed toy dataset.

## Status (day 1)

**Implemented and tested:**

- `InMemoryBackend` — a plain Python `dict`.
- `SQLiteBackend` — a real SQLite table via stdlib `sqlite3`.
- `run_benchmark()` harness that stores/retrieves/searches a fixed,
  hand-authored 18-entry toy dataset (`data/toy_dataset.json`) and
  returns a `BenchmarkResult` with real latency and recall numbers from
  the run you just performed.

**Not implemented yet** (see `DESIGN.md` and `BUILD-SCHEDULE.md` for
why and when):

- No DynamoDB backend — needs real AWS credentials/infrastructure not
  available in this build environment.
- No vector-store / embeddings backend — needs a real embeddings
  model/API to genuinely exercise.
- No cross-backend comparison CLI/report yet — planned for day 2, to be
  run and included with real output at that time.

This README does not include any benchmark numbers, because numbers
belong to a specific run on a specific machine, not to static
documentation — see "Run the benchmark yourself" below to produce your
own.

## Install

```bash
pip install -r requirements.txt --break-system-packages
```

(`sqlite3` is part of the Python standard library — no install needed
for `SQLiteBackend`.)

## Run the tests

From the repo root:

```bash
python3 -m pytest tests/ -v
```

This covers, for both `InMemoryBackend` and `SQLiteBackend`:

- store/retrieve round trip
- overwriting an existing key
- missing key returns `None`
- `search` returns relevant results, ranked reasonably
- `search` respects `top_k`
- `search` with no matching terms returns an empty list
- SQLite-specific: file-backed persistence across connections, and
  isolation between separate `:memory:` instances

`tests/test_harness.py` additionally checks that `run_benchmark()`
produces a `BenchmarkResult` with well-formed fields (non-negative
latencies, recall between 0 and 1) using `InMemoryBackend` against the
real toy dataset.

## Run the benchmark yourself

```bash
python3 -m memory_bench.harness
```

This runs the toy dataset through `InMemoryBackend` and prints a
`BenchmarkResult` summary with real, freshly measured latency (in ms)
and recall@3 numbers — nothing here is precomputed.

To benchmark `SQLiteBackend` instead:

```bash
python3 -c "
from memory_bench.backends.sqlite_backend import SQLiteBackend
from memory_bench.harness import run_benchmark, load_dataset

backend = SQLiteBackend(':memory:')  # or a real file path to persist
result = run_benchmark(backend, load_dataset(), top_k=3, backend_name='SQLiteBackend')
print(result.summary())
"
```

Or import `run_benchmark` and `load_dataset` from `memory_bench.harness`
directly in your own script and pass in any object that implements the
`MemoryBackend` protocol (`memory_bench/backend.py`).

## Toy dataset

`data/toy_dataset.json` is 18 hand-authored key/value/query triples
(see the `_comment` field in the file itself). It exists purely to give
the harness fixed, reproducible input — it is not a real user
conversation log or an external dataset.

## Layout

```
memory_bench/
  backend.py               # MemoryBackend protocol/ABC + shared scoring helper
  backends/
    in_memory.py            # InMemoryBackend
    sqlite_backend.py        # SQLiteBackend
  harness.py                # run_benchmark(), BenchmarkResult, load_dataset()
data/
  toy_dataset.json           # fixed 18-entry toy dataset
tests/
  test_backends.py           # backend correctness tests
  test_harness.py            # harness sanity tests
DESIGN.md                    # scope, interface, what's deferred and why
BUILD-SCHEDULE.md            # day-by-day plan
```
