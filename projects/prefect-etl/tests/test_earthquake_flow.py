"""End-to-end tests for the earthquake ETL flow."""

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import OperationalError

from pipeline.flows.earthquake_flow import earthquake_etl_flow

MOCK_GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        {
            "id": "test1",
            "properties": {
                "mag": 3.5,
                "place": "Test Location",
                "time": 1700000000000,
                "magType": "ml",
                "type": "earthquake",
                "title": "M 3.5 Test",
                "url": "https://example.com",
                "felt": 5,
                "tsunami": 0,
            },
            "geometry": {"type": "Point", "coordinates": [-122.0, 37.0, 10.0]},
        }
    ],
}


@patch("pipeline.tasks.load.create_engine")
@patch("pipeline.db.create_engine")
@patch("pipeline.tasks.extract.httpx.get")
def test_earthquake_flow_end_to_end(mock_get, mock_db_create_engine, mock_load_create_engine):
    """Full flow test: extract -> transform -> load with all externals mocked."""
    # Mock the HTTP response
    mock_response = MagicMock()
    mock_response.json.return_value = MOCK_GEOJSON
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

    result = earthquake_etl_flow(
        api_url="https://fake.usgs.gov",
        connection_url="postgresql+psycopg2://fake",
        min_magnitude=0.0,
    )

    assert result == 1
    mock_get.assert_called_once()
    # Verify check_connection was called
    mock_db_create_engine.assert_called_once()
    mock_check_conn.execute.assert_called_once()
    # Verify load happened
    mock_conn.execute.assert_called_once()
    mock_conn.commit.assert_called_once()


@patch("pipeline.db.create_engine")
def test_earthquake_flow_fails_on_connection_error(mock_create_engine):
    """Flow should fail fast when database connection check fails."""
    # Mock a connection failure
    mock_create_engine.side_effect = OperationalError("Connection refused", None, None)

    with pytest.raises(OperationalError):
        earthquake_etl_flow(
            api_url="https://fake.usgs.gov",
            connection_url="postgresql+psycopg2://fake",
            min_magnitude=0.0,
        )
