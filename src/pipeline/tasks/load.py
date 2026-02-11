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
