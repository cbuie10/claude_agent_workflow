# CLAUDE.md — Agent Instructions

## Project Overview
Prefect v3 ETL pipeline project. Extracts data from public APIs and loads
into PostgreSQL. Python 3.12, managed with uv.

## Commands
- Install deps: `uv sync --all-extras`
- Lint: `uv run ruff check src/ tests/`
- Fix lint: `uv run ruff check --fix src/ tests/`
- Test: `uv run pytest tests/ -v`
- Run a flow: `uv run python -m pipeline.flows.<flow_module>`

## Project Structure
- `src/pipeline/tasks/` — Prefect `@task` functions (extract, transform, load)
- `src/pipeline/flows/` — Prefect `@flow` functions that compose tasks
- `src/pipeline/config.py` — environment variable configuration with defaults
- `tests/` — pytest tests, one test file per task/flow module
- `docker/init.sql` — PostgreSQL table definitions

## Reference Implementation
See `src/pipeline/flows/earthquake_flow.py` and its tasks in
`src/pipeline/tasks/extract.py`, `transform.py`, `load.py` for the
canonical pattern to follow when building new pipelines.

## Conventions for New Pipelines

### Adding a new pipeline
1. Create task files in `src/pipeline/tasks/` if new extract/transform/load logic is needed
2. Create a flow file in `src/pipeline/flows/` that imports and composes tasks
3. Create corresponding test files in `tests/`
4. Add any new SQL tables to `docker/init.sql`
5. Run `uv run ruff check src/ tests/` and `uv run pytest tests/ -v` before submitting

### Code style
- Type hints on all function signatures
- Every `@task` must have a docstring
- Every `@flow` must have a docstring and use `log_prints=True`
- Use `httpx` for HTTP requests (not requests)
- Use SQLAlchemy `create_engine` + `text()` for SQL queries
- Use `ON CONFLICT` upserts for idempotent loads
- Use `get_run_logger()` for logging inside flows

### Testing
- Test tasks using `.fn()` to call the unwrapped function
- Mock HTTP calls with `unittest.mock.patch` on `httpx.get`
- Mock database calls with `unittest.mock.patch` on `create_engine`
- The `conftest.py` provides a session-scoped `prefect_test_harness` fixture
- All tests must pass before the PR is ready

### Configuration
- New environment variables go in `src/pipeline/config.py` with sensible defaults
- Update `.env.example` with any new variables

## Do NOT
- Do not modify `docker/docker-compose.yml` unless the issue explicitly asks for it
- Do not add new dependencies to `pyproject.toml` — mention needed deps in the PR description
- Do not use `print()` — use Prefect's `get_run_logger()` instead
- Do not write integration tests that require a running database — mock all DB calls
