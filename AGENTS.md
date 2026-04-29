# AGENTS.md

Codex instructions for VistaFlow. This file adapts the existing `CLAUDE.md` intent
to the Codex rule file that is read from the repository root.

## Scope

VistaFlow is a rail journey search and administration system. The product goal is
to show more complete, fairer train route options rather than optimize for ticket
sales or commercial ranking. Keep changes aligned with journey search, sessioned
result filtering, railway data maintenance, admin operations, and shared UI.

## Rule Priority

1. `AGENTS.md` in the current directory tree, nearest file wins.
2. `CLAUDE.md` remains source context only; do not rely on it as Codex runtime
   instructions unless a user explicitly asks to update Claude Code behavior.
3. User instructions in the current conversation override this file.

## Applicable Rules

- Use `C:\Users\admin\.codex\rules\common\` when available.
- TODO: run `dayu-rules` later if stack-specific Dayu rule folders should be
  resolved for React, TypeScript, FastAPI, Python, Docker, or testing.

## Stack And Environment

- Monorepo package manager: `pnpm@10.33.0`.
- Frontend apps: React 19, TypeScript 5.9, Vite 8, Vitest, Tailwind CSS 4.
- Backend: Python 3.12, FastAPI, asyncpg, httpx, Redis, Playwright, uv.
- Data services: PostgreSQL 16 and Redis.
- Root env sample: `.env.example`; API env sample: `apps/api/.env.example`;
  frontend env samples: `apps/web/.env.example`, `apps/admin/.env.example`.
- Do not commit real `.env`, `.env.development`, `.env.local`, tokens, passwords,
  or generated admin credentials.

## Repository Structure

```text
apps/api/                  FastAPI service, background tasks, integrations, tests
apps/web/                  public journey search React app
apps/admin/                admin React app for auth, tasks, data, logs, config
packages/ui/               shared React components and UI exports
packages/utils/            shared formatting and React utility hooks
packages/types/            shared domain TypeScript types
packages/api-client/       shared Axios client helpers
packages/api-types/        generated OpenAPI TypeScript types
packages/design-tokens/    shared CSS tokens, themes, typography, fonts
infra/sql/                 PostgreSQL schema and seed data
docker/                    Docker build files for web image
deploy/                    deployment-related files
```

Dependency direction: apps may import workspace packages; shared packages must not
import app code. `packages/ui` may use `packages/utils` and design tokens, but it
must stay reusable by both `apps/web` and `apps/admin`.

## Domain Vocabulary

- Journey search session: cached route-search result used for pagination and
  filtering under `/api/v1/journey-search-sessions`.
- Route / segment / transfer: frontend route display entities in
  `apps/web/src/types/route.ts`.
- Task type: backend scheduled or manual maintenance unit such as `fetch-station`,
  `fetch-station-geo`, `fetch-trains`, `fetch-train-stops`, `fetch-train-runs`.
- Railway base data: stations, trains, train stops, and run data seeded from
  `infra/sql/seeds/` and maintained by admin/API tasks.
- Admin token: current admin authentication token stored through backend auth
  config and frontend `tokenStorage`.

## Required Workflow

1. Read the relevant README, package config, source files, and tests before
   editing. Do not infer architecture from filenames alone.
2. State assumptions when task scope is ambiguous. For risky areas below, stop and
   ask before widening behavior.
3. Make surgical changes. Every changed line should trace to the user's request.
4. Prefer the smallest implementation that passes the relevant tests. Avoid
   speculative abstractions, broad rewrites, and unrelated cleanup.
5. Validate with the narrowest command that covers the change, then broaden when a
   shared package, API contract, or cross-app behavior is touched.

Stop and ask when a change would alter route ranking semantics, generated API
types, admin authentication, task execution side effects, seed data shape, Docker
publishing, or secret handling.

## Architecture Rules

| Area | May depend on | Must not depend on |
| --- | --- | --- |
| `apps/web` | `@vistaflow/*`, browser APIs, API client | `apps/admin`, backend internals |
| `apps/admin` | `@vistaflow/*`, admin services, API client | `apps/web`, backend internals |
| `packages/ui` | React, peer deps, design tokens, utils | app-specific services/stores/routes |
| `packages/utils` | framework-light helpers and shared hooks | app-specific state or API clients |
| `apps/api/app/*/router.py` | schemas, dependencies, services | direct ad hoc DB logic when service/repository exists |
| `apps/api/app/tasks` | task registry, handlers, repositories | frontend code or UI assumptions |

Use existing API response envelopes such as `APIResponse.ok(...)` and
`APIResponse.fail(...)` instead of introducing parallel response shapes.

## Prohibited Patterns

- Do not "improve" adjacent code, formatting, or comments while solving an
  unrelated issue; mention unrelated cleanup separately.
- Do not add features, configurability, or fallback paths that were not requested.
- Do not bypass package boundaries by importing app files into shared packages.
- Do not edit generated API types by hand; use the existing generation workflow.
- Do not hardcode credentials, base URLs beyond existing env examples, or tokens.
- Do not silently change mock/real API switching behavior controlled by
  `VITE_USE_MOCK`.

## Security Rules

| Zone | Paths | Rule |
| --- | --- | --- |
| Admin auth | `apps/api/app/auth/`, `apps/admin/src/services/authService.ts`, `apps/admin/src/utils/tokenStorage.ts` | Treat token creation, persistence, and storage as security-sensitive. Remove debug credential logging when touching auth. |
| Admin APIs | `apps/api/app/admin_data/`, `apps/api/app/system/`, `apps/api/app/tasks/` | Preserve authorization requirements and validate payloads at boundaries. |
| External crawlers | `apps/api/app/integrations/`, `apps/api/tests/manual/`, `apps/api/tests/crawl/` | Keep live network behavior isolated from unit tests; do not make live calls in default tests. |
| Config/secrets | `.env*`, `apps/*/.env*`, `apps/api/app/config.py`, `apps/api/app/auth/config.py` | Use env variables and examples only; never commit real secret values. |

## Testing Rules

- For backend logic, add or update tests under `apps/api/tests/unit`,
  `apps/api/tests/integration`, or `apps/api/tests/contract` matching the changed
  layer.
- For frontend logic, colocate Vitest tests next to services, utils, stores, or
  shared components as the repo already does.
- Manual/live crawl tests under `apps/api/tests/manual` and `apps/api/tests/crawl`
  are not part of the default verification loop.
- For UI changes, run the relevant build/test command and use Playwright or a local
  browser smoke check when layout or interaction behavior changes.

## Validation Commands

Use exact commands from repo configuration:

```bash
pnpm build:web
pnpm lint:web
pnpm test:web
pnpm build:admin
pnpm test:admin
pnpm build:packages
pnpm test
cd apps/api && uv run ruff check .
cd apps/api && uv run mypy app tests
cd apps/api && uv run pytest --cov=app --cov-report=term-missing
```

Local development commands:

```bash
pnpm dev:web
pnpm dev:admin
cd apps/api && uv run uvicorn app.main:app --reload --port 8000
cd apps/api && uv run python -m app.tasks.worker
docker compose up -d
```

## Completion Checklist

For features and fixes:

- Relevant source and tests were read before editing.
- Scope stayed tied to the user request.
- Tests were added or updated for behavior changes where practical.
- Relevant validation command was run, or the reason it could not run is stated.
- Secrets and env files were not exposed.

For refactors:

- Behavior is covered by existing or added tests before changing structure.
- Public exports, API shapes, and package boundaries remain compatible.
- Dead code removal is limited to code made unused by the refactor unless the user
  explicitly requested broader cleanup.
