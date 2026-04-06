# Implementation Plan: Railway Crawl Task Types

**Branch**: `002-railway-crawl-tasks` | **Date**: 2026-04-05 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-railway-crawl-tasks/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Add three new implemented railway crawl task types to VistaFlow's existing backend task center so
administrators can configure and manually execute train catalog sync, train-stop sync, and per-date
train-run sync inside the current task-management workflow. Preserve the existing 12306 request
parameters, invocation pattern, and response interpretation used by the current crawler approach,
while adapting execution, validation, logging, and persistence to VistaFlow's tasks domain.

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: FastAPI, Pydantic v2, asyncpg, httpx, pydantic-settings  
**Storage**: PostgreSQL 16 with existing `task`, `task_run`, `task_run_log`, `trains`, `train_stops`, and `train_runs` tables under `infra/sql/`  
**Testing**: pytest, pytest-asyncio, unit tests for task validation/service/runner/handlers, API tests for task endpoints, repository-oriented regression tests for railway persistence  
**Target Platform**: Linux server/container running `apps/api`  
**Project Type**: Backend web service  
**Performance Goals**: Task CRUD and trigger APIs remain within normal admin interaction latency; accepted runs appear in run history immediately; each run records processed counts and final status within one execution cycle  
**Constraints**: Non-blocking async I/O, parameterized SQL, admin-only task APIs, one active run per task, planner remains zero-I/O, 12306 integration contract stays unchanged, external HTTP calls require timeouts and controlled retry behavior  
**Scale/Scope**: `apps/api/app/tasks/`, `apps/api/app/integrations/crawler/`, `apps/api/app/railway/`, `apps/api/app/models.py`, `apps/api/app/main.py`, `infra/sql/`, `apps/api/tests/`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] Domain boundaries are preserved: routers stay HTTP-only, task services orchestrate validation and execution, crawler integration owns upstream HTTP behavior, and railway repositories own SQL persistence.
- [x] API contracts, error behavior, auth impact, and persistence impact are documented in the spec.
- [x] Required automated verification is identified: task-type catalog tests, task create/update validation tests, handler/runner tests, and API contract coverage for new railway task definitions and runs.
- [x] Async safety, secret handling, SQL parameterization, and external timeout requirements are satisfied by extending the async crawler client and existing asyncpg/httpx patterns.
- [x] Observability, migration, rollout, and operational follow-up work are captured through task run history, per-run logs, migration updates, and handler summaries.
- [x] No constitution exception is currently required.

## Project Structure

### Documentation (this feature)

```text
specs/002-railway-crawl-tasks/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- railway-crawl-tasks.openapi.yaml
`-- tasks.md
```

### Source Code (repository root)

```text
apps/api/
|-- app/
|   |-- integrations/
|   |   `-- crawler/
|   |       `-- client.py
|   |-- railway/
|   |   |-- repository.py
|   |   `-- schemas.py                 # only if railway-facing response models need extension
|   |-- tasks/
|   |   |-- constants.py
|   |   |-- exceptions.py
|   |   |-- handlers.py
|   |   |-- repository.py
|   |   |-- router.py
|   |   |-- runner.py
|   |   |-- schemas.py
|   |   `-- service.py
|   |-- main.py
|   `-- models.py
`-- tests/
    |-- contract/
    |-- integration/
    `-- unit/

infra/
`-- sql/
    |-- schema.sql
    `-- migrations/
```

**Structure Decision**: Extend the existing `tasks` domain in place, add the new 12306 crawl capabilities to the existing crawler integration without changing its upstream contract, and keep all new persistence logic inside `railway/repository.py` plus forward-only SQL migrations when schema support is needed.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution violations identified.
