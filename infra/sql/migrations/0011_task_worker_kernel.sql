BEGIN;

ALTER TABLE task
    ADD COLUMN IF NOT EXISTS latest_result_level VARCHAR(16);

ALTER TABLE task
    DROP CONSTRAINT IF EXISTS ck_task_status;

ALTER TABLE task
    ADD CONSTRAINT ck_task_status
    CHECK (status IN ('idle', 'pending', 'running', 'completed', 'error', 'terminated'));

ALTER TABLE task
    DROP CONSTRAINT IF EXISTS ck_task_latest_run_status;

ALTER TABLE task
    ADD CONSTRAINT ck_task_latest_run_status
    CHECK (
        latest_run_status IS NULL
        OR latest_run_status IN ('pending', 'running', 'completed', 'error', 'terminated')
    );

ALTER TABLE task
    DROP CONSTRAINT IF EXISTS ck_task_latest_result_level;

ALTER TABLE task
    ADD CONSTRAINT ck_task_latest_result_level
    CHECK (latest_result_level IS NULL OR latest_result_level IN ('success', 'warning', 'error'));

ALTER TABLE task_run
    ADD COLUMN IF NOT EXISTS worker_id VARCHAR(128),
    ADD COLUMN IF NOT EXISTS heartbeat_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS cancel_requested BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS cancel_requested_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS result_level VARCHAR(16);

ALTER TABLE task_run
    DROP CONSTRAINT IF EXISTS ck_task_run_status;

ALTER TABLE task_run
    ADD CONSTRAINT ck_task_run_status
    CHECK (status IN ('pending', 'running', 'completed', 'error', 'terminated'));

ALTER TABLE task_run
    DROP CONSTRAINT IF EXISTS ck_task_run_result_level;

ALTER TABLE task_run
    ADD CONSTRAINT ck_task_run_result_level
    CHECK (result_level IS NULL OR result_level IN ('success', 'warning', 'error'));

CREATE INDEX IF NOT EXISTS idx_task_run_status_created_at
    ON task_run (status, created_at, id);

CREATE INDEX IF NOT EXISTS idx_task_run_running_heartbeat
    ON task_run (status, heartbeat_at, started_at);

COMMENT ON COLUMN task.latest_result_level IS '最近一次执行结果级别';
COMMENT ON COLUMN task_run.worker_id IS '当前处理该任务的 worker 标识';
COMMENT ON COLUMN task_run.heartbeat_at IS 'worker 最后一次心跳时间';
COMMENT ON COLUMN task_run.cancel_requested IS '是否已请求终止';
COMMENT ON COLUMN task_run.cancel_requested_at IS '请求终止时间';
COMMENT ON COLUMN task_run.result_level IS '执行结果级别（success/warning/error）';

COMMIT;
