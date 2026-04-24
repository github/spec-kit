# [PROJECT_NAME] Data Warehouse Constitution

<!--
  This constitution defines the non-negotiable standards for all data warehouse development
  in this project. It supersedes individual preferences and local conventions.
  Amendments require documented rationale, team review, and a migration plan.
-->

---

## I. Dimensional Modeling Standards (NON-NEGOTIABLE)

All warehouse models MUST follow dimensional modeling principles:

- Every fact table MUST have a **grain statement** documented in its feature spec before implementation begins
- Fact tables contain **measures** (additive, semi-additive, or non-additive) plus **foreign keys** to dimension tables — no business logic columns
- Dimension tables contain **descriptive attributes** plus a system-generated surrogate key and the source business key
- Raw and staging data MUST NOT be exposed to BI consumers — only the mart/serving layer is consumer-facing
- **Conformed dimensions** MUST be shared across fact tables — never duplicated with different definitions
- The modeling pattern (star, snowflake, data vault) MUST be justified in the feature plan

---

## II. Naming Conventions (NON-NEGOTIABLE)

**Table Prefixes**:

| Object Type | Prefix | Example |
|-------------|--------|---------|
| Fact tables | `fct_` | `fct_orders`, `fct_web_sessions` |
| Dimension tables | `dim_` | `dim_customer`, `dim_product` |
| Staging models | `stg_[source]__[entity]` | `stg_salesforce__accounts` (double underscore) |
| Intermediate models | `int_[domain]__[transform]` | `int_finance__revenue_allocation` |
| Aggregate tables | `agg_[fact]_[grain]` | `agg_orders_monthly` |
| Bridge tables | `bridge_[a]_[b]` | `bridge_customer_account` |
| Quarantine tables | `quarantine.[table]_rejected` | `quarantine.fct_orders_rejected` |

**Column Conventions**:

| Column Type | Convention | Example |
|------------|-----------|---------|
| Surrogate keys | `[entity]_key` (BIGINT) | `customer_key`, `product_key` |
| Business/natural keys | `[entity]_id` | `customer_id`, `order_id` |
| SCD Type 2 control | `valid_from`, `valid_to`, `is_current` | — |
| Audit columns (all tables) | `created_at`, `updated_at`, `source_system`, `load_id` | — |
| All column names | snake_case, lowercase | `net_revenue`, `order_line_id` |

**Schema/Layer Names**:

| Layer | Name |
|-------|------|
| Raw ingestion | `raw` or `bronze` |
| Cleaned/typed | `staging` or `silver` |
| Consumer-facing | `mart` or `gold` |

---

## III. SCD (Slowly Changing Dimension) Standards (NON-NEGOTIABLE)

- The SCD type for **every dimension attribute** MUST be documented in the feature spec before any dimension is built
- **SCD Type 2** MUST use these control columns: `valid_from TIMESTAMP NOT NULL`, `valid_to TIMESTAMP` (NULL = currently active row), `is_current BOOLEAN NOT NULL`
- **Business keys are immutable** — they MUST never be updated; only descriptive attributes may change
- **Surrogate keys are system-generated** — they carry no business meaning and MUST never be exposed to source systems
- Historical rows in SCD Type 2 dimensions MUST be **preserved permanently** — never deleted during normal operation

---

## IV. Data Quality Gates (NON-NEGOTIABLE)

All pipelines MUST enforce these gates before data reaches the serving layer:

1. **No NULLs** in surrogate keys or business key columns
2. **No duplicates** at the defined grain of every fact table
3. **Referential integrity** — every fact foreign key must resolve to a dimension surrogate key
4. **Row count plausibility** — new load row count must be within an expected variance of the prior load

**Failure policy**: Pipelines that fail a mandatory DQ check MUST abort and route failing records to the quarantine table. Silent continuation is prohibited.

**Warning checks** (NULL rate thresholds, measure anomaly detection) MUST alert but MUST NOT block the pipeline.

---

## V. Pipeline Idempotency (NON-NEGOTIABLE)

All ETL/ELT pipelines MUST be idempotent:

- Re-running the pipeline for the **same time window** MUST produce **identical results** — no data duplication
- Each pipeline run MUST be identifiable via a unique `load_id` (run identifier)
- **Full reloads** MUST be executable without manual table manipulation
- The idempotency strategy (MERGE, DELETE+INSERT by partition, or truncate-reload) MUST be documented in the feature plan for every table

---

## VI. Data Lineage & Documentation

- Every model MUST have a **source-to-target field mapping** (`data-lineage.md`) completed before implementation
- **Business rule derivations** MUST be documented in the feature spec — not only in code comments
- All mart tables MUST include **column-level descriptions** in the schema metadata (dbt `schema.yml` or equivalent)
- Each feature MUST include a `quickstart.md` with sign-off queries and expected results for each consumer use case

---

## VII. Performance Standards

- Consumer-facing fact tables MUST be **partitioned by date** unless explicitly justified otherwise
- **Query patterns known at design time** MUST be supported by clustering, sorting, or indexing documented in the plan
- Incremental loads MUST complete within the SLA window defined in the feature spec
- **Unbounded full-table scans** on mart tables (for regular consumer queries) MUST be justified in the plan's Complexity Tracking section

---

## VIII. Security & Compliance

[Define project-specific rules — examples below; replace or remove as appropriate]

- Columns containing PII MUST be identified in the feature spec and treated as SCD Type 1 (always current, no history)
- PII columns MUST NOT appear in quarantine tables in plaintext — use tokenization or hashing
- Data retention periods MUST be defined per table in the feature spec and enforced by automated purge jobs
- Access to raw and staging layers is restricted to the data engineering team; mart access is role-controlled per consumer group

---

## [Project-Specific Standards]

[Add additional standards relevant to your organization: compliance frameworks, specific platform rules, approved technology list, etc.]

---

## Governance

- This constitution **supersedes** all local conventions, individual preferences, and prior practices
- Amendments require: written rationale, review by at least two senior team members, and a migration plan for any existing models affected
- All feature plans MUST include a **Constitution Check table** verifying compliance before implementation begins
- Constitution violations MUST be documented and justified in the plan's Complexity Tracking section — unexplained violations block code review approval

**Version**: 1.0.0 | **Ratified**: [DATE] | **Last Amended**: [DATE]
