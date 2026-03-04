"""Tests for database connection and query execution."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from mssql_mcp.config import Config
from mssql_mcp.database import build_connection_string, check_write_safety, execute_query


class TestBuildConnectionString:
    def test_sql_auth(self, config: Config) -> None:
        """SQL auth should include UID and PWD."""
        conn_str = build_connection_string(config)
        assert "UID=test_user" in conn_str
        assert "PWD=test_pass" in conn_str
        assert "Trusted_Connection" not in conn_str
        assert "SERVER=test-server,1433" in conn_str
        assert "DATABASE=test_db" in conn_str

    def test_windows_auth(self, config_windows: Config) -> None:
        """Windows auth should use Trusted_Connection."""
        conn_str = build_connection_string(config_windows)
        assert "Trusted_Connection=yes" in conn_str
        assert "UID=" not in conn_str
        assert "PWD=" not in conn_str

    def test_includes_driver(self, config: Config) -> None:
        """Connection string should include the ODBC driver."""
        conn_str = build_connection_string(config)
        assert "DRIVER={ODBC Driver 17 for SQL Server}" in conn_str

    def test_trust_certificate(self, config: Config) -> None:
        """Connection string should include TrustServerCertificate."""
        conn_str = build_connection_string(config)
        assert "TrustServerCertificate=yes" in conn_str

    def test_database_override(self, config: Config) -> None:
        """Database override should replace the configured database."""
        conn_str = build_connection_string(config, database="other_db")
        assert "DATABASE=other_db" in conn_str
        assert "DATABASE=test_db" not in conn_str

    def test_database_override_none_uses_config(self, config: Config) -> None:
        """Passing None for database should use config default."""
        conn_str = build_connection_string(config, database=None)
        assert "DATABASE=test_db" in conn_str


class TestCheckWriteSafety:
    @pytest.mark.parametrize(
        "sql",
        [
            "INSERT INTO t VALUES (1)",
            "UPDATE t SET x = 1",
            "DELETE FROM t",
            "DROP TABLE t",
            "TRUNCATE TABLE t",
            "ALTER TABLE t ADD col INT",
            "CREATE TABLE t (id INT)",
            "EXEC sp_help",
            "MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET x = 1",
        ],
    )
    def test_blocks_write_in_read_only(self, sql: str) -> None:
        """Write operations should be blocked in read-only mode."""
        with pytest.raises(ValueError, match="read-only"):
            check_write_safety(sql, read_only=True)

    def test_allows_select_in_read_only(self) -> None:
        """SELECT should be allowed in read-only mode."""
        check_write_safety("SELECT * FROM t", read_only=True)  # Should not raise

    def test_allows_write_when_not_read_only(self) -> None:
        """Write operations should be allowed when read-only is false."""
        check_write_safety("INSERT INTO t VALUES (1)", read_only=False)  # Should not raise


class TestExecuteQuery:
    @patch("mssql_mcp.database.get_connection")
    def test_returns_list_of_dicts(
        self, mock_get_conn: MagicMock, config: Config, mock_connection: MagicMock
    ) -> None:
        """execute_query should return a list of dicts with column names as keys."""
        mock_get_conn.return_value = mock_connection
        results = execute_query(config, "SELECT id, name, value FROM t")

        assert len(results) == 2
        assert results[0] == {"id": 1, "name": "alpha", "value": 100}
        assert results[1] == {"id": 2, "name": "beta", "value": 200}

    @patch("mssql_mcp.database.get_connection")
    def test_respects_max_rows(
        self, mock_get_conn: MagicMock, config: Config, mock_connection: MagicMock
    ) -> None:
        """execute_query should pass max_rows to fetchmany."""
        mock_get_conn.return_value = mock_connection
        execute_query(config, "SELECT * FROM t")
        mock_connection.cursor().fetchmany.assert_called_once_with(config.max_rows)

    @patch("mssql_mcp.database.get_connection")
    def test_parameterized_query(
        self, mock_get_conn: MagicMock, config: Config, mock_connection: MagicMock
    ) -> None:
        """execute_query should pass params to cursor.execute."""
        mock_get_conn.return_value = mock_connection
        execute_query(config, "SELECT * FROM t WHERE id = ?", params=(42,))
        mock_connection.cursor().execute.assert_called_once_with(
            "SELECT * FROM t WHERE id = ?", (42,)
        )

    def test_blocks_write_in_read_only(self, config: Config) -> None:
        """execute_query should block write queries when read-only."""
        with pytest.raises(ValueError, match="read-only"):
            execute_query(config, "DROP TABLE users")

    @patch("mssql_mcp.database.get_connection")
    def test_closes_connection(
        self, mock_get_conn: MagicMock, config: Config, mock_connection: MagicMock
    ) -> None:
        """Connection should always be closed after query."""
        mock_get_conn.return_value = mock_connection
        execute_query(config, "SELECT 1")
        mock_connection.close.assert_called_once()

    @patch("mssql_mcp.database.get_connection")
    def test_handles_no_result_set(
        self, mock_get_conn: MagicMock, mock_connection: MagicMock
    ) -> None:
        """Queries without result sets (e.g. INSERT) should return affected_rows."""
        cfg = Config(
            database="db", user="u", password="p", read_only=False
        )
        mock_cursor = mock_connection.cursor()
        mock_cursor.description = None
        mock_cursor.rowcount = 5
        mock_get_conn.return_value = mock_connection

        results = execute_query(cfg, "INSERT INTO t VALUES (1)")
        assert results == [{"affected_rows": 5}]
