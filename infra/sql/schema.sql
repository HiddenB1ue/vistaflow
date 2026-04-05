-- VistaFlow 完整数据库 schema（一次性初始化脚本）
-- 等价于按序执行所有 migrations/
-- 用于本地快速初始化或测试环境重建

\ir migrations/0001_stations.sql
\ir migrations/0002_trains_and_stops.sql
\ir migrations/0003_train_runs.sql
\ir migrations/0004_task_credential_log.sql
