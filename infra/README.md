# VistaFlow 数据库基础设施

## 目录结构

```text
infra/sql/
├── schema.sql          # 完整初始化脚本
└── migrations/         # 按表拆分的建表脚本
    ├── 0001_stations.sql
    ├── 0002_trains.sql
    ├── 0003_train_stops.sql
    ├── 0004_train_runs.sql
    ├── 0005_task.sql
    ├── 0006_credential.sql
    ├── 0007_log.sql
    ├── 0008_task_run.sql
    └── 0009_task_run_log.sql
```

## 当前约定

- 每个 SQL 文件只对应一张表
- 外键约束已移除，表间仅保留逻辑关联字段
- 索引暂不创建
- 字段定义直接写在 `CREATE TABLE` 中，不再通过额外 `ALTER TABLE` 补列
- 每张表和每个字段都要求有中文注释

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
# 创建数据库
psql -U postgres -c "CREATE DATABASE vistaflow;"
psql -U postgres -c "CREATE USER vistaflow WITH PASSWORD 'vistaflow';"
psql -U postgres -c "GRANT ALL ON DATABASE vistaflow TO vistaflow;"

psql -U postgres -d vistaflow -c "GRANT USAGE, CREATE ON SCHEMA public TO vistaflow;"
psql -U postgres -d postgres -c "ALTER DATABASE vistaflow OWNER TO vistaflow;"


# 执行 schema
psql -U vistaflow -d vistaflow -f infra/sql/schema.sql
```
