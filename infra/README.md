# VistaFlow 数据库基础设施

## 目录结构

```text
infra/sql/
├── schema.sql                 # 完整初始化脚本
├── migrations/                # 按表拆分的建表脚本
│   ├── 0001_stations.sql
│   ├── 0002_trains.sql
│   ├── 0003_train_stops.sql
│   ├── 0004_train_runs.sql
│   ├── 0005_task.sql
│   ├── 0006_credential.sql
│   ├── 0007_log.sql
│   ├── 0008_task_run.sql
│   ├── 0009_task_run_log.sql
│   └── 0010_system_setting.sql
└── seeds/                     # Docker 首次建库时导入的基础数据
    ├── seed_base_tables.sql
    ├── stations.csv
    ├── trains.csv
    └── train_stops.csv
```

## 当前约定

- 每个 SQL 文件只对应一张表
- 表间保留逻辑关联字段，不引入外键约束
- `schema.sql` 负责串联 migrations 与基础种子导入
- `infra/sql/seeds/*.csv` 可以为空文件，但必须保留表头

## 主要表

| 表名 | 说明 |
|---|---|
| `stations` | 车站主数据 |
| `trains` | 车次主数据 |
| `train_stops` | 车次经停明细 |
| `train_runs` | 车次按日运行事实 |
| `task` | 任务定义 |
| `task_run` | 任务执行记录 |
| `task_run_log` | 任务执行日志 |
| `credential` | 外部凭证 |
| `log` | 系统日志 |

## 初始化

```bash
psql -U postgres -c "CREATE DATABASE vistaflow;"
psql -U postgres -c "CREATE USER vistaflow WITH PASSWORD 'vistaflow';"
psql -U postgres -c "GRANT ALL ON DATABASE vistaflow TO vistaflow;"
psql -U postgres -d vistaflow -c "GRANT USAGE, CREATE ON SCHEMA public TO vistaflow;"
psql -U postgres -d postgres -c "ALTER DATABASE vistaflow OWNER TO vistaflow;"

psql -U vistaflow -d vistaflow -f infra/sql/schema.sql
```

## Docker 首次建库导入基础数据

- `docker-compose.yml` 和 `docker-compose.dev.yml` 会将 `infra/sql/seeds` 挂载到 Postgres 容器的 `/docker-entrypoint-initdb.d/seeds`
- Postgres 首次初始化数据库时，会在建表后执行 `seed_base_tables.sql`
- 该脚本会依次导入：
  - `stations.csv`
  - `trains.csv`
  - `train_stops.csv`

注意：

- 这些脚本只会在数据库数据目录为空、首次初始化时执行
- 如果已经存在旧的 `postgres_data` volume，需要先删除 volume 再重新 `docker compose up`

## 从现有数据库导出基础种子

如果你已经有一份完整的基础数据数据库，可以运行导出脚本生成种子 CSV：

```bash
cd apps/api
uv run python scripts/export_base_seeds.py --database-url "postgresql://vistaflow:vistaflow@localhost:5432/vistaflow"
```

默认输出目录为仓库下的 `infra/sql/seeds/`。
