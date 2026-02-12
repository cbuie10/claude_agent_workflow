# Claude Agent Guide

How the autonomous Claude agent builds data pipelines from GitHub Issues.

## Architecture Overview

```
┌─────────────┐     ┌──────────────────┐     ┌──────────────┐
│ GitHub Issue │────>│  GitHub Actions   │────>│ Pull Request │
│ (you write)  │     │  claude.yml       │     │ (Claude opens)│
└─────────────┘     │                    │     └──────┬───────┘
                    │  1. Checkout repo   │            │
                    │  2. Install deps    │            v
                    │  3. Run Claude      │     ┌──────────────┐
                    │     agent           │     │  CI Pipeline  │
                    └──────────────────┘     │  ci.yml       │
                                              │  ruff + pytest │
                                              └──────────────┘
```

## How It Triggers

The Claude agent runs when **any of these events** occur and the body/title contains `@claude`:

| Event | Trigger |
|-------|---------|
| Issue opened | Title contains `@claude` |
| Issue comment | Comment body contains `@claude` |
| PR review comment | Comment body contains `@claude` |

The workflow is defined in `.github/workflows/claude.yml`.

## What Claude Does

When triggered, the agent:

1. **Reads the issue** to understand what pipeline to build
2. **Reads `CLAUDE.md`** for project conventions (code style, file locations, testing patterns)
3. **Reads existing code** to follow established patterns (earthquake pipeline as reference)
4. **Creates a new branch** from `main`
5. **Writes code**: extract task, transform task, load task, flow, tests, SQL schema
6. **Runs lint and tests** (`uv run ruff check` + `uv run pytest`)
7. **Pushes the branch** and opens a pull request
8. **CI triggers** on the PR — lint and tests run again independently

## Creating an Issue for Claude

### Using the template

1. Go to your repo's **Issues** tab
2. Click **New Issue**
3. Select the **Pipeline Request** template
4. Fill in all sections:
   - **Data Source**: The API URL and what data it returns
   - **Target Table**: Table name and column descriptions
   - **Transform Requirements**: What transformations to apply
   - **Acceptance Criteria**: Checkboxes (pre-filled by template)
5. Make sure the title starts with `@claude:`

### Example issue title

```
@claude: Build Open-Meteo weather forecast pipeline
```

### Example issue body

```markdown
## Data Source
Open-Meteo free weather API (provide the full URL).
Returns JSON with hourly arrays for temperature, humidity, and wind speed.

## Target Table
`weather_forecasts` with columns:
- id (composite: lat_lon_timestamp)
- latitude, longitude
- forecast_time (from hourly time array)
- temperature_f, relative_humidity, wind_speed_mph

## Transform Requirements
- Flatten hourly arrays into individual rows
- Parse ISO8601 timestamps to datetime
- Filter out rows where temperature is null
- Generate composite ID from rounded lat/lon + timestamp

## Acceptance Criteria
- [ ] Extract task fetches data from the source
- [ ] Transform task processes raw data into the target schema
- [ ] Load task upserts into the PostgreSQL table
- [ ] Flow composes all three tasks with logging
- [ ] Unit tests pass for all new tasks
- [ ] Lint passes with ruff
- [ ] SQL CREATE TABLE statement added to docker/init.sql
```

## Reviewing a Claude PR

When Claude opens a PR, check:

1. **CI status** — lint and tests must be green
2. **Code quality** — does it follow the patterns in the existing codebase?
3. **SQL schema** — is the `CREATE TABLE` in `docker/init.sql` correct?
4. **Test coverage** — are extract, transform, load, and flow all tested?
5. **Upsert logic** — does `ON CONFLICT DO UPDATE` make sense for the data?

## Requesting Changes

If something needs fixing, comment on the PR with `@claude` followed by what you want changed:

```
@claude fix the transform to handle null wind speed values
```

```
@claude add a test for when the API returns an empty response
```

Claude will read your comment, make the changes, and push a new commit to the same PR.

## Agent Permissions

The agent has permission to:

| Action | Allowed |
|--------|---------|
| Read/write/edit files | Yes |
| Run `uv run *` commands | Yes (lint, test, run flows) |
| Git operations (branch, commit, push) | Yes (built into the action) |
| Add new dependencies | No (by convention via CLAUDE.md) |
| Modify docker-compose.yml | No (by convention via CLAUDE.md) |
| Deploy or run production commands | No |

These are configured in the `settings` block of `.github/workflows/claude.yml`.

## Agent Configuration

### `CLAUDE.md` (agent instructions)

This file tells Claude:
- How to run commands (`uv sync`, `uv run ruff check`, `uv run pytest`)
- Where to put files (tasks in `src/pipeline/tasks/`, flows in `src/pipeline/flows/`)
- Code conventions (type hints, docstrings, httpx, ON CONFLICT upserts)
- What NOT to do (no new deps, no modifying docker-compose, no print statements)

### `.github/workflows/claude.yml` (workflow config)

Key settings:
- **`claude_args: "--max-turns 50"`** — allows up to 50 API round-trips (complex pipelines need 30-40)
- **`settings.permissions.allow`** — Bash commands the agent can run (scoped to `uv run *`)

### `.github/ISSUE_TEMPLATE/pipeline_request.md`

Structured template that guides both you and the agent. The acceptance criteria checklist ensures Claude covers all bases.

## Costs

Each agent run costs Anthropic API credits based on the number of turns. A typical pipeline build uses 30-40 turns. Monitor usage in your Anthropic dashboard.

## Troubleshooting

### Agent doesn't trigger

- Check that the issue title or comment contains `@claude` (exact match, case-sensitive)
- Verify the `ANTHROPIC_API_KEY` secret is set in repo Settings > Secrets > Actions
- Check the Actions tab for workflow run failures

### Agent hits max turns

If the agent runs out of turns before completing, it may not push its branch. Increase `--max-turns` in `claude.yml` (default: 50).

### Agent writes code that doesn't follow conventions

Improve `CLAUDE.md` with more specific instructions. The agent treats `CLAUDE.md` as its primary guide — the more explicit you are, the better the output.

### CI fails on the PR

Comment `@claude` on the PR with the error. Example:

```
@claude the ruff check is failing on line 42 of transform.py — please fix
```
