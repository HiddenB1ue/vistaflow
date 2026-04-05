BEGIN;

CREATE TABLE IF NOT EXISTS task (
    id              BIGSERIAL PRIMARY KEY,
    name            VARCHAR(128) NOT NULL,
    type            VARCHAR(32)  NOT NULL,
    type_label      VARCHAR(64)  NOT NULL,
    status          VARCHAR(32)  NOT NULL DEFAULT 'pending',
    description     TEXT,
    cron            VARCHAR(64),
    metrics_label   VARCHAR(64)  NOT NULL DEFAULT '',
    metrics_value   VARCHAR(128) NOT NULL DEFAULT '',
    timing_label    VARCHAR(64)  NOT NULL DEFAULT '',
    timing_value    VARCHAR(128) NOT NULL DEFAULT '',
    error_message   TEXT,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_task_type   CHECK (type IN ('fetch-station','geocode','fetch-status','price','cleanup')),
    CONSTRAINT ck_task_status CHECK (status IN ('running','pending','completed','error','terminated'))
);

CREATE TABLE IF NOT EXISTS credential (
    id              BIGSERIAL PRIMARY KEY,
    name            VARCHAR(128) NOT NULL,
    description     TEXT,
    raw_key         TEXT         NOT NULL,
    quota_info      VARCHAR(256),
    expires_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS log (
    id                BIGSERIAL PRIMARY KEY,
    severity          VARCHAR(16)  NOT NULL,
    message           TEXT         NOT NULL,
    highlighted_terms TEXT[],
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_log_severity CHECK (severity IN ('SUCCESS','INFO','WARN','ERROR','SYSTEM'))
);

CREATE INDEX IF NOT EXISTS idx_log_created_at ON log (created_at DESC);

COMMIT;
