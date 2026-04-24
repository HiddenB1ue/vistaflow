BEGIN;

CREATE TABLE IF NOT EXISTS task (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    type VARCHAR(32) NOT NULL,
    type_label VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'idle',
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    description TEXT,
    cron VARCHAR(64),
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    latest_run_id BIGINT,
    latest_run_status VARCHAR(32),
    latest_run_started_at TIMESTAMPTZ,
    latest_run_finished_at TIMESTAMPTZ,
    latest_error_message TEXT,
    latest_result_level VARCHAR(16),
    metrics_label VARCHAR(64) NOT NULL DEFAULT '最近结果',
    metrics_value VARCHAR(128) NOT NULL DEFAULT '',
    timing_label VARCHAR(64) NOT NULL DEFAULT '最近耗时',
    timing_value VARCHAR(128) NOT NULL DEFAULT '',
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_task_name UNIQUE (name),
    CONSTRAINT ck_task_type CHECK (
        type IN (
            'fetch-station',
            'fetch-station-geo',
            'fetch-trains',
            'fetch-train-stops',
            'fetch-train-runs',
            'price'
        )
    ),
    CONSTRAINT ck_task_status CHECK (
        status IN ('idle', 'pending', 'running', 'completed', 'error', 'terminated')
    ),
    CONSTRAINT ck_task_latest_run_status CHECK (
        latest_run_status IS NULL
        OR latest_run_status IN ('pending', 'running', 'completed', 'error', 'terminated')
    ),
    CONSTRAINT ck_task_latest_result_level CHECK (
        latest_result_level IS NULL OR latest_result_level IN ('success', 'warning', 'error')
    )
);

COMMENT ON TABLE task IS '任务定义表';
COMMENT ON COLUMN task.id IS '任务主键 ID';
COMMENT ON COLUMN task.name IS '任务名称';
COMMENT ON COLUMN task.type IS '任务类型';
COMMENT ON COLUMN task.type_label IS '任务类型中文名称';
COMMENT ON COLUMN task.status IS '任务当前状态';
COMMENT ON COLUMN task.enabled IS '任务是否启用';
COMMENT ON COLUMN task.description IS '任务说明';
COMMENT ON COLUMN task.cron IS '定时表达式，当前预留';
COMMENT ON COLUMN task.payload IS '任务参数负载';
COMMENT ON COLUMN task.latest_run_id IS '最近一次执行 ID，逻辑关联 task_run.id';
COMMENT ON COLUMN task.latest_run_status IS '最近一次执行状态';
COMMENT ON COLUMN task.latest_run_started_at IS '最近一次执行开始时间';
COMMENT ON COLUMN task.latest_run_finished_at IS '最近一次执行结束时间';
COMMENT ON COLUMN task.latest_error_message IS '最近一次执行错误信息';
COMMENT ON COLUMN task.latest_result_level IS '最近一次执行结果级别';
COMMENT ON COLUMN task.metrics_label IS '结果指标名称';
COMMENT ON COLUMN task.metrics_value IS '结果指标值';
COMMENT ON COLUMN task.timing_label IS '耗时指标名称';
COMMENT ON COLUMN task.timing_value IS '耗时指标值';
COMMENT ON COLUMN task.error_message IS '任务当前错误信息';
COMMENT ON COLUMN task.created_at IS '记录创建时间';
COMMENT ON COLUMN task.updated_at IS '记录更新时间';

COMMIT;
