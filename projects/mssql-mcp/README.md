# MSSQL MCP Server

A custom [Model Context Protocol](https://modelcontextprotocol.io/) server that gives Claude Code (and other MCP clients) direct access to Microsoft SQL Server databases.

Built with [FastMCP](https://github.com/jlowin/fastmcp) and [pyodbc](https://github.com/mkleehammer/pyodbc).

## What It Does

When this server is running, Claude Code gets these database tools:

| Tool | Description |
|------|-------------|
| `query` | Execute SQL queries (read-only by default) |
| `list_databases` | List all databases on the server with size and status |
| `use_database` | Switch the active database for all subsequent queries |
| `list_tables` | List all tables in a schema with row counts |
| `list_schemas` | List all database schemas |
| `describe_table` | Get column names, types, nullability, primary keys |
| `get_database_info` | Server version, database name, edition, size |
| `check_connection` | Test connectivity to the database |

## How It Works

```
You (in chat)  -->  Claude Code  -->  MCP Server (this project)  -->  SQL Server
                                       runs as a subprocess
                                       Claude starts it automatically
```

The MCP server runs as a **subprocess** that Claude Code launches on demand. Claude sends tool calls over stdio, the server executes them against SQL Server via pyodbc, and returns results.

## Quick Start

### Prerequisites
- Python 3.12+
- [ODBC Driver 17 for SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)
- Access to a SQL Server instance

### Install

```bash
cd projects/mssql-mcp
uv sync --all-extras
```

### Configure

```bash
cp .env.example .env
# Edit .env with your SQL Server connection details
```

### Register with Claude Code

Add to your `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "mssql": {
      "command": "uv",
      "args": ["run", "python", "-m", "mssql_mcp.server"],
      "cwd": "C:/path/to/projects/mssql-mcp",
      "env": {
        "MSSQL_HOST": "your-server",
        "MSSQL_DATABASE": "your-database",
        "MSSQL_USER": "your-user",
        "MSSQL_PASSWORD": "your-password"
      }
    }
  }
}
```

Or for **Windows Authentication**:

```json
{
  "mcpServers": {
    "mssql": {
      "command": "uv",
      "args": ["run", "python", "-m", "mssql_mcp.server"],
      "cwd": "C:/path/to/projects/mssql-mcp",
      "env": {
        "MSSQL_HOST": "your-server",
        "MSSQL_DATABASE": "your-database",
        "MSSQL_WINDOWS_AUTH": "true"
      }
    }
  }
}
```

### Verify

Restart Claude Code. You should be able to ask things like:
- "What databases are on this server?"
- "Switch to the sales database"
- "List all tables in my database"
- "Describe the users table"
- "Show me the top 10 rows from orders"

**Note**: `MSSQL_DATABASE` is the *starting* database. You can switch between any database on the server using `use_database()` during a conversation.

## Safety Features

- **Read-only by default** — only SELECT queries allowed until you set `MSSQL_READ_ONLY=false`
- **Query timeout** — queries are killed after 30 seconds (configurable)
- **Row limits** — results capped at 10,000 rows (configurable)
- **Keyword blocking** — DROP, TRUNCATE, ALTER, etc. are blocked in read-only mode

## Configuration Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `MSSQL_HOST` | `localhost` | Server hostname or IP |
| `MSSQL_PORT` | `1433` | Server port |
| `MSSQL_DATABASE` | *(required)* | Default database (can switch at runtime) |
| `MSSQL_USER` | | Username (SQL auth) |
| `MSSQL_PASSWORD` | | Password (SQL auth) |
| `MSSQL_DRIVER` | `ODBC Driver 17 for SQL Server` | ODBC driver name |
| `MSSQL_WINDOWS_AUTH` | `false` | Use Windows/AD authentication |
| `MSSQL_READ_ONLY` | `true` | Block write operations |
| `MSSQL_QUERY_TIMEOUT` | `30` | Query timeout in seconds |
| `MSSQL_MAX_ROWS` | `10000` | Max rows per query |

## Development

```bash
# Run tests
uv run pytest tests/ -v

# Lint
uv run ruff check src/ tests/
```

## Documentation

| Guide | Description |
|-------|-------------|
| [Setup Guide](docs/setup-guide.md) | Full installation and team onboarding |
| [Architecture](docs/architecture.md) | How MCP works — concepts for the team |
| [Adding Tools](docs/adding-tools.md) | How to extend the server with new tools |
