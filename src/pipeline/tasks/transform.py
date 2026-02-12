"""Transform tasks — reshape and clean raw data."""

from datetime import datetime, timezone

from prefect import task


@task(name="transform_earthquake_data")
def transform_earthquake_data(raw_data: dict, min_magnitude: float = 0.0) -> list[dict]:
    """Flatten GeoJSON features into a list of row dictionaries.

    Each row maps directly to a column in the earthquakes table.
    Filters out events below min_magnitude.
    """
    rows = []

    for feature in raw_data.get("features", []):
        props = feature.get("properties", {})
        geometry = feature.get("geometry", {})
        coords = geometry.get("coordinates", [0, 0, 0])

        magnitude = props.get("mag")
        if magnitude is None or magnitude < min_magnitude:
            continue

        row = {
            "id": feature.get("id"),
            "magnitude": magnitude,
            "place": props.get("place"),
            "occurred_at": datetime.fromtimestamp(
                props.get("time", 0) / 1000, tz=timezone.utc
            ),
            "longitude": coords[0],
            "latitude": coords[1],
            "depth_km": coords[2],
            "magnitude_type": props.get("magType"),
            "event_type": props.get("type"),
            "title": props.get("title"),
            "detail_url": props.get("url"),
            "felt": props.get("felt"),
            "tsunami": props.get("tsunami"),
        }
        rows.append(row)

    return rows


@task(name="transform_weather_data")
def transform_weather_data(raw_data: dict) -> list[dict]:
    """Flatten hourly weather arrays into a list of row dictionaries.

    Each row maps directly to a column in the weather_forecasts table.
    Filters out any rows where temperature is null.
    """
    rows = []

    latitude = raw_data.get("latitude")
    longitude = raw_data.get("longitude")
    hourly = raw_data.get("hourly", {})

    times = hourly.get("time", [])
    temperatures = hourly.get("temperature_2m", [])
    humidities = hourly.get("relative_humidity_2m", [])
    wind_speeds = hourly.get("wind_speed_10m", [])

    for i, time_str in enumerate(times):
        temperature = temperatures[i] if i < len(temperatures) else None
        humidity = humidities[i] if i < len(humidities) else None
        wind_speed = wind_speeds[i] if i < len(wind_speeds) else None

        # Filter out rows where temperature is null
        if temperature is None:
            continue

        # Parse ISO8601 time string to datetime (assume UTC)
        forecast_time = datetime.fromisoformat(time_str.replace("Z", "+00:00"))

        # Generate composite ID from rounded coordinates and timestamp
        rounded_lat = round(latitude, 2)
        rounded_lon = round(longitude, 2)
        composite_id = f"{rounded_lat}_{rounded_lon}_{time_str}"

        row = {
            "id": composite_id,
            "latitude": latitude,
            "longitude": longitude,
            "forecast_time": forecast_time,
            "temperature_f": temperature,
            "relative_humidity": humidity,
            "wind_speed_mph": wind_speed,
        }
        rows.append(row)

    return rows
