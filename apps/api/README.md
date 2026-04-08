# VistaFlow Backend

Repo-wide governance for backend delivery lives in
`.specify/memory/constitution.md`. `ARCHITECTURE.md` may be stricter, but it does
not replace the backend constitution.

All backend feature work MUST preserve domain boundaries, document API/data/ops
impact during specification, and pass `uv run ruff check .`,
`uv run mypy app tests`, and `uv run pytest --cov=app --cov-report=term-missing`
before merge.

## Tech Stack

Python 3.12 + FastAPI + asyncpg backend service.

## Quick Start

```bash
cd apps/api

# Install dependencies
uv sync

# Copy environment variables
cp .env.example .env.development
# Edit .env.development and fill in database / external service configuration

# Start the dev server
uv run uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

## Development

```bash
# Lint
uv run ruff check .

# Type check
uv run mypy app tests

# Test
uv run pytest --cov=app --cov-report=term-missing
```

## Task Module

The backend task API currently supports the following management endpoints:

- `GET /api/v1/admin/tasks/types`: list supported task types and execution metadata
- `GET /api/v1/admin/tasks` / `POST /api/v1/admin/tasks`: query and create task definitions
- `GET /api/v1/admin/tasks/{id}` / `PATCH /api/v1/admin/tasks/{id}` / `DELETE /api/v1/admin/tasks/{id}`: view, update, or delete a task
- `POST /api/v1/admin/tasks/{id}/runs`: create a pending task run
- `GET /api/v1/admin/tasks/{id}/runs`: query task run history
- `GET /api/v1/admin/task-runs/{id}`: inspect one run
- `GET /api/v1/admin/task-runs/{id}/logs`: inspect run logs
- `POST /api/v1/admin/task-runs/{id}/terminate`: terminate a pending run or request cancellation for a running run

Task execution now happens in a separate worker process:

```bash
cd apps/api
uv run python -m app.tasks.worker
```

Implemented executable task types:

- `fetch-station`
- `fetch-trains`
- `fetch-train-stops`
- `fetch-train-runs`

Reserved but not yet implemented task type:

- `price`

### Railway Crawl Tasks

The railway task feature extends the existing task domain and keeps the 12306
request parameters, request method, and response parsing contract unchanged.
Administrators can define and manually execute these task types through the same
`/api/v1/admin/tasks` API surface.

#### 1. `fetch-trains`

Payload:

```json
{
  "date": "2026-04-05",
  "keyword": "G"
}
```

`keyword` is optional. When omitted or empty, the task will iterate the built-in
root keyword set (`c d g k s t y z 0-9`) inside the same run.

Behavior:

- treat `keyword` as a train-prefix crawl seed rather than a generic free-text query
- recursively expand child keywords using the current 12306 search boundary
  rules (`result_limit=200`, `expand_span=3`, `max_keyword_length=6`)
- normalize the payload date to `YYYY-MM-DD`
- aggregate one flattened result set per seed keyword
- dedupe repeated `station_train_code` values inside crawler aggregation
- idempotently upsert matching rows into `trains`
- update `task_run.progress_snapshot` and logs at seed-keyword granularity

#### 2. `fetch-train-stops`

Payload:

```json
{
  "date": "2026-04-05",
  "keyword": "G1"
}
```

Behavior:

- resolve target `train_no` values from the local `trains` table
- accept either exact `train_no` or exact `station_train_code` as `keyword`
- when `keyword` is omitted or empty, iterate all `train_no` values currently stored in `trains`
- fetch stop details with the unchanged 12306 query contract
- call the upstream stop API strictly by `train_no`
- idempotently upsert into `train_stops`
- depend on `fetch-trains` as the source of truth for `trains`

#### 3. `fetch-train-runs`

Payload:

```json
{
  "date": "2026-04-05",
  "keyword": "G1"
}
```

Behavior:

- use `keyword` as a train-prefix seed rather than an exact single-train identifier
- when `keyword` is omitted or empty, iterate the built-in root keyword set (`c d g k s t y z 0-9`) inside the same run
- recursively collect the full matching prefix branch for the requested date
- keep only rows whose normalized run date matches the payload date
- keep only rows whose `station_train_code` starts with the requested keyword
- preserve the upstream 12306 request and response contract
- derive one-day run facts and normalize run status
- idempotently upsert into `trains` and `train_runs`
- fail the run when no matching run fact is returned for the requested keyword set

## Architecture

See [ARCHITECTURE.md](./ARCHITECTURE.md)
