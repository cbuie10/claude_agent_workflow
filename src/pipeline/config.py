"""Project configuration — reads from environment variables with local dev defaults."""

import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://pipeline_user:pipeline_pass@localhost:5432/pipeline_db",
)

EARTHQUAKE_API_URL = os.getenv(
    "EARTHQUAKE_API_URL",
    "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson",
)

MIN_MAGNITUDE = float(os.getenv("MIN_MAGNITUDE", "0.0"))
