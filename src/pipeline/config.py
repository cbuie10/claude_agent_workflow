"""Project configuration — reads from environment variables with local dev defaults."""

import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://pipeline_user:pipeline_pass@localhost:5432/pipeline_db",
)

PREFECT_API_URL = os.getenv(
    "PREFECT_API_URL",
    "http://localhost:4200/api",
)

EARTHQUAKE_API_URL = os.getenv(
    "EARTHQUAKE_API_URL",
    "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson",
)

MIN_MAGNITUDE = float(os.getenv("MIN_MAGNITUDE", "0.0"))

WEATHER_API_URL = os.getenv(
    "WEATHER_API_URL",
    "https://api.open-meteo.com/v1/forecast?latitude=40.7128&longitude=-74.006&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m&temperature_unit=fahrenheit&forecast_days=1",
)
