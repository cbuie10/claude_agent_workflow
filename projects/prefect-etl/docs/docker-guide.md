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

### `oklahoma_wells` table

| Column | Type | Description |
|--------|------|-------------|
| `api` | `TEXT PRIMARY KEY` | 10-digit API well number |
| `well_records_docs` | `TEXT` | Well records documentation URL |
| `well_name` | `TEXT` | Name of the well |
| `well_num` | `TEXT` | Well number |
| `operator` | `TEXT` | Current operator name |
| `well_status` | `TEXT` | Well status code (PA, AC, TA, etc.) |
| `well_type` | `TEXT` | Well type code (OIL, GAS, DRY, etc.) |
| `symbol_class` | `TEXT` | Map symbol classification |
| `sh_lat` | `DOUBLE PRECISION` | Surface hole latitude |
| `sh_lon` | `DOUBLE PRECISION` | Surface hole longitude |
| `county` | `TEXT` | Oklahoma county |
| `section` | `TEXT` | PLSS section |
| `township` | `TEXT` | PLSS township |
| `range` | `TEXT` | PLSS range |
| `qtr4` | `TEXT` | Quarter-quarter-quarter-quarter section |
| `qtr3` | `TEXT` | Quarter-quarter-quarter section |
| `qtr2` | `TEXT` | Quarter-quarter section |
| `qtr1` | `TEXT` | Quarter section |
| `pm` | `TEXT` | Principal meridian |
| `footage_ew` | `REAL` | Footage east/west from section line |
| `ew` | `TEXT` | East or West indicator |
| `footage_ns` | `REAL` | Footage north/south from section line |
| `ns` | `TEXT` | North or South indicator |
| `inserted_at` | `TIMESTAMP WITH TIME ZONE` | When the row was loaded (auto-set) |

### `well_transfers` table

| Column | Type | Description |
|--------|------|-------------|
| `event_date` | `DATE` | Transfer date (part of composite PK) |
| `api_number` | `TEXT` | API well number (part of composite PK) |
| `well_name` | `TEXT` | Name of the well |
| `well_num` | `TEXT` | Well number |
| `well_type` | `TEXT` | Well type code |
| `well_status` | `TEXT` | Well status code |
| `pun_16ez` | `TEXT` | Production unit number (1016ez form) |
| `pun_02a` | `TEXT` | Production unit number (1002A form) |
| `location_type` | `TEXT` | Location record type |
| `surf_long_x` | `DOUBLE PRECISION` | Surface longitude |
| `surf_lat_y` | `DOUBLE PRECISION` | Surface latitude |
| `county` | `TEXT` | Oklahoma county |
| `section` | `TEXT` | PLSS section |
| `township` | `TEXT` | PLSS township |
| `range` | `TEXT` | PLSS range |
| `pm` | `TEXT` | Principal meridian |
| `q1` | `TEXT` | Quarter section 1 (160 ac) |
| `q2` | `TEXT` | Quarter section 2 (40 ac) |
| `q3` | `TEXT` | Quarter section 3 (10 ac) |
| `q4` | `TEXT` | Quarter section 4 (2.5 ac) |
| `footage_ns` | `REAL` | Footage north/south from section line |
| `ns` | `TEXT` | North or South indicator |
| `footage_ew` | `REAL` | Footage east/west from section line |
| `ew` | `TEXT` | East or West indicator |
| `from_operator_number` | `INTEGER` | Previous operator OCC ID |
| `from_operator_name` | `TEXT` | Previous operator name |
| `from_operator_address` | `TEXT` | Previous operator address |
| `from_operator_phone` | `TEXT` | Previous operator phone |
| `to_operator_name` | `TEXT` | New operator name |
| `to_operator_number` | `INTEGER` | New operator OCC ID |
| `to_operator_address` | `TEXT` | New operator address |
| `to_operator_phone` | `TEXT` | New operator phone |
| `inserted_at` | `TIMESTAMP WITH TIME ZONE` | When the row was loaded (auto-set) |

> **Note:** `well_transfers` uses a composite primary key of `(api_number, event_date)`. See [Oklahoma Wells Data Model](oklahoma-wells-data-model.md) for the relationship between these two tables.

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
