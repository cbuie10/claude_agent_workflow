"""End-to-end tests for the weather forecast ETL flow."""

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import OperationalError

from pipeline.flows.weather_flow import weather_forecast_etl_flow

MOCK_WEATHER_DATA = {
    "latitude": 40.71,
    "longitude": -73.99,
    "hourly": {
        "time": ["2024-01-01T00:00", "2024-01-01T01:00"],
        "temperature_2m": [32.5, 31.8],
        "relative_humidity_2m": [65, 68],
        "wind_speed_10m": [8.2, 7.5],
    },
}


@patch("pipeline.tasks.load.create_engine")
@patch("pipeline.db.create_engine")
@patch("pipeline.tasks.extract.httpx.get")
def test_weather_flow_end_to_end(mock_get, mock_db_create_engine, mock_load_create_engine):
    """Full flow test: extract -> transform -> load with all externals mocked."""
    # Mock the HTTP response
    mock_response = MagicMock()
    mock_response.json.return_value = MOCK_WEATHER_DATA
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    # Mock the database connection for check_connection
    mock_check_conn = MagicMock()
    mock_check_engine = MagicMock()
    mock_check_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_check_conn)
    mock_check_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
    mock_db_create_engine.return_value = mock_check_engine

    # Mock the database connection for load
    mock_conn = MagicMock()
    mock_engine = MagicMock()
    mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
    mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
    mock_load_create_engine.return_value = mock_engine

    result = weather_forecast_etl_flow(
        api_url="https://fake-weather-api.com",
        connection_url="postgresql+psycopg2://fake",
    )

    assert result == 2
    mock_get.assert_called_once()
    # Verify check_connection was called
    mock_db_create_engine.assert_called_once()
    mock_check_conn.execute.assert_called_once()
    # Verify load happened (2 rows)
    assert mock_conn.execute.call_count == 2
    mock_conn.commit.assert_called_once()


@patch("pipeline.db.create_engine")
def test_weather_flow_fails_on_connection_error(mock_create_engine):
    """Flow should fail fast when database connection check fails."""
    # Mock a connection failure
    mock_create_engine.side_effect = OperationalError("Connection refused", None, None)

    with pytest.raises(OperationalError):
        weather_forecast_etl_flow(
            api_url="https://fake-weather-api.com",
            connection_url="postgresql+psycopg2://fake",
        )
