# Research: Backend Task Management API

## Decision 1: Separate task definition from task execution history

- **Decision**: Keep a persistent task-definition record and add a separate run-history table plus per-run log table.
- **Rationale**: The current `task` table mixes long-lived configuration with the latest execution status. A dedicated run table allows repeatable manual execution, preserves audit history, and supports run-level diagnostics without overwriting prior results.
- **Alternatives considered**:
  - Reuse the existing `task` table only: rejected because every run would overwrite previous outcomes and provide no historical audit trail.
  - Store run history in the existing global `log` table only: rejected because logs alone cannot model run status transitions or result summaries.

## Decision 2: Use an in-memory active-run registry for start/terminate control

- **Decision**: Maintain a runtime registry that maps `run_id` to the active `asyncio.Task` object and metadata for the current application instance.
- **Rationale**: Manual execution and termination require direct access to the running coroutine. This design is lightweight, fits the current single-instance assumptions, and preserves async safety.
- **Alternatives considered**:
  - Introduce Celery or another distributed queue now: rejected as too large for the current feature scope.
  - Poll database status only: rejected because it cannot terminate a currently running coroutine.

## Decision 3: Treat unsupported task types as catalog entries with explicit availability metadata

- **Decision**: Publish a task type catalog that marks whether a type is currently implemented, and reject execution of unimplemented types with a clear business error.
- **Rationale**: The project already advertises placeholder task types. Making availability explicit gives UI and operators a truthful contract while preserving the existing extension pattern.
- **Alternatives considered**:
  - Hide placeholder types entirely: rejected because it obscures planned system capabilities.
  - Keep placeholder execution as successful no-op: rejected because it misleads operators about whether data was actually collected.

## Decision 4: Keep automatic cron dispatch out of this feature

- **Decision**: Persist schedule metadata (`cron`) and enable/disable state, but do not build an automatic scheduler in this iteration.
- **Rationale**: The immediate gap is missing management, run control, and observability APIs. Scheduling can layer on top later once task definitions and run tracking are trustworthy.
- **Alternatives considered**:
  - Implement a full scheduler now: rejected because it would expand scope into process lifecycle, recovery, and distributed coordination.

## Decision 5: Add task-specific run logs while optionally continuing global logging

- **Decision**: Persist run logs in a dedicated `task_run_log` table and continue writing summary events to the existing global log table where useful.
- **Rationale**: Task-specific log retrieval must be deterministic per run, while the global log endpoint remains useful for operational overview.
- **Alternatives considered**:
  - Replace global logs entirely: rejected because other system flows already use the shared log table.
  - Use only global logs with string matching: rejected because it is unreliable and cannot guarantee full per-run reconstruction.
