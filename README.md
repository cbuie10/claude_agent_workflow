# Claude Agent Workflow

A knowledge repo for the Warwick team — learning and building with Claude Code, MCP servers, and autonomous AI agents.

## Projects

| Project | Description | Status |
|---------|-------------|--------|
| [Prefect ETL](projects/prefect-etl/) | Autonomous data pipeline system where Claude builds ETL pipelines from GitHub Issues | Production |
| [MSSQL MCP Server](projects/mssql-mcp/) | Custom MCP server for SQL Server — gives Claude direct database access | In Development |

## Quick Navigation

### Prefect ETL Pipeline
Autonomous ETL system: create a GitHub Issue, Claude writes the pipeline code, opens a PR.

```bash
cd projects/prefect-etl
uv sync --all-extras
docker compose -f docker/docker-compose.yml up -d
uv run python -m pipeline.flows.earthquake_flow
```

See [projects/prefect-etl/README.md](projects/prefect-etl/README.md) for full docs.

### MSSQL MCP Server
A FastMCP-based server that connects Claude Code to SQL Server databases.

```bash
cd projects/mssql-mcp
uv sync --all-extras
# Configure .env with your SQL Server connection
python -m mssql_mcp.server
```

See [projects/mssql-mcp/README.md](projects/mssql-mcp/README.md) for full docs.

## Shared Documentation

| Guide | Description |
|-------|-------------|
| [Claude Agent Guide](docs/claude-agent-guide.md) | How claude-code-action works with GitHub Issues and PRs |

## Repo Structure

```
claude_agent_workflow/
├── projects/
│   ├── prefect-etl/           # Prefect v3 ETL pipelines
│   │   ├── src/pipeline/      # Source code
│   │   ├── tests/             # 52 unit tests
│   │   ├── docs/              # ETL-specific guides
│   │   └── docker/            # PostgreSQL + Prefect server
│   └── mssql-mcp/             # MSSQL MCP server
│       ├── src/mssql_mcp/     # FastMCP server source
│       ├── tests/             # Server tests
│       └── docs/              # MCP guides for the team
├── docs/                      # Shared knowledge docs
├── .github/workflows/         # CI + Claude agent
├── CLAUDE.md                  # Agent instructions
└── README.md                  # This file
```

## Development

Each project has its own `pyproject.toml` and dependency set. Work within project directories:

```bash
# ETL project
cd projects/prefect-etl && uv sync --all-extras && uv run pytest tests/ -v

# MCP project
cd projects/mssql-mcp && uv sync --all-extras && uv run pytest tests/ -v
```
