# Claude Agent Workflow

An autonomous data pipeline system where a Claude AI agent builds ETL pipelines from GitHub Issues. You describe what data you want in an issue, Claude writes the Python code and tests, and submits a pull request for your review.

## How It Works

```
GitHub Issue          Claude Agent           Pull Request          You
"Build a weather  --> reads issue +      --> creates branch,   --> review,
 data pipeline"       CLAUDE.md,              writes code,        request
                      writes ETL code,        opens PR            changes,
                      runs tests                                  merge
```

1. **You create a GitHub Issue** describing a new data pipeline (API source, target table, transforms)
2. **Claude agent triggers** via GitHub Actions, reads the issue and `CLAUDE.md` for conventions
3. **Claude writes code** — extract/transform/load tasks, a Prefect flow, tests, and SQL schema
4. **CI runs automatically** — linting (ruff) and tests (pytest) must pass
5. **You review the PR** — approve, request changes with `@claude fix XYZ`, or close
6. **Merge and run** — pull locally and execute the new pipeline

## Tech Stack

| Component | Tool |
|-----------|------|
| Language | Python 3.12 (managed with [uv](https://docs.astral.sh/uv/)) |
| Database | PostgreSQL 16 (Docker) |
| Orchestration | [Prefect v3](https://docs.prefect.io/) |
| AI Agent | [claude-code-action](https://github.com/anthropics/claude-code-action) |
| CI | GitHub Actions |
| Linter | ruff |
| Tests | pytest |

## Current Pipelines

### Earthquake ETL
- **Source**: [USGS Earthquake API](https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson) (real-time, no auth required)
- **Table**: `earthquakes` — magnitude, location, depth, timestamps
- **Run**: `uv run python -m pipeline.flows.earthquake_flow`

### Weather Forecast ETL
- **Source**: [Open-Meteo API](https://open-meteo.com/) (free, no auth required)
- **Table**: `weather_forecasts` — temperature, humidity, wind speed (hourly, NYC)
- **Run**: `uv run python -m pipeline.flows.weather_flow`

## Quick Start

```bash
# Prerequisites: Docker, Python 3.12, uv (https://docs.astral.sh/uv/)

# Clone and install
git clone https://github.com/cbuie10/claude_agent_workflow.git
cd claude_agent_workflow
uv sync --all-extras

# Start PostgreSQL
docker compose -f docker/docker-compose.yml up -d

# Run a pipeline
uv run python -m pipeline.flows.earthquake_flow

# Run tests
uv run pytest tests/ -v
```

## Project Structure

```
claude_agent_workflow/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                # Lint + test on push/PR
│   │   └── claude.yml            # Claude agent trigger
│   └── ISSUE_TEMPLATE/
│       └── pipeline_request.md   # Structured issue template
├── docker/
│   ├── docker-compose.yml        # PostgreSQL container
│   └── init.sql                  # Table definitions
├── src/pipeline/
│   ├── config.py                 # Environment variable config
│   ├── db.py                     # DB connection helper
│   ├── flows/
│   │   ├── earthquake_flow.py    # Earthquake ETL flow
│   │   └── weather_flow.py       # Weather forecast ETL flow
│   └── tasks/
│       ├── extract.py            # API fetch tasks
│       ├── transform.py          # Data reshaping tasks
│       └── load.py               # PostgreSQL upsert tasks
├── tests/                        # 24 unit + integration tests
├── docs/                         # Detailed guides
├── CLAUDE.md                     # Agent instructions
└── pyproject.toml                # Dependencies and tool config
```

## Documentation

| Guide | Description |
|-------|-------------|
| [Getting Started](docs/getting-started.md) | Prerequisites, installation, first pipeline run |
| [Docker & PostgreSQL](docs/docker-guide.md) | Container management, connecting to the database, querying data |
| [Querying Data](docs/querying-data.md) | SQL examples for exploring earthquake and weather data |
| [Claude Agent Guide](docs/claude-agent-guide.md) | How the autonomous agent works, creating issues, reviewing PRs |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+psycopg2://pipeline_user:pipeline_pass@localhost:5432/pipeline_db` | PostgreSQL connection string |
| `EARTHQUAKE_API_URL` | USGS all-hour feed | Earthquake data source |
| `WEATHER_API_URL` | Open-Meteo NYC forecast | Weather data source |
| `MIN_MAGNITUDE` | `0.0` | Minimum earthquake magnitude to load |

## Development

```bash
# Lint
uv run ruff check src/ tests/

# Auto-fix lint issues
uv run ruff check --fix src/ tests/

# Run tests
uv run pytest tests/ -v
```

## Creating a New Pipeline via GitHub Issue

1. Go to **Issues > New Issue > Pipeline Request**
2. Fill in the template: data source URL, target table schema, transform requirements
3. Make sure the title contains `@claude`
4. The Claude agent will pick it up, write the code, and open a PR

See [Claude Agent Guide](docs/claude-agent-guide.md) for the full walkthrough.

## License

This is a teaching/demo project.
