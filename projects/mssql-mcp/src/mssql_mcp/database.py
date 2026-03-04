"""Database connection and query execution for SQL Server.

Uses pyodbc to connect via ODBC Driver 17. Supports both SQL
authentication (user/password) and Windows authentication
(Trusted_Connection).
"""

from __future__ import annotations

import re
from typing import Any

import pyodbc

from mssql_mcp.config import Config

# Keywords that are blocked in read-only mode
_WRITE_KEYWORDS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER|CREATE|EXEC|EXECUTE|MERGE|GRANT|REVOKE|DENY)\b",
    re.IGNORECASE,
)


def build_connection_string(cfg: Config, database: str | None = None) -> str:
    """Build a pyodbc connection string from config.

    Args:
        cfg: Server configuration.
        database: Override the database name. If None, uses cfg.database.

    Returns a semicolon-delimited ODBC connection string.
    Uses Trusted_Connection for Windows auth, or UID/PWD for SQL auth.
    """
    db = database or cfg.database
    parts = [
        f"DRIVER={{{cfg.driver}}}",
        f"SERVER={cfg.host},{cfg.port}",
        f"DATABASE={db}",
    ]

    if cfg.windows_auth:
        parts.append("Trusted_Connection=yes")
    else:
        parts.append(f"UID={cfg.user}")
        parts.append(f"PWD={cfg.password}")

    parts.append("TrustServerCertificate=yes")
    return ";".join(parts)


def get_connection(cfg: Config, database: str | None = None) -> pyodbc.Connection:
    """Open a pyodbc connection with the configured timeout.

    Args:
        cfg: Server configuration.
        database: Override the database name. If None, uses cfg.database.
    """
    conn_str = build_connection_string(cfg, database=database)
    conn = pyodbc.connect(conn_str, timeout=cfg.query_timeout)
    conn.timeout = cfg.query_timeout
    return conn


def check_write_safety(sql: str, read_only: bool) -> None:
    """Raise ValueError if the query contains write operations in read-only mode."""
    if read_only and _WRITE_KEYWORDS.search(sql):
        raise ValueError(
            f"Write operations are blocked in read-only mode. "
            f"Set MSSQL_READ_ONLY=false to allow write queries. "
            f"Blocked query: {sql[:100]}..."
        )


def execute_query(
    cfg: Config,
    sql: str,
    params: tuple[Any, ...] | None = None,
    database: str | None = None,
) -> list[dict[str, Any]]:
    """Execute a SQL query and return results as a list of dicts.

    Args:
        cfg: Server configuration.
        sql: The SQL query to execute.
        params: Optional query parameters for parameterized queries.
        database: Override the database to query. If None, uses the active database.

    Returns:
        List of dicts where keys are column names.

    Raises:
        ValueError: If the query is blocked by read-only mode.
        pyodbc.Error: If the query fails at the database level.
    """
    check_write_safety(sql, cfg.read_only)

    conn = get_connection(cfg, database=database)
    try:
        cursor = conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)

        # If the query doesn't return rows (e.g. INSERT), return affected count
        if cursor.description is None:
            row_count = cursor.rowcount
            conn.commit()
            return [{"affected_rows": row_count}]

        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchmany(cfg.max_rows)
        return [dict(zip(columns, row)) for row in rows]
    finally:
        conn.close()
