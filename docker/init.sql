CREATE TABLE IF NOT EXISTS earthquakes (
    id              TEXT PRIMARY KEY,
    magnitude       REAL,
    place           TEXT,
    occurred_at     TIMESTAMP WITH TIME ZONE,
    longitude       DOUBLE PRECISION,
    latitude        DOUBLE PRECISION,
    depth_km        DOUBLE PRECISION,
    magnitude_type  TEXT,
    event_type      TEXT,
    title           TEXT,
    detail_url      TEXT,
    felt            INTEGER,
    tsunami         INTEGER,
    inserted_at     TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS weather_forecasts (
    id                  TEXT PRIMARY KEY,
    latitude            DOUBLE PRECISION,
    longitude           DOUBLE PRECISION,
    forecast_time       TIMESTAMP WITH TIME ZONE,
    temperature_f       REAL,
    relative_humidity   REAL,
    wind_speed_mph      REAL,
    fetched_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS oklahoma_wells (
    api              TEXT PRIMARY KEY,
    well_records_docs TEXT,
    well_name        TEXT,
    well_num         TEXT,
    operator         TEXT,
    well_status      TEXT,
    well_type        TEXT,
    symbol_class     TEXT,
    sh_lat           DOUBLE PRECISION,
    sh_lon           DOUBLE PRECISION,
    county           TEXT,
    section          TEXT,
    township         TEXT,
    range            TEXT,
    qtr4             TEXT,
    qtr3             TEXT,
    qtr2             TEXT,
    qtr1             TEXT,
    pm               TEXT,
    footage_ew       REAL,
    ew               TEXT,
    footage_ns       REAL,
    ns               TEXT,
    inserted_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
