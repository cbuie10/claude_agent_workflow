"""Extract tasks — fetch raw data from external sources."""

import httpx
from prefect import task


@task(name="extract_earthquake_data", retries=2, retry_delay_seconds=10)
def extract_earthquake_data(api_url: str) -> dict:
    """Fetch earthquake GeoJSON from the USGS API."""
    response = httpx.get(api_url, timeout=30.0)
    response.raise_for_status()
    return response.json()


@task(name="extract_weather_data", retries=2, retry_delay_seconds=10)
def extract_weather_data(api_url: str) -> dict:
    """Fetch weather forecast JSON from the Open-Meteo API."""
    response = httpx.get(api_url, timeout=30.0)
    response.raise_for_status()
    return response.json()
