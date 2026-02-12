"""Tests for the OCC Wells ETL flow."""

from unittest.mock import patch

from pipeline.flows.occ_wells_flow import occ_wells_etl_flow


def test_occ_wells_flow_completes_successfully():
    """The flow should orchestrate extract, transform, and load tasks."""
    # Mock the database connection check
    with patch("pipeline.flows.occ_wells_flow.check_connection"):
        # Mock extract to return sample CSV
        mock_csv = "API,WELL_NAME,OPERATOR\n3500100002,PENN MUTUAL LIFE,OTC/OCC"
        with patch(
            "pipeline.flows.occ_wells_flow.extract_occ_wells_data",
            return_value=mock_csv,
        ):
            # Mock transform to return sample rows
            mock_rows = [
                {
                    "api": "3500100002",
                    "well_name": "PENN MUTUAL LIFE",
                    "operator": "OTC/OCC",
                }
            ]
            with patch(
                "pipeline.flows.occ_wells_flow.transform_occ_wells_data",
                return_value=mock_rows,
            ):
                # Mock load to return count
                with patch(
                    "pipeline.flows.occ_wells_flow.load_occ_wells_data",
                    return_value=1,
                ) as mock_load:
                    result = occ_wells_etl_flow()

    assert result == 1
    mock_load.assert_called_once()


def test_occ_wells_flow_uses_custom_parameters():
    """The flow should accept custom CSV URL and connection URL."""
    custom_csv_url = "https://custom-url.com/wells.csv"
    custom_db_url = "postgresql+psycopg2://custom:pass@localhost:5432/custom_db"

    with patch("pipeline.flows.occ_wells_flow.check_connection"):
        mock_csv = "API,WELL_NAME\n3500100002,TEST"
        with patch(
            "pipeline.flows.occ_wells_flow.extract_occ_wells_data",
            return_value=mock_csv,
        ) as mock_extract:
            mock_rows = [{"api": "3500100002", "well_name": "TEST"}]
            with patch(
                "pipeline.flows.occ_wells_flow.transform_occ_wells_data",
                return_value=mock_rows,
            ):
                with patch(
                    "pipeline.flows.occ_wells_flow.load_occ_wells_data",
                    return_value=1,
                ) as mock_load:
                    occ_wells_etl_flow(
                        csv_url=custom_csv_url,
                        connection_url=custom_db_url,
                    )

    # Verify custom parameters were used
    mock_extract.assert_called_once()
    mock_load.assert_called_once()
    # Check that load was called with custom connection URL
    call_args = mock_load.call_args
    assert call_args[0][1] == custom_db_url
