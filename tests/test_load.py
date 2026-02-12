"""Tests for the load task."""

from unittest.mock import MagicMock, patch

from pipeline.tasks.load import load_earthquake_data, load_weather_data

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
