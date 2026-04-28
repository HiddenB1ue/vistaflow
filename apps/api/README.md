# VistaFlow API

`apps/api` 是 VistaFlow 的后端服务，基于 FastAPI、asyncpg、httpx 和 Redis。

当前负责：

- 用户端出行查询与会话化结果分页
- 管理端认证、系统配置、日志与概览数据
- 任务定义、执行记录、日志追踪与 Worker 调度
- 铁路基础数据抓取与站点经纬度补全

## Directory Structure

```text
apps/api/
├── app/                          # 应用源码
│   ├── admin_data/               # 管理端数据查询与编辑接口
│   ├── auth/                     # 管理端认证
│   ├── integrations/             # 外部服务接入，例如 12306、地理编码
│   ├── journeys/                 # 出行搜索接口
│   ├── journey_search_sessions/  # 会话化搜索与分页筛选
│   ├── planner/                  # 路线规划与排序逻辑
│   ├── railway/                  # 铁路基础数据接口
│   ├── system/                   # 系统配置、概览、日志等后台能力
│   ├── tasks/                    # 任务定义、执行、注册与 worker 逻辑
│   ├── config.py                 # 全局配置
│   ├── database.py               # 数据库连接与依赖
│   └── main.py                   # FastAPI 入口
├── tests/                        # 测试目录
│   ├── unit/                     # 单元测试
│   ├── integration/              # 集成测试
│   ├── contract/                 # API 合同测试
│   ├── manual/                   # 手动联调测试
│   └── crawl/                    # 抓取脚本与实验性测试
├── .env.example                  # 环境变量示例
├── pyproject.toml                # Python 项目配置
└── Dockerfile                    # 镜像构建文件
```

## Requirements

- Python 3.12
- `uv`
- PostgreSQL 16
- Redis

## Environment Variables

复制 `apps/api/.env.example` 为 `apps/api/.env.development`：

```bash
cd apps/api
cp .env.example .env.development
```

常用配置项：

- `DATABASE_URL`：PostgreSQL 连接串
- `REDIS_URL`：Redis 连接串
- `CORS_ORIGINS`：允许的前端来源
- `APP_ENV`：运行环境，开发环境通常为 `development`
- `APP_VERSION`：应用版本号
- `ADMIN_USERNAME`：管理员用户名
- `ADMIN_PASSWORD`：管理员密码
- `ADMIN_TOKEN`：可选，预置管理端令牌
- `JOURNEY_SEARCH_TTL_SECONDS`：出行搜索会话缓存时间

## Local Development

安装依赖：

```bash
cd apps/api
uv sync
python -m playwright install chromium
```

启动 API：

```bash
uv run uvicorn app.main:app --reload --port 8000
```

开发环境常用地址：

- Swagger：`http://localhost:8000/docs`
- Health：`http://localhost:8000/healthz`

12306 real-time pricing requires a local Playwright Chromium install.
If Chromium is missing, the API can still start, but the first 12306 price query
will fail with an installation hint.

## Worker

任务执行使用独立 Worker 进程，开发时通常需要与 API 一起启动：

```bash
cd apps/api
uv run python -m app.tasks.worker
```

## Quality Checks

```bash
cd apps/api
uv run ruff check .
uv run mypy app tests
uv run pytest --cov=app --cov-report=term-missing
```

## API Groups

- `/api/v1/journeys`：出行搜索接口
- `/api/v1/journey-search-sessions`：会话化搜索与分页筛选
- `/api/v1/auth`：管理端登录认证
- `/api/v1/admin/tasks`：任务管理与执行
- `/api/v1/admin/data`：铁路基础数据管理
- `/api/v1/admin/system`：系统配置、概览、日志等后台接口
- `/healthz`：健康检查

## Implemented Task Types

- `fetch-station`
- `fetch-station-geo`
- `fetch-trains`
- `fetch-train-stops`
- `fetch-train-runs`

预留但尚未实现：

- `price`

## Notes

- 后端主要配置集中在 `app/config.py` 和 `app/auth/config.py`
- 文档以本 README 为主，目录说明和启动方式统一在这里维护
