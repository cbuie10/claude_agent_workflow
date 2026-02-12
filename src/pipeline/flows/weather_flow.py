"""Weather forecast ETL flow — extracts from Open-Meteo, transforms, loads into PostgreSQL."""

from prefect import flow, get_run_logger

from pipeline.config import DATABASE_URL, WEATHER_API_URL
from pipeline.db import check_connection
from pipeline.tasks.extract import extract_weather_data
from pipeline.tasks.load import load_weather_data
from pipeline.tasks.transform import transform_weather_data


@flow(name="weather-forecast-etl", log_prints=True)
def weather_forecast_etl_flow(
    api_url: str = WEATHER_API_URL,
    connection_url: str = DATABASE_URL,
) -> int:
    """Extract weather forecast data from Open-Meteo, transform, and load into PostgreSQL."""
    logger = get_run_logger()

    logger.info("Checking database connection to %s", connection_url)
    check_connection(connection_url)
    logger.info("Database connection verified")

    logger.info("Extracting weather forecast data from %s", api_url)
    raw_data = extract_weather_data(api_url)

    hourly_count = len(raw_data.get("hourly", {}).get("time", []))
    logger.info("Transforming %d hourly forecast records", hourly_count)
    rows = transform_weather_data(raw_data)

    logger.info("Loading %d rows into PostgreSQL", len(rows))
    loaded_count = load_weather_data(rows, connection_url)

    logger.info("Pipeline complete: %d rows loaded", loaded_count)
    return loaded_count


if __name__ == "__main__":
    weather_forecast_etl_flow()
