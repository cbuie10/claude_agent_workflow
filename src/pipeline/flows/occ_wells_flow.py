"""OCC Wells ETL flow — extracts from OCC, transforms, loads into PostgreSQL."""

from prefect import flow, get_run_logger

from pipeline.config import DATABASE_URL, OCC_WELLS_CSV_URL
from pipeline.db import check_connection
from pipeline.tasks.extract import extract_occ_wells_data
from pipeline.tasks.load import load_occ_wells_data
from pipeline.tasks.transform import transform_occ_wells_data


@flow(name="occ-wells-etl", log_prints=True)
def occ_wells_etl_flow(
    csv_url: str = OCC_WELLS_CSV_URL,
    connection_url: str = DATABASE_URL,
) -> int:
    """Extract OCC wells data from CSV, transform, and load into PostgreSQL."""
    logger = get_run_logger()

    logger.info("Checking database connection to %s", connection_url)
    check_connection(connection_url)
    logger.info("Database connection verified")

    logger.info("Extracting OCC wells data from %s", csv_url)
    raw_csv = extract_occ_wells_data(csv_url)

    logger.info("Transforming OCC wells CSV data")
    rows = transform_occ_wells_data(raw_csv)

    logger.info("Loading %d rows into PostgreSQL", len(rows))
    loaded_count = load_occ_wells_data(rows, connection_url)

    logger.info("Pipeline complete: %d rows loaded", loaded_count)
    return loaded_count


if __name__ == "__main__":
    occ_wells_etl_flow()
