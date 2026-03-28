BEGIN;

CREATE TABLE IF NOT EXISTS trains (
  id                  BIGSERIAL PRIMARY KEY,
  train_no            VARCHAR(32)  NOT NULL,
  station_train_code  VARCHAR(32),
  from_station_id     BIGINT REFERENCES stations(id),
  from_station        VARCHAR(64),
  to_station_id       BIGINT REFERENCES stations(id),
  to_station          VARCHAR(64),
  total_num           INTEGER,
  is_active           BOOLEAN      NOT NULL DEFAULT TRUE,
  created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  CONSTRAINT uq_trains_train_no        UNIQUE (train_no),
  CONSTRAINT ck_trains_total_num_pos   CHECK (total_num IS NULL OR total_num > 0)
);

COMMENT ON TABLE  trains                    IS '车次主表';
COMMENT ON COLUMN trains.train_no           IS '车次号（如 550000G10101）';
COMMENT ON COLUMN trains.station_train_code IS '车次代码（如 G1）';
COMMENT ON COLUMN trains.from_station       IS '始发站';
COMMENT ON COLUMN trains.to_station         IS '终到站';
COMMENT ON COLUMN trains.total_num          IS '总经停站数';
COMMENT ON COLUMN trains.is_active          IS '是否有效';

CREATE INDEX IF NOT EXISTS idx_trains_from_station ON trains (from_station);
CREATE INDEX IF NOT EXISTS idx_trains_to_station   ON trains (to_station);

-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS train_stops (
  id                  BIGSERIAL PRIMARY KEY,
  train_no            VARCHAR(32)  NOT NULL REFERENCES trains(train_no) ON DELETE CASCADE,
  station_no          INTEGER      NOT NULL,
  station_name        VARCHAR(64),
  station_train_code  VARCHAR(32),
  arrive_time         VARCHAR(8),
  start_time          VARCHAR(8),
  running_time        VARCHAR(8),
  arrive_day_diff     SMALLINT,
  arrive_day_str      VARCHAR(16),
  is_start            VARCHAR(8),
  start_station_name  VARCHAR(64),
  end_station_name    VARCHAR(64),
  train_class_name    VARCHAR(32),
  service_type        VARCHAR(16),
  created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  CONSTRAINT uq_train_stops_train_station_no UNIQUE (train_no, station_no),
  CONSTRAINT ck_train_stops_station_no_pos   CHECK (station_no > 0)
);

COMMENT ON TABLE  train_stops                   IS '车次经停明细';
COMMENT ON COLUMN train_stops.train_no          IS '车次号';
COMMENT ON COLUMN train_stops.station_no        IS '站序（从 1 开始）';
COMMENT ON COLUMN train_stops.station_name      IS '站点名称';
COMMENT ON COLUMN train_stops.arrive_time       IS '到达时刻（HH:MM）';
COMMENT ON COLUMN train_stops.start_time        IS '出发时刻（HH:MM）';
COMMENT ON COLUMN train_stops.arrive_day_diff   IS '到达日偏移（0 当日，1 次日）';

CREATE INDEX IF NOT EXISTS idx_train_stops_train_no     ON train_stops (train_no);
CREATE INDEX IF NOT EXISTS idx_train_stops_station_name ON train_stops (station_name);

COMMIT;
