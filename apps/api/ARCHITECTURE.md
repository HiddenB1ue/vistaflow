# VistaFlow 后端架构文档

> **文档版本** v2.0
> **架构风格** 按业务领域组织（Domain-Driven Structure）
> **参考规范** [zhanymkanov/fastapi-best-practices](https://github.com/zhanymkanov/fastapi-best-practices)、[Netflix/dispatch](https://github.com/Netflix/dispatch)

---

## 1. 架构哲学

**原则一：按领域组织，不按文件类型**
代码按业务领域（railway、journeys、tasks、system、auth）划分目录，每个领域自包含 router、schemas、service、repository、dependencies。新增功能 = 新增领域目录，不修改已有领域。

**原则二：IO 与业务逻辑分离**
Repository 只管 SQL，Service 只管编排，Planner 是零 IO 纯函数。任何一层的替换不影响其他层。

**原则三：可测试性优先**
Planner 零依赖可直接测试。外部集成通过抽象基类（ABC）定义，Service 依赖抽象而非具体实现，测试时可替换为 Mock。

---

## 2. 技术选型

| 类别 | 选型 | 版本 |
|------|------|------|
| 语言 | Python | 3.12 |
| Web 框架 | FastAPI | 0.115.x |
| 数据验证 | Pydantic | v2 |
| 数据库 | PostgreSQL | 16 |
| 数据库驱动 | asyncpg | 0.30.x |
| HTTP 客户端 | httpx | 0.27.x |
| 配置管理 | pydantic-settings | 2.x |
| 包管理 | uv | latest |
| 测试 | pytest + pytest-asyncio | latest |
| Lint | ruff | latest |

---

## 3. 目录结构

```
app/
├── main.py                     # FastAPI 应用入口
├── database.py                 # BaseRepository + asyncpg 连接池
├── models.py                   # 全局领域模型（dataclass）+ 类型别名
├── schemas.py                  # 全局 Schema（APIResponse[T]）
├── config.py                   # 全局配置（pydantic-settings）
├── exceptions.py               # 全局异常（BusinessError 等）
│
├── railway/                    # 铁路基础数据领域
│   ├── router.py               # /stations, /stations/suggest, /trains/{code}/stops
│   ├── schemas.py              # StationFullResponse, TrainStopsResponse 等
│   ├── service.py              # StationService, TrainService
│   ├── repository.py           # StationRepository, TrainRepository, TimetableRepository, SeatRepository
│   ├── dependencies.py         # get_db_pool, StationServiceDep, TrainServiceDep
│   └── exceptions.py           # TrainNotFound
│
├── journeys/                   # 行程规划领域
│   ├── router.py               # /journeys/search
│   ├── schemas.py              # JourneySearchRequest, JourneySearchResponse
│   ├── service.py              # JourneyService
│   ├── dependencies.py         # JourneyServiceDep
│   └── utils.py                # _route_id, _build_journey_result 等辅助函数
│
├── tasks/                      # 数据爬取任务领域
│   ├── router.py               # /admin-api/v1/tasks/*（需鉴权）
│   ├── schemas.py              # TaskResponse
│   ├── service.py              # TaskService
│   ├── repository.py           # TaskRepository（task 表）
│   ├── runner.py               # TaskRunner（worker 侧执行器）
│   ├── worker.py               # PostgreSQL 队列 worker 入口
│   ├── handlers.py             # 兼容测试的任务包装层
│   ├── dependencies.py         # TaskServiceDep
│   ├── constants.py            # TaskType, TaskStatus
│   └── exceptions.py           # TaskNotFound, TaskAlreadyRunning
│
├── system/                     # 系统运维领域
│   ├── router.py               # /healthz, /admin-api/v1/system/*
│   ├── schemas.py              # CredentialResponse, LogResponse, SparklineResponse 等
│   ├── credential_service.py   # CredentialService
│   ├── credential_repository.py # CredentialRepository（credential 表）
│   ├── log_service.py          # LogService
│   ├── log_repository.py       # LogRepository（log 表）
│   ├── overview_service.py     # OverviewService（占位）
│   ├── dependencies.py         # CredentialServiceDep, LogServiceDep
│   └── constants.py            # LogSeverity, CredentialHealth
│
├── auth/                       # 认证领域
│   ├── dependencies.py         # require_admin_auth（Bearer Token 校验）
│   ├── config.py               # AuthSettings（ADMIN_TOKEN）
│   └── exceptions.py           # AuthenticationError
│
├── planner/                    # 路线规划算法（纯函数，零 IO）
│   ├── index.py                # build_station_index()
│   ├── search.py               # search_journeys()（DFS）
│   ├── filters.py              # 过滤函数
│   ├── ranking.py              # 排序、分组、去重
│   └── time_utils.py           # 时间工具函数
│
└── integrations/               # 外部服务集成（抽象基类 + 真实实现）
    ├── ticket_12306/           # 12306 票价查询
    │   ├── client.py           # AbstractTicketClient + Live/Null 实现
    │   ├── parser.py           # 响应解析
    │   └── models.py           # TicketSegmentData
    ├── crawler/                # 12306 数据爬取
    │   └── client.py           # AbstractCrawlerClient + Live/Null 实现
    └── geo/                    # 高德地图 API
        └── client.py           # AbstractGeoClient + Amap/Null 实现
```

---

## 4. 领域内文件职责

每个领域目录包含以下文件（按需创建，不强制全部存在）：

| 文件 | 职责 |
|------|------|
| `router.py` | API 端点定义，只处理请求/响应，不含业务逻辑 |
| `schemas.py` | Pydantic I/O 模型，对外暴露的 API 契约 |
| `service.py` | 业务逻辑编排，调用 repository + planner + integrations |
| `repository.py` | 数据访问，只管 SQL，返回领域模型 |
| `dependencies.py` | FastAPI Depends 工厂函数 |
| `constants.py` | 领域常量和枚举 |
| `exceptions.py` | 领域异常，继承全局 BusinessError |
| `utils.py` | 非业务逻辑的辅助函数 |
| `config.py` | 领域级 BaseSettings（按需拆分） |

---

## 5. 跨领域 import 规则

使用显式模块名，禁止通配符 import：

```python
from app.railway import repository as railway_repository
from app.system import log_service
from app.auth import dependencies as auth_dependencies
```

---

## 6. 异步路由规则

- `async def` 路由：只使用非阻塞 IO（`await` 调用）
- `def` 路由（同步）：用于阻塞 IO（FastAPI 自动放入线程池）
- CPU 密集型任务：使用 `multiprocessing` 或 Celery
- 同步库在异步上下文中使用 `run_in_threadpool()`

---

## 7. 依赖注入规则

- 优先使用 `async` 依赖，避免线程池开销
- 依赖用于验证，不仅仅是 DI（如校验资源是否存在）
- 依赖可链式组合，FastAPI 自动缓存同一请求内的依赖结果
- 鉴权通过 `Depends(require_admin_auth)` 在路由级别注入，不通过 URL 前缀区分

---

## 8. 数据库规范

### 连接池

asyncpg Pool 在 `main.py` lifespan 中创建，挂载到 `app.state.db_pool`，所有 Repository 通过 `BaseRepository(pool)` 注入。

### SQL 规范

- 参数化查询，禁止字符串拼接
- 查询结果在 Repository 层转换为领域模型，不向上暴露 asyncpg Record
- 复杂查询写多行字符串

### 表命名规范

- `lower_case_snake` 格式
- 单数形式：`station`、`train`、`task`、`log`
- 相关表用领域前缀分组：`train_stop`、`train_run`
- 时间字段后缀：`_at`（datetime）、`_date`（date）

---

## 9. 配置规范

全局配置在 `config.py`，领域配置在各自 `config.py`（如 `auth/config.py`）。

```python
# 全局配置
from app.config import get_settings

# 领域配置
from app.auth.config import auth_settings
```

环境变量从 `.env.development` 读取，通过 pydantic-settings 类型安全解析。

---

## 10. 错误处理

### 异常分层

```
Integrations → ExternalServiceError
Repository   → 原生 asyncpg 异常
Service      → BusinessError / NotFoundError
Router       → 全局异常处理器自动映射 HTTP 状态码
```

### HTTP 状态码映射

| 异常 | 状态码 | 场景 |
|------|--------|------|
| Pydantic ValidationError | 422 | 参数校验失败 |
| NotFoundError | 404 | 资源不存在 |
| BusinessError | 400 | 业务规则违反 |
| ExternalServiceError | 503 | 外部服务不可用 |
| TaskAlreadyRunning | 409 | 任务重复触发 |
| 未预期异常 | 500 | 兜底 |

### 统一响应格式

```json
{ "success": true, "data": { ... }, "error": null }
{ "success": false, "data": null, "error": "错误描述" }
```

---

## 11. 外部集成规范

- 定义抽象基类（ABC），Service 层依赖抽象
- 每个集成提供 `Live*` 真实实现和 `Null*` 空实现
- 使用 `httpx.AsyncClient`，在 lifespan 中创建并复用
- 所有外部请求设置超时
- 响应错误在 integrations 层捕获，不向上透传 httpx 异常

---

## 12. 质量规范

### Lint & 类型检查

```bash
uv run ruff check app/
uv run ruff format app/
uv run mypy app/
```

### 测试

```bash
uv run pytest --cov=app --cov-report=term-missing
```

从第 0 天起使用 async 测试客户端（httpx.AsyncClient + ASGITransport）。

### 代码规模约束

| 维度 | 限制 |
|------|------|
| 单个函数 | ≤ 50 行 |
| 单个文件 | ≤ 400 行 |
| 嵌套深度 | ≤ 4 层 |
| 函数参数 | ≤ 8 个 |

---

## 13. 扩展约定

### 新增业务领域

1. 在 `app/` 下新建领域目录
2. 创建 `router.py`、`schemas.py`、`service.py` 等文件
3. 在 `main.py` 中注册路由
4. 不修改已有领域代码

### 新增任务类型

1. 在 `tasks/handlers.py` 中编写新的 handler 函数
2. 在 `tasks/types/__init__.py` 中注册新的 `TaskTypeDefinition`
3. runner.py 本身不需要修改

### 替换外部数据源

实现新的抽象基类子类，在 `main.py` lifespan 中替换注入即可。

---

## 14. 禁止事项

- ❌ 在 `planner/` 中执行任何 IO
- ❌ 在 `router.py` 中包含业务逻辑
- ❌ Service 层直接写 SQL 或 import asyncpg
- ❌ Repository 层互相调用
- ❌ 跨层级跳跃调用（router 直接调 repository）
- ❌ SQL 字符串拼接
- ❌ 在响应中暴露数据库错误堆栈
- ❌ 敏感配置（Cookie、Token、API Key）硬编码在代码中
- ❌ 使用 `Any` 类型（必须附注释说明原因）
- ❌ 修改传入的列表或字典参数
- ❌ 在 async 路由中执行阻塞 IO（如 `time.sleep`）
