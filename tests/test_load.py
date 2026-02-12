"""Tests for the load task."""

from unittest.mock import MagicMock, patch

from pipeline.tasks.load import (
    load_earthquake_data,
    load_occ_wells_data,
    load_weather_data,
    load_well_transfers_data,
)

SAMPLE_ROWS = [
    {
        "id": "test1",
        "magnitude": 3.0,
        "place": "Test Location",
        "occurred_at": "2024-01-01T00:00:00+00:00",
        "longitude": -122.0,
        "latitude": 37.0,
        "depth_km": 10.0,
        "magnitude_type": "ml",
        "event_type": "earthquake",
        "title": "M 3.0 Test",
        "detail_url": "https://example.com",
        "felt": None,
        "tsunami": 0,
    },
]


def test_load_returns_zero_for_empty_rows():
    """Should return 0 immediately when given no rows — no DB calls."""
    result = load_earthquake_data.fn([], "postgresql+psycopg2://fake")
    assert result == 0


def test_load_executes_and_returns_count():
    """Should execute SQL for each row and return the count."""
    mock_conn = MagicMock()
    mock_engine = MagicMock()
    mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
    mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)

    with patch("pipeline.tasks.load.create_engine", return_value=mock_engine):
        result = load_earthquake_data.fn(SAMPLE_ROWS, "postgresql+psycopg2://fake")

    assert result == 1
    assert mock_conn.execute.call_count == 1
    mock_conn.commit.assert_called_once()


SAMPLE_WEATHER_ROWS = [
    {
        "id": "40.71_-73.99_2024-01-01T00:00",
        "latitude": 40.71,
        "longitude": -73.99,
        "forecast_time": "2024-01-01T00:00:00+00:00",
        "temperature_f": 32.5,
        "relative_humidity": 65,
        "wind_speed_mph": 8.2,
    },
]


def test_load_weather_returns_zero_for_empty_rows():
    """Should return 0 immediately when given no rows — no DB calls."""
    result = load_weather_data.fn([], "postgresql+psycopg2://fake")
    assert result == 0


def test_load_weather_executes_and_returns_count():
    """Should execute SQL for each row and return the count."""
    mock_conn = MagicMock()
    mock_engine = MagicMock()
    mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
    mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)

    with patch("pipeline.tasks.load.create_engine", return_value=mock_engine):
        result = load_weather_data.fn(SAMPLE_WEATHER_ROWS, "postgresql+psycopg2://fake")

    assert result == 1
    assert mock_conn.execute.call_count == 1
    mock_conn.commit.assert_called_once()


SAMPLE_OCC_WELLS_ROWS = [
    {
        "api": "3500100002",
        "well_records_docs": "http://example.com",
        "well_name": "PENN MUTUAL LIFE",
        "well_num": "#1",
        "operator": "OTC/OCC NOT ASSIGNED",
        "well_status": "PA",
        "well_type": "DRY",
        "symbol_class": "PLUGGED",
        "sh_lat": 35.894723,
        "sh_lon": -94.78241,
        "county": "ADAIR",
        "section": "5.00",
        "township": "16N",
        "range": "24E",
        "qtr4": "NE",
        "qtr3": "NW",
        "qtr2": "SE",
        "qtr1": "NW",
        "pm": "IM",
        "footage_ew": 330.0,
        "ew": "E",
        "footage_ns": 990.0,
        "ns": "S",
    },
]


def test_load_occ_wells_returns_zero_for_empty_rows():
    """Should return 0 immediately when given no rows — no DB calls."""
    result = load_occ_wells_data.fn([], "postgresql+psycopg2://fake")
    assert result == 0


def test_load_occ_wells_executes_and_returns_count():
    """Should execute SQL for each row and return the count."""
    mock_conn = MagicMock()
    mock_engine = MagicMock()
    mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
    mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)

    with patch("pipeline.tasks.load.create_engine", return_value=mock_engine):
        result = load_occ_wells_data.fn(SAMPLE_OCC_WELLS_ROWS, "postgresql+psycopg2://fake")

    assert result == 1
    assert mock_conn.execute.call_count == 1
    mock_conn.commit.assert_called_once()


SAMPLE_WELL_TRANSFERS_ROWS = [
    {
        "event_date": "2026-01-12",
        "api_number": "3503702931",
        "well_name": "SMITH",
        "well_num": "1",
        "well_type": "2DNC",
        "well_status": "AC",
        "pun_16ez": None,
        "pun_02a": None,
        "location_type": "Surface",
        "surf_long_x": -96.504201,
        "surf_lat_y": 35.662024,
        "county": "037-CREEK",
        "section": "30",
        "township": "14N",
        "range": "08E",
        "pm": "IM",
        "q1": "NW",
        "q2": "SE",
        "q3": "SE",
        "q4": "SE",
        "footage_ns": 240.0,
        "ns": "S",
        "footage_ew": 220.0,
        "ew": "E",
        "from_operator_number": 24793,
        "from_operator_name": "1978 INVESTMENTS LLC",
        "from_operator_address": "4320 E 9TH ST  CUSHING- OK 74023",
        "from_operator_phone": "(918) 285-0093",
        "to_operator_name": "CHIZUM OIL LLC",
        "to_operator_number": 21860,
        "to_operator_address": "346 S Lulu St  Wichita- KS 67211",
        "to_operator_phone": "(316) 990-6248",
    },
]


def test_load_well_transfers_returns_zero_for_empty_rows():
    """Should return 0 immediately when given no rows — no DB calls."""
    result = load_well_transfers_data.fn([], "postgresql+psycopg2://fake")
    assert result == 0


def test_load_well_transfers_executes_and_returns_count():
    """Should execute SQL for each row and return the count."""
    mock_conn = MagicMock()
    mock_engine = MagicMock()
    mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
    mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)

    with patch("pipeline.tasks.load.create_engine", return_value=mock_engine):
        result = load_well_transfers_data.fn(SAMPLE_WELL_TRANSFERS_ROWS, "postgresql+psycopg2://fake")

    assert result == 1
    assert mock_conn.execute.call_count == 1
    mock_conn.commit.assert_called_once()
