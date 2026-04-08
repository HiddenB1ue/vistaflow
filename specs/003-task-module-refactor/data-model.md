# Data Model: Task Module Refactor

## 1. Task Type Definition

Represents the canonical in-code definition for one task type.

### Fields

- `type`: stable task type identifier used by persisted task definitions and API responses
- `label`: human-readable display name shown in the task type catalog
- `description`: operator-facing explanation of the task's purpose
- `implemented`: whether the task can be executed now
- `supports_cron`: whether the task type can participate in future scheduling workflows
- `capabilities`: execution capability declaration (manual run support, termination support, progress support, etc.)
- `param_contract`: ordered parameter definitions and payload normalization behavior
- `executor`: task execution entrypoint used by the runtime

### Validation Rules

- `type` must remain unique across all task type definitions
- `type` must remain compatible with persisted `task.type` values already stored
- an executable task type must declare both a parameter contract and an executor
- non-executable task types may remain visible in the catalog, but must not be triggerable

## 2. Task Capability Contract

Describes the framework-level runtime abilities of a task type.

### Fields

- `can_run`: whether a task type may be manually executed
- `can_terminate`: whether an active run can be terminated by administrators
- `supports_progress_snapshot`: whether the task writes structured progress details
- `supports_cron`: whether future scheduled execution is allowed
- `default_summary_behavior`: whether the framework supplies a fallback summary when the task does not

### Validation Rules

- capability values must be explicit for every task type
- termination support must not be implied only by runtime status
- public task APIs must expose behavior consistent with capability declarations

## 3. Task Parameter Contract

Represents the task-type-specific contract used by task create/update/run validation.

### Fields

- `key`: stable payload field name
- `label`: display label for operators
- `value_type`: logical input type such as date or text
- `required`: whether the field must be present after normalization
- `placeholder`: suggested UI placeholder
- `description`: operator-facing help text
- `normalizer`: task-type-owned normalization and validation rule set

### Validation Rules

- task payloads must be normalized through the same contract for create, update, and execute paths
- payload normalization must not depend on duplicated per-endpoint branches
- validation failures must map to a consistent business error surface

## 4. Task Execution Context Contract

Defines the stable shared runtime boundary supplied to all task executors.

### Fields

- `task_definition`: the persisted task being executed
- `run_record`: current task run identity and lifecycle context
- `logging_port`: framework-provided log and summary writer interface
- `progress_port`: framework-provided progress snapshot writer interface
- `persistence_ports`: stable access to task/run persistence needed by all executors
- `service_access`: explicit access path to task-family-specific runtime dependencies

### Validation Rules

- the shared contract must remain business-agnostic
- business-specific dependencies must not be added directly unless they are shared by all task families
- missing required service access for a task type must fail deterministically during registration or execution setup

## 5. Task Runtime Outcome

Represents the normalized result returned by any task executor.

### Fields

- `status`: completed, error, terminated, or other supported lifecycle result
- `summary`: operator-facing execution summary
- `metrics_value`: result count or metric string shown in the task center
- `timing_value`: optional execution duration override
- `progress_snapshot`: structured progress payload compatible with current consumers
- `error_message`: actionable failure message when execution does not succeed

### Validation Rules

- every execution path must end in a normalized outcome or a framework-mapped failure
- the runtime outcome must remain compatible with current `task_run` and `task` persistence fields
- progress snapshots may vary in detail, but must preserve the stable outer structure already consumed by the API

## Relationships

- One **Task Type Definition** owns one **Task Capability Contract** and one **Task Parameter Contract** bundle.
- One persisted task definition references one **Task Type Definition** by `type`.
- One task run is executed through one **Task Execution Context Contract** and produces one **Task Runtime Outcome**.
- Existing persisted `task`, `task_run`, and `task_run_log` records remain unchanged as durable runtime records; this feature primarily refactors the in-code relationships around them.

## State & Lifecycle Notes

- Task type registration is validated at startup or test time before operators interact with the task catalog.
- Persisted task definitions continue to move through existing statuses (`idle`, `running`, `completed`, `error`, `terminated`).
- Task runs continue to move through existing statuses (`pending`, `running`, `completed`, `error`, `terminated`).
- This feature does not redefine persisted task lifecycle states; it standardizes how task types participate in that lifecycle.
