# Tasks: Task Module Refactor

**Input**: Design documents from `/specs/003-task-module-refactor/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Automated tests are REQUIRED by the backend constitution. Each user story includes the applicable unit, integration, contract, and regression coverage needed to verify the change.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this belongs to (e.g. `[US1]`, `[US2]`, `[US3]`)
- Include exact file paths in descriptions

## Path Conventions

- Backend application code lives in `apps/api/app/`
- Backend automated tests live in `apps/api/tests/`
- SQL schema and migration artifacts live in `infra/sql/`
- Paths shown below assume a backend feature in this repository

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Capture the current compatibility baseline and create the internal scaffolding for the refactor.

- [ ] T001 Capture the current task-module compatibility baseline in `apps/api/tests/contract/test_task_management_api.py`, `apps/api/tests/integration/tasks/test_railway_task_execution.py`, `apps/api/tests/unit/tasks/test_runner.py`, and `apps/api/tests/unit/tasks/test_service.py`
- [ ] T002 Create the internal task-definition scaffolding in `apps/api/app/tasks/definition.py`, `apps/api/app/tasks/registry.py`, `apps/api/app/tasks/execution.py`, and `apps/api/app/tasks/types/__init__.py`
- [ ] T003 [P] Create registry-focused test scaffolding in `apps/api/tests/unit/tasks/test_registry.py` and `apps/api/tests/integration/tasks/test_task_registry.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish the shared registry, execution boundary, and compatibility rules required by all user stories.

**CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T004 Refactor shared task type and capability contracts out of `apps/api/app/tasks/constants.py` and `apps/api/app/models.py` into `apps/api/app/tasks/definition.py`
- [ ] T005 [P] Implement registry loading, duplicate-definition checks, and lookup helpers in `apps/api/app/tasks/registry.py` and `apps/api/app/tasks/types/__init__.py`
- [ ] T006 [P] Implement the shared execution context, lifecycle ports, and runtime result helpers in `apps/api/app/tasks/execution.py` and `apps/api/app/tasks/progress.py`
- [ ] T007 [P] Update task dependency wiring and runtime bootstrapping in `apps/api/app/tasks/dependencies.py` and `apps/api/app/main.py` to provide registry-aware services
- [ ] T008 Implement shared task-definition diagnostics and framework-level errors in `apps/api/app/tasks/exceptions.py`
- [ ] T009 Document the no-destructive-migration compatibility baseline in `apps/api/README.md` and `specs/003-task-module-refactor/quickstart.md`

**Checkpoint**: Foundation ready - user story implementation can now begin.

---

## Phase 3: User Story 1 - 用统一方式定义和注册任务类型 (Priority: P1) MVP

**Goal**: Let developers define metadata, payload rules, and execution entrypoints from one task-type-owned definition path instead of multiple hardcoded registries.

**Independent Test**: A new or migrated task type can be loaded into the catalog, validated on create/update, and resolved for execution through one unified registration path.

### Tests for User Story 1 (REQUIRED)

- [ ] T010 [P] [US1] Extend contract coverage for registry-driven task catalogs and payload validation reuse in `apps/api/tests/contract/test_task_management_api.py`
- [ ] T011 [P] [US1] Add unit coverage for task-definition validity, uniqueness, and payload normalization in `apps/api/tests/unit/tasks/test_registry.py`
- [ ] T012 [P] [US1] Add integration coverage for registry-backed task catalog loading in `apps/api/tests/integration/tasks/test_task_registry.py`

### Implementation for User Story 1

- [ ] T013 [US1] Implement registry-driven task catalog serialization in `apps/api/app/tasks/schemas.py` and `apps/api/app/tasks/service.py`
- [ ] T014 [US1] Migrate built-in task metadata and parameter contracts into `apps/api/app/tasks/types/fetch_station.py`, `apps/api/app/tasks/types/fetch_trains.py`, `apps/api/app/tasks/types/fetch_train_stops.py`, `apps/api/app/tasks/types/fetch_train_runs.py`, and `apps/api/app/tasks/types/price.py`
- [ ] T015 [US1] Remove hardcoded task-type metadata ownership from `apps/api/app/tasks/constants.py` and update shared task exports in `apps/api/app/tasks/__init__.py`
- [ ] T016 [US1] Refactor task create/update validation to consume task-type-owned contracts in `apps/api/app/tasks/schemas.py`, `apps/api/app/tasks/service.py`, and `apps/api/app/tasks/repository.py`

**Checkpoint**: User Story 1 should now be fully functional and testable independently.

---

## Phase 4: User Story 2 - 在重构后继续稳定运行现有任务 (Priority: P1)

**Goal**: Keep the existing admin task API and all four implemented task types behaviorally compatible after migration to the new registry structure.

**Independent Test**: The current implemented task types can still be queried, created, run, inspected, and terminated through the same endpoints, with compatible summaries, logs, and progress snapshots.

### Tests for User Story 2 (REQUIRED)

- [ ] T017 [P] [US2] Extend contract coverage for existing run/log/terminate compatibility in `apps/api/tests/contract/test_task_management_api.py`
- [ ] T018 [P] [US2] Add integration regression coverage for migrated built-in task execution in `apps/api/tests/integration/tasks/test_railway_task_execution.py` and `apps/api/tests/integration/tasks/test_task_registry.py`
- [ ] T019 [P] [US2] Add unit regression coverage for migrated built-in task behavior in `apps/api/tests/unit/tasks/test_runner.py` and `apps/api/tests/unit/tasks/test_service.py`

### Implementation for User Story 2

- [ ] T020 [US2] Move `fetch-station` execution behavior into `apps/api/app/tasks/types/fetch_station.py` and remove redundant logic from `apps/api/app/tasks/handlers.py`
- [ ] T021 [US2] Move railway task execution behavior into `apps/api/app/tasks/types/fetch_trains.py`, `apps/api/app/tasks/types/fetch_train_stops.py`, and `apps/api/app/tasks/types/fetch_train_runs.py`
- [ ] T022 [US2] Refactor `apps/api/app/tasks/runner.py` to dispatch through the unified registry instead of the hardcoded `TASK_HANDLERS` map
- [ ] T023 [US2] Refactor `apps/api/app/tasks/service.py` and `apps/api/app/tasks/router.py` to preserve existing task API responses and run semantics after the registry migration
- [ ] T024 [US2] Reconcile reserved and orphan task behaviors by updating `apps/api/app/tasks/types/price.py`, `apps/api/app/tasks/constants.py`, and `apps/api/app/tasks/handlers.py`

**Checkpoint**: User Stories 1 and 2 should both work independently.

---

## Phase 5: User Story 3 - 为未来不同风格的任务预留一致扩展点 (Priority: P2)

**Goal**: Introduce stable capability and execution-context boundaries so future task families can be added without expanding shared business-specific plumbing.

**Independent Test**: A non-railway or example task definition can be onboarded through the same registry and lifecycle contracts without adding new business-specific fields to the shared execution context.

### Tests for User Story 3 (REQUIRED)

- [ ] T025 [P] [US3] Add unit coverage for capability declarations and execution-context boundaries in `apps/api/tests/unit/tasks/test_registry.py` and `apps/api/tests/unit/tasks/test_runner.py`
- [ ] T026 [P] [US3] Add integration coverage for capability-based execution and termination diagnostics in `apps/api/tests/integration/tasks/test_task_registry.py`
- [ ] T027 [P] [US3] Add regression coverage for onboarding an example non-railway task definition in `apps/api/tests/unit/tasks/test_registry.py` and `apps/api/tests/unit/tasks/test_service.py`

### Implementation for User Story 3

- [ ] T028 [US3] Implement task capability declarations and fallback lifecycle defaults in `apps/api/app/tasks/definition.py`, `apps/api/app/tasks/exceptions.py`, and `apps/api/app/tasks/service.py`
- [ ] T029 [US3] Implement the stable execution-context and service-access boundary in `apps/api/app/tasks/execution.py`, `apps/api/app/tasks/dependencies.py`, and `apps/api/app/tasks/runner.py`
- [ ] T030 [US3] Add registry diagnostics and invalid-definition failure handling in `apps/api/app/tasks/registry.py` and `apps/api/app/tasks/router.py`
- [ ] T031 [US3] Document the standard task-type onboarding path in `apps/api/README.md` and `specs/003-task-module-refactor/quickstart.md`

**Checkpoint**: All user stories should now be independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finish cleanup, documentation, and full validation across the refactored module.

- [ ] T032 [P] Review and reduce legacy file sprawl in `apps/api/app/tasks/handlers.py`, `apps/api/app/tasks/constants.py`, and `apps/api/app/tasks/schemas.py`
- [ ] T033 [P] Update task-module architecture guidance in `apps/api/ARCHITECTURE.md` and `apps/api/README.md`
- [ ] T034 Run the quickstart walkthrough in `specs/003-task-module-refactor/quickstart.md`
- [ ] T035 Run backend quality gates from `apps/api/` using `uv run ruff check .`, `uv run mypy app tests`, and `uv run pytest --cov=app --cov-report=term-missing`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup** - No dependencies; can start immediately.
- **Phase 2: Foundational** - Depends on Phase 1; blocks all user stories.
- **Phase 3: User Story 1** - Depends on Phase 2; delivers the new registration path and is the recommended MVP.
- **Phase 4: User Story 2** - Depends on Phase 2 and can begin after the foundation is ready.
- **Phase 5: User Story 3** - Depends on Phase 2 and can begin after the foundation is ready.
- **Phase 6: Polish** - Depends on the user stories selected for delivery.

### User Story Dependencies

- **US1**: No dependency on other user stories after the foundational phase.
- **US2**: Depends on US1's registry structure for the migration target, but remains independently testable from the operator perspective.
- **US3**: Depends on the common registry and migrated runner/service structure, but should remain independently testable with an example task definition.

### Within Each User Story

- Write or update automated tests before considering the story complete.
- Complete definition/registry updates before changing service and runner wiring.
- Migrate concrete built-in task implementations before deleting legacy hardcoded mappings.
- Finish lifecycle and diagnostics changes before final documentation cleanup.

### Parallel Opportunities

- `T003` can run in parallel with `T001`-`T002`.
- `T005`, `T006`, and `T007` can run in parallel after `T004`.
- Within US1, `T010`, `T011`, and `T012` can run in parallel.
- Within US2, `T017`, `T018`, and `T019` can run in parallel.
- Within US3, `T025`, `T026`, and `T027` can run in parallel.
- `T032` and `T033` can run in parallel during polish.

---

## Parallel Example: User Story 1

```bash
# Launch the registry-focused tests together:
Task: "Extend contract coverage for registry-driven task catalogs and payload validation reuse in apps/api/tests/contract/test_task_management_api.py"
Task: "Add unit coverage for task-definition validity, uniqueness, and payload normalization in apps/api/tests/unit/tasks/test_registry.py"
Task: "Add integration coverage for registry-backed task catalog loading in apps/api/tests/integration/tasks/test_task_registry.py"

# Launch metadata migration work in parallel once the shared contracts exist:
Task: "Migrate built-in task metadata and parameter contracts into apps/api/app/tasks/types/fetch_station.py, apps/api/app/tasks/types/fetch_trains.py, apps/api/app/tasks/types/fetch_train_stops.py, apps/api/app/tasks/types/fetch_train_runs.py, and apps/api/app/tasks/types/price.py"
Task: "Refactor task create/update validation to consume task-type-owned contracts in apps/api/app/tasks/schemas.py, apps/api/app/tasks/service.py, and apps/api/app/tasks/repository.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Stop and validate that task-type registration, catalog loading, and payload validation are unified.
5. Demo the registry-based onboarding workflow before migrating all built-in task implementations.

### Incremental Delivery

1. Deliver Setup + Foundational.
2. Deliver US1 so task-type registration and validation become unified.
3. Deliver US2 so existing operator behavior remains compatible on the new structure.
4. Deliver US3 so future task families have stable extensibility hooks.
5. Finish with Phase 6 polish and full backend quality gates.

### Parallel Team Strategy

1. One developer owns shared task-definition contracts and registry wiring.
2. One developer migrates existing built-in task definitions and runner behavior.
3. One developer owns compatibility and extensibility test coverage.
4. Documentation and final cleanup can run in parallel after the core migration stabilizes.

---

## Notes

- [P] tasks use different files and can proceed without waiting on the same incomplete file.
- [US1] is the recommended MVP scope.
- Preserve existing task API behavior and stored task/run semantics unless the spec and plan are explicitly updated.
- Avoid introducing distributed scheduling or destructive schema changes as part of this refactor.
- Commit after each completed task or logical task group.
