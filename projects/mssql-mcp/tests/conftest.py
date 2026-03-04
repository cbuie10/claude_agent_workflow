"""Shared test fixtures for the MSSQL MCP server."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from mssql_mcp.config import Config


@pytest.fixture()
def config() -> Config:
    """Return a test config with SQL auth."""
    return Config(
        host="test-server",
        port=1433,
        database="test_db",
        user="test_user",
        password="test_pass",
        driver="ODBC Driver 17 for SQL Server",
        windows_auth=False,
        read_only=True,
        query_timeout=30,
        max_rows=100,
    )


@pytest.fixture()
def config_windows() -> Config:
    """Return a test config with Windows auth."""
    return Config(
        host="test-server",
        port=1433,
        database="test_db",
        user="",
        password="",
        driver="ODBC Driver 17 for SQL Server",
        windows_auth=True,
        read_only=True,
        query_timeout=30,
        max_rows=100,
    )


@pytest.fixture()
def mock_cursor() -> MagicMock:
    """Return a mock pyodbc cursor."""
    cursor = MagicMock()
    cursor.description = [("id",), ("name",), ("value",)]
    cursor.fetchmany.return_value = [
        (1, "alpha", 100),
        (2, "beta", 200),
    ]
    return cursor


@pytest.fixture()
def mock_connection(mock_cursor: MagicMock) -> MagicMock:
    """Return a mock pyodbc connection that produces mock_cursor."""
    conn = MagicMock()
    conn.cursor.return_value = mock_cursor
    return conn
