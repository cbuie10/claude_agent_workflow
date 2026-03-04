# Architecture: How MCP Works

This document explains the Model Context Protocol (MCP) for team members who want to understand what's happening under the hood.

## What is MCP?

MCP (Model Context Protocol) is an open standard created by Anthropic that lets AI tools (like Claude Code) connect to external data sources and services. Think of it like a **USB port for AI** — a standardized way to plug in new capabilities.

```
Without MCP:                        With MCP:
You copy data from DB        -->    Claude queries the DB directly
You paste it into chat              using tools you defined
Claude analyzes it                  No copy-paste needed
```

## The Architecture

```
┌──────────────┐     stdio (JSON-RPC)     ┌──────────────┐     pyodbc/ODBC     ┌──────────────┐
│              │ ◄──────────────────────► │              │ ◄────────────────► │              │
│  Claude Code │     tool calls &         │  MCP Server  │     SQL queries    │  SQL Server  │
│  (MCP Client)│     results              │  (FastMCP)   │     & results      │  (Database)  │
│              │                          │              │                    │              │
└──────────────┘                          └──────────────┘                    └──────────────┘
    AI Agent                              Your Python code                    Your data
```

### Key Components

**MCP Client** (Claude Code)
- Discovers available tools from the server
- Decides when to call a tool based on your conversation
- Sends tool call requests as JSON-RPC messages over stdio

**MCP Server** (this project)
- Defines tools with names, descriptions, and parameter schemas
- Receives tool call requests from the client
- Executes the requested operation (e.g., SQL query)
- Returns results to the client

**Transport** (stdio)
- Communication happens over standard input/output
- Claude Code launches the server as a subprocess
- Messages are JSON-RPC formatted

## How a Query Flows

```
1. You ask: "How many orders were placed last month?"

2. Claude Code decides to use the `query` tool

3. Claude Code sends over stdio:
   {
     "method": "tools/call",
     "params": {
       "name": "query",
       "arguments": {
         "sql": "SELECT COUNT(*) AS order_count FROM orders WHERE order_date >= '2026-02-01'"
       }
     }
   }

4. MCP Server receives the request:
   - Checks read-only safety (SELECT is allowed)
   - Opens pyodbc connection to SQL Server
   - Executes the query
   - Formats results as a table

5. MCP Server returns over stdio:
   {
     "content": [
       { "type": "text", "text": "order_count\n-----------\n1,247" }
     ]
   }

6. Claude Code reads the result and responds:
   "There were 1,247 orders placed last month."
```

## FastMCP

[FastMCP](https://github.com/jlowin/fastmcp) is a Python framework that handles all the protocol details. Instead of implementing JSON-RPC yourself, you just write Python functions with decorators:

```python
from fastmcp import FastMCP

mcp = FastMCP("My Server")

@mcp.tool()
def my_tool(param: str) -> str:
    """Description of what this tool does."""
    return do_something(param)

mcp.run()  # Starts listening on stdio
```

FastMCP automatically:
- Generates the tool schema from your function signature and type hints
- Handles JSON-RPC serialization/deserialization
- Manages the stdio transport
- Reports errors back to the client

## Security Model

### Read-Only Mode
By default, the server blocks any SQL that contains write keywords (INSERT, UPDATE, DELETE, DROP, etc.). This is a first line of defense — you should also use a database user with restricted permissions.

### Query Timeouts
Queries are killed after a configurable timeout (default 30s) to prevent runaway queries from locking the database.

### Row Limits
Results are capped at a configurable maximum (default 10,000 rows) to prevent the AI from pulling massive datasets into memory.

### Credential Isolation
Database credentials are stored in environment variables or Claude Code's local settings file — never in source code.

## Multi-Database Support

The server connects to one SQL Server instance but can access any database on it:

- **`list_databases()`** queries `sys.databases` from master to discover all databases
- **`use_database(name)`** switches the active database by opening new connections to the specified database
- **Three-part names** like `[other_db].[dbo].[table]` work in any query without switching

The active database is stored as module-level state (`_active_database`) and resets when the server process restarts. All tools pass the active database to `get_connection()` and `execute_query()` via the `database` parameter, which overrides the configured default in the connection string.

## How Claude Code Discovers Tools

When Claude Code starts, it reads `~/.claude/settings.json` for MCP server configurations. For each server, it:

1. Launches the subprocess using the configured `command` and `args`
2. Sends a `tools/list` request to discover available tools
3. Registers those tools so they can be used during conversation

This happens automatically — you don't need to tell Claude which tools to use. It decides based on your questions and the tool descriptions.
