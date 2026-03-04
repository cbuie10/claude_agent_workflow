# CLAUDE.md — Agent Instructions

## Repo Overview
Multi-project knowledge repo. Each project lives under `projects/` with its own
pyproject.toml, tests, and docs. Python 3.12, managed with uv.

## Commands (run from project directories)

### Prefect ETL (`projects/prefect-etl/`)
- Install: `cd projects/prefect-etl && uv sync --all-extras`
- Lint: `cd projects/prefect-etl && uv run ruff check src/ tests/`
- Test: `cd projects/prefect-etl && uv run pytest tests/ -v`
- Run a flow: `cd projects/prefect-etl && uv run python -m pipeline.flows.<flow_module>`

### MSSQL MCP (`projects/mssql-mcp/`)
- Install: `cd projects/mssql-mcp && uv sync --all-extras`
- Lint: `cd projects/mssql-mcp && uv run ruff check src/ tests/`
- Test: `cd projects/mssql-mcp && uv run pytest tests/ -v`
- Run server: `cd projects/mssql-mcp && python -m mssql_mcp.server`

## Project Structure
- `projects/prefect-etl/` — Prefect v3 ETL pipeline project
- `projects/mssql-mcp/` — FastMCP server for SQL Server
- `docs/` — Shared documentation

## Conventions for Prefect ETL
See `projects/prefect-etl/CLAUDE.md` or the reference implementation
`projects/prefect-etl/src/pipeline/flows/earthquake_flow.py`.

### Code style (all projects)
- Type hints on all function signatures
- Every public function must have a docstring
- Use `ruff` for linting (line-length 100)
- Use `pytest` for testing, mock external dependencies

## Conventions for MSSQL MCP
- Tools go in `projects/mssql-mcp/src/mssql_mcp/server.py`
- DB connection logic in `database.py`, config in `config.py`
- Environment variables for all connection settings (never hardcode)
- Read-only mode is the default — write operations require explicit opt-in

## Git Conventions
- Use **single-line** commit messages: `git commit -m "Short description of changes"`
- Do NOT use multiline commit messages
- Do NOT add Co-authored-by trailers
- Keep commit messages under 100 characters

## Do NOT
- Do not modify `projects/prefect-etl/docker/docker-compose.yml` unless explicitly asked
- Do not add new dependencies without mentioning in the PR description
- Do not write integration tests that require running services — mock all external calls
