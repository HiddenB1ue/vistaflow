---

description: "Task list for backend task management API implementation"
---

# Tasks: Backend Task Management API

**Input**: Design documents from `/specs/001-task-management-api/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Automated tests are REQUIRED by the backend constitution. Each user story includes the unit, contract, and API coverage needed for safe delivery.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Backend application code lives in `apps/api/app/`
- Backend automated tests live in `apps/api/tests/`
- SQL schema and migration artifacts live in `infra/sql/`
- Paths shown below assume a backend feature in this repository

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare contracts, migrations, and test scaffolding for the task-management feature

- [X] T001 Create migration skeleton and schema updates in `infra/sql/migrations/0005_task_management_api.sql` and `infra/sql/schema.sql`
- [X] T002 [P] Create task-management contract test scaffold in `apps/api/tests/contract/test_task_management_api.py`
- [X] T003 [P] Create task-domain unit test scaffolds in `apps/api/tests/unit/tasks/test_service.py` and `apps/api/tests/unit/tasks/test_runner.py`
- [X] T004 [P] Create task API test scaffold and shared test doubles in `apps/api/tests/unit/tasks/test_router.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core task-domain infrastructure that must exist before any user story is delivered

**CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Implement task type catalog, status enums, and metadata helpers in `apps/api/app/tasks/constants.py`
- [X] T006 [P] Implement task definition, task run, and task log request/response models in `apps/api/app/tasks/schemas.py`
- [X] T007 Implement task-domain exceptions for unsupported type, duplicate name, disabled task, active run conflicts, and run termination errors in `apps/api/app/tasks/exceptions.py`
- [X] T008 Implement repositories for task definitions, task runs, and task run logs in `apps/api/app/tasks/repository.py`
- [X] T009 [P] Implement in-memory active-run registry in `apps/api/app/tasks/runtime.py`
- [X] T010 Update task dependency wiring to provide repositories, runtime registry, and service dependencies in `apps/api/app/tasks/dependencies.py` and `apps/api/app/main.py`

**Checkpoint**: Task infrastructure is ready for story-specific delivery

---

## Phase 3: User Story 1 - ?????? (Priority: P1) MVP

**Goal**: Allow admins to manage task definitions without touching the database directly

**Independent Test**: Admin can create, list, fetch, update, enable/disable, and delete a task definition through authenticated API calls

### Tests for User Story 1 (REQUIRED)

- [X] T011 [P] [US1] Add contract coverage for task type catalog and task definition CRUD endpoints in `apps/api/tests/contract/test_task_management_api.py`
- [X] T012 [P] [US1] Add unit coverage for task definition validation and CRUD service flows in `apps/api/tests/unit/tasks/test_service.py`
- [X] T013 [P] [US1] Add API/router coverage for task type listing and task definition CRUD endpoints in `apps/api/tests/unit/tasks/test_router.py`

### Implementation for User Story 1

- [X] T014 [P] [US1] Implement task type catalog responses and task definition request/response models in `apps/api/app/tasks/schemas.py` and `apps/api/app/tasks/constants.py`
- [X] T015 [US1] Implement task definition CRUD workflows in `apps/api/app/tasks/service.py`
- [X] T016 [US1] Implement task type and task definition endpoints in `apps/api/app/tasks/router.py`
- [X] T017 [US1] Implement persistence queries and deletion safeguards for task definitions in `apps/api/app/tasks/repository.py`

**Checkpoint**: Admin can fully manage task definitions through API and see supported task types

---

## Phase 4: User Story 2 - ????????? (Priority: P1)

**Goal**: Allow admins to start and terminate task runs while preserving one-active-run safety

**Independent Test**: Admin can trigger a manual run for an enabled task, see the new run state immediately, and terminate an active run without leaving the task stuck in running status

### Tests for User Story 2 (REQUIRED)

- [X] T018 [P] [US2] Add contract coverage for run trigger and termination endpoints in `apps/api/tests/contract/test_task_management_api.py`
- [X] T019 [P] [US2] Add unit coverage for run creation, active-run conflicts, unsupported task types, and termination flows in `apps/api/tests/unit/tasks/test_service.py` and `apps/api/tests/unit/tasks/test_runner.py`
- [X] T020 [P] [US2] Add API/router coverage for run trigger and termination endpoints in `apps/api/tests/unit/tasks/test_router.py`

### Implementation for User Story 2

- [X] T021 [P] [US2] Implement task-run state persistence and run-log persistence methods in `apps/api/app/tasks/repository.py`
- [X] T022 [P] [US2] Refactor handler context to include run-aware logging and summaries in `apps/api/app/tasks/handlers.py`
- [X] T023 [US2] Implement run orchestration, cancellation handling, and active-run registry integration in `apps/api/app/tasks/runner.py` and `apps/api/app/tasks/runtime.py`
- [X] T024 [US2] Implement task run trigger and termination service flows in `apps/api/app/tasks/service.py`
- [X] T025 [US2] Implement run trigger and termination endpoints in `apps/api/app/tasks/router.py`

**Checkpoint**: Admin can trigger and stop task runs safely, with current real task types executing through the new pipeline

---

## Phase 5: User Story 3 - ??????????? (Priority: P2)

**Goal**: Let admins inspect run history, run details, and per-run logs to diagnose outcomes

**Independent Test**: After one or more runs complete, admin can fetch task run history, run detail, and ordered run logs through dedicated endpoints

### Tests for User Story 3 (REQUIRED)

- [X] T026 [P] [US3] Add contract coverage for run history, run detail, and run log endpoints in `apps/api/tests/contract/test_task_management_api.py`
- [X] T027 [P] [US3] Add unit coverage for run history formatting and log retrieval in `apps/api/tests/unit/tasks/test_service.py`
- [X] T028 [P] [US3] Add API/router coverage for run history, run detail, and run log endpoints in `apps/api/tests/unit/tasks/test_router.py`

### Implementation for User Story 3

- [X] T029 [P] [US3] Implement run detail, run history, and run log response models in `apps/api/app/tasks/schemas.py`
- [X] T030 [US3] Implement run history and log retrieval queries in `apps/api/app/tasks/repository.py`
- [X] T031 [US3] Implement run history and run log service flows in `apps/api/app/tasks/service.py`
- [X] T032 [US3] Implement run history, run detail, and run log endpoints in `apps/api/app/tasks/router.py`

**Checkpoint**: Admin can inspect every run and understand whether the task actually collected or stored data

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Finish observability, docs, and validation across all task stories

- [X] T033 [P] Update task module documentation in `apps/api/README.md` and feature usage steps in `specs/001-task-management-api/quickstart.md`
- [X] T034 Review global log integration and task summary logging in `apps/api/app/tasks/handlers.py` and `apps/api/app/system/log_repository.py`
- [X] T035 Run backend quality gates from `apps/api/` and record final validation in `specs/001-task-management-api/tasks.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: Depend on Foundational phase completion
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational and establishes the management API baseline
- **User Story 2 (P1)**: Can start after Foundational but depends on the task definition model from User Story 1 for realistic flows
- **User Story 3 (P2)**: Depends on User Story 2 because run history and logs require persisted runs

### Within Each User Story

- Tests must be authored before implementation is considered complete
- Repository support precedes service orchestration
- Services precede routers
- Story checkpoint must pass before moving to the next story

### Parallel Opportunities

- Setup test scaffolds can be created in parallel
- Foundational constants/schemas/runtime work can be parallelized while repository/service wiring remains sequential
- Within each story, contract tests, unit tests, and router tests can be written in parallel
- Schema-only and handler-only changes may proceed in parallel when they touch different files

---

## Parallel Example: User Story 2

```bash
Task: "Add contract coverage for run trigger and termination endpoints in apps/api/tests/contract/test_task_management_api.py"
Task: "Add unit coverage for run creation, active-run conflicts, unsupported task types, and termination flows in apps/api/tests/unit/tasks/test_service.py and apps/api/tests/unit/tasks/test_runner.py"
Task: "Add API/router coverage for run trigger and termination endpoints in apps/api/tests/unit/tasks/test_router.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Setup
2. Complete Foundational task infrastructure
3. Deliver task type catalog plus task definition CRUD
4. Validate the admin task management baseline

### Incremental Delivery

1. Add task definition management (US1)
2. Layer manual execution and termination (US2)
3. Layer history and run logs (US3)
4. Finish documentation and validation

### Parallel Team Strategy

With multiple developers:

1. One developer handles SQL/repository groundwork
2. One developer handles service/runner/runtime logic
3. One developer handles API schemas/router/tests
4. Merge at story checkpoints only

---

## Notes

- [P] tasks = different files, no dependencies
- Story labels map tasks to specific user stories for traceability
- Keep task-specific execution logs separate from the existing global log stream
- Do not reintroduce successful no-op placeholder execution for unsupported task types
- Preserve existing authenticated access rules on all task-management endpoints
