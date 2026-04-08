# Research: Task Module Refactor

## Decision 1: Replace dispersed task-type mappings with a unified task definition registry

- **Decision**: Introduce a single registry abstraction where each task type contributes one self-contained definition object describing metadata, capability flags, payload contract, and execution entrypoint.
- **Rationale**: The current design spreads task metadata across `constants.py`, `schemas.py`, `runner.py`, and `handlers.py`, which makes new task onboarding error-prone and encourages drift. A unified registry lets create/update/execute flows read from the same source of truth.
- **Alternatives considered**:
  - Keep the current split mapping approach and only add comments: rejected because it reduces readability but not change surface.
  - Build fully dynamic plugin discovery from the filesystem: rejected for now because it adds runtime magic and weaker startup determinism than the project currently needs.

## Decision 2: Modularize task implementations by task type while keeping the tasks domain intact

- **Decision**: Split concrete task logic into per-task modules under the existing `apps/api/app/tasks/` domain (for example a `types/` or `definitions/` subpackage), while retaining shared lifecycle orchestration in the tasks domain.
- **Rationale**: This preserves constitution-mandated domain boundaries and removes the growing `handlers.py` bottleneck without pushing task logic into unrelated domains.
- **Alternatives considered**:
  - Keep all handlers in one file and only extract helper functions: rejected because it does not solve long-term growth or ownership clarity.
  - Move each task into its business domain (`railway/`, `system/`, etc.) immediately: rejected because the current task lifecycle, validation, and runtime logic still belongs to `tasks/`, and a full cross-domain execution framework is beyond this feature scope.

## Decision 3: Keep current external API and persistence contracts stable during the refactor

- **Decision**: Treat the existing admin task API, stored task definitions, task run history, task run logs, and progress snapshot shape as compatibility boundaries; internal refactor may reorganize code, but should not require path changes, response rewrites, or destructive data migration.
- **Rationale**: The primary risk of this feature is regression in current task management behavior. Preserving the public and persisted contracts keeps the refactor incremental and reviewable.
- **Alternatives considered**:
  - Redesign task API responses during the refactor: rejected because it broadens scope and increases migration risk.
  - Introduce new tables for task-type metadata immediately: rejected because task-type capability metadata can remain code-defined unless a later feature proves persistence is required.

## Decision 4: Introduce a stable execution context boundary instead of growing a business-specific handler context

- **Decision**: Define a stable shared execution context contract for lifecycle concerns (run id, logging, repositories, progress updates, termination support) and move business-specific dependencies behind explicit provider or service access patterns used by task definitions.
- **Rationale**: The current `HandlerContext` is already biased toward railway tasks. Without a cleaner boundary, every new task family will keep inflating shared context with unrelated dependencies.
- **Alternatives considered**:
  - Continue injecting every dependency into one expanding context object: rejected because it increases coupling and makes non-railway tasks awkward.
  - Build a full dependency injection container for task execution: rejected because FastAPI request-time DI already exists and a bespoke runtime container would be overkill for this refactor.

## Decision 5: Preserve the current in-process execution model for now

- **Decision**: Keep the existing in-process `asyncio.create_task` execution model, runtime registry, and recovery semantics unchanged during this refactor.
- **Rationale**: The user goal is extensibility and maintainability, not distributed scheduling. Separating structural cleanup from execution architecture change keeps the feature bounded and reduces delivery risk.
- **Alternatives considered**:
  - Migrate to Celery, APScheduler, or a distributed worker model now: rejected because it would turn a maintainability refactor into a platform rewrite.
  - Add cron execution in the same feature: rejected because current `cron` support remains reserved and is not necessary to achieve the extensibility objective.

## Decision 6: Use automated compatibility tests as the primary regression guard

- **Decision**: Expand unit, integration, and contract tests to verify that existing task types still expose the same catalog entries, payload behavior, run lifecycle, logs, and termination semantics after migration to the new registry structure.
- **Rationale**: A refactor of this kind is only safe if compatibility is continuously verified at the framework and task-type level.
- **Alternatives considered**:
  - Rely on manual smoke testing: rejected by the backend constitution and insufficient for lifecycle-heavy code.
  - Only test the new registration layer: rejected because it would miss regressions in migrated task behaviors.
