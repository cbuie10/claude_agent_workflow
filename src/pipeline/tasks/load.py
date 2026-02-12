"""Load tasks — insert data into PostgreSQL."""

from prefect import task
from sqlalchemy import create_engine, text


@task(name="load_earthquake_data")
def load_earthquake_data(rows: list[dict], connection_url: str) -> int:
    """Upsert earthquake rows into PostgreSQL.

    Uses ON CONFLICT to make the load idempotent — safe to re-run
    without creating duplicate rows.
    """
    if not rows:
        return 0

    upsert_sql = text("""
        INSERT INTO earthquakes (
            id, magnitude, place, occurred_at, longitude, latitude,
            depth_km, magnitude_type, event_type, title, detail_url,
            felt, tsunami
        ) VALUES (
            :id, :magnitude, :place, :occurred_at, :longitude, :latitude,
            :depth_km, :magnitude_type, :event_type, :title, :detail_url,
            :felt, :tsunami
        )
        ON CONFLICT (id) DO UPDATE SET
            magnitude = EXCLUDED.magnitude,
            place = EXCLUDED.place,
            felt = EXCLUDED.felt,
            tsunami = EXCLUDED.tsunami
    """)

    engine = create_engine(connection_url)
    with engine.connect() as conn:
        for row in rows:
            conn.execute(upsert_sql, row)
        conn.commit()

    return len(rows)


@task(name="load_weather_data")
def load_weather_data(rows: list[dict], connection_url: str) -> int:
    """Upsert weather forecast rows into PostgreSQL.

    Uses ON CONFLICT to make the load idempotent — safe to re-run
    without creating duplicate rows.
    """
    if not rows:
        return 0

    upsert_sql = text("""
        INSERT INTO weather_forecasts (
            id, latitude, longitude, forecast_time, temperature_f,
            relative_humidity, wind_speed_mph
        ) VALUES (
            :id, :latitude, :longitude, :forecast_time, :temperature_f,
            :relative_humidity, :wind_speed_mph
        )
        ON CONFLICT (id) DO UPDATE SET
            temperature_f = EXCLUDED.temperature_f,
            relative_humidity = EXCLUDED.relative_humidity,
            wind_speed_mph = EXCLUDED.wind_speed_mph
    """)

    engine = create_engine(connection_url)
    with engine.connect() as conn:
        for row in rows:
            conn.execute(upsert_sql, row)
        conn.commit()

    return len(rows)


@task(name="load_occ_wells_data")
def load_occ_wells_data(rows: list[dict], connection_url: str) -> int:
    """Upsert Oklahoma wells rows into PostgreSQL.

    Uses ON CONFLICT to make the load idempotent — safe to re-run
    without creating duplicate rows.
    """
    if not rows:
        return 0

    upsert_sql = text("""
        INSERT INTO oklahoma_wells (
            api, well_records_docs, well_name, well_num, operator,
            well_status, well_type, symbol_class, sh_lat, sh_lon,
            county, section, township, range, qtr4, qtr3, qtr2, qtr1,
            pm, footage_ew, ew, footage_ns, ns
        ) VALUES (
            :api, :well_records_docs, :well_name, :well_num, :operator,
            :well_status, :well_type, :symbol_class, :sh_lat, :sh_lon,
            :county, :section, :township, :range, :qtr4, :qtr3, :qtr2, :qtr1,
            :pm, :footage_ew, :ew, :footage_ns, :ns
        )
        ON CONFLICT (api) DO UPDATE SET
            well_records_docs = EXCLUDED.well_records_docs,
            well_name = EXCLUDED.well_name,
            well_num = EXCLUDED.well_num,
            operator = EXCLUDED.operator,
            well_status = EXCLUDED.well_status,
            well_type = EXCLUDED.well_type,
            symbol_class = EXCLUDED.symbol_class,
            sh_lat = EXCLUDED.sh_lat,
            sh_lon = EXCLUDED.sh_lon,
            county = EXCLUDED.county,
            section = EXCLUDED.section,
            township = EXCLUDED.township,
            range = EXCLUDED.range,
            qtr4 = EXCLUDED.qtr4,
            qtr3 = EXCLUDED.qtr3,
            qtr2 = EXCLUDED.qtr2,
            qtr1 = EXCLUDED.qtr1,
            pm = EXCLUDED.pm,
            footage_ew = EXCLUDED.footage_ew,
            ew = EXCLUDED.ew,
            footage_ns = EXCLUDED.footage_ns,
            ns = EXCLUDED.ns
    """)

    engine = create_engine(connection_url)
    with engine.connect() as conn:
        for row in rows:
            conn.execute(upsert_sql, row)
        conn.commit()

    return len(rows)
