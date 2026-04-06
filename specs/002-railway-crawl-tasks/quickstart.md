# Quickstart: Railway Crawl Task Types

## Prerequisites

1. Start the backend from `apps/api/`.
2. Ensure task-management migrations are already applied and the railway tables exist.
3. Provide an admin bearer token accepted by the existing auth layer.
4. Ensure the crawler integration is configured so VistaFlow can reach 12306.
5. Keep the 12306-side request parameters, request method, and response parsing contract unchanged.

## Scenario 1: Discover the three railway crawl task types

```bash
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  http://localhost:8000/task-types
```

Expected result: the catalog includes:

- `fetch-trains`
- `fetch-train-stops`
- `fetch-train-runs`

Each type also returns its parameter schema.

## Scenario 2: Create and run a train catalog crawl task

```bash
curl -X POST \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  http://localhost:8000/tasks \
  -d '{
    "name": "Train catalog G sync",
    "type": "fetch-trains",
    "description": "Sync G-prefix trains for one date",
    "enabled": true,
    "cron": null,
    "payload": {
      "date": "2026-04-05",
      "keyword": "G"
    }
  }'
```

Run it:

```bash
curl -X POST \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  http://localhost:8000/tasks/1/run
```

Expected result: a new task run is accepted immediately, later reaches `completed`, and shows how many train rows were written or updated.

## Scenario 3: Create and run a train stops crawl task

```bash
curl -X POST \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  http://localhost:8000/tasks \
  -d '{
    "name": "Train G1 stops sync",
    "type": "fetch-train-stops",
    "description": "Sync stop details for G1",
    "enabled": true,
    "cron": null,
    "payload": {
      "date": "2026-04-05",
      "train_code": "G1"
    }
  }'
```

Run it and then inspect the returned `run.id`:

```bash
curl -X POST \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  http://localhost:8000/tasks/2/run

curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  http://localhost:8000/task-runs/$RUN_ID/logs
```

Expected result: stop rows are written to `train_stops`, and logs show the crawl, normalization, and persistence outcome.

## Scenario 4: Create and run a per-date train run task

```bash
curl -X POST \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  http://localhost:8000/tasks \
  -d '{
    "name": "Train G1 run sync",
    "type": "fetch-train-runs",
    "description": "Sync whether G1 runs on one date",
    "enabled": true,
    "cron": null,
    "payload": {
      "date": "2026-04-05",
      "train_code": "G1"
    }
  }'
```

Run it:

```bash
curl -X POST \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  http://localhost:8000/tasks/3/run
```

Expected result: VistaFlow writes or updates the matching `train_runs` row for that train/date pair and exposes the imported-count summary in run history.

## Scenario 5: Verify invalid payloads are rejected early

```bash
curl -X POST \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  http://localhost:8000/tasks \
  -d '{
    "name": "Broken task",
    "type": "fetch-train-stops",
    "enabled": true,
    "payload": {
      "date": "bad-date",
      "train_code": ""
    }
  }'
```

Expected result: the API rejects the request before storing the task definition.
