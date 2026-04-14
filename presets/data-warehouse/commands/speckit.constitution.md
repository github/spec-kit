---
description: Create or update the data warehouse project constitution in .specify/memory/constitution.md.
---

## User Input

```text
$ARGUMENTS
```

## Outline

### 1. Collect Project Context

Ask the user (or infer from the current project if files exist) for:

**Warehouse Platform**
- What database/platform? (Snowflake, BigQuery, Redshift, Databricks, Postgres+dbt, etc.)
- Are there multiple environments? (dev, staging, prod)

**Modeling Philosophy**
- Default modeling pattern? (Star schema preferred / Snowflake schema allowed / Data Vault required)
- Are conformed dimensions required? Or is each domain fully autonomous?

**Naming Conventions**
- Any project-specific deviations from the standard `fct_/dim_/stg_` convention?
- Schema/layer names? (raw/staging/mart vs. bronze/silver/gold vs. custom)
- Any column naming conventions beyond the defaults?

**SCD Standards**
- Default SCD strategy when unspecified in a feature spec? (Type 1 is the safest default)
- Is historical preservation required for any dimension class by policy (e.g., customer data must always be Type 2)?

**Data Quality**
- Which DQ tool is used? (dbt tests, Great Expectations, Soda, custom framework)
- What is the default row count variance threshold for the mandatory check? (suggest ±10%)
- Is there a centralized DQ results table that all pipelines must write to?

**Performance Standards**
- SLA window for nightly batch? (e.g., "All marts available by 06:00 local business timezone")
- Maximum acceptable incremental load duration?
- Are there budget/cost constraints on compute?

**Security & Compliance**
- Which columns are always PII and must be treated as Type 1 (always current)?
- Are there data retention requirements?
- Which teams have access to which layers?

**Orchestration**
- What orchestration tool is used? (Airflow, dbt Cloud, Prefect, Azure Data Factory, none)
- Are there required pipeline metadata/audit patterns?

### 2. Draft the Constitution

Write `.specify/memory/constitution.md` using the DW constitution template. Fill every section with the project's specific answers. Where the user did not specify, use the proven defaults from the template and note them as defaults.

The constitution MUST include all eight standard sections:
1. Dimensional Modeling Standards
2. Naming Conventions (with the full table for table prefixes, column conventions, and schema/layer names)
3. SCD Standards
4. Data Quality Gates
5. Pipeline Idempotency
6. Data Lineage & Documentation
7. Performance Standards
8. Security & Compliance

Plus: Governance section (version, ratification date, amendment process)

If a section doesn't apply to this project (e.g., no PII data), keep the section heading and note "Not applicable — [reason]" rather than deleting it.

### 3. Validate the Constitution

Verify the drafted constitution is self-consistent:

- Naming conventions don't conflict with each other
- SCD defaults are compatible with stated PII policy (PII must be Type 1)
- DQ gate thresholds are achievable given the stated SLA window
- Performance standards are specific (times, not vague "fast")

Surface any contradictions to the user before writing.

### 4. Write the Constitution File

Write the complete constitution to `.specify/memory/constitution.md`.

If a constitution file already exists at that path:
- Show the user a diff of what will change
- Ask for confirmation before overwriting
- Or create `.specify/memory/constitution-draft.md` for the user to review first

### 5. Report Completion

Report to the user:
- Location: `.specify/memory/constitution.md`
- Summary of the key decisions captured (modeling pattern, naming scheme, DQ tool, SLA)
- Any defaults applied (list them explicitly)
- How to amend: "Edit `.specify/memory/constitution.md` directly; update the Version and Last Amended date; add a note in the Governance section about what changed and why"

---

## DW Constitution Quick Guidelines

- **Be specific, not aspirational** — "queries should be fast" is not a standard; "P1 consumer queries must return in < 5 seconds" is
- **Every naming convention needs an example** — abstract rules get misinterpreted; concrete examples prevent it
- **SCD policy belongs in the constitution** — individual feature specs should reference the constitution's default, not re-derive it each time
- **DQ gate defaults should be conservative** — it's easier to relax a threshold later than to explain why bad data reached consumers
- **The constitution is a living document** — date it, version it, and establish the amendment process so it gets updated rather than ignored
