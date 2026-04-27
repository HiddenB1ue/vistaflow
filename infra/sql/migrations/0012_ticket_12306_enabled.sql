BEGIN;

DELETE FROM system_setting
WHERE key = 'ticket_12306_cookie'
  AND EXISTS (
      SELECT 1
      FROM system_setting
      WHERE key = 'ticket_12306_enabled'
  );

UPDATE system_setting
SET
    key = 'ticket_12306_enabled',
    value = CASE
        WHEN enabled = TRUE AND BTRIM(value) <> '' THEN 'true'
        ELSE 'false'
    END,
    value_type = 'bool',
    category = 'system',
    label = '12306 票价查询',
    description = '控制是否启用 12306 实时票价与余票查询。',
    updated_at = NOW()
WHERE key = 'ticket_12306_cookie';

INSERT INTO system_setting (key, value, value_type, category, label, description, enabled)
VALUES (
    'ticket_12306_enabled',
    'false',
    'bool',
    'system',
    '12306 票价查询',
    '控制是否启用 12306 实时票价与余票查询。',
    TRUE
)
ON CONFLICT (key) DO NOTHING;

COMMIT;
