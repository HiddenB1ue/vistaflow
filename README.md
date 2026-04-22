# VistaFlow

VistaFlow 是一个铁路出行方案查询引擎，目标不是替代 12306 或携程去买票，而是解决一个更具体的问题：**在众多方案里，哪个才是真正适合你的？**

主流铁路 App 的方案列表通常很长，但排序逻辑不透明，偏好设置粗糙，换乘信息也只给一个时长数字。VistaFlow 的出发点是把方案决策的控制权还给用户：支持细粒度的出行偏好配置，所有换乘方案默认保证同站，排序规则优先减少换乘次数，没有任何商业排序干扰。

## 与主流平台的差异

| | 12306 / 携程 / 智行 | VistaFlow |
|---|---|---|
| 换乘方案 | 有，但换乘信息简略 | 有，且默认保证同站换乘 |
| 排序逻辑 | 不透明，可能含商业因素 | 换乘次数优先，再按耗时/出发时间 |
| 偏好配置 | 粗粒度（席别、直达） | 细粒度（时间窗口、换乘时长、车型、指定/排除车次、换乘站） |
| 商业干扰 | 存在（手续费、推荐逻辑） | 无，纯方案查询 |
| 数据来源 | 实时接口 | 自建本地时刻表，基于 12306 数据 |

## 核心能力

**偏好驱动的方案搜索**

搜索参数不只是"出发地 + 目的地 + 日期"，用户可以配置：

- 出发时间窗口（如只看 08:00–12:00 出发的车）
- 到达截止时间
- 最小/最大换乘等待时间
- 允许或排除特定车型（G/D/K/Z/T 等）
- 允许或排除特定车次
- 允许或排除特定换乘站
- 最多换乘次数（0–3 次）

这些偏好直接影响后端搜索逻辑，而不是在结果出来后再做客户端过滤。

**透明的排序规则**

支持三种排序维度：总耗时、出发时间、票价。后端排序（耗时/出发时间）的优先级固定且公开：换乘次数 → 主排序字段 → 总耗时 → 出发时间 → 到达时间，换乘少的方案天然排在前面。票价排序在前端基于参考票价完成，无票价数据的方案排在末尾。

**同站换乘保证**

所有包含换乘的方案，换乘均在同一车站内完成，不存在需要出站再进站的情况。

**自建数据管道**

通过后台任务系统定期从 12306 抓取站点、车次、经停数据，存入本地 PostgreSQL。搜索基于本地时刻表，响应速度快，不受 12306 接口限流影响。管理端提供任务调度、数据管理、系统配置的完整后台界面。

## 技术栈

**后端** (`apps/api`)
- Python 3.12 + FastAPI + asyncpg
- Redis（搜索会话缓存）
- PostgreSQL 16（时刻表与铁路基础数据）
- 自研 DFS 路线规划引擎（`app/planner`）
- 异步 12306 数据抓取客户端，含限速与退避策略

**用户端** (`apps/web`)
- React 19 + TypeScript + Vite
- TanStack Query + Zustand

**管理端** (`apps/admin`)
- React 19 + TypeScript + Vite
- 任务调度、数据管理、系统配置、日志查看

**共享包** (`packages/`)
- `@vistaflow/ui`：共享 UI 组件库
- `@vistaflow/design-tokens`：设计令牌
- `@vistaflow/types`：共享类型定义
- `@vistaflow/api-client`：共享 API 客户端
- `@vistaflow/utils`：共享工具函数

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

### 1. 安装依赖

```bash
pnpm install
```

### 2. 配置后端环境

```bash
cd apps/api
uv sync
cp .env.example .env.development
```

根据本地环境修改 `.env.development`，至少需要可用的 PostgreSQL 和 Redis 连接。

### 3. 启动 API

```bash
cd apps/api
uv run uvicorn app.main:app --reload --port 8000
```

- Swagger 文档：`http://localhost:8000/docs`
- 健康检查：`http://localhost:8000/healthz`

### 4. 启动任务 Worker

```bash
cd apps/api
uv run python -m app.tasks.worker
```

### 5. 启动前端

```bash
# 用户端
pnpm dev:web    # http://localhost:5173

# 管理端
pnpm dev:admin  # http://localhost:5174
```

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
