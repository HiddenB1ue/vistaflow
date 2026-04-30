\encoding UTF8

-- VistaFlow 完整数据库初始化脚本
-- 作用等同于按顺序执行 migrations 目录下的建表脚本
-- 用于本地初始化或测试环境重建

\ir migrations/0001_stations.sql
\ir migrations/0002_trains.sql
\ir migrations/0003_train_stops.sql
\ir migrations/0004_train_runs.sql
\ir migrations/0005_task.sql
\ir migrations/0006_credential.sql
\ir migrations/0007_log.sql
\ir migrations/0008_task_run.sql
\ir migrations/0009_task_run_log.sql
\ir migrations/0010_system_setting.sql
\ir migrations/0011_task_cron_scheduler.sql
\ir migrations/0012_ticket_12306_enabled.sql
\ir migrations/0013_route_plan_cache.sql
\ir migrations/0014_route_plan_segment_fk.sql
\ir seeds/seed_base_tables.sql
