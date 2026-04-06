# Tasks: Railway Crawl Task Types

**Input**: Design documents from `/specs/002-railway-crawl-tasks/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Automated tests are REQUIRED by the backend constitution. Each user story includes the applicable unit, integration, contract, and regression coverage needed to verify the change.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., [US1], [US2], [US3])
- Include exact file paths in descriptions

## Path Conventions

- Backend application code lives in `apps/api/app/`
- Backend automated tests live in `apps/api/tests/`
- SQL schema and migration artifacts live in `infra/sql/`
- Paths shown below assume a backend feature in this repository

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare the backend test surface and feature scaffolding for railway crawl tasks.

- [x] T001 Create the integration task test package in `apps/api/tests/integration/tasks/__init__.py`
- [x] T002 Update shared crawler/task fixtures in `apps/api/tests/conftest.py`
- [x] T003 [P] Create the railway repository regression test module in `apps/api/tests/unit/railway/test_repository.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish shared task metadata, crawler interfaces, persistence helpers, and schema support required by all user stories.

**CRITICAL**: No user story work can begin until this phase is complete.

- [x] T004 Update task type literals and catalog definitions in `apps/api/app/tasks/constants.py` and `apps/api/app/models.py`
- [x] T005 [P] Add shared railway task parameter schema models in `apps/api/app/tasks/schemas.py`
- [x] T006 [P] Extend the crawler abstraction for trains, stops, and runs in `apps/api/app/integrations/crawler/client.py`
- [x] T007 [P] Add shared train, stop, and run persistence helpers in `apps/api/app/railway/repository.py`
- [x] T008 Update railway crawl storage artifacts in `infra/sql/migrations/0006_railway_crawl_tasks.sql` and `infra/sql/schema.sql`
- [x] T009 Add shared railway task exceptions and execution helper structures in `apps/api/app/tasks/exceptions.py` and `apps/api/app/tasks/handlers.py`

**Checkpoint**: Foundation ready - user story implementation can now begin.

---

## Phase 3: User Story 1 - 配置铁路采集任务 (Priority: P1) MVP

**Goal**: Let administrators discover the three railway task types and create, update, and read valid railway task definitions through the existing task API.

**Independent Test**: `GET /task-types` returns the three railway task types with parameter metadata, and `POST /tasks` / `PATCH /tasks/{task_id}` accept normalized valid payloads while rejecting invalid railway payloads.

### Tests for User Story 1 (REQUIRED)

- [x] T010 [P] [US1] Extend task catalog and task definition contract coverage in `apps/api/tests/contract/test_task_management_api.py`
- [x] T011 [P] [US1] Add railway task configuration integration coverage in `apps/api/tests/integration/tasks/test_railway_task_configuration.py`
- [x] T012 [P] [US1] Extend railway payload validation coverage in `apps/api/tests/unit/tasks/test_service.py` and `apps/api/tests/unit/tasks/test_router.py`

### Implementation for User Story 1

- [x] T013 [US1] Implement railway payload normalization and task type response serialization in `apps/api/app/tasks/schemas.py`
- [x] T014 [US1] Implement railway task create/update validation orchestration in `apps/api/app/tasks/service.py`
- [x] T015 [US1] Persist normalized railway task payloads in `apps/api/app/tasks/repository.py`
- [x] T016 [US1] Expose railway task catalog and validation behavior through `apps/api/app/tasks/router.py`

**Checkpoint**: User Story 1 should now be fully functional and testable independently.

---

## Phase 4: User Story 2 - 同步车次与经停数据 (Priority: P1)

**Goal**: Let administrators manually run train catalog and train-stop tasks so VistaFlow writes idempotent train and stop data into the existing railway tables with run logs and summaries.

**Independent Test**: A configured `fetch-trains` or `fetch-train-stops` task can be run through the existing task API, writes expected rows into `trains` / `train_stops`, and exposes run status, summary, and logs without duplicate logical rows.

### Tests for User Story 2 (REQUIRED)

- [x] T017 [P] [US2] Extend task-run contract coverage for `fetch-trains` and `fetch-train-stops` in `apps/api/tests/contract/test_task_management_api.py`
- [x] T018 [P] [US2] Add execution integration coverage for train catalog and stop sync in `apps/api/tests/integration/tasks/test_railway_task_execution.py`
- [x] T019 [P] [US2] Add train catalog and stop sync regression coverage in `apps/api/tests/unit/tasks/test_runner.py` and `apps/api/tests/unit/railway/test_repository.py`

### Implementation for User Story 2

- [x] T020 [US2] Implement train catalog crawl collection and normalization in `apps/api/app/integrations/crawler/client.py`
- [x] T021 [US2] Implement train catalog upsert and train-resolution helpers in `apps/api/app/railway/repository.py`
- [x] T022 [US2] Implement `fetch-trains` and `fetch-train-stops` execution handlers in `apps/api/app/tasks/handlers.py`
- [x] T023 [US2] Register train catalog and stop sync handlers in `apps/api/app/tasks/runner.py`
- [x] T024 [US2] Update run summary and log persistence for train catalog and stop sync in `apps/api/app/tasks/repository.py` and `apps/api/app/tasks/service.py`

**Checkpoint**: User Stories 1 and 2 should both work independently.

---

## Phase 5: User Story 3 - 同步指定日期的运行车次记录 (Priority: P2)

**Goal**: Let administrators manually run a per-date train-run task so VistaFlow records idempotent run facts for a specific train/date combination while preserving the unchanged 12306 protocol.

**Independent Test**: A configured `fetch-train-runs` task can be run through the existing task API, writes or updates the matching `train_runs` row, and reports actionable errors when the source returns no run fact or no parent train can be resolved.

### Tests for User Story 3 (REQUIRED)

- [x] T025 [P] [US3] Extend task-run contract coverage for `fetch-train-runs` in `apps/api/tests/contract/test_task_management_api.py`
- [x] T026 [P] [US3] Add execution integration coverage for per-date run sync in `apps/api/tests/integration/tasks/test_railway_task_execution.py`
- [x] T027 [P] [US3] Add run-sync regression coverage in `apps/api/tests/unit/tasks/test_runner.py` and `apps/api/tests/unit/railway/test_repository.py`

### Implementation for User Story 3

- [x] T028 [US3] Implement per-date train-run crawl collection with the unchanged 12306 contract in `apps/api/app/integrations/crawler/client.py`
- [x] T029 [US3] Implement train-run normalization and upsert helpers in `apps/api/app/railway/repository.py`
- [x] T030 [US3] Implement the `fetch-train-runs` handler and zero-result error semantics in `apps/api/app/tasks/handlers.py`
- [x] T031 [US3] Register per-date run sync execution behavior in `apps/api/app/tasks/runner.py` and `apps/api/app/tasks/service.py`

**Checkpoint**: All user stories should now be independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finish documentation, cross-story observability review, and backend quality verification.

- [x] T032 [P] Update backend task usage documentation in `apps/api/README.md`
- [x] T033 Review cross-story log/error text and task summaries in `apps/api/app/tasks/handlers.py` and `apps/api/app/tasks/exceptions.py`
- [x] T034 [P] Validate the feature walkthrough in `specs/002-railway-crawl-tasks/quickstart.md`
- [x] T035 Run backend quality gates from `apps/api/` using `uv run ruff check .`, `uv run mypy app tests`, and `uv run pytest --cov=app --cov-report=term-missing`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup** - No dependencies; can start immediately.
- **Phase 2: Foundational** - Depends on Phase 1; blocks all user stories.
- **Phase 3: User Story 1** - Depends on Phase 2; delivers the MVP.
- **Phase 4: User Story 2** - Depends on Phase 2 and can begin after foundation is ready.
- **Phase 5: User Story 3** - Depends on Phase 2 and can begin after foundation is ready.
- **Phase 6: Polish** - Depends on the user stories selected for delivery.

### User Story Dependencies

- **US1**: No dependency on other user stories after the foundational phase.
- **US2**: No dependency on US1 for implementation, but reuses the same task API surface and benefits from US1 task-definition support.
- **US3**: No dependency on US2 for code structure, but test fixtures should seed parent train data so run-fact behavior stays independently testable.

### Within Each User Story

- Write or update automated tests before considering the story complete.
- Complete crawler/repository changes before final handler wiring for execution stories.
- Complete service-layer validation before router-level contract confirmation for configuration work.
- Finish handler/runner wiring before polish on summary/log wording.

### Parallel Opportunities

- `T003` can run in parallel with `T001`-`T002`.
- `T005`, `T006`, and `T007` can run in parallel after `T004`.
- Within US1, `T010`, `T011`, and `T012` can run in parallel.
- Within US2, `T017`, `T018`, and `T019` can run in parallel.
- Within US3, `T025`, `T026`, and `T027` can run in parallel.
- `T032` and `T034` can run in parallel during polish.

---

## Parallel Example: User Story 1

```bash
# Launch the three validation-focused test tasks together:
Task: "Extend task catalog and task definition contract coverage in apps/api/tests/contract/test_task_management_api.py"
Task: "Add railway task configuration integration coverage in apps/api/tests/integration/tasks/test_railway_task_configuration.py"
Task: "Extend railway payload validation coverage in apps/api/tests/unit/tasks/test_service.py and apps/api/tests/unit/tasks/test_router.py"

# Launch independent shared groundwork together once T004 is complete:
Task: "Add shared railway task parameter schema models in apps/api/app/tasks/schemas.py"
Task: "Extend the crawler abstraction for trains, stops, and runs in apps/api/app/integrations/crawler/client.py"
Task: "Add shared train, stop, and run persistence helpers in apps/api/app/railway/repository.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Stop and validate `GET /task-types`, `POST /tasks`, and `PATCH /tasks/{task_id}` for railway task payloads.
5. Demo or merge the task-definition support if incremental delivery is desired.

### Incremental Delivery

1. Deliver Setup + Foundational.
2. Deliver US1 so administrators can define railway crawl tasks.
3. Deliver US2 so train catalog and stop synchronization work end-to-end.
4. Deliver US3 so per-date run synchronization works end-to-end.
5. Finish with Phase 6 polish and full backend quality gates.

### Parallel Team Strategy

1. One developer handles shared task metadata (`apps/api/app/tasks/constants.py`, `apps/api/app/tasks/schemas.py`).
2. One developer handles crawler protocol-preserving methods in `apps/api/app/integrations/crawler/client.py`.
3. One developer handles railway persistence in `apps/api/app/railway/repository.py`.
4. After the foundational phase, execution handlers and tests can split by user story.

---

## Notes

- [P] tasks use different files and can proceed without waiting on the same incomplete file.
- [US1] is the recommended MVP scope.
- Preserve the 12306-side request parameters, request method, and response structure while implementing all execution logic.
- Keep task API changes inside the existing tasks domain; do not add a separate railway admin entry point.
- Commit after each completed task or logical task group.
