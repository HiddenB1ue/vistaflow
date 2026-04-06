BEGIN;

CREATE TABLE IF NOT EXISTS stations (
    id BIGSERIAL PRIMARY KEY,
    telecode VARCHAR(10) NOT NULL,
    name VARCHAR(64) NOT NULL,
    pinyin VARCHAR(128),
    abbr VARCHAR(32),
    area_code VARCHAR(16),
    area_name VARCHAR(64),
    country_code VARCHAR(8) NOT NULL DEFAULT 'cn',
    country_name VARCHAR(64) NOT NULL DEFAULT '中国',
    longitude DOUBLE PRECISION,
    latitude DOUBLE PRECISION,
    geo_source VARCHAR(32),
    geo_updated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_stations_telecode UNIQUE (telecode)
);

COMMENT ON TABLE stations IS '车站主数据表';
COMMENT ON COLUMN stations.id IS '车站主键 ID';
COMMENT ON COLUMN stations.telecode IS '车站电报码，例如 BJP';
COMMENT ON COLUMN stations.name IS '车站中文名称';
COMMENT ON COLUMN stations.pinyin IS '车站全拼';
COMMENT ON COLUMN stations.abbr IS '车站简拼';
COMMENT ON COLUMN stations.area_code IS '12306 区域编码';
COMMENT ON COLUMN stations.area_name IS '区域名称';
COMMENT ON COLUMN stations.country_code IS '国家编码';
COMMENT ON COLUMN stations.country_name IS '国家名称';
COMMENT ON COLUMN stations.longitude IS '车站经度，当前使用 GCJ-02';
COMMENT ON COLUMN stations.latitude IS '车站纬度，当前使用 GCJ-02';
COMMENT ON COLUMN stations.geo_source IS '坐标来源';
COMMENT ON COLUMN stations.geo_updated_at IS '坐标最近更新时间';
COMMENT ON COLUMN stations.created_at IS '记录创建时间';
COMMENT ON COLUMN stations.updated_at IS '记录更新时间';

COMMIT;
