BEGIN;

ALTER TABLE task_run
ADD COLUMN IF NOT EXISTS progress_snapshot JSONB;

COMMENT ON COLUMN task_run.progress_snapshot IS '任务执行进度快照（结构化 JSON）';

COMMIT;
