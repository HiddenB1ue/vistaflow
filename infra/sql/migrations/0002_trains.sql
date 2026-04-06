BEGIN;

CREATE TABLE IF NOT EXISTS trains (
    id BIGSERIAL PRIMARY KEY,
    train_no VARCHAR(32) NOT NULL,
    station_train_code VARCHAR(32),
    from_station_id BIGINT,
    from_station VARCHAR(64),
    to_station_id BIGINT,
    to_station VARCHAR(64),
    total_num INTEGER,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_trains_train_no UNIQUE (train_no),
    CONSTRAINT ck_trains_total_num_pos CHECK (total_num IS NULL OR total_num > 0)
);

COMMENT ON TABLE trains IS '车次主表';
COMMENT ON COLUMN trains.id IS '车次主键 ID';
COMMENT ON COLUMN trains.train_no IS '12306 车次唯一编号';
COMMENT ON COLUMN trains.station_train_code IS '公开车次号，例如 G1';
COMMENT ON COLUMN trains.from_station_id IS '始发站 ID，逻辑关联 stations.id';
COMMENT ON COLUMN trains.from_station IS '始发站名称';
COMMENT ON COLUMN trains.to_station_id IS '终到站 ID，逻辑关联 stations.id';
COMMENT ON COLUMN trains.to_station IS '终到站名称';
COMMENT ON COLUMN trains.total_num IS '经停站总数';
COMMENT ON COLUMN trains.is_active IS '是否为有效车次';
COMMENT ON COLUMN trains.created_at IS '记录创建时间';
COMMENT ON COLUMN trains.updated_at IS '记录更新时间';

COMMIT;
