"""Tests for the MCP server tool functions."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import mssql_mcp.server as server_module
from mssql_mcp.server import _format_results, _get_active_db


class TestFormatResults:
    def test_empty_results(self) -> None:
        """Should return a message for empty results."""
        assert _format_results([]) == "No results returned."

    def test_formats_table(self) -> None:
        """Should format results as an aligned table."""
        rows = [
            {"name": "alpha", "value": 100},
            {"name": "beta", "value": 200},
        ]
        result = _format_results(rows)
        assert "name" in result
        assert "value" in result
        assert "alpha" in result
        assert "200" in result
        # Should have header + separator + 2 data rows
        lines = result.strip().split("\n")
        assert len(lines) == 4

    def test_truncates_large_results(self) -> None:
        """Should show truncation message when results exceed max_display."""
        rows = [{"id": i} for i in range(100)]
        result = _format_results(rows, max_display=10)
        assert "showing 10 of 100" in result


class TestActiveDatabase:
    def setup_method(self) -> None:
        """Reset active database before each test."""
        server_module._active_database = None

    def test_default_uses_config(self) -> None:
        """When no database has been switched, should use config default."""
        active = _get_active_db()
        assert active == server_module._cfg.database

    def test_switched_database(self) -> None:
        """After switching, _get_active_db should return the new database."""
        server_module._active_database = "other_db"
        assert _get_active_db() == "other_db"

    @patch("mssql_mcp.server.get_connection")
    def test_use_database_switches(self, mock_get_conn: MagicMock) -> None:
        """use_database() should update the active database."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ("new_db",)
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        result = server_module.use_database("new_db")
        assert "new_db" in result
        assert server_module._active_database == "new_db"

    @patch("mssql_mcp.server.get_connection")
    def test_use_database_failure(self, mock_get_conn: MagicMock) -> None:
        """use_database() should not switch if connection fails."""
        mock_get_conn.side_effect = Exception("Access denied")

        result = server_module.use_database("bad_db")
        assert "Failed" in result
        assert server_module._active_database is None

    @patch("mssql_mcp.server.execute_query")
    def test_list_databases(self, mock_execute: MagicMock) -> None:
        """list_databases() should query master and show active database."""
        mock_execute.return_value = [
            {"database": "master", "status": "ONLINE", "size_mb": 10.0, "created": "2020-01-01"},
            {"database": "my_app", "status": "ONLINE", "size_mb": 500.0, "created": "2023-06-15"},
        ]

        result = server_module.list_databases()
        assert "Active database:" in result
        assert "master" in result
        assert "my_app" in result
        # Should query from master database
        mock_execute.assert_called_once()
        call_kwargs = mock_execute.call_args
        assert call_kwargs[1]["database"] == "master"
