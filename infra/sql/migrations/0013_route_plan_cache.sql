BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS route_plan_cache (
    plan_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_station TEXT NOT NULL,
    to_station TEXT NOT NULL,
    search_date DATE NOT NULL,
    transfer_count SMALLINT NOT NULL CHECK (transfer_count >= 0),
    status SMALLINT NOT NULL DEFAULT 0 CHECK (status IN (0, 1)),
    total_candidates INTEGER NOT NULL DEFAULT 0 CHECK (total_candidates >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (from_station, to_station, search_date, transfer_count)
);

CREATE INDEX IF NOT EXISTS idx_route_plan_cache_status
    ON route_plan_cache (status);

CREATE TABLE IF NOT EXISTS route_plan_candidate (
    plan_id UUID NOT NULL REFERENCES route_plan_cache(plan_id) ON DELETE CASCADE,
    route_id TEXT NOT NULL,
    transfer_count SMALLINT NOT NULL CHECK (transfer_count >= 0),
    is_direct BOOLEAN NOT NULL,
    origin_station TEXT NOT NULL,
    destination_station TEXT NOT NULL,
    origin_station_snapshot JSONB NOT NULL,
    destination_station_snapshot JSONB NOT NULL,
    path_points JSONB NOT NULL DEFAULT '[]'::jsonb,
    train_no_label TEXT NOT NULL,
    route_type TEXT NOT NULL,
    departure_date DATE NOT NULL,
    departure_time TEXT NOT NULL,
    arrival_date DATE NOT NULL,
    arrival_time TEXT NOT NULL,
    departure_abs_min INTEGER NOT NULL,
    arrival_abs_min INTEGER NOT NULL,
    duration_minutes INTEGER NOT NULL,
    train_codes TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    train_nos TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    train_types TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    transfer_stations TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    min_wait_minutes INTEGER,
    max_wait_minutes INTEGER,
    total_wait_minutes INTEGER NOT NULL DEFAULT 0,
    duration_rank INTEGER NOT NULL,
    departure_rank INTEGER NOT NULL,
    PRIMARY KEY (plan_id, route_id)
);

CREATE INDEX IF NOT EXISTS idx_route_plan_candidate_duration_rank
    ON route_plan_candidate (plan_id, duration_rank);

CREATE INDEX IF NOT EXISTS idx_route_plan_candidate_departure_rank
    ON route_plan_candidate (plan_id, departure_rank);

CREATE INDEX IF NOT EXISTS idx_route_plan_candidate_transfer_duration_rank
    ON route_plan_candidate (plan_id, transfer_count, duration_rank);

CREATE INDEX IF NOT EXISTS idx_route_plan_candidate_train_codes_gin
    ON route_plan_candidate USING GIN (train_codes);

CREATE INDEX IF NOT EXISTS idx_route_plan_candidate_train_nos_gin
    ON route_plan_candidate USING GIN (train_nos);

CREATE INDEX IF NOT EXISTS idx_route_plan_candidate_train_types_gin
    ON route_plan_candidate USING GIN (train_types);

CREATE INDEX IF NOT EXISTS idx_route_plan_candidate_transfer_stations_gin
    ON route_plan_candidate USING GIN (transfer_stations);

CREATE TABLE IF NOT EXISTS route_plan_segment (
    plan_id UUID NOT NULL REFERENCES route_plan_cache(plan_id) ON DELETE CASCADE,
    route_id TEXT NOT NULL,
    segment_index SMALLINT NOT NULL CHECK (segment_index >= 0),
    train_no TEXT NOT NULL,
    train_code TEXT NOT NULL,
    train_type TEXT NOT NULL,
    from_station TEXT NOT NULL,
    to_station TEXT NOT NULL,
    origin_station_snapshot JSONB NOT NULL,
    destination_station_snapshot JSONB NOT NULL,
    departure_date DATE NOT NULL,
    departure_time TEXT NOT NULL,
    arrival_date DATE NOT NULL,
    arrival_time TEXT NOT NULL,
    departure_abs_min INTEGER NOT NULL,
    arrival_abs_min INTEGER NOT NULL,
    duration_minutes INTEGER NOT NULL,
    stops_count INTEGER,
    PRIMARY KEY (plan_id, route_id, segment_index)
);

CREATE INDEX IF NOT EXISTS idx_route_plan_segment_plan_route
    ON route_plan_segment (plan_id, route_id);

COMMIT;
