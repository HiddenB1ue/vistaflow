\echo 'Seeding base railway tables from CSV files if present'

\set ON_ERROR_STOP on

BEGIN;

CREATE TEMP TABLE seed_stations (
    id BIGINT,
    telecode VARCHAR(10),
    name VARCHAR(64),
    pinyin VARCHAR(128),
    abbr VARCHAR(32),
    area_code VARCHAR(16),
    area_name VARCHAR(64),
    country_code VARCHAR(8),
    country_name VARCHAR(64),
    longitude DOUBLE PRECISION,
    latitude DOUBLE PRECISION,
    geo_source VARCHAR(32),
    geo_updated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
) ON COMMIT DROP;

\copy seed_stations FROM '/docker-entrypoint-initdb.d/seeds/stations.csv' WITH (FORMAT csv, HEADER true)

INSERT INTO stations (
    id,
    telecode,
    name,
    pinyin,
    abbr,
    area_code,
    area_name,
    country_code,
    country_name,
    longitude,
    latitude,
    geo_source,
    geo_updated_at,
    created_at,
    updated_at
)
SELECT
    id,
    NULLIF(BTRIM(telecode), ''),
    NULLIF(BTRIM(name), ''),
    NULLIF(BTRIM(pinyin), ''),
    NULLIF(BTRIM(abbr), ''),
    NULLIF(BTRIM(area_code), ''),
    NULLIF(BTRIM(area_name), ''),
    COALESCE(NULLIF(BTRIM(country_code), ''), 'cn'),
    COALESCE(NULLIF(BTRIM(country_name), ''), '中国'),
    longitude,
    latitude,
    NULLIF(BTRIM(geo_source), ''),
    geo_updated_at,
    COALESCE(created_at, NOW()),
    COALESCE(updated_at, NOW())
FROM seed_stations
WHERE id IS NOT NULL
  AND NULLIF(BTRIM(telecode), '') IS NOT NULL
  AND NULLIF(BTRIM(name), '') IS NOT NULL
ON CONFLICT (telecode) DO UPDATE
SET name = EXCLUDED.name,
    pinyin = EXCLUDED.pinyin,
    abbr = EXCLUDED.abbr,
    area_code = EXCLUDED.area_code,
    area_name = EXCLUDED.area_name,
    country_code = EXCLUDED.country_code,
    country_name = EXCLUDED.country_name,
    longitude = EXCLUDED.longitude,
    latitude = EXCLUDED.latitude,
    geo_source = EXCLUDED.geo_source,
    geo_updated_at = EXCLUDED.geo_updated_at,
    created_at = LEAST(stations.created_at, EXCLUDED.created_at),
    updated_at = GREATEST(stations.updated_at, EXCLUDED.updated_at);

CREATE TEMP TABLE seed_trains (
    train_no VARCHAR(32),
    station_train_code VARCHAR(32),
    from_station_id BIGINT,
    to_station_id BIGINT,
    from_station VARCHAR(64),
    to_station VARCHAR(64),
    total_num INTEGER,
    is_active BOOLEAN,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
) ON COMMIT DROP;

\copy seed_trains FROM '/docker-entrypoint-initdb.d/seeds/trains.csv' WITH (FORMAT csv, HEADER true)

INSERT INTO trains (
    train_no,
    station_train_code,
    from_station_id,
    from_station,
    to_station_id,
    to_station,
    total_num,
    is_active,
    created_at,
    updated_at
)
SELECT
    NULLIF(BTRIM(train_no), ''),
    NULLIF(BTRIM(station_train_code), ''),
    from_station_id,
    NULLIF(BTRIM(from_station), ''),
    to_station_id,
    NULLIF(BTRIM(to_station), ''),
    total_num,
    COALESCE(is_active, TRUE),
    COALESCE(created_at, NOW()),
    COALESCE(updated_at, NOW())
FROM seed_trains
WHERE NULLIF(BTRIM(train_no), '') IS NOT NULL
ON CONFLICT (train_no) DO UPDATE
SET station_train_code = EXCLUDED.station_train_code,
    from_station_id = EXCLUDED.from_station_id,
    from_station = EXCLUDED.from_station,
    to_station_id = EXCLUDED.to_station_id,
    to_station = EXCLUDED.to_station,
    total_num = EXCLUDED.total_num,
    is_active = EXCLUDED.is_active,
    created_at = LEAST(trains.created_at, EXCLUDED.created_at),
    updated_at = GREATEST(trains.updated_at, EXCLUDED.updated_at);

CREATE TEMP TABLE seed_train_stops (
    train_no VARCHAR(32),
    station_no INTEGER,
    station_name VARCHAR(64),
    station_train_code VARCHAR(32),
    arrive_time VARCHAR(8),
    start_time VARCHAR(8),
    running_time VARCHAR(8),
    arrive_day_diff SMALLINT,
    arrive_day_str VARCHAR(16),
    is_start VARCHAR(8),
    start_station_name VARCHAR(64),
    end_station_name VARCHAR(64),
    train_class_name VARCHAR(32),
    service_type VARCHAR(16),
    wz_num VARCHAR(16),
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
) ON COMMIT DROP;

\copy seed_train_stops FROM '/docker-entrypoint-initdb.d/seeds/train_stops.csv' WITH (FORMAT csv, HEADER true)

INSERT INTO train_stops (
    train_no,
    station_no,
    station_name,
    station_train_code,
    arrive_time,
    start_time,
    running_time,
    arrive_day_diff,
    arrive_day_str,
    is_start,
    start_station_name,
    end_station_name,
    train_class_name,
    service_type,
    wz_num,
    created_at,
    updated_at
)
SELECT
    NULLIF(BTRIM(train_no), ''),
    station_no,
    NULLIF(BTRIM(station_name), ''),
    NULLIF(BTRIM(station_train_code), ''),
    NULLIF(BTRIM(arrive_time), ''),
    NULLIF(BTRIM(start_time), ''),
    NULLIF(BTRIM(running_time), ''),
    arrive_day_diff,
    NULLIF(BTRIM(arrive_day_str), ''),
    NULLIF(BTRIM(is_start), ''),
    NULLIF(BTRIM(start_station_name), ''),
    NULLIF(BTRIM(end_station_name), ''),
    NULLIF(BTRIM(train_class_name), ''),
    NULLIF(BTRIM(service_type), ''),
    NULLIF(BTRIM(wz_num), ''),
    COALESCE(created_at, NOW()),
    COALESCE(updated_at, NOW())
FROM seed_train_stops
WHERE NULLIF(BTRIM(train_no), '') IS NOT NULL
  AND station_no IS NOT NULL
ON CONFLICT (train_no, station_no) DO UPDATE
SET station_name = EXCLUDED.station_name,
    station_train_code = EXCLUDED.station_train_code,
    arrive_time = EXCLUDED.arrive_time,
    start_time = EXCLUDED.start_time,
    running_time = EXCLUDED.running_time,
    arrive_day_diff = EXCLUDED.arrive_day_diff,
    arrive_day_str = EXCLUDED.arrive_day_str,
    is_start = EXCLUDED.is_start,
    start_station_name = EXCLUDED.start_station_name,
    end_station_name = EXCLUDED.end_station_name,
    train_class_name = EXCLUDED.train_class_name,
    service_type = EXCLUDED.service_type,
    wz_num = EXCLUDED.wz_num,
    created_at = LEAST(train_stops.created_at, EXCLUDED.created_at),
    updated_at = GREATEST(train_stops.updated_at, EXCLUDED.updated_at);

SELECT setval('stations_id_seq', COALESCE((SELECT MAX(id) FROM stations), 1), (SELECT EXISTS (SELECT 1 FROM stations)));
SELECT setval('trains_id_seq', COALESCE((SELECT MAX(id) FROM trains), 1), (SELECT EXISTS (SELECT 1 FROM trains)));
SELECT setval('train_stops_id_seq', COALESCE((SELECT MAX(id) FROM train_stops), 1), (SELECT EXISTS (SELECT 1 FROM train_stops)));

COMMIT;
