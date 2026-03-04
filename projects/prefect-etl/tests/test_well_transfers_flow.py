"""End-to-end tests for the well transfers ETL flow."""

from datetime import datetime
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from openpyxl import Workbook
from sqlalchemy.exc import OperationalError

from pipeline.flows.well_transfers_flow import well_transfers_etl_flow


def create_mock_excel_response():
    """Create a mock Excel workbook with test data."""
    wb = Workbook()
    ws = wb.active

    # Header row
    ws.append(
        [
            "EventDate",
            "API Number",
            "WellName",
            "WellNum",
            "Type",
            "Status",
            "PUN 16ez",
            "PUN 02A",
            "Location Type",
            "Surf_Long_X",
            "Surf_Lat_Y",
            "County",
            "Section",
            "Township",
            "Range",
            "PM",
            "Q1",
            "Q2",
            "Q3",
            "Q4",
            "FootageNS",
            "NS",
            "FootageEW",
            "EW",
            "FromOperatorNumber",
            "FromOperatorName",
            "FromOperatorAddressBlock",
            "FromOperatorPhone",
            "ToOperatorName",
            "ToOperatorNumber",
            "ToOperatorAddressBlock",
            "ToOperatorPhone",
        ]
    )

    # Data row
    ws.append(
        [
            datetime(2026, 1, 12),
            "3503702931",
            "SMITH",
            "1",
            "2DNC",
            "AC",
            None,
            None,
            "Surface",
            -96.504201,
            35.662024,
            "037-CREEK",
            "30",
            "14N",
            "08E",
            "IM",
            "NW",
            "SE",
            "SE",
            "SE",
            240.0,
            "S",
            220.0,
            "E",
            24793,
            "1978 INVESTMENTS LLC",
            "4320 E 9TH ST  CUSHING- OK 74023",
            "(918) 285-0093",
            "CHIZUM OIL LLC",
            21860,
            "346 S Lulu St  Wichita- KS 67211",
            "(316) 990-6248",
        ]
    )

    # Save to bytes
    excel_bytes = BytesIO()
    wb.save(excel_bytes)
    excel_bytes.seek(0)
    return excel_bytes.read()


@patch("pipeline.tasks.load.create_engine")
@patch("pipeline.db.create_engine")
@patch("pipeline.tasks.extract.httpx.get")
def test_well_transfers_flow_end_to_end(
    mock_get, mock_db_create_engine, mock_load_create_engine
):
    """Full flow test: extract -> transform -> load with all externals mocked."""
    # Mock the HTTP response with Excel file
    mock_response = MagicMock()
    mock_response.content = create_mock_excel_response()
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

    result = well_transfers_etl_flow(
        xlsx_url="https://fake.oklahoma.gov/transfers.xlsx",
        connection_url="postgresql+psycopg2://fake",
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
def test_well_transfers_flow_fails_on_connection_error(mock_create_engine):
    """Flow should fail fast when database connection check fails."""
    # Mock a connection failure
    mock_create_engine.side_effect = OperationalError("Connection refused", None, None)

    with pytest.raises(OperationalError):
        well_transfers_etl_flow(
            xlsx_url="https://fake.oklahoma.gov/transfers.xlsx",
            connection_url="postgresql+psycopg2://fake",
        )
