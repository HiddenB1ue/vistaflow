BEGIN;

INSERT INTO system_setting (key, value, value_type, category, label, description, enabled)
VALUES
    (
        'ticket_12306_cache_ttl_seconds',
        '1800',
        'int',
        'ticket_12306',
        '12306 票价缓存 TTL（秒）',
        '12306 余票/票价在 Redis 中的缓存有效期，默认 1800 秒（30 分钟）。',
        TRUE
    ),
    (
        'ticket_12306_http_concurrency',
        '8',
        'int',
        'ticket_12306',
        '12306 HTTP 并发数',
        '通过 HTTP 直连 12306 时的最大并发请求数，默认 8。',
        TRUE
    ),
    (
        'ticket_12306_http_enabled',
        'true',
        'bool',
        'ticket_12306',
        '12306 HTTP 直连',
        '是否启用 HTTP 直连 12306 查询票价；关闭后将统一回落到 Playwright 浏览器路径。',
        TRUE
    )
ON CONFLICT (key) DO NOTHING;

COMMIT;
