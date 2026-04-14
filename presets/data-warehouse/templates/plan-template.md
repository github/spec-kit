# Data Warehouse Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link to spec.md]  
**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

> **Note**: This template is filled by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

---

## Summary

[Extract from spec: what data is being warehoused, core modeling decision, and ETL approach — 2–4 sentences]

---

## Technical Context

**Warehouse Platform**: [e.g., Snowflake, BigQuery, Redshift, Databricks Delta Lake, dbt + Postgres]  
**Orchestration**: [e.g., Apache Airflow, dbt Cloud, Azure Data Factory, Prefect, no orchestrator]  
**ETL/ELT Framework**: [e.g., dbt Core, PySpark, AWS Glue, custom Python, Dataform]  
**Source Connectivity**: [e.g., Fivetran, Airbyte, custom extractor, JDBC, S3 drop zone]  
**Data Quality Tool**: [e.g., dbt tests, Great Expectations, Soda Core, custom framework]  
**Schema Layer Convention**: [e.g., Raw → Staging → Mart; Medallion Bronze/Silver/Gold]  
**Testing**: [e.g., dbt tests + pytest, Great Expectations suites, cargo test]  
**Performance Goals**: [e.g., "Incremental load < 30 min on 5M rows/day; P1 queries < 5 sec"]  
**Constraints**: [e.g., "Budget cap $X/month on warehouse compute; no PII in unencrypted columns"]  
**Scale/Scope**: [e.g., "500M-row fact table; 10M new rows/day; 5-year retention"]

---

## Constitution Check

*GATE: Must pass before schema design. Re-check after ETL design.*

| Constitution Principle | Status | Notes |
|------------------------|--------|-------|
| Dimensional Modeling Standards | [ ] Pass / [ ] Violation | [e.g., grain defined, conformed dims reused] |
| Naming Conventions | [ ] Pass / [ ] Violation | [e.g., fct_/dim_/stg_ prefixes applied] |
| SCD Standards | [ ] Pass / [ ] Violation | [e.g., SCD type documented per dim attribute] |
| DQ Gates | [ ] Pass / [ ] Violation | [e.g., mandatory checks defined before serving] |
| Pipeline Idempotency | [ ] Pass / [ ] Violation | [e.g., re-run strategy defined] |

> Violations must be justified in the Complexity Tracking section below.

---

## Schema Design

### Modeling Approach

**Pattern Selected**: [Star Schema / Snowflake Schema / Data Vault / Wide/Flat Table / Hybrid]  
**Rationale**: [Why this pattern fits the grain statement and consumer query patterns from the spec]

### Fact Table Design

```text
[fct_table_name]
  Grain:       One row per [unit] per [time period]
  Fact Type:   Transaction / Periodic Snapshot / Accumulating Snapshot
  Load Type:   Incremental (watermark: [column]) / Full Refresh / Append-Only
  Partition:   [date_key / load_date / month_key]
  Cluster/Sort:[high-cardinality FK columns used in common filters]

  Surrogate Key:
    [fact_id]           BIGINT IDENTITY — system-generated, no business meaning

  Foreign Keys (→ dimension surrogate keys):
    [customer_key]      → dim_customer.[customer_key]
    [product_key]       → dim_product.[product_key]
    [date_key]          → dim_date.[date_key]

  Degenerate Dimensions (in fact, no supporting dim table):
    [order_number]      — source order identifier

  Additive Measures:
    [gross_amount]      DECIMAL(18,2)
    [net_revenue]       DECIMAL(18,2)  — derived: gross − discount − tax
    [quantity]          INTEGER

  Semi/Non-additive Measures:
    [account_balance]   DECIMAL(18,2)  — semi-additive (sum across products; not time)

  Audit Columns:
    [load_id]           VARCHAR        — pipeline run identifier
    [loaded_at]         TIMESTAMP      — warehouse load timestamp
    [source_system]     VARCHAR        — originating system name
```

### Dimension Table Designs

```text
[dim_customer]
  Business Key:   customer_id (from source; never updated)
  Surrogate Key:  customer_key  BIGINT IDENTITY
  SCD Strategy:   Mixed (see SCD table below)

  Attributes (Type 2 — track history):
    customer_segment, billing_address, tier

  Attributes (Type 1 — overwrite, always current):
    email, phone_number  [PII — always show current value]

  SCD Control Columns (Type 2 only):
    valid_from    TIMESTAMP NOT NULL
    valid_to      TIMESTAMP           — NULL = currently active row
    is_current    BOOLEAN NOT NULL DEFAULT TRUE

  Audit Columns:
    created_at, updated_at, source_system, load_id
```

```text
[dim_product]
  Business Key:   sku  (from source)
  Surrogate Key:  product_key  BIGINT IDENTITY
  SCD Strategy:   Type 1 — overwrite all attributes on change

  Key Attributes: product_name, category, subcategory, brand, list_price
  Audit Columns:  created_at, updated_at, source_system, load_id
```

### SCD Implementation Strategy

| Dimension | Attribute(s) | SCD Type | Implementation |
|-----------|-------------|----------|----------------|
| dim_customer | customer_segment, address, tier | Type 2 | INSERT new row; set `valid_to` + `is_current=FALSE` on prior |
| dim_customer | email, phone | Type 1 | UPDATE in place on change |
| dim_product | all attributes | Type 1 | MERGE/UPSERT on `sku` |
| dim_geography | region_name | Type 3 | `current_region` + `prior_region` columns; no extra row |

### Bridge Tables *(if applicable)*

```text
[bridge_customer_account]
  Purpose:    Resolve many-to-many between customers and accounts
  Weighting:  equal / proportional by [allocation_factor column]
  Columns:    customer_key, account_key, allocation_factor, valid_from, valid_to
```

---

## ETL/ELT Architecture

### Layer Definitions

```text
Layer 1 — RAW / BRONZE
  Schema:      raw  (or  bronze)
  Contents:    Exact replica of source; zero transformations
  Load Type:   Append-only with load_timestamp + source_file metadata
  Retention:   [90 days / indefinite]
  Access:      Data engineering only (not exposed to BI consumers)

Layer 2 — STAGING / SILVER
  Schema:      staging  (or  silver)
  Contents:    Typed, cleaned, deduplicated, schema-validated data
  Load Type:   Truncate-reload per batch  OR  incremental by watermark
  Transformations: type casting, NULL handling, deduplication, rejection routing
  Access:      Data engineering only

Layer 3 — SERVING / MART / GOLD
  Schema:      mart  (or  gold)
  Contents:    Dimensional model — fact and dimension tables
  Load Type:   Incremental MERGE  OR  DELETE+INSERT by partition
  Access:      BI tools, analysts, data science, application APIs
```

### Load Strategy per Table

| Table | Load Type | Watermark Column | Dedup Strategy | Est. Duration |
|-------|-----------|-----------------|----------------|--------------|
| `raw.[source_table]` | Append | `load_timestamp` | None (raw = unmodified) | ~[X] min |
| `staging.[entity]` | Truncate-Reload | N/A | Dedupe on `[business_key]` | ~[X] min |
| `dim_customer` | SCD Merge | `customer_id` | Merge on business key | ~[X] min |
| `fct_sales` | Incremental Merge | `updated_at` | Merge on `[grain_cols]` | ~[X] min |
| `dim_date` | Static | N/A | Pre-populated; skip | N/A |

### Idempotency Design

| Layer | Re-run Strategy |
|-------|----------------|
| Raw | Append with `(source_file, record_hash)` dedup; idempotent via dedup key |
| Staging | Truncate before reload; or `DELETE WHERE load_date = :run_date` then INSERT |
| Dimensions | MERGE on business key; SCD2 hash comparison prevents duplicate row inserts |
| Facts | `DELETE WHERE [partition_key] = :run_date` then INSERT; or MERGE on grain |

---

## Data Quality Implementation

### DQ Check Design

| Check ID | Layer | Check Type | Implementation | Failure Action |
|----------|-------|-----------|----------------|---------------|
| DQ-001 | Staging | NOT NULL on `[pk_col]` | `dbt not_null` test | Abort pipeline; quarantine rows |
| DQ-002 | Mart | Referential integrity | `dbt relationships` test | Abort pipeline |
| DQ-003 | Mart | Duplicate grain | `dbt unique` on `[grain_cols]` | Abort pipeline |
| DQ-004 | Mart | Row count variance | Custom macro: ±[X]% vs prior run | Abort pipeline |
| DQ-005 | Staging | NULL rate threshold | Custom macro: NULL% on `[col]` | Alert only |
| DQ-006 | Mart | Measure anomaly | Custom macro: 7-day rolling avg | Alert only |

### Quarantine Schema

```text
quarantine.[table_name]_rejected
  Mirrors all columns of the source table, plus:
    rejection_reason    VARCHAR         — which DQ check failed and why
    rejected_at         TIMESTAMP       — when the record was quarantined
    source_run_id       VARCHAR         — pipeline run that rejected this row
    is_reprocessed      BOOLEAN         DEFAULT FALSE
```

### Alerting & Observability

- **Run audit table**: `[warehouse].[pipeline_runs]`  
  Tracks: `run_id`, `pipeline_name`, `started_at`, `finished_at`, `rows_ingested`, `rows_rejected`, `dq_checks_passed`, `dq_checks_failed`, `status`
- **Failure alerting**: [e.g., Slack webhook on DQ-001/002/003 abort; PagerDuty on SLA breach]
- **Health dashboard**: [e.g., pipeline health view in Tableau / Grafana / Metabase]

---

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── spec.md              # Feature specification (source of truth)
├── plan.md              # This file
├── data-lineage.md      # Source-to-target field mapping (column level)
├── data-contracts/      # Source system contracts
│   └── [source_name]-contract.md
├── quickstart.md        # Sign-off queries + expected results for each use case
└── tasks.md             # Implementation tasks (created by /speckit.tasks)
```

### Source Code Structure

```text
# Option A: dbt project
models/
├── staging/
│   └── [source_name]/
│       ├── stg_[source]__[entity].sql    # One staging model per source table
│       └── schema.yml                    # dbt tests + column docs
├── intermediate/                         # Complex multi-source joins (optional)
│   └── int_[domain]__[transform].sql
└── marts/
    └── [domain]/
        ├── fct_[business_process].sql    # Fact table
        ├── dim_[entity].sql              # Dimension tables
        └── schema.yml                   # dbt tests + consumer-facing docs

# Option B: Spark / Python ETL
pipelines/
├── extract/
│   └── [source_name]_extractor.py
├── transform/
│   ├── staging/
│   │   └── [source]_staging.py
│   └── marts/
│       ├── [fact_table]_transform.py
│       └── [dimension]_transform.py
├── load/
│   └── warehouse_loader.py
├── quality/
│   └── dq_checks.py
└── orchestration/
    └── [pipeline_name]_dag.py

tests/
├── unit/
│   └── test_[transform]_business_rules.py
├── integration/
│   └── test_[pipeline]_end_to_end.py
└── data_quality/
    └── [source_name]_dq_suite.py
```

**Structure Decision**: [Document which option was selected and why]

---

## Complexity Tracking

> **Fill ONLY when Constitution Check has violations that require justification**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| [e.g., Snowflake schema vs. star] | [specific query pattern prevents star] | [star schema caused fan-out join issues] |
| [e.g., Data Vault instead of direct mart] | [full audit trail required by compliance] | [direct mart cannot preserve source provenance] |
