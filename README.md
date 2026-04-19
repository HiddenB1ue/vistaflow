# VistaFlow

VistaFlow 是一个围绕铁路出行查询、任务调度与后台管理构建的 monorepo。仓库当前包含三个应用：

- `apps/api`：FastAPI 后端服务，提供出行查询、任务管理、系统配置和后台数据接口
- `apps/web`：用户端前端，负责搜索出行方案与展示结果列表
- `apps/admin`：管理端前端，负责任务、数据、配置、日志等后台操作

## Repository Structure

```text
.
├── apps/
│   ├── api/             # FastAPI 后端服务
│   ├── web/             # 用户端 Web 应用
│   └── admin/           # 管理端 Web 应用
├── packages/
│   ├── api-client/      # 共享 API 客户端
│   ├── design-tokens/   # 共享设计令牌
│   ├── types/           # 共享类型定义
│   ├── ui/              # 共享 UI 组件
│   └── utils/           # 共享工具函数
└── infra/               # SQL 与基础设施相关文件
```

## Requirements

- Node.js 20+
- pnpm 10+
- Python 3.12
- `uv`
- PostgreSQL 16
- Redis

## Quick Start

### 1. Install workspace dependencies

```bash
pnpm install
```

### 2. Prepare API environment

```bash
cd apps/api
uv sync
cp .env.example .env.development
```

根据本地环境修改 `.env.development`，至少需要可用的 PostgreSQL 和 Redis 连接。

### 3. Start the API

```bash
cd apps/api
uv run uvicorn app.main:app --reload --port 8000
```

可访问：

- Swagger 文档：`http://localhost:8000/docs`
- 健康检查：`http://localhost:8000/healthz`

### 4. Start the task worker

```bash
cd apps/api
uv run python -m app.tasks.worker
```

### 5. Start the frontend apps

在仓库根目录执行：

```bash
pnpm dev:web
pnpm dev:admin
```

默认地址：

- Web：`http://localhost:5173`
- Admin：`http://localhost:5174`

## Common Commands

仓库根目录：

```bash
pnpm dev:web
pnpm build:web
pnpm test:web

pnpm dev:admin
pnpm build:admin
pnpm test:admin

pnpm build:packages
pnpm test
```

API 目录：

```bash
cd apps/api
uv run ruff check .
uv run mypy app tests
uv run pytest --cov=app --cov-report=term-missing
```

## Documentation

- [API README](./apps/api/README.md)
- [Web README](./apps/web/README.md)
- [Admin README](./apps/admin/README.md)
- `infra/` 下的数据库与基础设施文件

## Notes

- 当前项目文档以各目录下的 `README.md` 为主
- `apps/web` 的用户端地图区域已经移除，结果页当前为路线列表视图
