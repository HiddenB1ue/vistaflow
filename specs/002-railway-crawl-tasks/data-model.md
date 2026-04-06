# Data Model: Railway Crawl Task Types

## Entity: TaskTypeCatalogEntry (extended)

**Purpose**: Exposes supported task types and their configuration rules to task-management clients.

### Fields

- `type`: string identifier
- `label`: display label
- `description`: human-readable purpose
- `implemented`: boolean
- `supports_cron`: boolean
- `param_schema`: ordered list of task parameter definitions

### Validation Rules

- `type` must be unique across the catalog.
- `param_schema` order is stable for client rendering.
- Implemented railway task types must publish their required payload fields.

## Entity: TaskParameterSpec

**Purpose**: Describes one user-supplied payload field for a task type.

### Fields

- `key`: payload key name
- `label`: display label
- `value_type`: primitive input type (`date`, `text`)
- `required`: boolean
- `placeholder`: example input
- `description`: validation/help text

## Entity: TaskDefinition (railway variants)

**Purpose**: Represents a reusable task configuration stored in the task center.

### Shared Fields

- `id`: integer, primary key
- `name`: string, unique
- `type`: enum including `fetch-trains`, `fetch-train-stops`, `fetch-train-runs`
- `description`: optional string
- `enabled`: boolean
- `cron`: optional string
- `payload`: object containing task-type-specific parameters
- `status`: enum (`idle`, `running`, `completed`, `error`, `terminated`)
- `latest_run_*`: latest execution summary fields
- `metrics_*`, `timing_*`: latest run metrics/timing labels and values
- `created_at`, `updated_at`: datetimes

### Payload Variants

#### FetchTrainsPayload
- `date`: required string date, normalized to `YYYY-MM-DD`
- `keyword`: required non-empty string

#### FetchTrainStopsPayload
- `date`: required string date, normalized to `YYYY-MM-DD`
- `train_code`: required non-empty train code string

#### FetchTrainRunsPayload
- `date`: required string date, normalized to `YYYY-MM-DD`
- `train_code`: required non-empty train code string

### Validation Rules

- `payload` must match the selected task type's variant.
- Empty or whitespace-only `keyword` / `train_code` values are invalid.
- Date values must be normalized before persistence and execution.
- A task cannot start a new run while another run is `pending` or `running`.

## Entity: TrainCatalogRow

**Purpose**: Normalized train discovery record returned by the crawler and prepared for persistence into `trains`.

### Fields

- `date`: source query date
- `train_no`: required stable train identity
- `station_train_code`: public train code shown to operators
- `from_station`: origin station name
- `to_station`: destination station name
- `total_num`: optional total stop count
- `keyword`: keyword that produced the match (execution metadata only)

### Validation Rules

- `train_no` is required.
- Duplicate logical rows are deduplicated by train identity and route fields before persistence.

## Entity: TrainStopRow

**Purpose**: Normalized stop detail row prepared for persistence into `train_stops`.

### Fields

- `train_no`: required train identity
- `train_date`: source date used for lookup
- `station_no`: required positive integer stop sequence
- `station_name`: station display name
- `station_train_code`: public train code
- `arrive_time`, `start_time`: optional time strings
- `running_time`: optional segment duration string
- `arrive_day_diff`: optional integer day offset
- `arrive_day_str`: optional display text for day offset
- `is_start`: optional marker from source payload
- `start_station_name`, `end_station_name`: route boundary station names
- `train_class_name`, `service_type`: optional source classification fields

### Validation Rules

- `(train_no, station_no)` must remain unique in persistence.
- Stop rows are invalid if `train_no` or `station_no` is missing.
- Stop rows must be ordered by `station_no` for downstream usage.

## Entity: TrainRunFact

**Purpose**: Normalized per-date train operating fact prepared for persistence into `train_runs`.

### Fields

- `train_no`: required train identity used to resolve `train_id`
- `run_date`: required normalized date
- `status`: normalized run status, defaulting to `running` when the upstream row proves the train runs on that date

### Validation Rules

- `(train_no, run_date)` maps to one logical run fact.
- Persistence requires a resolvable parent train identity.
- Repeat synchronization updates the existing fact instead of creating duplicates.

## Entity: TaskRun / TaskRunLog (existing execution model)

**Purpose**: Capture one execution attempt and its ordered diagnostic trail.

### Additional Railway Semantics

- `summary` records the business outcome, such as imported row count or the reason no target data was found.
- `metrics_value` stores a compact processed/imported count for task list display.
- Run logs must include at least: start, crawl outcome, persistence outcome, and final status/error.

## Relationships

- One `TaskTypeCatalogEntry` defines zero or more `TaskDefinition` records of the same `type`.
- One `TaskDefinition` has many `TaskRun` records.
- One `TaskRun` has many `TaskRunLog` records.
- One `TrainCatalogRow` may be materialized as one `Train Record` in `trains`.
- One `Train Record` has many `TrainStopRow` records and many `TrainRunFact` records.
