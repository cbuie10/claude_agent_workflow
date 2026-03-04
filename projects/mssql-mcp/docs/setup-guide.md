# Setup Guide

Step-by-step instructions for getting the MSSQL MCP server running with Claude Code.

## Prerequisites

### 1. Python 3.12+

Check your version:
```bash
python --version
```

We recommend using [uv](https://docs.astral.sh/uv/) for dependency management:
```bash
# Install uv (if not already installed)
pip install uv
```

### 2. ODBC Driver 17 for SQL Server

The server uses pyodbc, which requires Microsoft's ODBC driver.

**Windows:**
Download and install from [Microsoft's download page](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server).

**Verify installation:**
```bash
python -c "import pyodbc; print(pyodbc.drivers())"
```

You should see `ODBC Driver 17 for SQL Server` (or 18) in the list.

### 3. SQL Server Access

You need:
- Server hostname or IP address
- Database name
- Credentials (SQL auth username/password OR Windows/AD account with access)

## Installation

```bash
# Navigate to the project
cd projects/mssql-mcp

# Install dependencies
uv sync --all-extras
```

## Configuration

### Option A: Environment File

```bash
cp .env.example .env
```

Edit `.env` with your connection details:
```env
MSSQL_HOST=your-server.database.windows.net
MSSQL_DATABASE=your_database
MSSQL_USER=your_username
MSSQL_PASSWORD=your_password
```

For Windows Authentication:
```env
MSSQL_HOST=your-server
MSSQL_DATABASE=your_database
MSSQL_WINDOWS_AUTH=true
```

### Option B: Claude Code Settings (Recommended for Teams)

Add the server config to `~/.claude/settings.json`. This way Claude Code starts the server automatically — no need to run it manually.

```json
{
  "mcpServers": {
    "mssql": {
      "command": "uv",
      "args": ["run", "python", "-m", "mssql_mcp.server"],
      "cwd": "C:/Users/yourname/path/to/projects/mssql-mcp",
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

> **Security note**: Credentials in `settings.json` are stored on your local machine. For shared environments, consider using environment variables or a secrets manager instead.

## Verify It Works

### Test the connection directly

```bash
cd projects/mssql-mcp
uv run python -c "
from mssql_mcp.config import Config
from mssql_mcp.database import get_connection
cfg = Config()
cfg.validate()
conn = get_connection(cfg)
cursor = conn.cursor()
cursor.execute('SELECT @@VERSION')
print(cursor.fetchone()[0])
conn.close()
print('Connected successfully!')
"
```

### Test via Claude Code

After adding the MCP config and restarting Claude Code, try:

```
> What databases are on this server?
> Switch to the sales database
> List all tables in my database
> Describe the users table
> SELECT TOP 5 * FROM dbo.orders
```

Claude will automatically use the MCP tools to query your database.

## Working with Multiple Databases

The server connects to one database at a time (configured by `MSSQL_DATABASE`), but you can switch between any database on the server during a conversation:

```
> What databases are available?        # calls list_databases()
> Switch to the analytics database     # calls use_database("analytics")
> Show me the tables                   # now queries analytics
> Switch to the sales database         # calls use_database("sales")
```

You can also query across databases without switching by using three-part names:

```
> SELECT TOP 5 * FROM [analytics].[dbo].[events]
```

The active database resets to the configured default when the MCP server restarts (i.e., when you restart Claude Code).

## Troubleshooting

### "Can't open lib 'ODBC Driver 17 for SQL Server'"

The ODBC driver isn't installed. Download it from [Microsoft](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server).

### "Login failed for user"

- Double-check your `MSSQL_USER` and `MSSQL_PASSWORD`
- Ensure the user has access to the specified `MSSQL_DATABASE`
- If using Windows auth, set `MSSQL_WINDOWS_AUTH=true` and remove user/password

### "TCP Provider: No connection could be made"

- Verify `MSSQL_HOST` and `MSSQL_PORT` are correct
- Check that SQL Server is running and accepting TCP connections
- Check firewall rules

### MCP tools don't appear in Claude Code

- Ensure the `cwd` path in settings.json points to the `projects/mssql-mcp` directory
- Restart Claude Code after changing settings
- Check Claude Code logs for MCP connection errors

## Read-Only vs Read-Write

By default, the server only allows SELECT queries. To enable write operations:

```env
MSSQL_READ_ONLY=false
```

> **Warning**: Enabling write access means Claude can INSERT, UPDATE, DELETE, and run DDL statements. Use a database user with appropriate permissions and consider using a non-production database for testing.
