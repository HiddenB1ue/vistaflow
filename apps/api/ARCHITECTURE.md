# VistaFlow 后端架构契约与蓝图

> **文档版本** v1.0
> **状态** 生效中
> **适用范围** VistaFlow 后端工程全体成员
> **对应前端契约** vistaflow/frontend/Architecture .md

---

## 目录

1. [架构哲学](#1-架构哲学)
2. [技术选型决策表](#2-技术选型决策表)
3. [工程目录结构](#3-工程目录结构)
4. [分层架构与职责边界](#4-分层架构与职责边界)
5. [API 契约规范](#5-api-契约规范)
6. [数据库规范](#6-数据库规范)
7. [领域模型契约](#7-领域模型契约)
8. [规划算法契约](#8-规划算法契约)
9. [外部集成规范](#9-外部集成规范)
10. [配置与环境变量](#10-配置与环境变量)
11. [错误处理规范](#11-错误处理规范)
12. [工程规范与质量门禁](#12-工程规范与质量门禁)
13. [扩展性约定](#13-扩展性约定)
14. [禁止事项清单](#14-禁止事项清单)

---

## 1. 架构哲学

本项目的三条核心原则，所有技术决策必须服从这三条：

**原则一：IO 逻辑与业务逻辑必须分离**
数据库查询、HTTP 请求等 IO 操作绝不能渗透进业务逻辑层。Repository 层只管数据存取，Service 层只管业务编排，Planner 层是零 IO 的纯函数。任何一层的替换不得影响其他层。

**原则二：以类型契约驱动层间边界**
层与层之间只通过 `domain/` 中定义的类型传递数据。上层不感知下层的存储细节，下层不感知上层的 HTTP 细节。API 的输入/输出类型（`schemas/`）与内部领域类型（`domain/`）严格区分，不得混用。

**原则三：可测试性优先于实现便利**
任何不能被单元测试覆盖的设计都是错误的设计。Planner 算法层零依赖，可直接测试。Repository 层通过接口抽象，可被 mock。Service 层只依赖抽象接口，不依赖具体实现。

---

## 2. 技术选型决策表

| 类别 | 选型 | 版本 | 决策理由 | 替代品及放弃原因 |
|------|------|------|----------|------------------|
| 语言 | Python | 3.12 | 路线规划算法天然在 Python 生态；3.12 性能提升显著 | Go：重写算法成本高；Node.js：科学计算生态弱 |
| Web 框架 | FastAPI | 0.115.x | 原生异步、自动 OpenAPI 文档、Pydantic 深度集成 | Django REST：同步模型性能瓶颈；Flask：需大量手写 |
| 数据验证 | Pydantic | v2 | FastAPI 标配，v2 比 v1 快 5-10x，严格类型模式 | marshmallow：无类型推导；cerberus：性能差 |
| 数据库驱动 | asyncpg | 0.30.x | 原生异步 PostgreSQL，性能最优，内置连接池 | psycopg3（同步）：每请求建连，高并发下性能差 |
| HTTP 客户端 | httpx | 0.27.x | 原生 async/await，接口风格与 requests 一致 | aiohttp：API 繁琐；requests：同步阻塞 |
| 配置管理 | pydantic-settings | 2.x | 环境变量类型安全读取，与 Pydantic v2 无缝集成 | python-dotenv：无类型；dynaconf：过重 |
| 数据库 | PostgreSQL | 16 | 成熟稳定，JSON 支持好，全文检索能力强 | MySQL：JSON 支持弱；SQLite：不支持并发写 |
| 包管理 | uv | latest | 极速依赖解析，替代 pip + venv，锁文件确定性强 | poetry：较慢；pip：无锁文件 |
| 测试 | pytest + pytest-asyncio | latest | Python 测试标准，异步测试支持完善 | unittest：冗余；nose：已废弃 |

---

## 3. 工程目录结构

```
vistaflow/apps/api/
│
├── app/
│   ├── main.py                        # FastAPI 应用入口：注册路由、中间件、lifespan
│   ├── dependencies.py                # 全局依赖注入（db pool、service 工厂）
│   │
│   ├── config/
│   │   └── settings.py                # pydantic-settings 配置（从环境变量读取）
│   │
│   ├── api/                           # HTTP 接口层：只处理请求/响应，不含业务逻辑
│   │   ├── router.py                  # 聚合所有路由，挂载到 main.py
│   │   ├── health.py                  # GET /health
│   │   ├── journeys.py                # POST /api/journeys/search
│   │   ├── trains.py                  # GET /api/trains/{train_code}/stops
│   │   └── stations.py                # GET /api/stations
│   │
│   ├── schemas/                       # Pydantic I/O 模型（API 契约层，对外暴露）
│   │   ├── common.py                  # APIResponse[T] 通用响应包装
│   │   ├── journey.py                 # JourneySearchRequest / JourneySearchResponse
│   │   ├── train.py                   # TrainStopsResponse
│   │   └── station.py                 # StationGeoResponse
│   │
│   ├── services/                      # 业务逻辑层：编排 repository + planner + integrations
│   │   ├── journey_service.py         # 行程搜索编排
│   │   ├── train_service.py           # 车次经停查询
│   │   └── station_service.py         # 站点坐标查询
│   │
│   ├── repositories/                  # 数据访问层：只管 SQL，返回 domain 模型
│   │   ├── base.py                    # 基类（持有 asyncpg.Pool）
│   │   ├── timetable_repository.py    # 加载时刻表（train_stops 表）
│   │   ├── seat_repository.py         # 加载余票快照（availability_snapshots 表）
│   │   ├── station_repository.py      # 站点坐标 / 电报码查询
│   │   └── train_repository.py        # 经停站查询
│   │
│   ├── domain/                        # 领域模型：纯 Python dataclass，零 IO 依赖
│   │   ├── models.py                  # StopEvent / Segment / Journey / SeatInfo
│   │   └── types.py                   # 类型别名（StationIndex、SeatLookupKey 等）
│   │
│   ├── planner/                       # 路线规划算法：纯函数，零 IO，可独立单元测试
│   │   ├── index.py                   # build_station_departure_index()
│   │   ├── search.py                  # search_journeys() —— DFS 核心算法
│   │   ├── filters.py                 # 各类过滤函数（车型、时间窗口、换乘站等）
│   │   ├── ranking.py                 # 排序、分组、去重
│   │   └── time_utils.py              # parse_hhmm()、advance_past() 等时间工具
│   │
│   └── integrations/                  # 外部系统集成：有接口抽象，可 mock
│       └── ticket_12306/
│           ├── client.py              # httpx 异步客户端（抽象基类 + 真实实现）
│           ├── parser.py              # 解析 12306 响应报文
│           └── models.py              # TicketSegmentData / TicketQueryConfig
│
├── tests/
│   ├── unit/
│   │   ├── planner/                   # 算法单元测试（无需 DB，快速）
│   │   │   ├── test_search.py
│   │   │   ├── test_filters.py
│   │   │   └── test_ranking.py
│   │   └── services/                  # Service 层单元测试（mock repository）
│   ├── integration/                   # 集成测试（需要真实 DB）
│   │   └── test_repositories.py
│   └── conftest.py                    # pytest fixtures（db pool、mock clients）
│
├── pyproject.toml                     # 项目元数据 + 依赖（uv 管理）
├── uv.lock                            # 锁文件，确保环境一致性
├── .env.example                       # 环境变量模板
├── .env.development                   # 本地开发环境变量（不提交 git）
└── Dockerfile                         # 生产镜像
```

---

## 4. 分层架构与职责边界

### 4.1 层级划分

```
┌─────────────────────────────────────────┐
│              API 接口层                  │  ← 参数验证、HTTP 状态码映射、响应序列化
├─────────────────────────────────────────┤
│             Schemas 契约层               │  ← Pydantic I/O 模型，对外暴露的唯一类型
├─────────────────────────────────────────┤
│             Services 业务层              │  ← 编排逻辑，不直接碰 DB 和 HTTP
├───────────────────┬─────────────────────┤
│  Repositories 数据层  │  Integrations 集成层  │  ← 分别管理内部 DB 和外部 HTTP
├───────────────────┴─────────────────────┤
│              Planner 算法层              │  ← 纯函数，零 IO，可独立测试
├─────────────────────────────────────────┤
│              Domain 领域层               │  ← 贯穿所有层的类型契约
└─────────────────────────────────────────┘
```

### 4.2 各层职责边界（铁律）

**API 层（`api/*.py`）**
- ✅ 读取请求参数，调用对应 Service
- ✅ 将业务异常映射为 HTTP 状态码
- ✅ 将 Service 返回的 domain 模型转换为 Schema 响应
- ❌ 不可以包含任何业务判断逻辑
- ❌ 不可以直接调用 Repository 或 asyncpg
- ❌ 不可以直接访问外部 HTTP 服务

**Services 层（`services/*.py`）**
- ✅ 编排 Repository、Planner、Integrations 完成业务目标
- ✅ 将业务错误转换为自定义异常（供 API 层捕获）
- ✅ 决定是否启用票价增强（调用 12306 集成）
- ❌ 不可以直接写 SQL
- ❌ 不可以直接调用 asyncpg
- ❌ 不可以包含 HTTP 路由逻辑

**Repositories 层（`repositories/*.py`）**
- ✅ 执行所有 SQL 查询，使用 asyncpg.Pool
- ✅ 将数据库行转换为 domain 模型后返回
- ✅ 只处理本层的数据库异常（转换为领域异常）
- ❌ 不可以包含业务判断（如过滤逻辑）
- ❌ 不可以调用其他 Repository
- ❌ 不可以 import schemas/

**Planner 层（`planner/*.py`）**
- ✅ 接受 domain 模型作为输入，返回 domain 模型
- ✅ 纯函数，所有状态通过参数传入
- ✅ 可以使用标准库（collections、itertools 等）
- ❌ 不可以执行任何 IO（数据库、HTTP、文件）
- ❌ 不可以 import repositories/ 或 integrations/
- ❌ 不可以持有任何全局状态

**Integrations 层（`integrations/*.py`）**
- ✅ 封装外部 HTTP 服务调用
- ✅ 定义抽象基类（ABC），Service 层依赖抽象而非具体实现
- ✅ 将外部响应转换为 domain 模型
- ❌ 不可以包含业务逻辑
- ❌ 不可以直接操作数据库

---

## 5. API 契约规范

### 5.1 统一响应格式（`schemas/common.py`）

所有接口统一使用泛型响应包装：

```python
from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class APIResponse(BaseModel, Generic[T]):
    success: bool
    data: T | None = None
    error: str | None = None
```

成功响应示例：
```json
{ "success": true, "data": { ... }, "error": null }
```

失败响应示例：
```json
{ "success": false, "data": null, "error": "出发站不存在" }
```

### 5.2 接口清单

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/health` | 服务存活检查 |
| POST | `/api/journeys/search` | 搜索行程方案 |
| GET | `/api/trains/{train_code}/stops` | 查询车次经停站 |
| GET | `/api/stations` | 批量查询站点坐标 |

### 5.3 接口详细定义

**POST `/api/journeys/search`**

```python
# schemas/journey.py
class JourneySearchRequest(BaseModel):
    from_station: str                          # 出发站，如 "北京南"
    to_station: str                            # 到达站，如 "上海虹桥"
    date: date                                 # 出行日期
    transfer_count: int = 0                    # 最多换乘次数（0=仅直达）
    include_fewer_transfers: bool = True       # 是否包含换乘更少的方案
    allowed_train_types: list[str] = []        # 允许的车型前缀，如 ["G", "D"]
    excluded_train_types: list[str] = []       # 排除的车型前缀
    departure_time_start: time | None = None   # 出发时间窗口开始
    departure_time_end: time | None = None     # 出发时间窗口结束
    arrival_deadline: time | None = None       # 最晚到达时间
    min_transfer_minutes: int = 30             # 最短换乘时间（分钟）
    max_transfer_minutes: int | None = None    # 最长换乘时间（分钟）
    enable_ticket_enrich: bool = False         # 是否查询 12306 实时票价
    display_limit: int = 20                    # 返回方案数量上限

class JourneySegment(BaseModel):
    train_code: str           # 车次号，如 "G1"
    from_station: str
    to_station: str
    departure_time: str       # "HH:mm"
    arrival_time: str         # "HH:mm"
    duration_minutes: int
    seats: list[SeatSchema]

class JourneyResult(BaseModel):
    id: str
    is_direct: bool
    total_duration_minutes: int
    departure_time: str
    arrival_time: str
    min_price: float | None
    segments: list[JourneySegment]

class JourneySearchResponse(BaseModel):
    journeys: list[JourneyResult]
    total: int
    date: str
```

**GET `/api/trains/{train_code}/stops`**

```python
class StopItem(BaseModel):
    station_name: str
    arrival_time: str | None    # "HH:mm"，始发站为 null
    departure_time: str | None  # "HH:mm"，终到站为 null
    stop_number: int

class TrainStopsResponse(BaseModel):
    train_code: str
    stops: list[StopItem]
```

**GET `/api/stations?names=北京南&names=上海虹桥`**

```python
class StationGeoItem(BaseModel):
    name: str                  # 请求的站名
    longitude: float | None    # GCJ-02 坐标
    latitude: float | None
    found: bool

class StationGeoResponse(BaseModel):
    items: list[StationGeoItem]
```

### 5.4 CORS 配置

开发环境允许前端 `localhost:5173`，生产环境通过环境变量配置允许的 origins：

```python
# main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # 从环境变量读取
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

---

## 6. 数据库规范

### 6.1 连接池管理

asyncpg Pool 在应用启动时创建，整个生命周期复用，关闭时释放：

```python
# main.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db_pool = await asyncpg.create_pool(
        dsn=settings.database_url,
        min_size=5,
        max_size=20,
        command_timeout=30,
    )
    yield
    await app.state.db_pool.close()
```

### 6.2 Repository 基类

```python
# repositories/base.py
class BaseRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    # 子类通过 self._pool.acquire() 获取连接
```

### 6.3 SQL 规范

- 所有 SQL 使用参数化查询，禁止字符串拼接
- 复杂查询写多行字符串，不压缩成一行
- 查询结果立即转换为 domain 模型，不向上层暴露原始 asyncpg Record
- 单个查询超过 50 行 SQL，需在注释中说明用途

---

## 7. 领域模型契约

### 7.1 核心类型（`domain/models.py`）

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class StopEvent:
    """时刻表中的单个经停事件"""
    train_no: str
    stop_number: int
    station_name: str
    train_code: str           # 如 "G1"（station_train_code）
    arrive_abs_min: int | None  # 到站绝对分钟数（跨天累加）
    depart_abs_min: int | None  # 出站绝对分钟数

@dataclass(frozen=True)
class Segment:
    """行程中的一段（单趟列车）"""
    train_no: str
    train_code: str
    from_station: str
    to_station: str
    depart_abs_min: int
    arrive_abs_min: int

@dataclass(frozen=True)
class SeatInfo:
    """席别余票信息"""
    seat_type: str       # "zy"（一等座）/ "ze"（二等座）等
    status: str          # 显示用状态文字
    price: float | None
    available: bool
```

### 7.2 类型别名（`domain/types.py`）

```python
# 车次号 → 经停事件列表
Timetable = dict[str, list[StopEvent]]

# 站名 → [(车次号, 在该车次中的索引)]
StationIndex = dict[str, list[tuple[str, int]]]

# (train_no, from_station, to_station) → 席别列表
SeatLookupKey = tuple[str, str, str]
```

---

## 8. 规划算法契约

### 8.1 算法层设计原则

`planner/` 目录是整个后端最核心的部分，必须满足：

- **零 IO**：所有数据通过参数传入，不做任何数据库或 HTTP 调用
- **纯函数**：相同输入永远产生相同输出，无隐藏状态
- **可独立测试**：不依赖任何 FastAPI、asyncpg 或外部服务
- **高内聚**：算法相关工具函数（时间解析等）放在 `planner/time_utils.py`

### 8.2 核心函数签名

```python
# planner/search.py
def search_journeys(
    from_stations: set[str],
    to_stations: set[str],
    transfer_count: int,
    min_transfer_minutes: int,
    max_transfer_minutes: int | None,
    arrival_deadline_abs_min: int | None,
    departure_time_start_min: int | None,
    departure_time_end_min: int | None,
    departure_time_cross_day: bool,
    excluded_transfer_stations: set[str],
    allowed_transfer_stations: set[str],
    allowed_train_type_prefixes: tuple[str, ...],
    excluded_train_type_prefixes: set[str],
    excluded_train_tokens: set[str],
    allowed_train_tokens: set[str],
    timetable: Timetable,
    station_index: StationIndex,
) -> list[list[Segment]]: ...

# planner/index.py
def build_station_index(timetable: Timetable) -> StationIndex: ...

# planner/ranking.py
def rank_and_group(
    routes: list[list[Segment]],
    sort_by: Literal["duration", "price", "departure"],
    top_n_per_train_sequence: int,
    seat_data: dict[SeatLookupKey, list[SeatInfo]] | None,
) -> list[list[Segment]]: ...
```

---

## 9. 外部集成规范

### 9.1 抽象基类（必须定义）

Service 层只依赖抽象接口，不依赖具体实现，便于测试 mock：

```python
# integrations/ticket_12306/client.py
from abc import ABC, abstractmethod

class AbstractTicketClient(ABC):
    @abstractmethod
    async def fetch_tickets(
        self,
        legs: list[TicketLeg],
        date: str,
    ) -> dict[SeatLookupKey, TicketSegmentData]:
        ...

class Live12306TicketClient(AbstractTicketClient):
    """真实 12306 HTTP 客户端实现"""
    ...

class NullTicketClient(AbstractTicketClient):
    """空实现，enable_ticket_enrich=False 时使用"""
    async def fetch_tickets(self, legs, date):
        return {}
```

### 9.2 httpx 使用规范

- 使用 `httpx.AsyncClient` 并在应用生命周期内复用（不在每次请求中创建）
- 所有外部请求设置超时：`timeout=httpx.Timeout(20.0)`
- 响应错误在 `integrations/` 层捕获并转换为领域异常，不向上透传 httpx 异常

---

## 10. 配置与环境变量

### 10.1 配置定义（`config/settings.py`）

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # 数据库
    database_url: str = Field(..., alias="DATABASE_URL")

    # CORS
    cors_origins: list[str] = Field(default=["http://localhost:5173"])

    # 12306 集成（可选）
    ticket_12306_cookie: str = ""
    ticket_12306_endpoint: str = "queryG"

    # 应用
    app_env: str = "development"
    app_version: str = "1.0.0"

    model_config = SettingsConfigDict(env_file=".env.development", extra="ignore")


_settings: Settings | None = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
```

### 10.2 环境变量模板（`.env.example`）

```dotenv
# 数据库
DATABASE_URL=postgresql://vistaflow:password@localhost:5432/vistaflow

# CORS（生产环境填写前端域名）
CORS_ORIGINS=["http://localhost:5173"]

# 12306 票价增强（可选，留空则禁用票价查询）
TICKET_12306_COOKIE=
TICKET_12306_ENDPOINT=queryG

# 应用
APP_ENV=development
APP_VERSION=1.0.0
```

---

## 11. 错误处理规范

### 11.1 异常分层

```
Integrations 层抛出：ExternalServiceError
Repository 层抛出：  DatabaseError
Service 层转换为：   BusinessError（含 error_code 和用户友好 message）
API 层捕获并映射：   HTTP 状态码 + APIResponse(success=False, error=...)
```

### 11.2 HTTP 状态码映射

| 业务异常 | HTTP 状态码 | 场景 |
|----------|------------|------|
| 参数验证失败（Pydantic） | 422 | 缺少必填字段、类型错误 |
| BusinessError(NOT_FOUND) | 404 | 站点不存在 |
| BusinessError(INVALID_INPUT) | 400 | 出发站等于到达站 |
| BusinessError(EXTERNAL_ERROR) | 503 | 12306 服务不可用 |
| 未预期异常 | 500 | 兜底，记录完整堆栈 |

### 11.3 全局异常处理器

在 `main.py` 中注册，确保所有错误都返回统一的 `APIResponse` 格式：

```python
@app.exception_handler(BusinessError)
async def business_error_handler(request, exc: BusinessError):
    return JSONResponse(
        status_code=exc.http_status,
        content=APIResponse(success=False, error=exc.message).model_dump(),
    )
```

错误信息规范：
- 用户可见的 `error` 字段使用中文，描述用户能理解的问题
- 详细堆栈只写入服务端日志，不暴露给客户端

---

## 12. 工程规范与质量门禁

### 12.1 Python 配置（`pyproject.toml`）

```toml
[project]
name = "vistaflow-backend"
version = "1.0.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.30",
    "asyncpg>=0.30",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "httpx>=0.27",
]

[dependency-groups]
dev = [
    "pytest>=8",
    "pytest-asyncio>=0.23",
    "httpx",
    "ruff>=0.4",
    "mypy>=1.10",
]

[tool.ruff]
line-length = 100
select = ["E", "F", "I", "UP", "B", "SIM"]

[tool.mypy]
python_version = "3.12"
strict = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
```

### 12.2 质量门禁（CI 必须全部通过）

```
uv run ruff check .        # Lint，0 error
uv run mypy app/           # 类型检查，0 error
uv run pytest --cov=app --cov-report=term-missing  # 覆盖率 ≥ 80%
```

### 12.3 函数与文件规模约束

| 维度 | 限制 | 说明 |
|------|------|------|
| 单个函数行数 | ≤ 50 行 | 超出必须拆分 |
| 单个文件行数 | ≤ 400 行 | 超出按功能拆分模块 |
| 函数嵌套深度 | ≤ 4 层 | DFS 算法内部嵌套函数除外 |
| 函数参数数量 | ≤ 8 个 | 超出用 dataclass 封装 |

### 12.4 代码风格规范

- 所有公开函数必须有类型注解（mypy strict 强制）
- 禁止使用 `Any` 类型（必须附注释说明原因且经过 review）
- 不可变数据优先使用 `@dataclass(frozen=True)`，禁止在函数内修改传入的列表/字典
- 常量定义在模块顶部，使用全大写命名，禁止 hardcode 魔法数字

---

## 13. 扩展性约定

### 13.1 新增 API 接口

1. 在 `schemas/` 新建对应 Pydantic 模型文件
2. 在 `api/` 新建路由文件
3. 在 `api/router.py` 注册新路由
4. 在 `services/` 新建对应 Service（**不修改现有 Service**）
5. 如需新增数据表访问，在 `repositories/` 新建 Repository

### 13.2 替换数据库

替换 PostgreSQL 为其他存储时，影响范围仅限：
- `repositories/` 目录（重写 SQL 实现）
- `config/settings.py`（调整连接配置）
- `main.py` lifespan（调整连接池创建方式）
- Service 层、Planner 层、API 层**无需改动**

### 13.3 替换 12306 数据源

实现新的 `AbstractTicketClient` 子类，在 `dependencies.py` 中替换注入即可，Service 层代码**无需改动**。

### 13.4 新增算法能力

在 `planner/` 目录新增纯函数文件，在 `services/journey_service.py` 中调用。**不修改现有 planner 函数**，只新增。

---

## 14. 禁止事项清单

以下行为在任何情况下不得出现，Code Review 发现直接打回：

**IO 相关**
- ❌ 在 `planner/` 目录中执行任何数据库查询或 HTTP 请求
- ❌ 在 `api/` 层直接调用 `asyncpg` 或 `httpx`
- ❌ 在 `repositories/` 层调用外部 HTTP 服务
- ❌ 在请求处理中创建新的 `asyncpg` 连接（必须使用 Pool）

**类型相关**
- ❌ 使用 `Any` 类型（必须附注释说明原因且经过 review）
- ❌ 将 asyncpg `Record` 对象直接返回给 Service 层
- ❌ 将 `schemas/` 中的 Pydantic 模型传入 `planner/` 或 `repositories/` 层
- ❌ API 响应中直接返回 domain 模型（必须经过 Schema 转换）

**架构相关**
- ❌ Service 层直接 import `asyncpg` 或执行 SQL
- ❌ Repository 层互相调用（A repo 调用 B repo）
- ❌ Planner 层 import 任何 `repositories/`、`services/`、`integrations/` 模块
- ❌ 跨层级跳跃调用（如 API 层直接调用 Repository）

**安全相关**
- ❌ SQL 字符串拼接（必须使用参数化查询）
- ❌ 在响应中暴露数据库错误堆栈
- ❌ 将 12306 Cookie 等敏感配置 hardcode 在代码中
- ❌ 日志中打印完整的数据库连接串

**质量相关**
- ❌ 函数超过 50 行不拆分
- ❌ 跳过类型注解（mypy strict 会报错）
- ❌ 修改传入的列表或字典参数（immutable 原则）

---

*本文档适用于 VistaFlow 后端项目全生命周期。文档变更须经架构评审，变更记录追加至本文档末尾。*
