BEGIN;

ALTER TABLE IF EXISTS route_plan_segment
    DROP CONSTRAINT IF EXISTS route_plan_segment_plan_id_route_id_fkey;

ALTER TABLE IF EXISTS route_plan_segment
    DROP CONSTRAINT IF EXISTS route_plan_segment_plan_id_fkey;

ALTER TABLE IF EXISTS route_plan_segment
    ADD CONSTRAINT route_plan_segment_plan_id_fkey
    FOREIGN KEY (plan_id)
    REFERENCES route_plan_cache(plan_id)
    ON DELETE CASCADE;

COMMIT;
