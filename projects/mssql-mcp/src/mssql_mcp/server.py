"""FastMCP server exposing SQL Server tools to Claude Code.

Run directly:
    python -m mssql_mcp.server

Or register in Claude Code settings:
    {
        "mcpServers": {
            "mssql": {
                "command": "python",
                "args": ["-m", "mssql_mcp.server"],
                "cwd": "path/to/projects/mssql-mcp"
            }
        }
    }
"""

from __future__ import annotations

import json
from typing import Annotated

from fastmcp import FastMCP

from mssql_mcp.config import Config
from mssql_mcp.database import execute_query, get_connection

# ---------------------------------------------------------------------------
# Server setup
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "MSSQL Server",
    instructions=(
        "MCP server for querying Microsoft SQL Server databases. "
        "Use the available tools to explore schemas, list tables, "
        "describe columns, and run SQL queries."
    ),
)

# Load config once at startup
_cfg = Config()

# Active database — starts as the configured default, can be changed with use_database()
_active_database: str | None = None


def _get_active_db() -> str:
    """Return the currently active database name."""
    return _active_database or _cfg.database


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _format_results(rows: list[dict], max_display: int = 50) -> str:
    """Format query results as a readable table string."""
    if not rows:
        return "No results returned."

    # Get column names from first row
    columns = list(rows[0].keys())
    display_rows = rows[:max_display]

    # Calculate column widths
    widths = {col: len(str(col)) for col in columns}
    for row in display_rows:
        for col in columns:
            widths[col] = max(widths[col], len(str(row.get(col, ""))))

    # Build table
    header = " | ".join(str(col).ljust(widths[col]) for col in columns)
    separator = "-+-".join("-" * widths[col] for col in columns)
    lines = [header, separator]

    for row in display_rows:
        line = " | ".join(str(row.get(col, "")).ljust(widths[col]) for col in columns)
        lines.append(line)

    result = "\n".join(lines)
    if len(rows) > max_display:
        result += f"\n\n... showing {max_display} of {len(rows)} rows"
    elif len(rows) == _cfg.max_rows:
        result += f"\n\n... result capped at max_rows={_cfg.max_rows}"

    return result


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def query(
    sql: Annotated[str, "The SQL query to execute"],
) -> str:
    """Execute a SQL query against the active database.

    Returns results as a formatted table. By default the server runs in
    read-only mode — only SELECT queries are allowed. Set MSSQL_READ_ONLY=false
    to enable write operations.

    Tip: You can query across databases using three-part names like
    [other_db].[schema].[table] without switching databases.
    """
    rows = execute_query(_cfg, sql, database=_get_active_db())
    return _format_results(rows)


@mcp.tool()
def list_tables(
    schema: Annotated[str, "Schema name to list tables from"] = "dbo",
) -> str:
    """List all tables in the specified schema with their row counts."""
    sql = """
        SELECT
            t.TABLE_SCHEMA   AS [schema],
            t.TABLE_NAME     AS [table],
            p.rows           AS [row_count]
        FROM INFORMATION_SCHEMA.TABLES t
        JOIN sys.tables st
            ON st.name = t.TABLE_NAME
        JOIN sys.partitions p
            ON p.object_id = st.object_id AND p.index_id IN (0, 1)
        WHERE t.TABLE_SCHEMA = ?
          AND t.TABLE_TYPE = 'BASE TABLE'
        ORDER BY t.TABLE_NAME
    """
    rows = execute_query(_cfg, sql, params=(schema,), database=_get_active_db())
    return _format_results(rows)


@mcp.tool()
def list_schemas() -> str:
    """List all schemas in the active database."""
    sql = """
        SELECT
            s.name           AS [schema],
            COUNT(t.name)    AS [table_count]
        FROM sys.schemas s
        LEFT JOIN sys.tables t ON t.schema_id = s.schema_id
        GROUP BY s.name
        HAVING COUNT(t.name) > 0
        ORDER BY s.name
    """
    rows = execute_query(_cfg, sql, database=_get_active_db())
    return _format_results(rows)


@mcp.tool()
def describe_table(
    table: Annotated[str, "Table name to describe"],
    schema: Annotated[str, "Schema the table belongs to"] = "dbo",
) -> str:
    """Get column definitions for a table — names, types, nullability, and primary keys."""
    sql = """
        SELECT
            c.COLUMN_NAME                                     AS [column],
            c.DATA_TYPE                                       AS [type],
            COALESCE(CAST(c.CHARACTER_MAXIMUM_LENGTH AS VARCHAR), '') AS [max_length],
            c.IS_NULLABLE                                     AS [nullable],
            CASE WHEN pk.COLUMN_NAME IS NOT NULL THEN 'YES' ELSE 'NO' END AS [primary_key],
            COALESCE(c.COLUMN_DEFAULT, '')                    AS [default]
        FROM INFORMATION_SCHEMA.COLUMNS c
        LEFT JOIN (
            SELECT ku.TABLE_SCHEMA, ku.TABLE_NAME, ku.COLUMN_NAME
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE ku
                ON tc.CONSTRAINT_NAME = ku.CONSTRAINT_NAME
            WHERE tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
        ) pk
            ON pk.TABLE_SCHEMA = c.TABLE_SCHEMA
            AND pk.TABLE_NAME  = c.TABLE_NAME
            AND pk.COLUMN_NAME = c.COLUMN_NAME
        WHERE c.TABLE_SCHEMA = ?
          AND c.TABLE_NAME   = ?
        ORDER BY c.ORDINAL_POSITION
    """
    rows = execute_query(_cfg, sql, params=(schema, table), database=_get_active_db())
    if not rows:
        return f"Table [{schema}].[{table}] not found."
    return _format_results(rows)


@mcp.tool()
def get_database_info() -> str:
    """Get server and database metadata — version, name, collation, size.

    Shows info for the currently active database.
    """
    sql = """
        SELECT
            @@SERVERNAME                          AS [server_name],
            @@VERSION                             AS [version],
            DB_NAME()                             AS [database],
            SERVERPROPERTY('Collation')           AS [collation],
            SERVERPROPERTY('Edition')             AS [edition],
            (SELECT SUM(size) * 8 / 1024
             FROM sys.database_files)             AS [size_mb]
    """
    rows = execute_query(_cfg, sql, database=_get_active_db())
    if not rows:
        return "Could not retrieve database info."

    info = rows[0]
    lines = [f"{key}: {value}" for key, value in info.items()]
    return "\n".join(lines)


@mcp.tool()
def check_connection() -> str:
    """Test database connectivity. Returns connection status, active database, and server version."""
    try:
        conn = get_connection(_cfg, database=_get_active_db())
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()[0]
        conn.close()
        return f"Connected successfully.\nActive database: {_get_active_db()}\n\n{version}"
    except Exception as e:
        return f"Connection failed: {e}"


@mcp.tool()
def list_databases() -> str:
    """List all databases on the server with their size and status.

    Useful for discovering available databases before switching with use_database().
    """
    sql = """
        SELECT
            d.name                              AS [database],
            d.state_desc                        AS [status],
            CAST(SUM(f.size) * 8 / 1024.0 AS DECIMAL(10, 1)) AS [size_mb],
            d.create_date                       AS [created]
        FROM sys.databases d
        LEFT JOIN sys.master_files f ON f.database_id = d.database_id
        GROUP BY d.name, d.state_desc, d.create_date
        ORDER BY d.name
    """
    # Query sys.databases from master to see all databases on the server
    rows = execute_query(_cfg, sql, database="master")
    active = _get_active_db()
    result = _format_results(rows)
    return f"Active database: {active}\n\n{result}"


@mcp.tool()
def use_database(
    database: Annotated[str, "Name of the database to switch to"],
) -> str:
    """Switch the active database for all subsequent tool calls.

    This changes which database is queried by query(), list_tables(),
    list_schemas(), describe_table(), and get_database_info().
    Use list_databases() first to see available databases.
    """
    global _active_database

    # Verify the database exists and is accessible
    try:
        conn = get_connection(_cfg, database=database)
        cursor = conn.cursor()
        cursor.execute("SELECT DB_NAME()")
        confirmed = cursor.fetchone()[0]
        conn.close()
    except Exception as e:
        return f"Failed to switch to database [{database}]: {e}"

    _active_database = database
    return f"Switched to database [{confirmed}]. All tools will now query this database."


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Start the MCP server."""
    _cfg.validate()
    mcp.run()


if __name__ == "__main__":
    main()
