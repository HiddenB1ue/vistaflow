BEGIN;

CREATE TABLE IF NOT EXISTS train_stops (
    id BIGSERIAL PRIMARY KEY,
    train_no VARCHAR(32) NOT NULL,
    station_no INTEGER NOT NULL,
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
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_train_stops_train_station_no UNIQUE (train_no, station_no),
    CONSTRAINT ck_train_stops_station_no_pos CHECK (station_no > 0)
);

COMMENT ON TABLE train_stops IS '车次经停明细表';
COMMENT ON COLUMN train_stops.id IS '经停记录主键 ID';
COMMENT ON COLUMN train_stops.train_no IS '12306 车次唯一编号';
COMMENT ON COLUMN train_stops.station_no IS '站序，从 1 开始';
COMMENT ON COLUMN train_stops.station_name IS '经停车站名称';
COMMENT ON COLUMN train_stops.station_train_code IS '该站展示的公开车次号';
COMMENT ON COLUMN train_stops.arrive_time IS '到达时间，格式通常为 HH:MM';
COMMENT ON COLUMN train_stops.start_time IS '发车时间，格式通常为 HH:MM';
COMMENT ON COLUMN train_stops.running_time IS '本段运行时长';
COMMENT ON COLUMN train_stops.arrive_day_diff IS '到达相对始发日的天数偏移';
COMMENT ON COLUMN train_stops.arrive_day_str IS '到达日文字描述';
COMMENT ON COLUMN train_stops.is_start IS '是否始发站标记';
COMMENT ON COLUMN train_stops.start_station_name IS '始发站名称';
COMMENT ON COLUMN train_stops.end_station_name IS '终到站名称';
COMMENT ON COLUMN train_stops.train_class_name IS '列车等级名称';
COMMENT ON COLUMN train_stops.service_type IS '服务类型';
COMMENT ON COLUMN train_stops.wz_num IS '无座余票或补票标记';
COMMENT ON COLUMN train_stops.created_at IS '记录创建时间';
COMMENT ON COLUMN train_stops.updated_at IS '记录更新时间';

COMMIT;
