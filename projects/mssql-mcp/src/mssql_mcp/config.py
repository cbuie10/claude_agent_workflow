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


def _make_config(prefix: str = "MSSQL") -> type:
    """Create a Config dataclass that reads env vars with the given prefix.

    Default prefix is ``MSSQL`` → ``MSSQL_HOST``, ``MSSQL_PORT``, etc.
    A custom prefix like ``DBARIES`` → ``DBARIES_HOST``, ``DBARIES_PORT``, etc.
    """

    @dataclass(frozen=True)
    class Config:
        """Immutable server configuration."""

        # Connection
        host: str = field(default_factory=lambda: os.getenv(f"{prefix}_HOST", "localhost"))
        port: int = field(default_factory=lambda: int(os.getenv(f"{prefix}_PORT", "1433")))
        database: str = field(default_factory=lambda: os.getenv(f"{prefix}_DATABASE", ""))
        user: str = field(default_factory=lambda: os.getenv(f"{prefix}_USER", ""))
        password: str = field(default_factory=lambda: os.getenv(f"{prefix}_PASSWORD", ""))
        driver: str = field(
            default_factory=lambda: os.getenv(
                f"{prefix}_DRIVER", "ODBC Driver 17 for SQL Server"
            )
        )

        # Authentication
        windows_auth: bool = field(
            default_factory=lambda: _bool(os.getenv(f"{prefix}_WINDOWS_AUTH", "false"))
        )

        # Safety
        read_only: bool = field(
            default_factory=lambda: _bool(os.getenv(f"{prefix}_READ_ONLY", "true"))
        )

        # Limits
        query_timeout: int = field(
            default_factory=lambda: int(os.getenv(f"{prefix}_QUERY_TIMEOUT", "30"))
        )
        max_rows: int = field(
            default_factory=lambda: int(os.getenv(f"{prefix}_MAX_ROWS", "10000"))
        )

        def validate(self) -> None:
            """Raise ValueError if required settings are missing."""
            if not self.database:
                raise ValueError(f"{prefix}_DATABASE environment variable is required")
            if not self.windows_auth and (not self.user or not self.password):
                raise ValueError(
                    f"{prefix}_USER and {prefix}_PASSWORD are required "
                    f"when {prefix}_WINDOWS_AUTH is false"
                )

    return Config


# Default Config class using MSSQL_ prefix (backwards compatible)
Config = _make_config("MSSQL")

