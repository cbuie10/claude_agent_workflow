"""Tests for the transform task."""

from pipeline.tasks.transform import (
    transform_earthquake_data,
    transform_occ_wells_data,
    transform_weather_data,
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
SAMPLE_OCC_WELLS_CSV = (
    "API,WELL_RECORDS_DOCS,WELL_NAME,WELL_NUM,OPERATOR,WELLSTATUS,WELLTYPE,"
    "SYMBOL_CLASS,SH_LAT,SH_LON,COUNTY,SECTION,TOWNSHIP,RANGE,QTR4,QTR3,QTR2,"
    "QTR1,PM,FOOTAGE_EW,EW,FOOTAGE_NS,NS\n"
    "3500100002,http://example.com,PENN MUTUAL LIFE,#1,OTC/OCC NOT ASSIGNED,PA,"
    "DRY,PLUGGED,35.894723,-94.78241,ADAIR,5.00,16N,24E,NW,NE,SE,NW,IM,330,E,"
    "990,N\n"
    "3500100003,http://example.com,TEST WELL,#2,ACME OIL,A,OIL,ACTIVE,"
    "36.123456,-95.654321,TULSA,10.00,17N,25E,SE,NW,NE,SW,IM,660,W,1320,S\n"
    "3500100004,,EMPTY COORDS,#3,TEST OPERATOR,PA,GAS,PLUGGED,,,CREEK,12.00,"
    "18N,26E,,,,,IM,,,"
)


def test_transform_occ_wells_returns_list():
    """Should return a list of row dicts."""
    result = transform_occ_wells_data.fn(SAMPLE_OCC_WELLS_CSV)
    assert isinstance(result, list)
    assert len(result) == 3


def test_transform_occ_wells_maps_column_names():
    """Should map CSV column names to snake_case."""
    result = transform_occ_wells_data.fn(SAMPLE_OCC_WELLS_CSV)
    row = result[0]
    assert row["api"] == "3500100002"
    assert row["well_name"] == "PENN MUTUAL LIFE"
    assert row["well_num"] == "#1"
    assert row["operator"] == "OTC/OCC NOT ASSIGNED"
    assert row["well_status"] == "PA"
    assert row["well_type"] == "DRY"
    assert row["symbol_class"] == "PLUGGED"
    assert row["county"] == "ADAIR"


def test_transform_occ_wells_converts_floats():
    """Should convert latitude, longitude, and footage fields to float."""
    result = transform_occ_wells_data.fn(SAMPLE_OCC_WELLS_CSV)
    row = result[0]
    assert row["sh_lat"] == 35.894723
    assert row["sh_lon"] == -94.78241
    assert row["footage_ew"] == 330.0
    assert row["footage_ns"] == 990.0


def test_transform_occ_wells_handles_empty_floats():
    """Should convert empty float fields to None."""
    result = transform_occ_wells_data.fn(SAMPLE_OCC_WELLS_CSV)
    row = result[2]  # Third row has empty coordinates and footage
    assert row["sh_lat"] is None
    assert row["sh_lon"] is None
    assert row["footage_ew"] is None
    assert row["footage_ns"] is None


def test_transform_occ_wells_strips_whitespace():
    """Should strip whitespace from all text fields."""
    csv_with_whitespace = (
        "API,WELL_NAME,OPERATOR,WELLSTATUS,WELLTYPE,SYMBOL_CLASS,SH_LAT,SH_LON,"
        "COUNTY,SECTION,TOWNSHIP,RANGE,QTR4,QTR3,QTR2,QTR1,PM,FOOTAGE_EW,EW,"
        "FOOTAGE_NS,NS,WELL_RECORDS_DOCS,WELL_NUM\n"
        "3500100002,  PENN MUTUAL LIFE  ,  OTC/OCC  ,  PA  ,  DRY  ,  PLUGGED  ,"
        "35.894723,-94.78241,  ADAIR  ,5.00,16N,24E,NW,NE,SE,NW,IM,330,E,990,N,"
        "http://example.com,#1"
    )
    result = transform_occ_wells_data.fn(csv_with_whitespace)
    row = result[0]
    assert row["well_name"] == "PENN MUTUAL LIFE"
    assert row["operator"] == "OTC/OCC"
    assert row["county"] == "ADAIR"


def test_transform_occ_wells_filters_empty_api():
    """Should skip rows where API is empty or None."""
    csv_with_empty_api = (
        "API,WELL_NAME,OPERATOR,WELLSTATUS,WELLTYPE,SYMBOL_CLASS,SH_LAT,SH_LON,"
        "COUNTY,SECTION,TOWNSHIP,RANGE,QTR4,QTR3,QTR2,QTR1,PM,FOOTAGE_EW,EW,"
        "FOOTAGE_NS,NS,WELL_RECORDS_DOCS,WELL_NUM\n"
        ",EMPTY API,OTC/OCC,PA,DRY,PLUGGED,35.894723,-94.78241,ADAIR,5.00,16N,"
        "24E,NW,NE,SE,NW,IM,330,E,990,N,http://example.com,#1\n"
        "3500100002,VALID API,OTC/OCC,A,OIL,ACTIVE,36.123456,-95.654321,TULSA,"
        "10.00,17N,25E,SE,NW,NE,SW,IM,660,W,1320,S,http://example.com,#2"
    )
    result = transform_occ_wells_data.fn(csv_with_empty_api)
    assert len(result) == 1
    assert result[0]["api"] == "3500100002"


def test_transform_occ_wells_handles_all_23_columns():
    """Should include all 23 columns in output."""
    result = transform_occ_wells_data.fn(SAMPLE_OCC_WELLS_CSV)
    row = result[0]
    expected_keys = [
        "api",
        "well_records_docs",
        "well_name",
        "well_num",
        "operator",
        "well_status",
        "well_type",
        "symbol_class",
        "sh_lat",
        "sh_lon",
        "county",
        "section",
        "township",
        "range",
        "qtr4",
        "qtr3",
        "qtr2",
        "qtr1",
        "pm",
        "footage_ew",
        "ew",
        "footage_ns",
        "ns",
    ]
    for key in expected_keys:
        assert key in row


def test_transform_occ_wells_keeps_section_as_text():
    """Should keep SECTION as text (e.g., '5.00')."""
    result = transform_occ_wells_data.fn(SAMPLE_OCC_WELLS_CSV)
    row = result[0]
    assert row["section"] == "5.00"
    assert isinstance(row["section"], str)


def test_transform_occ_wells_handles_empty_csv():
    """Should return an empty list when CSV has only headers."""
    empty_csv = (
        "API,WELL_NAME,OPERATOR,WELLSTATUS,WELLTYPE,SYMBOL_CLASS,SH_LAT,SH_LON,"
        "COUNTY,SECTION,TOWNSHIP,RANGE,QTR4,QTR3,QTR2,QTR1,PM,FOOTAGE_EW,EW,"
        "FOOTAGE_NS,NS,WELL_RECORDS_DOCS,WELL_NUM"
    )
    result = transform_occ_wells_data.fn(empty_csv)
    assert result == []


def test_transform_occ_wells_handles_empty_text_fields():
    """Should handle empty text fields gracefully."""
    result = transform_occ_wells_data.fn(SAMPLE_OCC_WELLS_CSV)
    row = result[2]  # Third row has some empty fields
    assert row["well_records_docs"] == ""
    assert row["qtr4"] == ""
    assert row["qtr3"] == ""
