"""Tests for configuration loading and validation."""

from __future__ import annotations

import pytest

from mssql_mcp.config import Config


class TestConfig:
    def test_defaults(self) -> None:
        """Config should have sensible defaults."""
        cfg = Config(database="test_db", user="u", password="p")
        assert cfg.host == "localhost"
        assert cfg.port == 1433
        assert cfg.read_only is True
        assert cfg.query_timeout == 30
        assert cfg.max_rows == 10000

    def test_validate_missing_database(self) -> None:
        """Should raise if database is empty."""
        cfg = Config(database="", user="u", password="p")
        with pytest.raises(ValueError, match="MSSQL_DATABASE"):
            cfg.validate()

    def test_validate_missing_credentials(self) -> None:
        """Should raise if SQL auth is used but user/password are missing."""
        cfg = Config(database="db", user="", password="", windows_auth=False)
        with pytest.raises(ValueError, match="MSSQL_USER"):
            cfg.validate()

    def test_validate_windows_auth_no_credentials(self) -> None:
        """Should pass validation with Windows auth even without user/password."""
        cfg = Config(database="db", user="", password="", windows_auth=True)
        cfg.validate()  # Should not raise

    def test_frozen(self) -> None:
        """Config should be immutable."""
        cfg = Config(database="db", user="u", password="p")
        with pytest.raises(AttributeError):
            cfg.host = "other"  # type: ignore[misc]
