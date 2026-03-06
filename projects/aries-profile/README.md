# ARIES Profile

Documentation and profiling of Aries database views on the **dbaries** SQL Server.

## Contents

- [AC_ Views Profile](docs/ac-views-profile.md) — All 19 `AC_` views in the WARIES database:
  source tables, join logic, filters, column maps, and Mermaid diagrams.

## Quick Reference

| View | Type | Source DB | Description |
|------|------|-----------|-------------|
| AC_PROPERTY | Pass-through | ARIES_COMMON | Master well/property data (filtered to WARIES) |
| AC_COST | Pass-through | ARIES_COMMON | Operating costs, severance, capital |
| AC_DAILY | Pass-through | ARIES_COMMON | Daily production |
| AC_MONTHLY | Pass-through | ARIES_REPORTING | Monthly economic output by scenario |
| AC_PRODUCT | Pass-through | ARIES_COMMON | Monthly production actuals |
| AC_SHRINK | Pass-through | ARIES_COMMON | Gas shrinkage/processing parameters |
| AC_NOTE | Pass-through | ARIES_COMMON | Engineering notes |
| AC_DAILY_V | Join | WARIES | Daily production + well metadata |
| AC_MONTHLY_V | Join | WARIES | Monthly economics (WARBASE scenarios) |
| AC_MONTHLY_AFE_EVAL_V | Join | WARIES | Monthly economics (EVAL scenario) |
| AC_MONTHLY_MYTIEOUT_V | Join | WARIES | YE2019 tie-out aggregation |
| AC_ONELINE_V | Join | WARIES | One-line economics + property + BFIT flag |
| AC_ONELINE_V_ATHENA | Join | WARIES | Athena scenario + ownership interests |
| AC_PROD_NEW_WELLS_V | Join | WARIES | Production for wells < 2 years old |
| AC_PROPERTY_SPOTFIRE_V | Join | WARIES | Full dashboard view (property + cost + shrink + interest) |
| AC_PROPERTY_EVAL_PRE_COMMON | Pass-through | ARIES_COMMON | Pre-common EVAL property data |
| AC_PROPERTY_WARIES_PRE_COMMON | Pass-through | ARIES_COMMON | Pre-common WARIES property data |
| AC_DAILY_BACKPUP | Pass-through | ARIES_COMMON_1_27 | Daily production backup |
| ACQ | Filtered | WARIES | AC_PROPERTY where DBSKEY = 'ACQ' |

## Server Details

- **Server:** dbaries
- **Databases referenced:** WARIES, ARIES_COMMON, ARIES_REPORTING, ARIES_COMMON_1_27
- **Auth:** SQL auth (AriesRO) with VIEW DEFINITION permission
