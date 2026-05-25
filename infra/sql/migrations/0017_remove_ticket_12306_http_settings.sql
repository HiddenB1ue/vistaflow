BEGIN;

DELETE FROM system_setting
WHERE key IN (
    'ticket_12306_http_concurrency',
    'ticket_12306_http_enabled'
);

COMMIT;
