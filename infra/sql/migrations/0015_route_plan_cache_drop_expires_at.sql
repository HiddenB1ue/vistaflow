BEGIN;

DROP INDEX IF EXISTS idx_route_plan_cache_status_expires;

ALTER TABLE route_plan_cache
    DROP COLUMN IF EXISTS expires_at;

CREATE INDEX IF NOT EXISTS idx_route_plan_cache_status
    ON route_plan_cache (status);

COMMIT;
