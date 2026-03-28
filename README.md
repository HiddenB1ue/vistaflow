# VistaFlow

VistaFlow 是一个以铁路路线查询为核心的全栈项目，当前仓库已按多应用结构整理为：

```text
apps/
  api/      FastAPI 后端
  web/      用户端前端（Vite + React）
  admin/    管理端前端占位应用（第一阶段骨架）
packages/
  ui/
  design-tokens/
  utils/
  api-client/
infra/
```

## 快速开始

### 1. 初始化数据库

参考 [`infra/README.md`](./infra/README.md)。

### 2. 启动 API

```bash
cd apps/api
uv sync
cp .env.example .env.development
uv run uvicorn app.main:app --reload --port 8000
```

### 3. 启动用户端 Web

```bash
pnpm install
pnpm --filter @vistaflow/web dev
```

默认访问：<http://localhost:5173>

### 4. 启动管理端占位应用

```bash
pnpm --filter @vistaflow/admin dev
```

默认访问：<http://localhost:5174>

## 常用命令

```bash
pnpm --filter @vistaflow/web build
pnpm --filter @vistaflow/admin build
```

API 检查命令：

```bash
cd apps/api
uv run pytest
uv run ruff check .
uv run mypy app tests
```
