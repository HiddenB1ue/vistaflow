# Implementation Plan: Backend Task Management API

**Branch**: `001-task-management-api` | **Date**: 2026-04-05 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-task-management-api/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Build a complete backend task-management API for VistaFlow admin operations so that
operators can manage task definitions, manually execute tasks, terminate active runs,
and inspect run history plus per-run logs without direct database access. Preserve the
existing task handler registry and keep current real task types (`fetch-station`,
`geocode`) working inside the new execution model.

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: FastAPI, Pydantic v2, asyncpg, httpx, pydantic-settings  
**Storage**: PostgreSQL 16 with new task execution tables under `infra/sql/`  
**Testing**: pytest, pytest-asyncio, unit tests for service/runner, API tests with dependency overrides  
**Target Platform**: Linux server/container running `apps/api`  
**Project Type**: Backend web service  
**Performance Goals**: New manual task runs appear in task history within 5 seconds; task CRUD and history APIs return within normal admin interaction latency expectations  
**Constraints**: Non-blocking async I/O, parameterized SQL, admin-only access, one active run per task, planner remains zero-I/O, external calls require timeouts  
**Scale/Scope**: `apps/api/app/tasks/`, `apps/api/app/system/`, `apps/api/app/main.py`, `infra/sql/`, `apps/api/tests/`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] Domain boundaries are preserved: routers expose HTTP endpoints, services orchestrate workflows, repositories own SQL, runtime execution state stays in the tasks domain.
- [x] API contracts, error behavior, auth impact, and persistence impact are documented in the spec.
- [x] Required automated verification is identified: task service tests, task runtime/runner tests, and API tests for task definition and run endpoints.
- [x] Async safety, secret handling, SQL parameterization, and external timeout requirements are satisfied by reusing existing asyncpg/httpx patterns.
- [x] Observability, migration, rollout, and operational follow-up work are captured through task run history, per-run logs, and migration updates.
- [x] No constitution exception is currently required.

## Project Structure

### Documentation (this feature)

```text
specs/001-task-management-api/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- task-management.openapi.yaml
`-- tasks.md
```

### Source Code (repository root)

```text
apps/api/
|-- app/
|   |-- main.py
|   |-- tasks/
|   |   |-- constants.py
|   |   |-- dependencies.py
|   |   |-- exceptions.py
|   |   |-- handlers.py
|   |   |-- repository.py
|   |   |-- router.py
|   |   |-- runner.py
|   |   |-- schemas.py
|   |   |-- service.py
|   |   `-- runtime.py              # new in-memory active-run registry
|   `-- system/
|       |-- log_repository.py
|       `-- schemas.py              # only if shared logging contracts need updates
`-- tests/
    |-- integration/
    |-- contract/
    `-- unit/

infra/
`-- sql/
    |-- schema.sql
    `-- migrations/
        `-- 0005_task_management_api.sql
```

**Structure Decision**: Extend the existing `tasks` domain in place. Keep all new task
execution concepts inside that domain, add one runtime registry module for active
asyncio tasks, and update SQL migrations plus backend tests accordingly.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution violations identified.
