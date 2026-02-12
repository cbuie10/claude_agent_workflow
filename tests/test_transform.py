"""Tests for the transform task."""

from datetime import date, datetime

from pipeline.tasks.transform import (
    transform_earthquake_data,
    transform_occ_wells_data,
    transform_weather_data,
    transform_well_transfers_data,
)

# Sample GeoJSON that mimics real USGS data
SAMPLE_GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        {
            "id": "us7000abc1",
            "properties": {
                "mag": 4.5,
                "place": "10km NW of Somewhere",
                "time": 1700000000000,  # epoch milliseconds
                "magType": "ml",
                "type": "earthquake",
                "title": "M 4.5 - 10km NW of Somewhere",
                "url": "https://earthquake.usgs.gov/earthquakes/eventpage/us7000abc1",
                "felt": 12,
                "tsunami": 0,
            },
            "geometry": {"type": "Point", "coordinates": [-122.5, 37.8, 8.2]},
        },
        {
            "id": "us7000abc2",
            "properties": {
                "mag": 0.5,
                "place": "Tiny quake",
                "time": 1700000100000,
                "magType": "ml",
                "type": "earthquake",
                "title": "M 0.5",
                "url": "https://example.com",
                "felt": None,
                "tsunami": 0,
            },
            "geometry": {"type": "Point", "coordinates": [-118.0, 34.0, 5.0]},
        },
    ],
}


def test_transform_returns_list():
    """Should return a list of row dicts."""
    result = transform_earthquake_data.fn(SAMPLE_GEOJSON)
    assert isinstance(result, list)
    assert len(result) == 2


def test_transform_flattens_fields():
    """Should correctly flatten nested GeoJSON into flat row dicts."""
    result = transform_earthquake_data.fn(SAMPLE_GEOJSON)
    row = result[0]
    assert row["id"] == "us7000abc1"
    assert row["magnitude"] == 4.5
    assert row["place"] == "10km NW of Somewhere"
    assert row["longitude"] == -122.5
    assert row["latitude"] == 37.8
    assert row["depth_km"] == 8.2
    assert row["magnitude_type"] == "ml"
    assert row["felt"] == 12


def test_transform_converts_timestamp():
    """Should convert epoch milliseconds to a datetime."""
    result = transform_earthquake_data.fn(SAMPLE_GEOJSON)
    occurred_at = result[0]["occurred_at"]
    assert occurred_at.year == 2023
    assert occurred_at.month == 11


def test_transform_filters_by_min_magnitude():
    """Should exclude events below min_magnitude."""
    result = transform_earthquake_data.fn(SAMPLE_GEOJSON, min_magnitude=2.0)
    assert len(result) == 1
    assert result[0]["id"] == "us7000abc1"


def test_transform_handles_empty_features():
    """Should return an empty list when there are no features."""
    result = transform_earthquake_data.fn({"features": []})
    assert result == []


def test_transform_skips_null_magnitude():
    """Should skip features where magnitude is None."""
    data = {
        "features": [
            {
                "id": "null_mag",
                "properties": {"mag": None, "place": "Unknown", "time": 1700000000000},
                "geometry": {"coordinates": [0, 0, 0]},
            }
        ]
    }
    result = transform_earthquake_data.fn(data)
    assert result == []


# Sample weather data that mimics real Open-Meteo API response
SAMPLE_WEATHER_DATA = {
    "latitude": 40.71,
    "longitude": -73.99,
    "hourly": {
        "time": ["2024-01-01T00:00", "2024-01-01T01:00", "2024-01-01T02:00"],
        "temperature_2m": [32.5, 31.8, 30.2],
        "relative_humidity_2m": [65, 68, 70],
        "wind_speed_10m": [8.2, 7.5, 6.8],
    },
}


def test_transform_weather_returns_list():
    """Should return a list of row dicts."""
    result = transform_weather_data.fn(SAMPLE_WEATHER_DATA)
    assert isinstance(result, list)
    assert len(result) == 3


def test_transform_weather_flattens_hourly_arrays():
    """Should correctly flatten hourly arrays into flat row dicts."""
    result = transform_weather_data.fn(SAMPLE_WEATHER_DATA)
    row = result[0]
    assert row["latitude"] == 40.71
    assert row["longitude"] == -73.99
    assert row["temperature_f"] == 32.5
    assert row["relative_humidity"] == 65
    assert row["wind_speed_mph"] == 8.2


def test_transform_weather_generates_composite_id():
    """Should generate composite ID from rounded lat/lon and timestamp."""
    result = transform_weather_data.fn(SAMPLE_WEATHER_DATA)
    row = result[0]
    assert "id" in row
    assert row["id"] == "40.71_-73.99_2024-01-01T00:00"


def test_transform_weather_converts_timestamp():
    """Should convert ISO8601 time strings to datetime."""
    result = transform_weather_data.fn(SAMPLE_WEATHER_DATA)
    forecast_time = result[0]["forecast_time"]
    assert forecast_time.year == 2024
    assert forecast_time.month == 1
    assert forecast_time.day == 1
    assert forecast_time.hour == 0


def test_transform_weather_filters_null_temperature():
    """Should skip rows where temperature is None."""
    data = {
        "latitude": 40.71,
        "longitude": -73.99,
        "hourly": {
            "time": ["2024-01-01T00:00", "2024-01-01T01:00"],
            "temperature_2m": [None, 31.8],
            "relative_humidity_2m": [65, 68],
            "wind_speed_10m": [8.2, 7.5],
        },
    }
    result = transform_weather_data.fn(data)
    assert len(result) == 1
    assert result[0]["temperature_f"] == 31.8


def test_transform_weather_handles_empty_hourly():
    """Should return an empty list when there are no hourly records."""
    data = {
        "latitude": 40.71,
        "longitude": -73.99,
        "hourly": {"time": []},
    }
    result = transform_weather_data.fn(data)
    assert result == []


# Sample CSV data that mimics real OCC wells data
SAMPLE_OCC_CSV = (
    "API,WELL_RECORDS_DOCS,WELL_NAME,WELL_NUM,OPERATOR,WELLSTATUS,WELLTYPE,"
    "SYMBOL_CLASS,SH_LAT,SH_LON,COUNTY,SECTION,TOWNSHIP,RANGE,"
    "QTR4,QTR3,QTR2,QTR1,PM,FOOTAGE_EW,EW,FOOTAGE_NS,NS\n"
    "3500100002,http://example.com,PENN MUTUAL LIFE,#1,OTC/OCC NOT ASSIGNED,"
    "PA,DRY,PLUGGED,35.894723,-94.78241,ADAIR,5.00,16N,24E,"
    "NE,NW,SE,NW,IM,330.0,E,990.0,S\n"
    "3500100003,,TEST WELL,#2,ACME OIL,A,OIL,ACTIVE,,,ADAIR,6.00,16N,24E,,,,,,,,"
    "\n"
    ",,,#3,MISSING API,A,GAS,ACTIVE,36.123,-94.456,ALFALFA,,,,,,,,,,,"
)


def test_transform_occ_wells_returns_list():
    """Should return a list of row dicts."""
    result = transform_occ_wells_data.fn(SAMPLE_OCC_CSV)
    assert isinstance(result, list)
    assert len(result) == 2  # Third row has no API


def test_transform_occ_wells_maps_columns():
    """Should correctly map CSV columns to snake_case database columns."""
    result = transform_occ_wells_data.fn(SAMPLE_OCC_CSV)
    row = result[0]
    assert row["api"] == "3500100002"
    assert row["well_records_docs"] == "http://example.com"
    assert row["well_name"] == "PENN MUTUAL LIFE"
    assert row["well_num"] == "#1"
    assert row["operator"] == "OTC/OCC NOT ASSIGNED"
    assert row["well_status"] == "PA"
    assert row["well_type"] == "DRY"
    assert row["symbol_class"] == "PLUGGED"
    assert row["county"] == "ADAIR"
    assert row["section"] == "5.00"
    assert row["township"] == "16N"
    assert row["range"] == "24E"


def test_transform_occ_wells_converts_floats():
    """Should convert latitude, longitude, and footage to floats."""
    result = transform_occ_wells_data.fn(SAMPLE_OCC_CSV)
    row = result[0]
    assert isinstance(row["sh_lat"], float)
    assert row["sh_lat"] == 35.894723
    assert isinstance(row["sh_lon"], float)
    assert row["sh_lon"] == -94.78241
    assert isinstance(row["footage_ew"], float)
    assert row["footage_ew"] == 330.0
    assert isinstance(row["footage_ns"], float)
    assert row["footage_ns"] == 990.0


def test_transform_occ_wells_handles_empty_floats():
    """Should convert empty float fields to None."""
    result = transform_occ_wells_data.fn(SAMPLE_OCC_CSV)
    row = result[1]  # Second row has empty lat/lon
    assert row["sh_lat"] is None
    assert row["sh_lon"] is None


def test_transform_occ_wells_handles_empty_text():
    """Should convert empty text fields to None."""
    result = transform_occ_wells_data.fn(SAMPLE_OCC_CSV)
    row = result[1]  # Second row has empty well_records_docs
    assert row["well_records_docs"] is None


def test_transform_occ_wells_skips_empty_api():
    """Should skip rows where API is empty."""
    result = transform_occ_wells_data.fn(SAMPLE_OCC_CSV)
    assert len(result) == 2
    for row in result:
        assert row["api"]  # All returned rows should have an API


def test_transform_occ_wells_strips_whitespace():
    """Should strip whitespace from all text fields."""
    csv_with_spaces = """API,WELL_NAME
3500100002,  TEST WELL  """
    result = transform_occ_wells_data.fn(csv_with_spaces)
    assert result[0]["well_name"] == "TEST WELL"


def test_transform_occ_wells_handles_empty_csv():
    """Should return an empty list when CSV has only headers."""
    result = transform_occ_wells_data.fn("API,WELL_NAME\n")
    assert result == []


# Sample well transfers data that mimics real Excel row tuples
SAMPLE_WELL_TRANSFERS_ROWS = [
    (
        datetime(2026, 1, 12),  # EventDate
        "3503702931",  # API Number
        "SMITH",  # WellName
        "1",  # WellNum
        "2DNC",  # Type
        "AC",  # Status
        None,  # PUN 16ez
        None,  # PUN 02A
        "Surface",  # Location Type
        -96.504201,  # Surf_Long_X
        35.662024,  # Surf_Lat_Y
        "037-CREEK",  # County
        "30",  # Section
        "14N",  # Township
        "08E",  # Range
        "IM",  # PM
        "NW",  # Q1
        "SE",  # Q2
        "SE",  # Q3
        "SE",  # Q4
        240,  # FootageNS
        "S",  # NS
        220,  # FootageEW
        "E",  # EW
        24793,  # FromOperatorNumber
        "1978 INVESTMENTS LLC",  # FromOperatorName
        "4320 E 9TH ST  CUSHING- OK 74023",  # FromOperatorAddressBlock
        "(918) 285-0093",  # FromOperatorPhone
        "CHIZUM OIL LLC",  # ToOperatorName
        21860,  # ToOperatorNumber
        "346 S Lulu St  Wichita- KS 67211",  # ToOperatorAddressBlock
        "(316) 990-6248",  # ToOperatorPhone
    ),
    (
        datetime(2026, 1, 13),
        "3503702932",
        "JONES",
        2,  # numeric well num
        "OIL",
        "A",
        None,
        None,
        "Surface",
        None,  # empty longitude
        None,  # empty latitude
        "037-CREEK",
        "31",
        "14N",
        "08E",
        "IM",
        None,
        None,
        None,
        None,
        None,  # empty footage
        None,
        None,
        None,
        None,  # empty from operator number
        "TEST OPERATOR",
        "123 MAIN ST",
        None,
        "ANOTHER OPERATOR",
        None,  # empty to operator number
        "456 OAK AVE",
        None,
    ),
]


def test_transform_well_transfers_returns_list():
    """Should return a list of row dicts."""
    result = transform_well_transfers_data.fn(SAMPLE_WELL_TRANSFERS_ROWS)
    assert isinstance(result, list)
    assert len(result) == 2


def test_transform_well_transfers_maps_columns():
    """Should correctly map Excel columns to snake_case database columns."""
    result = transform_well_transfers_data.fn(SAMPLE_WELL_TRANSFERS_ROWS)
    row = result[0]
    assert row["api_number"] == "3503702931"
    assert row["well_name"] == "SMITH"
    assert row["well_num"] == "1"
    assert row["well_type"] == "2DNC"
    assert row["well_status"] == "AC"
    assert row["county"] == "037-CREEK"
    assert row["section"] == "30"
    assert row["township"] == "14N"
    assert row["range"] == "08E"
    assert row["pm"] == "IM"


def test_transform_well_transfers_converts_event_date():
    """Should convert EventDate datetime to date."""
    result = transform_well_transfers_data.fn(SAMPLE_WELL_TRANSFERS_ROWS)
    row = result[0]
    assert isinstance(row["event_date"], date)
    assert row["event_date"] == date(2026, 1, 12)


def test_transform_well_transfers_converts_floats():
    """Should convert longitude, latitude, and footage to floats."""
    result = transform_well_transfers_data.fn(SAMPLE_WELL_TRANSFERS_ROWS)
    row = result[0]
    assert isinstance(row["surf_long_x"], float)
    assert row["surf_long_x"] == -96.504201
    assert isinstance(row["surf_lat_y"], float)
    assert row["surf_lat_y"] == 35.662024
    assert isinstance(row["footage_ns"], float)
    assert row["footage_ns"] == 240.0
    assert isinstance(row["footage_ew"], float)
    assert row["footage_ew"] == 220.0


def test_transform_well_transfers_converts_ints():
    """Should convert operator numbers to ints."""
    result = transform_well_transfers_data.fn(SAMPLE_WELL_TRANSFERS_ROWS)
    row = result[0]
    assert isinstance(row["from_operator_number"], int)
    assert row["from_operator_number"] == 24793
    assert isinstance(row["to_operator_number"], int)
    assert row["to_operator_number"] == 21860


def test_transform_well_transfers_handles_none_values():
    """Should convert None and empty values to None."""
    result = transform_well_transfers_data.fn(SAMPLE_WELL_TRANSFERS_ROWS)
    row = result[1]
    assert row["surf_long_x"] is None
    assert row["surf_lat_y"] is None
    assert row["footage_ns"] is None
    assert row["footage_ew"] is None
    assert row["from_operator_number"] is None
    assert row["to_operator_number"] is None
    assert row["q1"] is None


def test_transform_well_transfers_converts_numeric_well_num_to_text():
    """Should convert numeric well_num to text."""
    result = transform_well_transfers_data.fn(SAMPLE_WELL_TRANSFERS_ROWS)
    row = result[1]
    assert isinstance(row["well_num"], str)
    assert row["well_num"] == "2"


def test_transform_well_transfers_skips_empty_api():
    """Should skip rows where API Number is empty or None."""
    rows_with_empty_api = [
        (datetime(2026, 1, 12), None, "WELL", "1"),  # None API
        (datetime(2026, 1, 13), "", "WELL2", "2"),  # Empty API
        (datetime(2026, 1, 14), "3503702931", "WELL3", "3"),  # Valid
    ]
    result = transform_well_transfers_data.fn(rows_with_empty_api)
    assert len(result) == 1
    assert result[0]["api_number"] == "3503702931"


def test_transform_well_transfers_handles_empty_list():
    """Should return an empty list when given no rows."""
    result = transform_well_transfers_data.fn([])
    assert result == []
