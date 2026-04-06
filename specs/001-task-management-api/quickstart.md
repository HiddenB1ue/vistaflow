# Quickstart: Backend Task Management API

## Prerequisites

1. Start the backend from `apps/api/`.
2. Ensure the new task-management migration has been applied.
3. Provide an admin bearer token accepted by the existing auth layer.

## Scenario 1: Discover available task types

```bash
curl -H "Authorization: Bearer $ADMIN_TOKEN"   http://localhost:8000/task-types
```

Expected result: a list of task types with labels, descriptions, and whether each type is currently implemented.

## Scenario 2: Create and inspect a task definition

```bash
curl -X POST   -H "Authorization: Bearer $ADMIN_TOKEN"   -H "Content-Type: application/json"   http://localhost:8000/tasks   -d '{
    "name": "Nightly Station Sync",
    "type": "fetch-station",
    "description": "Refresh station master data",
    "enabled": true,
    "cron": "0 2 * * *",
    "payload": {}
  }'
```

Then query it:

```bash
curl -H "Authorization: Bearer $ADMIN_TOKEN"   http://localhost:8000/tasks/1
```

Expected result: task definition includes its current status and latest-run summary fields.

## Scenario 3: Run the task manually and inspect history

```bash
curl -X POST   -H "Authorization: Bearer $ADMIN_TOKEN"   http://localhost:8000/tasks/1/run
```

Expected result: a new run record is returned immediately with `pending` or `running` state.

List run history:

```bash
curl -H "Authorization: Bearer $ADMIN_TOKEN"   http://localhost:8000/tasks/1/runs
```

Get run detail and logs:

```bash
curl -H "Authorization: Bearer $ADMIN_TOKEN"   http://localhost:8000/task-runs/1

curl -H "Authorization: Bearer $ADMIN_TOKEN"   http://localhost:8000/task-runs/1/logs
```

Expected result: the run transitions to a terminal state and logs explain whether data was collected and written.

## Scenario 4: Terminate a long-running execution

```bash
curl -X POST   -H "Authorization: Bearer $ADMIN_TOKEN"   http://localhost:8000/task-runs/1/terminate
```

Expected result: the run becomes `terminated`, and the parent task is no longer marked as running.
