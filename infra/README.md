# VistaFlow 数据库基础设施

## 目录结构

```
infra/sql/
├── schema.sql          # 完整 schema（一次性初始化用）
└── migrations/         # 增量变更脚本
    ├── 0001_stations.sql
    ├── 0002_trains_and_stops.sql
    └── 0003_train_runs.sql
```

## 表说明

| 表 | 必须 | 说明 |
|---|------|------|
| `stations` | 是 | 站点主数据，含 GCJ-02 坐标和电报码 |
| `trains` | 是 | 车次主表 |
| `train_stops` | 是 | 车次经停明细（时刻表核心数据）|
| `train_runs` | 否 | 按日开行状态，仅 `filter_running_only=true` 时查询 |

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

## 数据来源

时刻表数据（`trains` + `train_stops`）来自 12306，需通过数据导入脚本填充（待实现）。
站点坐标（`stations.longitude/latitude`）来自高德地图 Geocoding API。
