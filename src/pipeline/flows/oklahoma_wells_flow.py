"""Oklahoma Wells ETL flow — extracts from OCC CSV, transforms, loads into PostgreSQL."""

from prefect import flow, get_run_logger

from pipeline.config import DATABASE_URL, OCC_WELLS_CSV_URL
from pipeline.db import check_connection
from pipeline.tasks.extract import extract_occ_wells_data
from pipeline.tasks.load import load_occ_wells_data
from pipeline.tasks.transform import transform_occ_wells_data


@flow(name="oklahoma-wells-etl", log_prints=True)
def oklahoma_wells_etl_flow(
    csv_url: str = OCC_WELLS_CSV_URL,
    connection_url: str = DATABASE_URL,
) -> int:
    """Extract Oklahoma wells data from OCC CSV, transform, and load into PostgreSQL."""
    logger = get_run_logger()

    logger.info("Checking database connection to %s", connection_url)
    check_connection(connection_url)
    logger.info("Database connection verified")

    logger.info("Extracting Oklahoma wells data from %s", csv_url)
    csv_text = extract_occ_wells_data(csv_url)

    logger.info("Transforming CSV data (file size: %d bytes)", len(csv_text))
    rows = transform_occ_wells_data(csv_text)

    logger.info("Loading %d rows into PostgreSQL", len(rows))
    loaded_count = load_occ_wells_data(rows, connection_url)

    logger.info("Pipeline complete: %d rows loaded", loaded_count)
    return loaded_count


if __name__ == "__main__":
    oklahoma_wells_etl_flow()
