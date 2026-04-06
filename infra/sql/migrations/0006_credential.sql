BEGIN;

CREATE TABLE IF NOT EXISTS credential (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    description TEXT,
    raw_key TEXT NOT NULL,
    quota_info VARCHAR(256),
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE credential IS '外部凭证表';
COMMENT ON COLUMN credential.id IS '凭证主键 ID';
COMMENT ON COLUMN credential.name IS '凭证名称';
COMMENT ON COLUMN credential.description IS '凭证说明';
COMMENT ON COLUMN credential.raw_key IS '原始密钥内容';
COMMENT ON COLUMN credential.quota_info IS '额度信息';
COMMENT ON COLUMN credential.expires_at IS '过期时间';
COMMENT ON COLUMN credential.created_at IS '记录创建时间';
COMMENT ON COLUMN credential.updated_at IS '记录更新时间';

COMMIT;
