"""Oklahoma Well Transfers ETL flow — extracts from OCC Excel, transforms, loads into PostgreSQL."""

from prefect import flow, get_run_logger

from pipeline.config import DATABASE_URL, WELL_TRANSFERS_XLSX_URL
from pipeline.db import check_connection
from pipeline.tasks.extract import extract_well_transfers
from pipeline.tasks.load import load_well_transfers
from pipeline.tasks.transform import transform_well_transfers


@flow(name="well-transfers-etl", log_prints=True)
def well_transfers_etl_flow(
    xlsx_url: str = WELL_TRANSFERS_XLSX_URL,
    connection_url: str = DATABASE_URL,
) -> int:
    """Extract Oklahoma well transfers data from OCC Excel, transform, and load into PostgreSQL."""
    logger = get_run_logger()

    logger.info("Checking database connection to %s", connection_url)
    check_connection(connection_url)
    logger.info("Database connection verified")

    logger.info("Extracting well transfers data from %s", xlsx_url)
    raw_rows = extract_well_transfers(xlsx_url)

    logger.info("Transforming %d Excel rows", len(raw_rows))
    rows = transform_well_transfers(raw_rows)

    logger.info("Loading %d rows into PostgreSQL", len(rows))
    loaded_count = load_well_transfers(rows, connection_url)

    logger.info("Pipeline complete: %d rows loaded", loaded_count)
    return loaded_count


if __name__ == "__main__":
    well_transfers_etl_flow()
