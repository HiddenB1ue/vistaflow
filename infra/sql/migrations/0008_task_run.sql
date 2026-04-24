BEGIN;

CREATE TABLE IF NOT EXISTS task_run (
    id BIGSERIAL PRIMARY KEY,
    task_id BIGINT NOT NULL,
    task_name VARCHAR(128) NOT NULL,
    task_type VARCHAR(32) NOT NULL,
    trigger_mode VARCHAR(16) NOT NULL DEFAULT 'manual',
    status VARCHAR(32) NOT NULL DEFAULT 'pending',
    requested_by VARCHAR(64) NOT NULL DEFAULT 'admin',
    summary TEXT,
    metrics_value VARCHAR(128) NOT NULL DEFAULT '',
    error_message TEXT,
    termination_reason TEXT,
    progress_snapshot JSONB,
    worker_id VARCHAR(128),
    heartbeat_at TIMESTAMPTZ,
    cancel_requested BOOLEAN NOT NULL DEFAULT FALSE,
    cancel_requested_at TIMESTAMPTZ,
    result_level VARCHAR(16),
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_task_run_status CHECK (
        status IN ('pending', 'running', 'completed', 'error', 'terminated')
    ),
    CONSTRAINT ck_task_run_result_level CHECK (
        result_level IS NULL OR result_level IN ('success', 'warning', 'error')
    )
);

CREATE INDEX IF NOT EXISTS idx_task_run_status_created_at
    ON task_run (status, created_at, id);

CREATE INDEX IF NOT EXISTS idx_task_run_running_heartbeat
    ON task_run (status, heartbeat_at, started_at);

COMMENT ON TABLE task_run IS '任务执行记录表';
COMMENT ON COLUMN task_run.id IS '任务执行主键 ID';
COMMENT ON COLUMN task_run.task_id IS '任务 ID，逻辑关联 task.id';
COMMENT ON COLUMN task_run.task_name IS '执行时的任务名称快照';
COMMENT ON COLUMN task_run.task_type IS '执行时的任务类型快照';
COMMENT ON COLUMN task_run.trigger_mode IS '触发方式';
COMMENT ON COLUMN task_run.status IS '执行状态';
COMMENT ON COLUMN task_run.requested_by IS '触发人';
COMMENT ON COLUMN task_run.summary IS '执行摘要';
COMMENT ON COLUMN task_run.metrics_value IS '执行结果指标值';
COMMENT ON COLUMN task_run.error_message IS '错误信息';
COMMENT ON COLUMN task_run.termination_reason IS '终止原因';
COMMENT ON COLUMN task_run.progress_snapshot IS '任务执行进度快照（结构化 JSON）';
COMMENT ON COLUMN task_run.worker_id IS '当前处理该任务的 worker 标识';
COMMENT ON COLUMN task_run.heartbeat_at IS 'worker 最后一次心跳时间';
COMMENT ON COLUMN task_run.cancel_requested IS '是否已请求终止';
COMMENT ON COLUMN task_run.cancel_requested_at IS '请求终止时间';
COMMENT ON COLUMN task_run.result_level IS '执行结果级别（success/warning/error）';
COMMENT ON COLUMN task_run.started_at IS '执行开始时间';
COMMENT ON COLUMN task_run.finished_at IS '执行结束时间';
COMMENT ON COLUMN task_run.created_at IS '记录创建时间';
COMMENT ON COLUMN task_run.updated_at IS '记录更新时间';

COMMIT;
