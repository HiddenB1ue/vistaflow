BEGIN;

ALTER TABLE task
    DROP CONSTRAINT IF EXISTS ck_task_type;

ALTER TABLE task
    ADD CONSTRAINT ck_task_type CHECK (
        type IN (
            'fetch-station',
            'fetch-station-geo',
            'fetch-trains',
            'fetch-train-stops',
            'fetch-train-runs',
            'price'
        )
    );

COMMIT;
