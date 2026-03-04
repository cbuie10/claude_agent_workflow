# Adding New Tools

This guide shows how to extend the MCP server with new tools.

## The Pattern

Every tool follows the same pattern in `src/mssql_mcp/server.py`:

```python
@mcp.tool()
def tool_name(
    param: Annotated[str, "Description of this parameter"],
    optional_param: Annotated[int, "Optional with default"] = 10,
) -> str:
    """One-line description that Claude sees when deciding whether to use this tool.

    More detail here if needed — Claude reads this to understand when
    and how to call the tool.
    """
    rows = execute_query(_cfg, "SELECT ...", params=(param,))
    return _format_results(rows)
```

### Key Points

1. **Decorator**: `@mcp.tool()` registers the function as an MCP tool
2. **Type hints**: FastMCP generates the parameter schema from your type hints
3. **Annotated descriptions**: Use `Annotated[type, "description"]` to document parameters
4. **Docstring**: Claude reads this to decide when to call the tool — make it descriptive
5. **Return type**: Always return a `str` — Claude needs text it can read

## Example: Adding a "table_row_counts" Tool

Let's add a tool that shows row counts for all tables in the database.

### Step 1: Write the Tool

Add to `src/mssql_mcp/server.py`:

```python
@mcp.tool()
def table_row_counts() -> str:
    """Get row counts for all tables in the database, sorted by size."""
    sql = """
        SELECT
            s.name       AS [schema],
            t.name       AS [table],
            p.rows       AS [row_count]
        FROM sys.tables t
        JOIN sys.schemas s ON s.schema_id = t.schema_id
        JOIN sys.partitions p ON p.object_id = t.object_id AND p.index_id IN (0, 1)
        ORDER BY p.rows DESC
    """
    rows = execute_query(_cfg, sql)
    return _format_results(rows)
```

### Step 2: Write a Test

Add to `tests/test_server.py`:

```python
class TestTableRowCounts:
    @patch("mssql_mcp.server.execute_query")
    def test_returns_formatted_results(self, mock_execute):
        mock_execute.return_value = [
            {"schema": "dbo", "table": "orders", "row_count": 50000},
            {"schema": "dbo", "table": "users", "row_count": 1200},
        ]
        result = table_row_counts()
        assert "orders" in result
        assert "50000" in result
```

### Step 3: Test and Lint

```bash
uv run pytest tests/ -v
uv run ruff check src/ tests/
```

### Step 4: Restart Claude Code

After adding the tool, restart Claude Code so it re-discovers the available tools. Your new tool will appear automatically.

## Tips

- **Keep tools focused** — one tool should do one thing well
- **Use parameterized queries** — never interpolate user input into SQL strings
- **Return readable text** — Claude needs to understand the output to answer questions
- **Add safety checks** — use `check_write_safety()` if your tool runs user-provided SQL
- **Document clearly** — Claude decides which tool to call based on the docstring

## Common Patterns

### Tool that accepts a SQL WHERE clause
```python
@mcp.tool()
def search_orders(
    where_clause: Annotated[str, "SQL WHERE clause, e.g. 'status = ?'"],
    params: Annotated[str, "Comma-separated parameter values"] = "",
) -> str:
    """Search orders with a custom filter."""
    param_tuple = tuple(p.strip() for p in params.split(",")) if params else ()
    sql = f"SELECT TOP 100 * FROM orders WHERE {where_clause}"
    rows = execute_query(_cfg, sql, params=param_tuple)
    return _format_results(rows)
```

### Tool that returns JSON instead of a table
```python
import json

@mcp.tool()
def table_stats(table: Annotated[str, "Table name"]) -> str:
    """Get statistics for a table as JSON."""
    rows = execute_query(_cfg, f"SELECT COUNT(*) as cnt FROM [{table}]")
    return json.dumps(rows, indent=2, default=str)
```
