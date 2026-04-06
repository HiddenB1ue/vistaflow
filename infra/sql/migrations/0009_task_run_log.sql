BEGIN;

CREATE TABLE IF NOT EXISTS task_run_log (
    id BIGSERIAL PRIMARY KEY,
    run_id BIGINT NOT NULL,
    severity VARCHAR(16) NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_task_run_log_severity CHECK (severity IN ('SUCCESS', 'INFO', 'WARN', 'ERROR', 'SYSTEM'))
);

COMMENT ON TABLE task_run_log IS '任务执行日志表';
COMMENT ON COLUMN task_run_log.id IS '任务执行日志主键 ID';
COMMENT ON COLUMN task_run_log.run_id IS '任务执行 ID，逻辑关联 task_run.id';
COMMENT ON COLUMN task_run_log.severity IS '日志级别';
COMMENT ON COLUMN task_run_log.message IS '日志内容';
COMMENT ON COLUMN task_run_log.created_at IS '记录创建时间';

COMMIT;
