# Quickstart: Task Module Refactor

## Goal

Validate that the refactored backend task module:

1. still exposes the existing admin task APIs,
2. preserves behavior for the four implemented task types,
3. uses a unified task-type registry and validation path, and
4. lowers the effort required to onboard a new task type.

## Prerequisites

- Python dependencies installed in `apps/api/` via `uv sync`
- Local PostgreSQL configured for the existing backend schema
- Admin token configured in `.env.development`
- Existing task migrations applied

## Validation Workflow

### 1. Run the backend quality gates

```bash
cd apps/api
uv run ruff check .
uv run mypy app tests
uv run pytest --cov=app --cov-report=term-missing
```

Expected result:

- all task-related unit, integration, and contract tests pass
- existing task API regressions are caught before manual validation

### 2. Validate the task type catalog remains compatible

Start the backend locally:

```bash
cd apps/api
uv run uvicorn app.main:app --reload --port 8000
```

Query the task type catalog with the admin bearer token.

Expected result:

- `fetch-station`, `fetch-trains`, `fetch-train-stops`, and `fetch-train-runs` still appear
- each task type still returns label, description, `implemented`, `supportsCron`, and `paramSchema`
- the catalog is now backed by the unified task-type registry

### 3. Validate existing task CRUD and run flows

Using the existing admin task endpoints:

1. create or update one task for each implemented task type,
2. trigger a manual run for at least one railway task and one non-railway-compatible task,
3. fetch run detail and run logs,
4. terminate an active long-running task if one is available in test fixtures.

Expected result:

- API paths remain unchanged
- payload validation and normalization still work
- run status, summaries, logs, and progress snapshots remain readable
- historical run records remain queryable without migration work

### 4. Validate unified registration behavior

Create a temporary example task definition module in the new task-type registry structure used by the refactor.

Expected result:

- the example task appears in the registry-driven task catalog after startup
- create/update validation uses the task type's own payload contract
- execution routing uses the task type's own executor declaration
- missing executor or incomplete definition fails deterministically in tests or startup checks

### 5. Validate extensibility constraints

Review the example task onboarding diff.

Expected result:

- onboarding a standard new task type does not require editing more than two central task-module files
- framework code and concrete task implementation files remain clearly separated
- no business-specific dependencies were added to the shared execution context solely to support the example task

## Rollback Check

If compatibility validation fails, revert the refactor branch before merging and confirm that:

- the previous task registry and execution flow still boot successfully,
- persisted `task`, `task_run`, and `task_run_log` data remain intact,
- no destructive SQL migration is required to roll back this feature.
