---
name: Pipeline Request
about: Request a new ETL pipeline for Claude to build
title: "@claude: [Pipeline Name]"
labels: pipeline-request
---

## Data Source
<!-- What API or data source should be extracted from? Include the URL. -->

## Target Table
<!-- What should the PostgreSQL table be called? Describe the columns. -->

## Transform Requirements
<!-- What transformations should be applied? Filtering? Type conversions? -->

## Acceptance Criteria
- [ ] Extract task fetches data from the source
- [ ] Transform task processes raw data into the target schema
- [ ] Load task upserts into the PostgreSQL table
- [ ] Flow composes all three tasks with logging
- [ ] Unit tests pass for all new tasks
- [ ] Lint passes with ruff
- [ ] SQL CREATE TABLE statement added to docker/init.sql
