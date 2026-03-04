# Oklahoma Wells Data Model

## Overview

Two datasets from the Oklahoma Corporation Commission (OCC):

| Table | Source | Format | Rows | Refresh |
|-------|--------|--------|------|---------|
| `oklahoma_wells` | [RBDMS Wells](https://oklahoma.gov/content/dam/ok/en/occ/documents/og/ogdatafiles/rbdms-wells.csv) | CSV (~126 MB) | ~455K | Full snapshot each run |
| `well_transfers` | [Well Transfers](https://oklahoma.gov/content/dam/ok/en/occ/documents/og/ogdatafiles/well-transfers-daily.xlsx) | Excel (.xlsx) | ~900 | Rolling 30-day window |

**Relationship**: One well can have zero or many transfers. The join key is `oklahoma_wells.api = well_transfers.api_number`.

---

## Entity Relationship Diagram

```
  oklahoma_wells                            well_transfers
  ══════════════                            ══════════════
  PK  api               TEXT    ───1──M───  PK  api_number           TEXT
      well_records_docs  TEXT               PK  event_date           DATE
      well_name          TEXT                   well_name            TEXT
      well_num           TEXT                   well_num             TEXT
      operator           TEXT                   well_type            TEXT
      well_status        TEXT                   well_status          TEXT
      well_type          TEXT                   pun_16ez             TEXT
      symbol_class       TEXT                   pun_02a              TEXT
      sh_lat             DOUBLE PRECISION       location_type        TEXT
      sh_lon             DOUBLE PRECISION       surf_long_x          DOUBLE PRECISION
      county             TEXT                   surf_lat_y           DOUBLE PRECISION
      section            TEXT                   county               TEXT
      township           TEXT                   section              TEXT
      range              TEXT                   township             TEXT
      qtr4               TEXT                   range                TEXT
      qtr3               TEXT                   pm                   TEXT
      qtr2               TEXT                   q1                   TEXT
      qtr1               TEXT                   q2                   TEXT
      pm                 TEXT                   q3                   TEXT
      footage_ew         REAL                   q4                   TEXT
      ew                 TEXT                   footage_ns           REAL
      footage_ns         REAL                   ns                   TEXT
      ns                 TEXT                   footage_ew           REAL
      inserted_at        TIMESTAMPTZ            ew                   TEXT
                                                from_operator_number INTEGER
                                                from_operator_name   TEXT
                                                from_operator_address TEXT
                                                from_operator_phone  TEXT
                                                to_operator_name     TEXT
                                                to_operator_number   INTEGER
                                                to_operator_address  TEXT
                                                to_operator_phone    TEXT
                                                inserted_at          TIMESTAMPTZ
```

---

## Primary Keys

| Table | Primary Key | Notes |
|-------|-------------|-------|
| `oklahoma_wells` | `api` | 10-digit API well number. Single natural key. |
| `well_transfers` | `(api_number, event_date)` | Composite key. One transfer per well per day. |

Both tables use `ON CONFLICT ... DO UPDATE` upserts, making loads idempotent.

---

## Column Mapping (Shared Columns)

20 columns are semantically shared. 6 have different names between the two tables:

| Concept | `oklahoma_wells` | `well_transfers` | Same Name? |
|---------|-------------------|-------------------|------------|
| API number | `api` | `api_number` | No |
| Well name | `well_name` | `well_name` | Yes |
| Well number | `well_num` | `well_num` | Yes |
| Well type | `well_type` | `well_type` | Yes |
| Well status | `well_status` | `well_status` | Yes |
| Latitude | `sh_lat` | `surf_lat_y` | No |
| Longitude | `sh_lon` | `surf_long_x` | No |
| County | `county` | `county` | Yes |
| Section | `section` | `section` | Yes |
| Township | `township` | `township` | Yes |
| Range | `range` | `range` | Yes |
| Principal meridian | `pm` | `pm` | Yes |
| Quarter 1 (160 ac) | `qtr1` | `q1` | No |
| Quarter 2 (40 ac) | `qtr2` | `q2` | No |
| Quarter 3 (10 ac) | `qtr3` | `q3` | No |
| Quarter 4 (2.5 ac) | `qtr4` | `q4` | No |
| Footage N/S | `footage_ns` | `footage_ns` | Yes |
| N/S direction | `ns` | `ns` | Yes |
| Footage E/W | `footage_ew` | `footage_ew` | Yes |
| E/W direction | `ew` | `ew` | Yes |

### Columns Unique to `oklahoma_wells`

| Column | Type | Description |
|--------|------|-------------|
| `well_records_docs` | TEXT | URL to well records/documents |
| `operator` | TEXT | Current operator name |
| `symbol_class` | TEXT | Map symbology classification |

### Columns Unique to `well_transfers`

| Column | Type | Description |
|--------|------|-------------|
| `event_date` | DATE | Transfer date (part of PK) |
| `pun_16ez` | TEXT | Production unit number (1016ez form) |
| `pun_02a` | TEXT | Production unit number (1002A form) |
| `location_type` | TEXT | Location record type (e.g., Surface) |
| `from_operator_number` | INTEGER | Previous operator OCC ID |
| `from_operator_name` | TEXT | Previous operator name |
| `from_operator_address` | TEXT | Previous operator address |
| `from_operator_phone` | TEXT | Previous operator phone |
| `to_operator_number` | INTEGER | New operator OCC ID |
| `to_operator_name` | TEXT | New operator name |
| `to_operator_address` | TEXT | New operator address |
| `to_operator_phone` | TEXT | New operator phone |

---

## Data Quality Notes

1. **No enforced foreign key** — the relationship between `api` and `api_number` is logical only. Transfers may reference wells not yet in the wells table (or vice versa) depending on refresh timing.

2. **Column naming inconsistencies** — the two OCC source files use different naming conventions. The naming differences (api/api_number, sh_lat/surf_lat_y, qtr1/q1, etc.) are inherited from the source data and preserved as-is.

3. **Operator data divergence** — `oklahoma_wells.operator` is a single field with the current operator. `well_transfers` has detailed from/to operator records (name, number, address, phone). After a transfer, `oklahoma_wells.operator` should eventually match `well_transfers.to_operator_name`, but timing depends on when OCC updates each file.

4. **Rolling 30-day window** — the transfers Excel file only contains the last 30 days. Historical transfers accumulate in the database via upserts (old rows are never deleted), but if the pipeline stops running for 30+ days, a gap will form.

5. **Upsert-only (no deletes)** — wells that are removed from the OCC CSV remain in the database indefinitely. The `well_status` field indicates whether a well is active or plugged/abandoned.

6. **Composite key limitation** — `(api_number, event_date)` assumes at most one transfer per well per day. A second transfer on the same day would overwrite the first.

---

## Example Queries

### Join: Transfer history for a specific well

```sql
SELECT w.api, w.well_name, w.operator AS current_operator,
       t.event_date, t.from_operator_name, t.to_operator_name
FROM oklahoma_wells w
JOIN well_transfers t ON w.api = t.api_number
WHERE w.api = '3501500001'
ORDER BY t.event_date DESC;
```

### Recent transfers with current well data

```sql
SELECT w.api, w.well_name, w.county, w.well_status,
       t.event_date, t.from_operator_name, t.to_operator_name
FROM oklahoma_wells w
JOIN well_transfers t ON w.api = t.api_number
ORDER BY t.event_date DESC
LIMIT 20;
```

### Data quality check: transfers with no matching well

```sql
SELECT t.api_number, t.event_date, t.well_name
FROM well_transfers t
LEFT JOIN oklahoma_wells w ON t.api_number = w.api
WHERE w.api IS NULL;
```
