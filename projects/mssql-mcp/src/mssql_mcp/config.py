"""Configuration loaded from environment variables.

All SQL Server connection settings come from env vars so credentials
never appear in source code. Copy .env.example to .env and fill in
your values, or set them in your shell / Claude Code settings.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the project root (two levels up from this file)
_env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(_env_path)


def _bool(value: str) -> bool:
    """Parse a string into a boolean."""
    return value.strip().lower() in ("true", "1", "yes")


@dataclass(frozen=True)
class Config:
    """Immutable server configuration."""

    # Connection
    host: str = field(default_factory=lambda: os.getenv("MSSQL_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("MSSQL_PORT", "1433")))
    database: str = field(default_factory=lambda: os.getenv("MSSQL_DATABASE", ""))
    user: str = field(default_factory=lambda: os.getenv("MSSQL_USER", ""))
    password: str = field(default_factory=lambda: os.getenv("MSSQL_PASSWORD", ""))
    driver: str = field(
        default_factory=lambda: os.getenv("MSSQL_DRIVER", "ODBC Driver 17 for SQL Server")
    )

    # Authentication
    windows_auth: bool = field(
        default_factory=lambda: _bool(os.getenv("MSSQL_WINDOWS_AUTH", "false"))
    )

    # Safety
    read_only: bool = field(
        default_factory=lambda: _bool(os.getenv("MSSQL_READ_ONLY", "true"))
    )

    # Limits
    query_timeout: int = field(
        default_factory=lambda: int(os.getenv("MSSQL_QUERY_TIMEOUT", "30"))
    )
    max_rows: int = field(
        default_factory=lambda: int(os.getenv("MSSQL_MAX_ROWS", "10000"))
    )

    def validate(self) -> None:
        """Raise ValueError if required settings are missing."""
        if not self.database:
            raise ValueError("MSSQL_DATABASE environment variable is required")
        if not self.windows_auth and (not self.user or not self.password):
            raise ValueError(
                "MSSQL_USER and MSSQL_PASSWORD are required when MSSQL_WINDOWS_AUTH is false"
            )
