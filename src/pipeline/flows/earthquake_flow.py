"""Earthquake ETL flow — extracts from USGS, transforms, loads into PostgreSQL."""

from prefect import flow, get_run_logger

from pipeline.config import DATABASE_URL, EARTHQUAKE_API_URL, MIN_MAGNITUDE
from pipeline.db import check_connection
from pipeline.tasks.extract import extract_earthquake_data
from pipeline.tasks.load import load_earthquake_data
from pipeline.tasks.transform import transform_earthquake_data


@flow(name="earthquake-etl", log_prints=True)
def earthquake_etl_flow(
    api_url: str = EARTHQUAKE_API_URL,
    connection_url: str = DATABASE_URL,
    min_magnitude: float = MIN_MAGNITUDE,
) -> int:
    """Extract earthquake data from USGS, transform, and load into PostgreSQL."""
    logger = get_run_logger()

    logger.info("Checking database connection to %s", connection_url)
    check_connection(connection_url)
    logger.info("Database connection verified")

    logger.info("Extracting earthquake data from %s", api_url)
    raw_data = extract_earthquake_data(api_url)

    feature_count = len(raw_data.get("features", []))
    logger.info("Transforming %d features (min_magnitude=%.1f)", feature_count, min_magnitude)
    rows = transform_earthquake_data(raw_data, min_magnitude=min_magnitude)

    logger.info("Loading %d rows into PostgreSQL", len(rows))
    loaded_count = load_earthquake_data(rows, connection_url)

    logger.info("Pipeline complete: %d rows loaded", loaded_count)
    return loaded_count


if __name__ == "__main__":
    earthquake_etl_flow()
