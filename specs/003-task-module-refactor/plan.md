# Implementation Plan: Task Module Refactor

**Branch**: `003-task-module-refactor` | **Date**: 2026-04-07 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-task-module-refactor/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Refactor VistaFlow's backend task module so task types become self-describing, centrally registered, and modularized by task family while preserving the current admin task API, stored task/run data, and behavior of the four implemented task types. The design keeps the current in-process execution model, adds a stable registration and execution-context boundary, and uses compatibility-focused automated tests to prevent regressions while preparing the module for future task families such as `price`, `geocode`, or non-railway tasks.

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: FastAPI, Pydantic v2, asyncpg, httpx, pydantic-settings  
**Storage**: PostgreSQL 16 with existing `task`, `task_run`, `task_run_log`, and related railway tables under `infra/sql/`  
**Testing**: pytest, pytest-asyncio, contract tests for task APIs, unit tests for registry/validation/runner behavior, integration tests for task execution compatibility  
**Target Platform**: Linux server/container running `apps/api`  
**Project Type**: Backend web service  
**Performance Goals**: Existing admin task APIs retain current interactive latency expectations; registry loading remains deterministic at startup; task trigger requests continue to return accepted runs immediately; refactor adds no additional round trips to create/update/run flows  
**Constraints**: Non-blocking async I/O, parameterized SQL, admin-only task APIs, one active run per task, no destructive migration for existing task data, planner remains zero-I/O, external integration contracts remain unchanged, external HTTP calls keep explicit timeouts  
**Scale/Scope**: `apps/api/app/tasks/`, `apps/api/app/main.py`, `apps/api/app/models.py`, selected `apps/api/app/system/` and `apps/api/app/railway/` collaborators as needed, `apps/api/tests/`, `apps/api/README.md`, and `specs/003-task-module-refactor/`; SQL changes are optional and only allowed if compatibility-safe metadata storage is proven necessary

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] Domain boundaries are preserved: the refactor stays inside the `tasks` domain for lifecycle concerns and only touches collaborator domains where compatibility wiring requires it.
- [x] API contracts, error behavior, auth impact, and persistence impact are documented in the spec.
- [x] Required automated verification is identified (unit, integration, contract, regression) and will be mapped to concrete files.
- [x] Async safety, secret handling, SQL parameterization, and external timeout requirements remain unchanged by the refactor.
- [x] Observability, migration, rollout, and operational follow-up work are captured because this change affects task loading, task execution compatibility, and operator-visible diagnostics.
- [x] No constitution exception is currently required.

## Project Structure

### Documentation (this feature)

```text
specs/003-task-module-refactor/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- task-module-refactor.openapi.yaml
`-- tasks.md
```

### Source Code (repository root)

```text
apps/api/
|-- app/
|   |-- main.py
|   |-- models.py
|   |-- tasks/
|   |   |-- constants.py
|   |   |-- dependencies.py
|   |   |-- exceptions.py
|   |   |-- handlers.py
|   |   |-- progress.py
|   |   |-- repository.py
|   |   |-- router.py
|   |   |-- runner.py
|   |   |-- runtime.py
|   |   |-- schemas.py
|   |   |-- service.py
|   |   `-- [new task-type registry subpackage]/
|   |-- railway/
|   |   `-- repository.py        # only if task-type migration needs helper adjustments
|   `-- system/
|       `-- log_repository.py    # only if shared logging ports are refactored
`-- tests/
    |-- contract/
    |-- integration/
    `-- unit/

infra/
`-- sql/
    |-- schema.sql
    `-- migrations/
```

**Structure Decision**: Keep the refactor inside the existing `tasks` domain, introduce a dedicated internal package for task-type definitions/registry modules, preserve current routers/services/repositories as public task-domain entry points, and avoid cross-domain sprawl. SQL artifacts remain untouched unless design validation proves a compatibility-safe metadata addition is required.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution violations identified.
