BEGIN;

CREATE TABLE IF NOT EXISTS log (
    id BIGSERIAL PRIMARY KEY,
    severity VARCHAR(16) NOT NULL,
    message TEXT NOT NULL,
    highlighted_terms TEXT[],
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_log_severity CHECK (severity IN ('SUCCESS', 'INFO', 'WARN', 'ERROR', 'SYSTEM'))
);

COMMENT ON TABLE log IS '系统日志表';
COMMENT ON COLUMN log.id IS '日志主键 ID';
COMMENT ON COLUMN log.severity IS '日志级别';
COMMENT ON COLUMN log.message IS '日志内容';
COMMENT ON COLUMN log.highlighted_terms IS '高亮关键词列表';
COMMENT ON COLUMN log.created_at IS '记录创建时间';

COMMIT;
