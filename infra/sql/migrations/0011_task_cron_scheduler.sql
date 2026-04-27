BEGIN;

ALTER TABLE task
    ADD COLUMN IF NOT EXISTS next_run_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS last_scheduled_at TIMESTAMPTZ;

ALTER TABLE task
    ADD COLUMN IF NOT EXISTS schedule_mode VARCHAR(16) NOT NULL DEFAULT 'manual';

UPDATE task
SET schedule_mode = 'cron'
WHERE cron IS NOT NULL
  AND schedule_mode = 'manual';

ALTER TABLE task
    DROP CONSTRAINT IF EXISTS ck_task_schedule_mode;

ALTER TABLE task
    ADD CONSTRAINT ck_task_schedule_mode CHECK (
        schedule_mode IN ('manual', 'once', 'cron')
    );

ALTER TABLE task_run
    DROP CONSTRAINT IF EXISTS ck_task_run_trigger_mode;

ALTER TABLE task_run
    ADD CONSTRAINT ck_task_run_trigger_mode CHECK (
        trigger_mode IN ('manual', 'scheduled')
    );

CREATE INDEX IF NOT EXISTS idx_task_schedule_due
    ON task (next_run_at, id)
    WHERE enabled = TRUE AND schedule_mode IN ('once', 'cron') AND next_run_at IS NOT NULL;

COMMENT ON COLUMN task.cron IS '定时表达式，按 Asia/Shanghai 时区解释';
COMMENT ON COLUMN task.schedule_mode IS '任务调度模式: manual/once/cron';
COMMENT ON COLUMN task.next_run_at IS '下一次定时触发时间，UTC 存储';
COMMENT ON COLUMN task.last_scheduled_at IS '最近一次由调度器入队时间，UTC 存储';

COMMIT;
