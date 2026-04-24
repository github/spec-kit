---
description: Create a data warehouse implementation plan and store it in plan.md.
handoffs:
  - label: Generate DW Task List
    agent: speckit.tasks
    prompt: Generate the implementation task list for this data warehouse plan
---

## User Input

```text
$ARGUMENTS
```

## Outline

### 1. Load Context

- Read `.specify/feature.json` to get the feature directory path
- Read `<feature_directory>/spec.md` — the authoritative source of truth
- Read `.specify/memory/constitution.md` — project standards that govern every decision
- Read `<feature_directory>/data-contracts/` if present — source system schemas and SLAs

### 2. Constitution Check

Before any design work, verify the spec is compatible with the project constitution. Populate the Constitution Check table in `plan.md`:

| Principle | Status | Notes |
|-----------|--------|-------|
| Dimensional Modeling Standards | Pass / Violation | Grain defined? Conformed dims identified? |
| Naming Conventions | Pass / Violation | fct_/dim_/stg_ prefixes will be used? |
| SCD Standards | Pass / Violation | SCD type documented per dim attribute? |
| DQ Gates | Pass / Violation | Mandatory checks defined before serving? |
| Pipeline Idempotency | Pass / Violation | Re-run strategy clear? |

Record any violations in the Complexity Tracking section with justification. If a violation cannot be justified, surface it to the user before continuing.

### 3. Schema Design

Design the physical schema using the spec's Dimensional Model section:

**Fact Tables**: For each fact in the spec:
- Define the physical grain columns (which columns together form the grain)
- Choose Fact Type (Transaction / Periodic Snapshot / Accumulating Snapshot)
- List all foreign keys (to which dimension) and degenerate dimensions
- List all measures with additive / semi-additive / non-additive classification
- Choose Load Type: Incremental (with watermark column) / Full Refresh / Append-Only
- Choose Partition column (almost always `date_key` or equivalent date column)
- Choose Clustering/Sorting columns (FK columns used in common filters)
- Add standard audit columns: `load_id`, `loaded_at`, `source_system`

**Dimension Tables**: For each dimension in the spec:
- Define business key (from source; immutable)
- Define surrogate key (system-generated BIGINT)
- Document SCD strategy per attribute (use the spec's SCD column):
  - Type 1 (overwrite): UPDATE in place
  - Type 2 (history): new row on change with `valid_from / valid_to / is_current`
  - Type 3 (prior+current): add `prior_[attribute]` column, UPDATE in place
  - Static: no SCD logic needed
- List all descriptive attributes
- Add standard audit columns

**Bridge Tables** (if many-to-many relationships exist): Define weighting scheme and validity window.

### 4. ETL/ELT Architecture

Design the pipeline layer by layer:

**Layer Definitions**: Document schema names, contents, load type, retention policy, and access controls for each layer (Raw, Staging, Mart) per the constitution's layer naming convention.

**Load Strategy per Table**: For every table, specify:
- Load type (append, truncate-reload, incremental MERGE, incremental DELETE+INSERT)
- Watermark column (for incremental loads)
- Deduplication strategy (dedup key, hash-based, MERGE key)
- Estimated duration at expected volume

**Idempotency Design**: For each layer, document the re-run strategy that prevents duplicate data. No pipeline may silently create duplicates on re-execution.

### 5. Data Quality Implementation

Map each DQ check from the spec to a concrete implementation:

For each DQ-### item in the spec:
- Which layer does this check run in? (Staging or Mart)
- How is it implemented? (dbt test, custom macro, Great Expectations suite, Python assertion)
- What exactly triggers failure? (NULL count > 0, duplicate count > 0, row count delta > X%)
- Failure action: abort pipeline and quarantine, or alert and continue?

**Quarantine Schema**: Define the `quarantine.[table]_rejected` DDL (mirrors source columns + `rejection_reason`, `rejected_at`, `source_run_id`, `is_reprocessed`).

**Observability**: Define the `pipeline_runs` audit table schema and any alerting integrations (Slack, PagerDuty, email).

### 6. Source-to-Target Field Mapping

Create `<feature_directory>/data-lineage.md` with a column-level mapping table:

| Target Table | Target Column | Source System | Source Table | Source Column | Transformation Rule |
|-------------|--------------|--------------|-------------|--------------|---------------------|
| fct_[name] | net_revenue | [CRM] | orders | amount | `amount - discount - tax` |
| dim_customer | customer_segment | [CRM] | customers | spend_tier_code | `'A' → 'Premium'; 'B' → 'Standard'` |

### 7. Source System Contracts

For each source system in the spec, create `<feature_directory>/data-contracts/[source_name]-contract.md`:

```markdown
# Data Contract: [Source System Name]

**Version**: 1.0  **Owner**: [Team]  **Effective**: [DATE]

## Delivery
- Format: [REST API / flat file / DB snapshot / CDC stream]
- Schedule: [Nightly at HH:MM UTC / real-time / on-demand]
- Location: [S3 path / API endpoint / JDBC connection name]

## Schema Guarantee
[List columns the source guarantees will always be present and non-null]

## Known Limitations
[List known data quality issues, schema instability risks, or latency variances]

## Change Notification
[How source team will communicate schema changes — SLA for advance notice]
```

### 8. Quickstart Validation Document

Create `<feature_directory>/quickstart.md` with sign-off queries for each consumer use case:

```markdown
# Quickstart Validation: [FEATURE NAME]

## Use Case 1 Sign-Off Query (P1)

[SQL query that a business stakeholder can run to verify the P1 use case]

Expected result: [Describe what correct output looks like; include row count or totals if known]

## Use Case 2 Sign-Off Query (P2)

[SQL query for P2 validation]

Expected result: [Description]

## Reconciliation Query

[Query to compare total measures in the warehouse against a known source system total]
```

### 9. Project Structure Decision

Based on the technical context (platform, framework, team conventions), select and document the source code structure. Show only the chosen option — remove unused options from plan.md.

### 10. Write plan.md

Write the complete plan to `<feature_directory>/plan.md` using the DW plan template structure. Every section must be concrete — no placeholders left in the final output.

### 11. Report Completion

Report to the user:
- `plan.md` location
- Schema design summary (list fact and dimension tables)
- SCD strategy summary (dimension → SCD type mapping)
- Load strategy summary (table → load type)
- Constitution check results
- Artifacts created: `data-lineage.md`, `data-contracts/`, `quickstart.md`
- Next step: `/speckit.tasks`

---

## DW Planning Quick Guidelines

- **Schema decisions are implementation; SCD decisions are business** — the spec owns SCD type; the plan owns the SQL implementation
- **Never leave load type as "TBD"** — every table must have a documented strategy before tasks can be written
- **Grain integrity is paramount** — verify the chosen fact load strategy cannot produce duplicate rows at the grain
- **Dimension surrogate key stability matters** — if a dimension's surrogate key changes on reload, all fact foreign keys are broken
- **Always prefer star schema** over snowflake unless the constitution explicitly allows snowflake and there's a documented reason
- **Document the idempotency strategy** explicitly for every table — "use MERGE" is not enough; specify the MERGE key
