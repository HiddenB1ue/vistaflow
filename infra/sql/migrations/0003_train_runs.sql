BEGIN;

-- 记录每个车次在特定日期的开行状态。
-- 此表为可选数据：仅在 filter_running_only=true 时查询。
CREATE TABLE IF NOT EXISTS train_runs (
  id                BIGSERIAL PRIMARY KEY,
  train_id          BIGINT       NOT NULL REFERENCES trains(id) ON DELETE CASCADE,
  run_date          DATE         NOT NULL,
  status            VARCHAR(16)  NOT NULL DEFAULT 'running',
  source_updated_at TIMESTAMPTZ,
  created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  CONSTRAINT uq_train_runs_train_date UNIQUE (train_id, run_date),
  CONSTRAINT ck_train_runs_status
    CHECK (status IN ('running', 'suspended', 'cancelled', 'unknown'))
);

COMMENT ON TABLE  train_runs                    IS '车次按日开行实例';
COMMENT ON COLUMN train_runs.train_id           IS '关联车次 ID';
COMMENT ON COLUMN train_runs.run_date           IS '开行日期';
COMMENT ON COLUMN train_runs.status             IS '开行状态';
COMMENT ON COLUMN train_runs.source_updated_at  IS '来源数据更新时间';

CREATE INDEX IF NOT EXISTS idx_train_runs_date_status  ON train_runs (run_date, status);
CREATE INDEX IF NOT EXISTS idx_train_runs_train_date   ON train_runs (train_id, run_date);

COMMIT;
