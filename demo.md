# Demo: Running All Pipelines

## 1. Start Docker

Reset volumes (so any new tables from `init.sql` get created) and start services:

```bash
docker compose -f docker/docker-compose.yml down -v
docker compose -f docker/docker-compose.yml up -d
```

This starts:
- **PostgreSQL** on `localhost:5432`
- **Prefect Server** on `localhost:4200`

## 2. Set Prefect API URL

Tell Prefect to report flow runs to your local server:

```bash
export PREFECT_API_URL=http://localhost:4200/api
```

## 3. Run Pipelines

```bash
uv run python -m pipeline.flows.earthquake_flow
uv run python -m pipeline.flows.weather_flow
uv run python -m pipeline.flows.oklahoma_wells_flow
uv run python -m pipeline.flows.well_transfers_flow
```

> **Note:** The Oklahoma wells pipeline downloads ~126 MB and may take a few minutes.

As you add new pipelines, just add another line here:

```bash
uv run python -m pipeline.flows.<your_new_flow>
```

## 4. View in Prefect UI

Open **http://localhost:4200** in your browser to see flow runs, task details, and logs.

## 5. Query the Data

```bash
docker exec -it pipeline-postgres psql -U pipeline_user -d pipeline_db
```

Then run SQL:

```sql
SELECT COUNT(*) FROM earthquakes;
SELECT COUNT(*) FROM weather_forecasts;
SELECT COUNT(*) FROM oklahoma_wells;
SELECT COUNT(*) FROM well_transfers;
```

Type `\q` to exit psql.
