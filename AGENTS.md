# vista-flow Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-04-05

## Active Technologies
- PostgreSQL 16 with existing `task`, `task_run`, `task_run_log`, `trains`, `train_stops`, and `train_runs` tables under `infra/sql/` (002-railway-crawl-tasks)

- Python 3.12 + FastAPI, Pydantic v2, asyncpg, httpx, pydantic-settings (001-task-management-api)

## Project Structure

```text
backend/
frontend/
tests/
```

## Commands

cd src; pytest; ruff check .

## Code Style

Python 3.12: Follow standard conventions

## Recent Changes
- 002-railway-crawl-tasks: Added Python 3.12 + FastAPI, Pydantic v2, asyncpg, httpx, pydantic-settings

- 001-task-management-api: Added Python 3.12 + FastAPI, Pydantic v2, asyncpg, httpx, pydantic-settings

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
