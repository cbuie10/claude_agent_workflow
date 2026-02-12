"""Tests for the well transfers ETL flow."""

from unittest.mock import MagicMock, patch

from pipeline.flows.well_transfers_flow import well_transfers_etl_flow


def test_flow_runs_extract_transform_load_sequence():
    """Flow should call extract, transform, and load tasks in sequence."""
    # Mock database connection check
    mock_check_connection = MagicMock()

    # Mock extract task
    mock_extract = MagicMock()
    mock_extract.return_value = [("2026-01-12", "3503702931", "SMITH")]

    # Mock transform task
    mock_transform = MagicMock()
    mock_transform.return_value = [
        {
            "event_date": "2026-01-12",
            "api_number": "3503702931",
            "well_name": "SMITH",
        }
    ]

    # Mock load task
    mock_load = MagicMock()
    mock_load.return_value = 1

    with patch("pipeline.flows.well_transfers_flow.check_connection", mock_check_connection):
        with patch(
            "pipeline.flows.well_transfers_flow.extract_well_transfers_data", mock_extract
        ):
            with patch(
                "pipeline.flows.well_transfers_flow.transform_well_transfers_data",
                mock_transform,
            ):
                with patch(
                    "pipeline.flows.well_transfers_flow.load_well_transfers_data", mock_load
                ):
                    result = well_transfers_etl_flow(
                        xlsx_url="https://fake-url.com/file.xlsx",
                        connection_url="postgresql+psycopg2://fake",
                    )

    assert result == 1
    mock_check_connection.assert_called_once()
    mock_extract.assert_called_once()
    mock_transform.assert_called_once()
    mock_load.assert_called_once()
