"""Transform tasks — reshape and clean raw data."""

import csv
import io
from datetime import date, datetime, timezone

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


@task(name="transform_occ_wells_data")
def transform_occ_wells_data(csv_text: str) -> list[dict]:
    """Parse CSV text into a list of row dictionaries.

    Each row maps directly to a column in the oklahoma_wells table.
    Skips rows where API is empty or None.
    """
    rows = []
    reader = csv.DictReader(io.StringIO(csv_text))

    for csv_row in reader:
        # Skip rows where API is empty or None
        api = csv_row.get("API", "").strip()
        if not api:
            continue

        # Helper to convert to float or None
        def to_float(value: str) -> float | None:
            if not value or not value.strip():
                return None
            try:
                return float(value.strip())
            except ValueError:
                return None

        # Helper to strip text or return None
        def to_text(value: str) -> str | None:
            if not value:
                return None
            stripped = value.strip()
            return stripped if stripped else None

        row = {
            "api": api,
            "well_records_docs": to_text(csv_row.get("WELL_RECORDS_DOCS")),
            "well_name": to_text(csv_row.get("WELL_NAME")),
            "well_num": to_text(csv_row.get("WELL_NUM")),
            "operator": to_text(csv_row.get("OPERATOR")),
            "well_status": to_text(csv_row.get("WELLSTATUS")),
            "well_type": to_text(csv_row.get("WELLTYPE")),
            "symbol_class": to_text(csv_row.get("SYMBOL_CLASS")),
            "sh_lat": to_float(csv_row.get("SH_LAT")),
            "sh_lon": to_float(csv_row.get("SH_LON")),
            "county": to_text(csv_row.get("COUNTY")),
            "section": to_text(csv_row.get("SECTION")),
            "township": to_text(csv_row.get("TOWNSHIP")),
            "range": to_text(csv_row.get("RANGE")),
            "qtr4": to_text(csv_row.get("QTR4")),
            "qtr3": to_text(csv_row.get("QTR3")),
            "qtr2": to_text(csv_row.get("QTR2")),
            "qtr1": to_text(csv_row.get("QTR1")),
            "pm": to_text(csv_row.get("PM")),
            "footage_ew": to_float(csv_row.get("FOOTAGE_EW")),
            "ew": to_text(csv_row.get("EW")),
            "footage_ns": to_float(csv_row.get("FOOTAGE_NS")),
            "ns": to_text(csv_row.get("NS")),
        }
        rows.append(row)

    return rows


@task(name="transform_well_transfers_data")
def transform_well_transfers_data(raw_rows: list[tuple]) -> list[dict]:
    """Transform well transfer Excel rows into database row dictionaries.

    Each row maps directly to a column in the well_transfers table.
    Skips rows where API Number is empty or None.
    """
    rows = []

    # Helper functions
    def to_float(value) -> float | None:
        """Convert value to float or None."""
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def to_int(value) -> int | None:
        """Convert value to int or None."""
        if value is None or value == "":
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    def to_text(value) -> str | None:
        """Convert value to stripped text or None."""
        if value is None or value == "":
            return None
        text = str(value).strip()
        return text if text else None

    def to_date(value) -> date | None:
        """Convert datetime or date value to date or None."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        return None

    for raw_row in raw_rows:
        # Excel columns in order (32 total):
        # EventDate, API Number, WellName, WellNum, Type, Status, PUN 16ez, PUN 02A,
        # Location Type, Surf_Long_X, Surf_Lat_Y, County, Section, Township, Range,
        # PM, Q1, Q2, Q3, Q4, FootageNS, NS, FootageEW, EW, FromOperatorNumber,
        # FromOperatorName, FromOperatorAddressBlock, FromOperatorPhone, ToOperatorName,
        # ToOperatorNumber, ToOperatorAddressBlock, ToOperatorPhone

        # Skip rows where API Number is empty or None
        api_number = to_text(raw_row[1]) if len(raw_row) > 1 else None
        if not api_number:
            continue

        row = {
            "event_date": to_date(raw_row[0]) if len(raw_row) > 0 else None,
            "api_number": api_number,
            "well_name": to_text(raw_row[2]) if len(raw_row) > 2 else None,
            "well_num": to_text(raw_row[3]) if len(raw_row) > 3 else None,
            "well_type": to_text(raw_row[4]) if len(raw_row) > 4 else None,
            "well_status": to_text(raw_row[5]) if len(raw_row) > 5 else None,
            "pun_16ez": to_text(raw_row[6]) if len(raw_row) > 6 else None,
            "pun_02a": to_text(raw_row[7]) if len(raw_row) > 7 else None,
            "location_type": to_text(raw_row[8]) if len(raw_row) > 8 else None,
            "surf_long_x": to_float(raw_row[9]) if len(raw_row) > 9 else None,
            "surf_lat_y": to_float(raw_row[10]) if len(raw_row) > 10 else None,
            "county": to_text(raw_row[11]) if len(raw_row) > 11 else None,
            "section": to_text(raw_row[12]) if len(raw_row) > 12 else None,
            "township": to_text(raw_row[13]) if len(raw_row) > 13 else None,
            "range": to_text(raw_row[14]) if len(raw_row) > 14 else None,
            "pm": to_text(raw_row[15]) if len(raw_row) > 15 else None,
            "q1": to_text(raw_row[16]) if len(raw_row) > 16 else None,
            "q2": to_text(raw_row[17]) if len(raw_row) > 17 else None,
            "q3": to_text(raw_row[18]) if len(raw_row) > 18 else None,
            "q4": to_text(raw_row[19]) if len(raw_row) > 19 else None,
            "footage_ns": to_float(raw_row[20]) if len(raw_row) > 20 else None,
            "ns": to_text(raw_row[21]) if len(raw_row) > 21 else None,
            "footage_ew": to_float(raw_row[22]) if len(raw_row) > 22 else None,
            "ew": to_text(raw_row[23]) if len(raw_row) > 23 else None,
            "from_operator_number": to_int(raw_row[24]) if len(raw_row) > 24 else None,
            "from_operator_name": to_text(raw_row[25]) if len(raw_row) > 25 else None,
            "from_operator_address": to_text(raw_row[26]) if len(raw_row) > 26 else None,
            "from_operator_phone": to_text(raw_row[27]) if len(raw_row) > 27 else None,
            "to_operator_name": to_text(raw_row[28]) if len(raw_row) > 28 else None,
            "to_operator_number": to_int(raw_row[29]) if len(raw_row) > 29 else None,
            "to_operator_address": to_text(raw_row[30]) if len(raw_row) > 30 else None,
            "to_operator_phone": to_text(raw_row[31]) if len(raw_row) > 31 else None,
        }
        rows.append(row)

    return rows
