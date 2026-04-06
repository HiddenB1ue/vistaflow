BEGIN;

CREATE TABLE IF NOT EXISTS train_runs (
    id BIGSERIAL PRIMARY KEY,
    train_id BIGINT NOT NULL,
    run_date DATE NOT NULL,
    status VARCHAR(16) NOT NULL DEFAULT 'running',
    source_updated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_train_runs_train_date UNIQUE (train_id, run_date),
    CONSTRAINT ck_train_runs_status CHECK (status IN ('running', 'suspended', 'cancelled', 'unknown'))
);

COMMENT ON TABLE train_runs IS '车次按日运行事实表';
COMMENT ON COLUMN train_runs.id IS '运行记录主键 ID';
COMMENT ON COLUMN train_runs.train_id IS '车次 ID，逻辑关联 trains.id';
COMMENT ON COLUMN train_runs.run_date IS '运行日期';
COMMENT ON COLUMN train_runs.status IS '运行状态';
COMMENT ON COLUMN train_runs.source_updated_at IS '来源数据最近更新时间';
COMMENT ON COLUMN train_runs.created_at IS '记录创建时间';
COMMENT ON COLUMN train_runs.updated_at IS '记录更新时间';

COMMIT;
