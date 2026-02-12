# Getting Started

Step-by-step guide to set up the project from scratch and run your first pipeline.

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Docker | 20+ | [docker.com](https://docs.docker.com/get-docker/) |
| Python | 3.12+ | Installed via uv |
| uv | latest | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| git | 2.x | Pre-installed on macOS/Linux |
| gh (optional) | latest | `brew install gh` — only needed if you want to create issues from the CLI |

## 1. Clone the Repository

```bash
git clone https://github.com/cbuie10/claude_agent_workflow.git
cd claude_agent_workflow
```

## 2. Install Python Dependencies

[uv](https://docs.astral.sh/uv/) manages the Python version and virtual environment automatically:

```bash
uv sync --all-extras
```

This installs all runtime dependencies (Prefect, SQLAlchemy, httpx, etc.) and dev dependencies (pytest, ruff).

The `--all-extras` flag includes dev dependencies defined in `[project.optional-dependencies]`.

## 3. Start PostgreSQL & Prefect Server

The database and Prefect server run in Docker containers defined in `docker/docker-compose.yml`:

```bash
docker compose -f docker/docker-compose.yml up -d
```

This starts two containers:
- **PostgreSQL 16** — pipeline data (user: `pipeline_user`, password: `pipeline_pass`, port: `5432`)
- **Prefect Server** — flow run dashboard at [http://localhost:4200](http://localhost:4200)

Tables are created automatically from `docker/init.sql`.

Verify they're running:

```bash
docker ps
# Should show pipeline-postgres and prefect-server containers in "Up" status
```

## 4. Run Your First Pipeline

### Earthquake Pipeline

```bash
uv run python -m pipeline.flows.earthquake_flow
```

Expected output:

```
Extracting earthquake data from https://earthquake.usgs.gov/...
Transforming X features (min_magnitude=0.0)
Loading X rows into PostgreSQL
Pipeline complete: X rows loaded
```

### Weather Pipeline

```bash
uv run python -m pipeline.flows.weather_flow
```

Expected output:

```
Extracting weather forecast data from https://api.open-meteo.com/...
Transforming 24 hourly forecast records
Loading 24 rows into PostgreSQL
Pipeline complete: 24 rows loaded
```

## 5. View in Prefect UI

Open [http://localhost:4200](http://localhost:4200) in your browser. You should see the flow run(s) you just executed, with task-level detail, logs, and timing.

## 6. Verify the Data

Connect to PostgreSQL and check the rows:

```bash
docker exec -it pipeline-postgres psql -U pipeline_user -d pipeline_db
```

```sql
SELECT COUNT(*) FROM earthquakes;
SELECT COUNT(*) FROM weather_forecasts;
\q
```

See [Querying Data](querying-data.md) for more SQL examples.

## 7. Run the Tests

```bash
uv run pytest tests/ -v
```

All 24 tests should pass. These tests mock all external calls (HTTP and database), so they run fast and don't require Docker.

## 8. Lint the Code

```bash
uv run ruff check src/ tests/
```

Should report no errors.

## Configuration

All environment variables have sensible defaults for local development. To customize, copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Then edit `.env` to change values. See the [README](../README.md#environment-variables) for all available variables.

## What's Next?

- [Query your data](querying-data.md) in PostgreSQL
- [Learn how the Claude agent works](claude-agent-guide.md) and create your own pipeline via a GitHub Issue
- [Manage Docker and the database](docker-guide.md)
