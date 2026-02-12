# Docker & PostgreSQL Guide

This project uses Docker to run PostgreSQL 16. All data is stored in a Docker volume that persists across container restarts.

## Container Management

### Start the database

```bash
docker compose -f docker/docker-compose.yml up -d
```

The `-d` flag runs it in detached (background) mode.

### Stop the database

```bash
docker compose -f docker/docker-compose.yml down
```

Data is preserved in the `pgdata` volume. Your rows will still be there when you start again.

### Stop and delete all data

```bash
docker compose -f docker/docker-compose.yml down -v
```

The `-v` flag removes the volume. Next time you start, the database will be empty and tables will be recreated from `docker/init.sql`.

### Check container status

```bash
docker ps
```

Look for `pipeline-postgres` in the output.

### View container logs

```bash
docker logs pipeline-postgres
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
