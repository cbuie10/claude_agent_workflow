# Querying Data

SQL examples for exploring the earthquake, weather, Oklahoma wells, and well transfers data loaded by the pipelines.

## Connecting

```bash
docker exec -it pipeline-postgres psql -U pipeline_user -d pipeline_db
```

## Useful psql Commands

| Command | Description |
|---------|-------------|
| `\dt` | List all tables |
| `\d earthquakes` | Show earthquake table schema |
| `\d weather_forecasts` | Show weather table schema |
| `\d oklahoma_wells` | Show Oklahoma wells table schema |
| `\d well_transfers` | Show well transfers table schema |
| `\x` | Toggle expanded display (wide rows) |
| `\q` | Exit psql |

## Earthquake Queries

### Row count

```sql
SELECT COUNT(*) FROM earthquakes;
```

### Recent earthquakes, largest first

```sql
SELECT id, magnitude, place, occurred_at
FROM earthquakes
ORDER BY occurred_at DESC
LIMIT 10;
```

### Largest earthquakes by magnitude

```sql
SELECT magnitude, place, occurred_at, depth_km
FROM earthquakes
ORDER BY magnitude DESC
LIMIT 10;
```

### Earthquakes felt by people

```sql
SELECT magnitude, place, felt, occurred_at
FROM earthquakes
WHERE felt IS NOT NULL AND felt > 0
ORDER BY felt DESC;
```

### Earthquakes near a location (within ~1 degree)

```sql
SELECT id, magnitude, place, latitude, longitude
FROM earthquakes
WHERE latitude BETWEEN 33.0 AND 35.0
  AND longitude BETWEEN -119.0 AND -117.0
ORDER BY magnitude DESC;
```

### Earthquake count by magnitude range

```sql
SELECT
    CASE
        WHEN magnitude >= 5 THEN '5.0+'
        WHEN magnitude >= 4 THEN '4.0-4.9'
        WHEN magnitude >= 3 THEN '3.0-3.9'
        WHEN magnitude >= 2 THEN '2.0-2.9'
        WHEN magnitude >= 1 THEN '1.0-1.9'
        ELSE '< 1.0'
    END AS magnitude_range,
    COUNT(*) AS count
FROM earthquakes
GROUP BY 1
ORDER BY 1 DESC;
```

### Deep vs shallow earthquakes

```sql
SELECT
    CASE
        WHEN depth_km < 10 THEN 'Shallow (< 10km)'
        WHEN depth_km < 70 THEN 'Intermediate (10-70km)'
        ELSE 'Deep (70km+)'
    END AS depth_category,
    COUNT(*) AS count,
    ROUND(AVG(magnitude)::numeric, 2) AS avg_magnitude
FROM earthquakes
GROUP BY 1
ORDER BY 1;
```

### When the data was last loaded

```sql
SELECT MAX(inserted_at) AS last_load FROM earthquakes;
```

## Weather Forecast Queries

### Row count

```sql
SELECT COUNT(*) FROM weather_forecasts;
```

### Today's hourly forecast

```sql
SELECT forecast_time, temperature_f, relative_humidity, wind_speed_mph
FROM weather_forecasts
ORDER BY forecast_time;
```

### Temperature range for the forecast period

```sql
SELECT
    MIN(temperature_f) AS min_temp,
    MAX(temperature_f) AS max_temp,
    ROUND(AVG(temperature_f)::numeric, 1) AS avg_temp
FROM weather_forecasts;
```

### Windiest hours

```sql
SELECT forecast_time, wind_speed_mph, temperature_f
FROM weather_forecasts
ORDER BY wind_speed_mph DESC
LIMIT 5;
```

### Most humid hours

```sql
SELECT forecast_time, relative_humidity, temperature_f
FROM weather_forecasts
WHERE relative_humidity IS NOT NULL
ORDER BY relative_humidity DESC
LIMIT 5;
```

### Hourly weather summary

```sql
SELECT
    forecast_time,
    temperature_f || ' F' AS temp,
    relative_humidity || '%' AS humidity,
    wind_speed_mph || ' mph' AS wind
FROM weather_forecasts
ORDER BY forecast_time;
```

## Oklahoma Wells Queries

### Row count

```sql
SELECT COUNT(*) FROM oklahoma_wells;
```

### Wells by county

```sql
SELECT county, COUNT(*) AS well_count
FROM oklahoma_wells
GROUP BY county
ORDER BY well_count DESC
LIMIT 15;
```

### Search wells by operator

```sql
SELECT api, well_name, operator, well_status, county
FROM oklahoma_wells
WHERE operator ILIKE '%devon%'
ORDER BY well_name
LIMIT 20;
```

### Well status summary

```sql
SELECT well_status, COUNT(*) AS count
FROM oklahoma_wells
GROUP BY well_status
ORDER BY count DESC;
```

### Wells by type

```sql
SELECT well_type, COUNT(*) AS count
FROM oklahoma_wells
GROUP BY well_type
ORDER BY count DESC;
```

## Well Transfers Queries

### Row count

```sql
SELECT COUNT(*) FROM well_transfers;
```

### Most recent transfers

```sql
SELECT event_date, api_number, well_name, from_operator_name, to_operator_name
FROM well_transfers
ORDER BY event_date DESC
LIMIT 10;
```

### Transfer history for a specific well

```sql
SELECT event_date, from_operator_name, to_operator_name
FROM well_transfers
WHERE api_number = '3503702931'
ORDER BY event_date;
```

### Top acquirers (operators receiving the most wells)

```sql
SELECT to_operator_name, COUNT(*) AS acquisitions
FROM well_transfers
GROUP BY to_operator_name
ORDER BY acquisitions DESC
LIMIT 10;
```

### Transfers by county

```sql
SELECT county, COUNT(*) AS transfer_count
FROM well_transfers
GROUP BY county
ORDER BY transfer_count DESC
LIMIT 10;
```

## Cross-Table Queries

### Timestamp comparison (when each pipeline last ran)

```sql
SELECT 'earthquakes' AS pipeline, MAX(inserted_at) AS last_loaded FROM earthquakes
UNION ALL
SELECT 'weather_forecasts', MAX(fetched_at) FROM weather_forecasts
UNION ALL
SELECT 'oklahoma_wells', MAX(inserted_at) FROM oklahoma_wells
UNION ALL
SELECT 'well_transfers', MAX(inserted_at) FROM well_transfers;
```

### Row count summary

```sql
SELECT 'earthquakes' AS table_name, COUNT(*) AS rows FROM earthquakes
UNION ALL
SELECT 'weather_forecasts', COUNT(*) FROM weather_forecasts
UNION ALL
SELECT 'oklahoma_wells', COUNT(*) FROM oklahoma_wells
UNION ALL
SELECT 'well_transfers', COUNT(*) FROM well_transfers;
```

## Exporting Data

### Export to CSV

```bash
docker exec -it pipeline-postgres psql -U pipeline_user -d pipeline_db \
  -c "COPY earthquakes TO STDOUT WITH CSV HEADER" > earthquakes.csv
```

```bash
docker exec -it pipeline-postgres psql -U pipeline_user -d pipeline_db \
  -c "COPY weather_forecasts TO STDOUT WITH CSV HEADER" > weather.csv
```

```bash
docker exec -it pipeline-postgres psql -U pipeline_user -d pipeline_db \
  -c "COPY oklahoma_wells TO STDOUT WITH CSV HEADER" > oklahoma_wells.csv
```

```bash
docker exec -it pipeline-postgres psql -U pipeline_user -d pipeline_db \
  -c "COPY well_transfers TO STDOUT WITH CSV HEADER" > well_transfers.csv
```

## Re-running Pipelines

Pipelines use `ON CONFLICT DO UPDATE` (upsert), so they are safe to re-run:

- **Earthquake pipeline**: fetches the latest hour of data. Run multiple times to see new earthquakes appear.
- **Weather pipeline**: fetches the next 24 hours of forecasts for NYC. Run again for updated forecasts.
- **Oklahoma wells pipeline**: downloads the full OCC CSV (~126 MB). Re-run to pick up newly permitted wells.
- **Well transfers pipeline**: downloads the daily transfers Excel. Re-run for the latest transfer events.

```bash
uv run python -m pipeline.flows.earthquake_flow
uv run python -m pipeline.flows.weather_flow
uv run python -m pipeline.flows.oklahoma_wells_flow
uv run python -m pipeline.flows.well_transfers_flow
```

No duplicates will be created thanks to the upsert pattern.
