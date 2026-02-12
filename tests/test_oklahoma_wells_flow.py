"""Tests for the Oklahoma wells ETL flow."""

from unittest.mock import patch

from pipeline.flows.oklahoma_wells_flow import oklahoma_wells_etl_flow


def test_flow_composes_tasks_and_returns_loaded_count():
    """Should orchestrate extract, transform, load tasks and return loaded count."""
    # Mock all dependencies
    with (
        patch("pipeline.flows.oklahoma_wells_flow.check_connection") as mock_check,
        patch("pipeline.flows.oklahoma_wells_flow.extract_occ_wells_data") as mock_extract,
        patch("pipeline.flows.oklahoma_wells_flow.transform_occ_wells_data") as mock_transform,
        patch("pipeline.flows.oklahoma_wells_flow.load_occ_wells_data") as mock_load,
    ):
        # Configure mock return values
        mock_extract.return_value = "API,WELL_NAME\n3500100002,TEST\n"
        mock_transform.return_value = [{"api": "3500100002", "well_name": "TEST"}]
        mock_load.return_value = 1

        # Run the flow
        result = oklahoma_wells_etl_flow(
            csv_url="https://fake-url.com/wells.csv",
            connection_url="postgresql+psycopg2://fake",
        )

        # Verify all tasks were called
        mock_check.assert_called_once()
        mock_extract.assert_called_once()
        mock_transform.assert_called_once()
        mock_load.assert_called_once()

        # Verify the flow returned the loaded count
        assert result == 1


def test_flow_uses_default_config():
    """Should use default config values when no parameters are provided."""
    with (
        patch("pipeline.flows.oklahoma_wells_flow.check_connection"),
        patch("pipeline.flows.oklahoma_wells_flow.extract_occ_wells_data") as mock_extract,
        patch("pipeline.flows.oklahoma_wells_flow.transform_occ_wells_data"),
        patch("pipeline.flows.oklahoma_wells_flow.load_occ_wells_data"),
    ):
        mock_extract.return_value = "API\n"

        # Run without explicit arguments
        oklahoma_wells_etl_flow()

        # Verify extract was called (config would have been used)
        mock_extract.assert_called_once()
