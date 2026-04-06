# Research: Railway Crawl Task Types

## Decision 1: Preserve the 12306 crawl protocol exactly as-is

**Decision**: Keep the 12306-side request parameters, request assembly pattern, endpoint usage, and response shape interpretation aligned with the existing crawler approach already proven in `other/to-rome` and VistaFlow's current 12306 integrations.

**Rationale**: The user explicitly requires protocol stability on the crawler side. This limits change risk to VistaFlow's internal orchestration and avoids revalidating upstream request/response assumptions.

**Alternatives considered**:
- Re-design the 12306 client contract to use VistaFlow-native request/response models from the start — rejected because it changes the upstream protocol boundary.
- Introduce a brand-new crawler adapter layer with transformed payloads — rejected because it adds conversion complexity without user value for this feature.

## Decision 2: Add three implemented task types using VistaFlow naming conventions

**Decision**: Add `fetch-trains`, `fetch-train-stops`, and `fetch-train-runs` as implemented task types in the existing tasks domain, while exposing human-readable labels and parameter metadata through the task-type catalog.

**Rationale**: VistaFlow already uses hyphenated task identifiers such as `fetch-station`. Matching that convention keeps constants, validation, and run history internally consistent while still mapping cleanly to the user's three requested business actions.

**Alternatives considered**:
- Reuse `to-rome` names (`get_trains`, `get_stops`, `get_trains_run`) directly — rejected because they do not match VistaFlow's existing task-type style.
- Reuse the existing placeholder `fetch-status` for per-date train runs — rejected because the requested behavior is narrower and needs distinct payload rules plus persistence semantics.

## Decision 3: Validate task payloads inside the tasks domain before execution

**Decision**: Keep task creation and execution on the existing task endpoints, but introduce per-task-type payload validation and normalization in VistaFlow's tasks schemas/service layer, including task-type metadata that describes required fields.

**Rationale**: The feature adds no new admin entry point; it extends current task management behavior. Early payload validation prevents invalid tasks from being stored and allows `/task-types` to become the single source of truth for railway task configuration.

**Alternatives considered**:
- Validate only at execution time — rejected because it allows invalid task definitions to accumulate.
- Create dedicated railway admin endpoints — rejected because the spec requires reuse of VistaFlow's task center.

## Decision 4: Use idempotent upsert persistence across trains, stops, and runs

**Decision**: Persist train catalog rows into `trains`, stop rows into `train_stops`, and per-date run facts into `train_runs` using upsert-oriented repository operations. `fetch-train-stops` and `fetch-train-runs` may upsert parent train rows before writing dependent records when the incoming source data contains sufficient train identity information.

**Rationale**: The existing railway schema already models uniqueness around `train_no`, `(train_no, station_no)`, and `(train_id, run_date)`. Upsert semantics satisfy the user's repeat-execution requirement and align with the reference behavior in `to-rome`.

**Alternatives considered**:
- Insert-only writes — rejected because repeated task runs would create conflicts or data gaps.
- Delete-and-reload for every run — rejected because it is heavier operationally and risks partial data loss on failures.

## Decision 5: Differentiate zero-result behavior by task intent

**Decision**: Treat `fetch-trains` returning zero rows as a completed run with an explicit zero-count summary, because the query is exploratory by date + keyword. Treat `fetch-train-stops` and `fetch-train-runs` returning zero normalized rows as execution errors, because those tasks target a specific train/date combination and missing data is actionable.

**Rationale**: The spec requires the system to distinguish empty results from failures. The meaning of "no data" differs between broad train discovery and targeted stop/run synchronization.

**Alternatives considered**:
- Mark every zero-result run as success — rejected because targeted tasks would silently hide missing upstream data.
- Mark every zero-result run as failure — rejected because broad train discovery can legitimately return no matches for a keyword/date pair.
