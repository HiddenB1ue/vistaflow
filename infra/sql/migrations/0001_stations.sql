BEGIN;

CREATE TABLE IF NOT EXISTS stations (
  id                BIGSERIAL PRIMARY KEY,
  telecode          VARCHAR(10)  NOT NULL,
  name              VARCHAR(64)  NOT NULL,
  pinyin            VARCHAR(128),
  abbr              VARCHAR(32),
  area_code         VARCHAR(16),
  area_name         VARCHAR(64),
  country_code      VARCHAR(8)   NOT NULL DEFAULT 'cn',
  country_name      VARCHAR(64)  NOT NULL DEFAULT '中国',
  longitude         DOUBLE PRECISION,
  latitude          DOUBLE PRECISION,
  geo_source        VARCHAR(32),
  geo_updated_at    TIMESTAMPTZ,
  created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  CONSTRAINT uq_stations_telecode UNIQUE (telecode)
);

COMMENT ON TABLE  stations              IS '站点主数据';
COMMENT ON COLUMN stations.telecode     IS '站点电报码（如 BJP）';
COMMENT ON COLUMN stations.name         IS '站点中文名';
COMMENT ON COLUMN stations.pinyin       IS '站点全拼';
COMMENT ON COLUMN stations.abbr         IS '站点简拼';
COMMENT ON COLUMN stations.area_code    IS '12306 地区编码';
COMMENT ON COLUMN stations.area_name    IS '地区名称（城市/区域）';
COMMENT ON COLUMN stations.longitude    IS '经度（GCJ-02）';
COMMENT ON COLUMN stations.latitude     IS '纬度（GCJ-02）';
COMMENT ON COLUMN stations.geo_source   IS '坐标来源，如 amap_v3_geocode';

CREATE INDEX IF NOT EXISTS idx_stations_name   ON stations (name);
CREATE INDEX IF NOT EXISTS idx_stations_pinyin ON stations (pinyin);
CREATE INDEX IF NOT EXISTS idx_stations_abbr   ON stations (abbr);

COMMIT;
