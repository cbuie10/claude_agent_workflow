# Docker & PostgreSQL Guide

This project uses Docker to run PostgreSQL 16 and a self-hosted Prefect v3 server. All data is stored in a Docker volume that persists across container restarts.

## Container Management

### Start everything

```bash
docker compose -f docker/docker-compose.yml up -d
```

This starts two containers:
- **pipeline-postgres** — PostgreSQL 16 database
- **prefect-server** — Prefect v3 dashboard and API

The `-d` flag runs them in detached (background) mode. The Prefect server waits for PostgreSQL to be healthy before starting.

### Stop everything

```bash
docker compose -f docker/docker-compose.yml down
```

Data is preserved in the `pgdata` volume. Your rows and Prefect run history will still be there when you start again.

### Stop and delete all data

```bash
docker compose -f docker/docker-compose.yml down -v
```

The `-v` flag removes the volume. Next time you start, the database will be empty, tables will be recreated from `docker/init.sql`, and Prefect run history will be cleared.

### Check container status

```bash
docker ps
```

Look for both `pipeline-postgres` and `prefect-server` in the output.

### View container logs

```bash
docker logs pipeline-postgres
docker logs prefect-server
```

Add `-f` to follow/stream logs in real time.

### Restart with fresh schema

If you've edited `docker/init.sql` (e.g., added a new table), you need to remove the volume and start fresh for schema changes to take effect:

```bash
docker compose -f docker/docker-compose.yml down -v
docker compose -f docker/docker-compose.yml up -d
```

A plain `restart` does **not** re-run `init.sql`.

## Connecting to PostgreSQL

### From the command line (psql)

The `psql` client is included in the Docker container:

```bash
docker exec -it pipeline-postgres psql -U pipeline_user -d pipeline_db
```

This drops you into an interactive SQL prompt. Type `\q` to exit.

### Connection details

| Property | Value |
|----------|-------|
| Host | `localhost` |
| Port | `5432` |
| Database | `pipeline_db` |
| Username | `pipeline_user` |
| Password | `pipeline_pass` |

### Connection string (SQLAlchemy format)

```
postgresql+psycopg2://pipeline_user:pipeline_pass@localhost:5432/pipeline_db
```

### From a GUI tool

You can connect with any PostgreSQL client (pgAdmin, DBeaver, DataGrip, TablePlus, etc.) using the connection details above.

## Database Schema

The schema is defined in `docker/init.sql` and created automatically when the container first starts.

### `earthquakes` table

| Column | Type | Description |
|--------|------|-------------|
| `id` | `TEXT PRIMARY KEY` | USGS event ID (e.g., `us7000abc1`) |
| `magnitude` | `REAL` | Richter magnitude |
| `place` | `TEXT` | Human-readable location |
| `occurred_at` | `TIMESTAMP WITH TIME ZONE` | When the earthquake occurred |
| `longitude` | `DOUBLE PRECISION` | Epicenter longitude |
| `latitude` | `DOUBLE PRECISION` | Epicenter latitude |
| `depth_km` | `DOUBLE PRECISION` | Depth in kilometers |
| `magnitude_type` | `TEXT` | Type (ml, mb, mw, etc.) |
| `event_type` | `TEXT` | Usually "earthquake" |
| `title` | `TEXT` | USGS title string |
| `detail_url` | `TEXT` | Link to USGS event page |
| `felt` | `INTEGER` | Number of felt reports |
| `tsunami` | `INTEGER` | Tsunami flag (0 or 1) |
| `inserted_at` | `TIMESTAMP WITH TIME ZONE` | When the row was loaded (auto-set) |

### `weather_forecasts` table

| Column | Type | Description |
|--------|------|-------------|
| `id` | `TEXT PRIMARY KEY` | Composite: `lat_lon_timestamp` |
| `latitude` | `DOUBLE PRECISION` | Forecast location latitude |
| `longitude` | `DOUBLE PRECISION` | Forecast location longitude |
| `forecast_time` | `TIMESTAMP WITH TIME ZONE` | Hour of the forecast |
| `temperature_f` | `REAL` | Temperature in Fahrenheit |
| `relative_humidity` | `REAL` | Relative humidity (%) |
| `wind_speed_mph` | `REAL` | Wind speed in mph |
| `fetched_at` | `TIMESTAMP WITH TIME ZONE` | When the row was loaded (auto-set) |

## Adding a New Table

When Claude (or you) builds a new pipeline, a new table definition goes in `docker/init.sql`:

```sql
CREATE TABLE IF NOT EXISTS your_new_table (
    id    TEXT PRIMARY KEY,
    -- your columns here
    inserted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

Then recreate the database to pick up the new schema:

```bash
docker compose -f docker/docker-compose.yml down -v
docker compose -f docker/docker-compose.yml up -d
```

## Troubleshooting

### "Connection refused" when running a pipeline

The PostgreSQL container isn't running. Start it:

```bash
docker compose -f docker/docker-compose.yml up -d
```

### Port 5432 already in use

Another PostgreSQL instance is using the port. Either stop it or change the port mapping in `docker-compose.yml`:

```yaml
ports:
  - "5433:5432"  # Use 5433 on host
```

Then update your `DATABASE_URL` to use port 5433.

### Tables don't exist after schema changes

`init.sql` only runs on the **first** container start (when the volume is empty). To re-run it:

```bash
docker compose -f docker/docker-compose.yml down -v
docker compose -f docker/docker-compose.yml up -d
```

## Prefect Server

The Prefect v3 server runs alongside PostgreSQL and provides a web dashboard for viewing flow runs.

### Access the Prefect UI

Open [http://localhost:4200](http://localhost:4200) in your browser after starting the containers.

### How it works

- Prefect stores its metadata in a separate `prefect_db` database on the same PostgreSQL instance
- The `00-create-prefect-db.sh` init script creates this database automatically on first start
- When `PREFECT_API_URL=http://localhost:4200/api` is set (via `.env`), flows automatically report runs to the server
- Without `PREFECT_API_URL` set, flows still work but runs don't appear in the UI

### View Prefect server logs

```bash
docker logs prefect-server
docker logs -f prefect-server   # follow/stream
```

### Check Prefect server health

```bash
curl http://localhost:4200/api/health
```

### Port 4200 already in use

Change the port mapping in `docker-compose.yml`:

```yaml
ports:
  - "4201:4200"  # Use 4201 on host
```

Then update `PREFECT_API_URL` in your `.env` to `http://localhost:4201/api`.
