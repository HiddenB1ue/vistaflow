# Data Model: Backend Task Management API

## Entity: TaskDefinition

**Purpose**: Represents a reusable task configuration that operators manage and trigger repeatedly.

### Fields

- `id`: integer, primary key
- `name`: string, unique, 1-128 chars
- `type`: enum (`fetch-station`, `geocode`, `fetch-status`, `price`, `cleanup`)
- `type_label`: string, derived display label
- `description`: optional string
- `enabled`: boolean
- `cron`: optional string schedule expression for future automation
- `payload`: object/dictionary for task-specific configuration
- `status`: enum (`idle`, `running`, `completed`, `error`, `terminated`)
- `latest_run_id`: optional integer reference to latest run
- `latest_run_status`: optional enum matching run status
- `latest_run_started_at`: optional datetime
- `latest_run_finished_at`: optional datetime
- `latest_error_message`: optional string
- `metrics_label`: string summary label
- `metrics_value`: string summary value
- `timing_label`: string summary label
- `timing_value`: string summary value
- `created_at`: datetime
- `updated_at`: datetime

### Validation Rules

- `name` must be unique.
- `type` must exist in the task type catalog.
- `cron` may be null or a non-empty string.
- `payload` defaults to `{}` and must be a JSON object.
- Only one active run is allowed per task definition at a time.

### State Transitions

- `idle` -> `running` when a new run starts
- `running` -> `completed` | `error` | `terminated` when the active run finishes
- `completed` / `error` / `terminated` -> `running` when a later run starts

## Entity: TaskRun

**Purpose**: Represents one concrete execution of a task definition.

### Fields

- `id`: integer, primary key
- `task_id`: foreign key to TaskDefinition
- `trigger_mode`: enum (`manual`)
- `status`: enum (`pending`, `running`, `completed`, `error`, `terminated`)
- `requested_by`: string summary of trigger source (initially `admin`)
- `summary`: optional string result summary
- `metrics_value`: string summary output for the run
- `error_message`: optional string
- `termination_reason`: optional string
- `started_at`: optional datetime
- `finished_at`: optional datetime
- `created_at`: datetime
- `updated_at`: datetime

### Validation Rules

- `task_id` must reference an existing task.
- A run can be terminated only while it is `running`.
- `finished_at` must be null until the run reaches a terminal state.

### State Transitions

- `pending` -> `running`
- `running` -> `completed` | `error` | `terminated`

## Entity: TaskRunLog

**Purpose**: Stores ordered event logs for a single task run.

### Fields

- `id`: integer, primary key
- `run_id`: foreign key to TaskRun
- `severity`: enum (`INFO`, `SUCCESS`, `WARN`, `ERROR`, `SYSTEM`)
- `message`: string
- `created_at`: datetime

### Validation Rules

- `run_id` must reference an existing run.
- Logs are immutable after insertion.

## Entity: TaskTypeCatalogEntry

**Purpose**: Exposes supported task types to API consumers.

### Fields

- `type`: string identifier
- `label`: display label
- `description`: string
- `implemented`: boolean
- `supports_cron`: boolean

### Relationships

- One `TaskDefinition` has many `TaskRun` records.
- One `TaskRun` has many `TaskRunLog` records.
- Each `TaskDefinition` references one catalog entry by `type`.
