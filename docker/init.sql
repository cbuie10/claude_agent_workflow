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
