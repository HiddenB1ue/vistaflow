BEGIN;

CREATE TABLE IF NOT EXISTS system_setting (
    id BIGSERIAL PRIMARY KEY,
    key VARCHAR(128) NOT NULL,
    value TEXT NOT NULL DEFAULT '',
    value_type VARCHAR(16) NOT NULL,
    category VARCHAR(32) NOT NULL,
    label VARCHAR(128) NOT NULL,
    description TEXT,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_system_setting_key UNIQUE (key),
    CONSTRAINT ck_system_setting_value_type CHECK (
        value_type IN ('string', 'int', 'float', 'bool', 'json')
    ),
    CONSTRAINT ck_system_setting_category CHECK (
        category IN ('amap', 'ticket_12306', 'task', 'system')
    )
);

COMMENT ON TABLE system_setting IS '系统配置表';
COMMENT ON COLUMN system_setting.id IS '配置主键 ID';
COMMENT ON COLUMN system_setting.key IS '配置唯一键';
COMMENT ON COLUMN system_setting.value IS '配置值（统一按文本存储）';
COMMENT ON COLUMN system_setting.value_type IS '配置值类型';
COMMENT ON COLUMN system_setting.category IS '配置分类';
COMMENT ON COLUMN system_setting.label IS '配置展示名称';
COMMENT ON COLUMN system_setting.description IS '配置说明';
COMMENT ON COLUMN system_setting.enabled IS '配置项是否生效';
COMMENT ON COLUMN system_setting.created_at IS '记录创建时间';
COMMENT ON COLUMN system_setting.updated_at IS '记录更新时间';

INSERT INTO system_setting (key, value, value_type, category, label, description, enabled)
VALUES
    ('amap_api_key', '', 'string', 'amap', '高德 API Key', '用于高德地理编码的 Web 服务 Key。留空表示未配置。', TRUE),
    ('amap_max_retries', '3', 'int', 'amap', '高德最大重试次数', '单次高德查询遇到限流时的最大重试次数。', TRUE),
    ('amap_retry_delay_seconds', '1.0', 'float', 'amap', '高德基础重试间隔', '高德限流后的基础重试间隔，单位秒。', TRUE),
    ('amap_min_interval_seconds', '0.35', 'float', 'amap', '高德最小请求间隔', '两次高德请求之间的最小间隔，单位秒。', TRUE),
    ('amap_rate_limit_cooldown_seconds', '3.0', 'float', 'amap', '高德限流冷却时间', '高德明确限流后的冷却等待时间，单位秒。', TRUE),
    ('ticket_12306_enabled', 'false', 'bool', 'system', '12306 票价查询', '控制是否启用 12306 实时票价与余票查询。', TRUE),
    ('geo_enrich_enabled', 'false', 'bool', 'task', '坐标补全开关', '是否允许自动执行站点坐标补全流程。', TRUE),
    ('auto_crawl_enabled', 'false', 'bool', 'task', '自动抓取开关', '是否允许按计划自动执行抓取任务。', TRUE),
    ('price_sync_enabled', 'false', 'bool', 'task', '票价同步开关', '是否启用票价与余票增强链路。', TRUE),
    ('preview_write_enabled', 'false', 'bool', 'task', '预览后落库开关', '是否要求补全类任务先预览再落库。', TRUE),
    ('maintenance_mode', 'false', 'bool', 'system', '维护模式', '是否开启系统维护模式。', TRUE)
ON CONFLICT (key) DO NOTHING;

COMMIT;
