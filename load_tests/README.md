# Load tests

Performance/throughput tests using [Locust](https://locust.io/). Unlike the
`tests/` suite (which checks *correctness*), these measure how the system
behaves under many concurrent users: requests/sec, latency percentiles, and
error rate.

## Setup

```bash
uv add locust          # one-time, adds Locust to the project
```

## Run

1. Start the app in one terminal:
   ```bash
   uv run uvicorn app.app:app --port 8000
   ```
2. Start Locust in another:
   ```bash
   uv run locust -f load_tests/locustfile.py --host http://localhost:8000
   ```
   Open http://localhost:8089, set the number of users + spawn rate, and start.

Headless example (10 users, 2/s spawn, 30 seconds):
```bash
uv run locust -f load_tests/locustfile.py --host http://localhost:8000 \
    --headless -u 10 -r 2 -t 30s
```

## What it drives

- **`ChatUser`** — POST `/chat` (the main, LLM-backed flow) and GET `/chat/poll`.
- **`AdminUser`** — GET `/admin/pending`.

## Caveats

- **`POST /chat` calls the real LLM**, so every request consumes API tokens and
  is subject to provider rate limits — keep user counts low. Throughput here is
  dominated by the LLM provider's latency, not the app's own code.
- The app uses `InMemorySaver` and a single process, so this is a smoke-level
  load check for a mentor-review project, not a production capacity test.
