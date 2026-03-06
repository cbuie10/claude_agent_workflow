# Aries Database Ecosystem

> How WARIES, EVAL, and ARIES_COMMON share data on the **dbaries** SQL Server.

## The Big Picture

ARIES_COMMON is the **single source of truth** for well and property data. The
WARIES and EVAL databases don't store their own copies — they create **views**
that point back to ARIES_COMMON tables. Each database sees only the properties
assigned to it via filter columns in the common tables.

```mermaid
graph TB
    subgraph LEGEND[" "]
        direction LR
        L1[🟦 Base Table]
        L2[🟨 View]
        L3[🟩 Reporting Table]
    end

    subgraph AC["ARIES_COMMON — Master Database"]
        direction TB
        APC["🟦 AC_PROPERTY_COMMON<br/>───────────────────<br/>168 columns · 272,867 rows<br/><b>The master property table</b><br/>Contains WARIES_ and EVAL_<br/>prefixed columns for each DB"]
        ACC["🟦 AC_COST<br/>30 cols · 95K rows"]
        ACD["🟦 AC_DAILY<br/>13 cols · 25.4M rows"]
        ACPROD["🟦 AC_PRODUCT<br/>17 cols · 28.6M rows"]
        ACS["🟦 AC_SHRINK<br/>20 cols · 95K rows"]
        ACN["🟦 AC_NOTE<br/>4 cols · 130K rows"]
        APEPC["🟦 AC_PROPERTY_EVAL_PRE_COMMON<br/>106 cols · 72K rows"]
        APWPC["🟦 AC_PROPERTY_WARIES_PRE_COMMON<br/>89 cols · 12.7K rows"]
    end

    subgraph AR["ARIES_REPORTING"]
        ACM_SRC["🟩 AC_MONTHLY<br/>Monthly economic output"]
    end

    subgraph W["WARIES — Reserves & Economics"]
        direction TB
        W_PROP["🟨 AC_PROPERTY<br/><i>WARIES_DBSKEY → DBSKEY</i><br/><i>WARIES_WEG_RSV_CAT → WEG_RSV_CAT</i><br/>Filter: both NOT NULL"]
        W_COST["🟨 AC_COST"]
        W_DAILY["🟨 AC_DAILY"]
        W_PROD["🟨 AC_PRODUCT"]
        W_SHRINK["🟨 AC_SHRINK"]
        W_NOTE["🟨 AC_NOTE"]
        W_MONTHLY["🟨 AC_MONTHLY"]
        W_APEPC["🟨 AC_PROPERTY_EVAL_PRE_COMMON"]
        W_APWPC["🟨 AC_PROPERTY_WARIES_PRE_COMMON"]
        W_RPT["🟨 8 Reporting Views<br/><i>AC_DAILY_V, AC_MONTHLY_V,<br/>AC_ONELINE_V, AC_PROPERTY_SPOTFIRE_V,<br/>AC_PROD_NEW_WELLS_V, ACQ, etc.</i>"]
    end

    subgraph E["EVAL — Evaluation Scenarios"]
        direction TB
        E_PROP["🟨 AC_PROPERTY<br/><i>EVAL_DBSKEY → DBSKEY</i><br/><i>EVAL_WEG_RSV_CAT → WEG_RSV_CAT</i><br/>Filter: both NOT NULL"]
        E_DAILY["🟨 AC_DAILY"]
        E_PROD["🟨 AC_PRODUCT"]
        E_NOTE["🟨 AC_NOTE"]
        E_SHRINK["🟨 AC_SHRINK_OLD_10_21_19"]
        E_APEPC["🟨 AC_PROPERTY_EVAL_PRE_COMMON"]
        E_APWPC["🟨 AC_PROPERTY_WARIES_PRE_COMMON"]
        E_RPT["🟨 7 Reporting Views<br/><i>AC_MONTHLY_UNION_V,<br/>AC_ONELINE_UNION_V,<br/>AC_PROPERTY_UNION_V, etc.</i>"]
        E_LOCAL["🟦 36 Local AC_ Tables<br/><i>AC_ECONOMIC, AC_INTEREST,<br/>AC_ONELINE, AC_RESERVES,<br/>AC_FCST, AC_DEAL, etc.</i>"]
    end

    APC -->|"view"| W_PROP
    ACC -->|"view"| W_COST
    ACD -->|"view"| W_DAILY
    ACPROD -->|"view"| W_PROD
    ACS -->|"view"| W_SHRINK
    ACN -->|"view"| W_NOTE
    APEPC -->|"view"| W_APEPC
    APWPC -->|"view"| W_APWPC
    ACM_SRC -->|"view"| W_MONTHLY

    APC -->|"view"| E_PROP
    ACD -->|"view"| E_DAILY
    ACPROD -->|"view"| E_PROD
    ACN -->|"view"| E_NOTE
    ACS -->|"view"| E_SHRINK
    APEPC -->|"view"| E_APEPC
    APWPC -->|"view"| E_APWPC

    W_PROP --> W_RPT
    W_COST --> W_RPT
    W_SHRINK --> W_RPT
    W_MONTHLY --> W_RPT

    E_PROP --> E_RPT
    E_LOCAL --> E_RPT
```

---

## How Property Assignment Works

The key to the whole system is **AC_PROPERTY_COMMON** in ARIES_COMMON. It has
168 columns and contains **every property across all Aries databases**. Each
database gets its own set of filter/assignment columns:

```mermaid
graph LR
    subgraph APC["AC_PROPERTY_COMMON (168 columns)"]
        direction TB
        SHARED["Shared columns<br/>─────────────<br/>PROPNUM, WELL_NAME, API,<br/>LEASE, STATE, COUNTY,<br/>LATITUDE, LONGITUDE,<br/>... ~160 shared fields"]
        WARIES_COLS["WARIES columns<br/>─────────────<br/>WARIES_DBSKEY<br/>WARIES_WEG_RSV_CAT"]
        EVAL_COLS["EVAL columns<br/>─────────────<br/>EVAL_DBSKEY<br/>EVAL_WEG_RSV_CAT<br/>EVAL_STATUS"]
    end

    subgraph WARIES_VIEW["WARIES.dbo.AC_PROPERTY"]
        W["SELECT ...<br/>WARIES_DBSKEY <b>AS DBSKEY</b>,<br/>WARIES_WEG_RSV_CAT <b>AS WEG_RSV_CAT</b>,<br/>... shared columns ...<br/>WHERE WARIES_DBSKEY IS NOT NULL<br/>AND WARIES_WEG_RSV_CAT IS NOT NULL"]
    end

    subgraph EVAL_VIEW["EVAL.dbo.AC_PROPERTY"]
        EV["SELECT ...<br/>EVAL_DBSKEY <b>AS DBSKEY</b>,<br/>EVAL_WEG_RSV_CAT <b>AS WEG_RSV_CAT</b>,<br/>... shared columns ...<br/>WHERE EVAL_DBSKEY IS NOT NULL<br/>AND EVAL_WEG_RSV_CAT IS NOT NULL"]
    end

    WARIES_COLS --> W
    SHARED --> W
    EVAL_COLS --> EV
    SHARED --> EV
```

**What this means in practice:**

- A property in WARIES has `WARIES_DBSKEY` and `WARIES_WEG_RSV_CAT` populated
- A property in EVAL has `EVAL_DBSKEY` and `EVAL_WEG_RSV_CAT` populated
- A property can exist in **both** databases (both sets of columns populated)
- Each database's view aliases away the prefix, so `DBSKEY` always means "my database's key"
- EVAL's AC_PROPERTY also exposes `WARIES_DBSKEY` and `WARIES_WEG_RSV_CAT` as-is (columns 121 and 134), allowing cross-database lookups

---

## Shared vs. Local Data

```mermaid
graph TD
    subgraph shared["Shared Data (lives in ARIES_COMMON)"]
        direction LR
        S1["Well/Property master<br/>(AC_PROPERTY_COMMON)"]
        S2["Operating costs<br/>(AC_COST)"]
        S3["Daily production<br/>(AC_DAILY)"]
        S4["Monthly production<br/>(AC_PRODUCT)"]
        S5["Shrinkage params<br/>(AC_SHRINK)"]
        S6["Notes<br/>(AC_NOTE)"]
    end

    subgraph reporting["Shared Reporting (lives in ARIES_REPORTING)"]
        R1["Monthly economics<br/>(AC_MONTHLY)"]
    end

    subgraph local_eval["EVAL-Only Data (local tables)"]
        direction LR
        L1["AC_ECONOMIC (48+ scenarios)"]
        L2["AC_INTEREST"]
        L3["AC_ONELINE"]
        L4["AC_RESERVES"]
        L5["AC_DEAL"]
        L6["AC_FCST / AC_PZFCST"]
        L7["AC_DETAIL / AC_ECOSUM"]
        L8["AC_HISTORIC / AC_RATIO"]
        L9["AC_WELL / AC_TEST"]
        L10["AC_OWNER / AC_SETUP"]
    end

    subgraph local_waries["WARIES-Only Data"]
        direction LR
        W1["AC_ONELINE (local table)"]
        W2["BFIT_LIST_V"]
        W3["FULL_INTEREST_V"]
    end

    shared -->|"Both WARIES and EVAL<br/>create views to this data"| WARIES_EVAL["WARIES & EVAL"]
    reporting -->|"Both reference<br/>monthly economics"| WARIES_EVAL
```

### Key difference between WARIES and EVAL

| Aspect | WARIES | EVAL |
|--------|--------|------|
| **Purpose** | Reserves & economics reporting | Evaluation scenarios |
| **AC_ views (from common)** | 9 pass-through views | 7 pass-through views |
| **AC_ reporting views** | 8 join views | 7 join/union views |
| **Local AC_ base tables** | Few (AC_ONELINE) | 36 tables (economics, forecasts, deals, interests, reserves) |
| **AC_PROPERTY filter** | `WARIES_DBSKEY IS NOT NULL` | `EVAL_DBSKEY IS NOT NULL` (inferred) |

EVAL has significantly more local tables because it stores detailed economic
run outputs (scenarios, forecasts, reserves) that don't need to be shared.

---

## The PROPNUM Key

Every table and view in the ecosystem joins on `PROPNUM` (varchar 12). This is
the universal well/property identifier across all Aries databases.

```mermaid
erDiagram
    AC_PROPERTY_COMMON {
        varchar PROPNUM PK
        varchar WARIES_DBSKEY
        varchar WARIES_WEG_RSV_CAT
        varchar EVAL_DBSKEY
        varchar EVAL_WEG_RSV_CAT
        varchar EVAL_STATUS
    }
    AC_COST {
        varchar PROPNUM PK
    }
    AC_DAILY {
        varchar PROPNUM PK
        date D_DATE PK
    }
    AC_PRODUCT {
        varchar PROPNUM PK
        date P_DATE PK
    }
    AC_SHRINK {
        varchar PROPNUM PK
    }
    AC_NOTE {
        varchar PROPNUM PK
        datetime NOTE_DATE PK
    }
    AC_MONTHLY {
        varchar PROPNUM PK
        varchar SCENARIO PK
        date OUTDATE PK
    }

    AC_PROPERTY_COMMON ||--o| AC_COST : PROPNUM
    AC_PROPERTY_COMMON ||--o{ AC_DAILY : PROPNUM
    AC_PROPERTY_COMMON ||--o{ AC_PRODUCT : PROPNUM
    AC_PROPERTY_COMMON ||--o| AC_SHRINK : PROPNUM
    AC_PROPERTY_COMMON ||--o{ AC_NOTE : PROPNUM
    AC_PROPERTY_COMMON ||--o{ AC_MONTHLY : PROPNUM
```

---

## Data Flow Summary

```mermaid
flowchart TB
    subgraph ENTRY["Data Entry / ETL"]
        IHS["IHS / Enverus<br/>(production data)"]
        ENG["Engineering team<br/>(property setup, costs)"]
        ARIES_APP["Aries application<br/>(economic runs)"]
    end

    subgraph COMMON["ARIES_COMMON"]
        direction LR
        PROP["AC_PROPERTY_COMMON<br/>(272K properties)"]
        PROD_DATA["AC_PRODUCT (28.6M rows)<br/>AC_DAILY (25.4M rows)<br/>AC_COST · AC_SHRINK · AC_NOTE"]
    end

    subgraph REPORTING["ARIES_REPORTING"]
        MONTHLY["AC_MONTHLY<br/>(scenario outputs)"]
    end

    subgraph CONSUMERS["Consumer Databases"]
        direction LR
        WARIES_DB["WARIES<br/>19 AC_ views<br/>Reserves & reporting"]
        EVAL_DB["EVAL<br/>14 AC_ views + 36 local tables<br/>Evaluation scenarios"]
    end

    subgraph TOOLS["Downstream Tools"]
        direction LR
        SPOTFIRE["Spotfire dashboards"]
        ATHENA["Athena reports"]
        ENGINEERS["Engineering analysis"]
    end

    IHS --> PROD_DATA
    ENG --> PROP
    ENG --> PROD_DATA
    ARIES_APP --> MONTHLY
    ARIES_APP --> EVAL_DB

    PROP -->|"filtered views"| CONSUMERS
    PROD_DATA -->|"pass-through views"| CONSUMERS
    MONTHLY -->|"pass-through views"| CONSUMERS

    WARIES_DB --> TOOLS
    EVAL_DB --> TOOLS
```

---

## Scale Reference

| Database | AC_ Tables | AC_ Views | Key Table | Rows |
|----------|-----------|-----------|-----------|------|
| **ARIES_COMMON** | 8 active + backups | 3 | AC_PROPERTY_COMMON | 272,867 |
| | | | AC_PRODUCT | 28,620,396 |
| | | | AC_DAILY | 25,449,014 |
| | | | AC_COST | 95,435 |
| | | | AC_SHRINK | 95,220 |
| | | | AC_NOTE | 129,815 |
| **ARIES_REPORTING** | 1 active | 0 | AC_MONTHLY | (scenario output) |
| **WARIES** | 0 (views only) | 19 | — | — |
| **EVAL** | 36 | 14 | AC_ECONOMIC, AC_INTEREST, etc. | (local scenarios) |

---

## Key Takeaways

1. **Don't edit ARIES_COMMON directly** — changes propagate to all databases instantly through views
2. **Property assignment** is controlled by populating `WARIES_DBSKEY`/`EVAL_DBSKEY` in AC_PROPERTY_COMMON
3. **Production and cost data is shared** — AC_DAILY, AC_PRODUCT, AC_COST, AC_SHRINK are the same data in both WARIES and EVAL
4. **Monthly economics come from ARIES_REPORTING** — Aries application writes scenario outputs there
5. **EVAL has local tables** for detailed economic modeling that WARIES doesn't need
6. **PROPNUM is the universal key** — every join in the ecosystem uses it
