# DW Profiler — Architecture & Design

## Problem Statement

The data warehouse has 50-500 tables spread across multiple databases on a single
SQL Server instance. Column naming is inconsistent across databases — the same
business entity might appear as `customer_id`, `cust_no`, `client_number`, or
`CustomerID` depending on which team built the table.

We need a tool that:
1. **Profiles** every column across every database (types, cardinality, samples, patterns)
2. **Discovers relationships** — both explicit (FKs) and inferred (similar names, overlapping values)
3. **Builds a queryable graph** so Claude (or a human) can ask: "What columns across any database relate to API number?"
4. **Visualizes** the schema as an interactive network diagram

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         DW Profiler System                          │
│                                                                     │
│  ┌──────────┐    ┌──────────────┐    ┌────────────┐    ┌─────────┐ │
│  │  Crawler  │───►│   Profiler   │───►│  Matcher   │───►│  Neo4j  │ │
│  │  Phase 1  │    │   Phase 2    │    │  Phase 3   │    │ Phase 4 │ │
│  └──────────┘    └──────────────┘    └────────────┘    └─────────┘ │
│       │                 │                  │                 ▲      │
│       ▼                 ▼                  ▼                 │      │
│  metadata.json    profiles/           matches.json      import     │
│  (schemas,        (per-table          (scored            edges     │
│   tables,          JSON/Parquet)       column pairs)              │
│   columns)                                                        │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  MCP Tools (in mssql-mcp server)                             │   │
│  │  • profile_table → run profiler on demand                    │   │
│  │  • find_related_columns → Cypher query to Neo4j              │   │
│  │  • get_lineage_path → shortest path between two tables       │   │
│  │  • search_graph → full-text search across column metadata    │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Storage Strategy

### Raw Data → Files (outside Neo4j)

| Data | Format | Location | Why |
|------|--------|----------|-----|
| Schema metadata | JSON | `data/metadata/` | Small, versionable, human-readable |
| Column profiles | Parquet | `data/profiles/` | Columnar, fast reads, compact for stats |
| Sample values | JSON | `data/samples/` | Per-table top-N values per column |
| Match scores | JSON | `data/matches/` | Scored column pairs before import |
| Profile reports | HTML | `data/reports/` | ydata-profiling output for humans |

**Why outside Neo4j**: Raw profiling data is large, tabular, and changes frequently
during profiling iterations. Files are cheap, versionable, and don't require Neo4j
to be running during profiling. Neo4j is optimized for graph traversal, not bulk
data storage.

### Graph Data → Neo4j

Only the **graph structure** goes into Neo4j — nodes and edges with properties.

#### Node Types

```
(:Database {name, server, size_mb, status})

(:Schema {name, database})

(:Table {name, schema, database, row_count, size_mb, profiled_at})

(:Column {
    name, table, schema, database,
    data_type, max_length, is_nullable, is_primary_key,
    cardinality, null_rate, sample_pattern,
    profile_path    ← pointer to full profile on disk
})
```

#### Edge Types

```
(:Database)-[:CONTAINS]->(:Schema)
(:Schema)-[:CONTAINS]->(:Table)
(:Table)-[:HAS_COLUMN]->(:Column)

# Explicit relationships
(:Column)-[:FOREIGN_KEY {constraint_name}]->(:Column)

# Inferred relationships (the interesting part)
(:Column)-[:INFERRED_MATCH {
    confidence: 0.0-1.0,
    method: "name"|"semantic"|"value_overlap"|"pattern"|"statistical",
    evidence: "description of why this match was inferred",
    overlap_pct: 0.85,     ← for value-based matches
    name_similarity: 0.92  ← for name-based matches
}]->(:Column)
```

#### Example Cypher Queries

```cypher
-- Find all columns related to "api_number" across all databases
MATCH (c:Column)-[r:INFERRED_MATCH|FOREIGN_KEY]-(related:Column)
WHERE c.name CONTAINS 'api' OR related.name CONTAINS 'api'
RETURN c.database, c.table, c.name,
       type(r) as relationship,
       r.confidence,
       related.database, related.table, related.name
ORDER BY r.confidence DESC

-- Shortest path between two tables in different databases
MATCH path = shortestPath(
    (a:Table {name: 'orders', database: 'sales'})-[*]-(b:Table {name: 'customers', database: 'crm'})
)
RETURN path

-- Find all tables that share columns with a given table
MATCH (t:Table {name: 'well_transfers'})-[:HAS_COLUMN]->(c:Column)
      -[:INFERRED_MATCH]->(related:Column)<-[:HAS_COLUMN]-(other:Table)
WHERE other <> t
RETURN other.database, other.name, COUNT(*) as shared_columns
ORDER BY shared_columns DESC

-- Community detection: which tables cluster together?
MATCH (t:Table)-[:HAS_COLUMN]->(:Column)-[:INFERRED_MATCH]-(:Column)<-[:HAS_COLUMN]-(t2:Table)
RETURN t.database + '.' + t.name AS source,
       t2.database + '.' + t2.name AS target,
       COUNT(*) AS weight
```

## Phase 1: Metadata Crawl

**Input**: SQL Server connection (via existing MCP server or direct pyodbc)
**Output**: `data/metadata/metadata.json`

```python
# Pseudocode
for database in list_databases():
    for schema in list_schemas(database):
        for table in list_tables(database, schema):
            columns = describe_table(database, schema, table)
            foreign_keys = get_foreign_keys(database, schema, table)
            row_count = get_row_count(database, schema, table)
            # Store metadata
```

**SQL queries needed**:
- `INFORMATION_SCHEMA.TABLES` — all tables
- `INFORMATION_SCHEMA.COLUMNS` — all columns with types
- `INFORMATION_SCHEMA.KEY_COLUMN_USAGE` + `REFERENTIAL_CONSTRAINTS` — foreign keys
- `sys.dm_db_partition_stats` — row counts without full table scans
- `sys.databases` — database list

**Estimated time**: ~1-2 minutes for 500 tables (metadata only, no data sampling)

## Phase 2: Data Profiling

**Input**: Metadata from Phase 1
**Output**: `data/profiles/` (Parquet) + `data/samples/` (JSON)

For each column, compute:

| Metric | SQL Approach | Purpose |
|--------|-------------|---------|
| Cardinality | `COUNT(DISTINCT col)` | Uniqueness indicator |
| Null rate | `SUM(CASE WHEN col IS NULL THEN 1 END) / COUNT(*)` | Data quality |
| Min / Max | `MIN(col), MAX(col)` | Range |
| Top 10 values | `SELECT TOP 10 col, COUNT(*) ... GROUP BY col ORDER BY COUNT(*) DESC` | Pattern detection |
| Sample pattern | Regex on top values (e.g., "XX-####") | Format matching |
| Mean / StdDev | `AVG(CAST(col AS FLOAT)), STDEV(...)` | Numeric distribution |

**Sampling strategy**: For tables > 100K rows, use `TABLESAMPLE (1000 ROWS)` or
`SELECT TOP 1000 ... ORDER BY NEWID()` to avoid full table scans.

**Estimated time**: ~10-30 minutes for 500 tables (sampling 1000 rows each)

**Optional**: Run `ydata-profiling` for rich HTML reports per table (slower but
produces beautiful interactive reports for the team).

## Phase 3: Relationship Inference

**Input**: Profiles + samples from Phase 2
**Output**: `data/matches/matches.json`

### Layer 1: Explicit Foreign Keys (confidence: 1.0)
Already captured in Phase 1. Direct import into Neo4j as `FOREIGN_KEY` edges.

### Layer 2: Name-Based Matching (confidence: 0.6-0.9)
Normalize column names and compare:
```python
def normalize(name: str) -> str:
    # customer_id, CustomerID, cust_id → customerid
    name = name.lower()
    name = re.sub(r'[_\-\s]+', '', name)  # remove separators
    return name
```
Then fuzzy match with Levenshtein distance or token-based similarity.

### Layer 3: Semantic Matching via Claude (confidence: 0.5-0.85)
For column pairs that didn't match on name but have compatible types:
```
Prompt: "Are these two columns likely the same business entity?
Column A: 'cust_no' (varchar, table: orders, sample values: C001, C002, C003)
Column B: 'client_number' (varchar, table: invoices, sample values: C001, C004, C005)
Rate confidence 0-1 and explain."
```
**Batch this** — send groups of candidate pairs to reduce API calls.

### Layer 4: Value Overlap (confidence: 0.4-0.95)
For columns with same data type, compute Jaccard similarity on sampled values:
```python
overlap = len(values_a & values_b) / len(values_a | values_b)
```
High overlap (>0.7) between columns in different tables = likely relationship.

Also check **inclusion dependency**: if all values in column A exist in column B,
A likely references B (FK-like relationship).

### Layer 5: Pattern + Statistical Matching (confidence: 0.3-0.6)
- Same regex pattern (e.g., both match `\d{2}-\d{5}`)
- Same cardinality range + data type
- Similar value distributions (KS test or histogram comparison)

### Scoring

Each method produces a confidence score. Final edge confidence is the **max** across
methods (not average — a single strong signal is enough):

```python
edge_confidence = max(
    name_similarity * 0.9,
    semantic_score,
    value_overlap * 0.95,
    pattern_match * 0.6,
    statistical_match * 0.5,
)
```

Only import edges with confidence ≥ 0.4 into Neo4j. Store all scores in the
`INFERRED_MATCH` edge properties for transparency.

## Phase 4: Neo4j Import

**Input**: Metadata + match scores
**Output**: Populated Neo4j graph

### Import Strategy

Use the **Neo4j Python driver** (`neo4j` pip package) with batch UNWIND operations:

```python
# Batch create nodes
session.run("""
    UNWIND $columns AS col
    MERGE (c:Column {name: col.name, table: col.table, database: col.database})
    SET c += col.properties
""", columns=column_batch)

# Batch create inferred edges
session.run("""
    UNWIND $matches AS m
    MATCH (a:Column {name: m.source_col, table: m.source_table, database: m.source_db})
    MATCH (b:Column {name: m.target_col, table: m.target_table, database: m.target_db})
    MERGE (a)-[r:INFERRED_MATCH]->(b)
    SET r.confidence = m.confidence,
        r.method = m.method,
        r.evidence = m.evidence
""", matches=match_batch)
```

### Indexes

```cypher
CREATE INDEX FOR (d:Database) ON (d.name);
CREATE INDEX FOR (t:Table) ON (t.name, t.database);
CREATE INDEX FOR (c:Column) ON (c.name);
CREATE FULLTEXT INDEX column_search FOR (c:Column) ON EACH [c.name, c.table, c.database];
```

### Incremental Updates

After initial load, re-profiling should be incremental:
1. Compare `sys.dm_db_partition_stats` row counts to last profiled counts
2. Only re-profile tables that changed significantly (>5% row count change)
3. Re-run matching only for updated columns
4. MERGE (upsert) into Neo4j — don't delete and recreate

## Phase 5: MCP Integration

Add tools to the existing `mssql-mcp` server (or a new `dw-profiler-mcp` server)
that query Neo4j:

| Tool | Description |
|------|-------------|
| `profile_table(db, schema, table)` | Profile a table on demand, store results, update Neo4j |
| `find_related_columns(column, table, database)` | Cypher: find INFERRED_MATCH and FK edges |
| `get_lineage_path(from_table, to_table)` | Cypher: shortest path between two tables |
| `search_columns(keyword)` | Full-text search across column names and metadata |
| `get_table_clusters()` | Community detection: which tables are tightly connected? |
| `profile_status()` | Show when each database was last profiled |

## Project Structure

```
projects/dw-profiler/
├── src/dw_profiler/
│   ├── __init__.py
│   ├── crawler.py          # Phase 1: metadata extraction
│   ├── profiler.py         # Phase 2: column statistics + sampling
│   ├── matcher.py          # Phase 3: name, semantic, value matching
│   ├── graph.py            # Phase 4: Neo4j import/query
│   ├── mcp_tools.py        # Phase 5: MCP tool definitions
│   └── config.py           # Configuration (SQL Server + Neo4j)
├── scripts/
│   ├── crawl.py            # CLI: run full metadata crawl
│   ├── profile.py          # CLI: run profiling (all or specific DB)
│   ├── match.py            # CLI: run matching pipeline
│   ├── import_graph.py     # CLI: import into Neo4j
│   └── full_pipeline.py    # CLI: run everything end-to-end
├── data/                   # Raw profiling output (gitignored)
│   ├── metadata/
│   ├── profiles/
│   ├── samples/
│   ├── matches/
│   └── reports/
├── tests/
├── docs/
│   ├── architecture.md     # This document
│   ├── setup-guide.md      # Neo4j + Python setup
│   └── cypher-queries.md   # Useful graph queries for the team
├── docker/
│   └── docker-compose.yml  # Neo4j container
├── pyproject.toml
├── .env.example
└── README.md
```

## Dependencies

```toml
[project]
dependencies = [
    "pyodbc>=5.0",            # SQL Server connectivity
    "python-dotenv>=1.0",     # Environment config
    "neo4j>=5.0",             # Neo4j Python driver
    "pandas>=2.0",            # Data manipulation
    "pyarrow>=14.0",          # Parquet read/write
    "valentine-package",      # Schema matching algorithms
    "networkx>=3.0",          # Graph algorithms (optional, for analysis)
    "pyvis>=0.3",             # HTML graph export (optional)
    "fastmcp>=2.0",           # MCP server (if standalone)
]

[project.optional-dependencies]
profiling = ["ydata-profiling>=4.0"]  # Rich HTML reports
```

## Neo4j Setup

Run Neo4j via Docker (add to project's docker-compose):

```yaml
services:
  neo4j:
    image: neo4j:5-community
    ports:
      - "7474:7474"   # Browser UI
      - "7687:7687"   # Bolt protocol
    environment:
      NEO4J_AUTH: neo4j/your_password
    volumes:
      - neo4j_data:/data
volumes:
  neo4j_data:
```

Browse the graph at http://localhost:7474

## Estimated Scale

| Metric | Estimate |
|--------|----------|
| Databases | 5-15 |
| Tables | 50-500 |
| Columns | 500-5,000 |
| Neo4j nodes | ~6,000 (DB + Schema + Table + Column) |
| FK edges | ~200-500 |
| Inferred edges | ~1,000-10,000 (depends on threshold) |
| Profiling time (initial) | ~30 minutes |
| Profiling time (incremental) | ~5 minutes |
| Neo4j import time | < 1 minute |

## Open Questions

1. **Claude for semantic matching**: Should we use the Anthropic API directly in the
   matcher, or have the user review candidate matches via Claude Code conversation?
2. **Scheduling**: Should profiling run on a schedule (e.g., nightly) or on-demand only?
3. **Access control**: Should the profiler sample data from all databases, or should
   some be excluded? (sensitive data considerations)
4. **Historical tracking**: Should we version profiles over time to detect schema drift?
