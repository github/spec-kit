# Data Warehouse Feature Specification: [FEATURE NAME]

**Feature Branch**: `[###-feature-name]`  
**Created**: [DATE]  
**Status**: Draft  
**Grain**: [One row per ... per ...] *(define before filling any other section)*  
**Input**: User description: "$ARGUMENTS"

## Overview

[2–3 sentences: what data is being warehoused, for whom, and what business questions it answers]

---

## Data Sources

<!--
  List every source system contributing data to this feature.
  Be specific about format, refresh frequency, volume, and owner.
  This section drives ETL design and SLA feasibility.
-->

| Source System | Format | Refresh Frequency | Estimated Volume | Owner / Contact |
|---------------|--------|-------------------|------------------|-----------------|
| [e.g., Salesforce CRM] | [REST API / DB snapshot / CSV] | [Daily / Hourly / Real-time] | [~5M rows/day] | [team or person] |
| [e.g., ERP system] | [JDBC / flat files] | [Nightly batch] | [~500K rows/day] | [team or person] |

### Source Data Quality Baseline

- **Known Issues**: [e.g., "NULL customer_id on guest-checkout orders, ~2% of rows"]
- **Latency**: [e.g., "Source data available by 03:00 UTC after nightly close"]
- **Historical Availability**: [e.g., "Clean history from 2020-01-01; earlier data is unreliable"]

---

## Consumer Use Cases

<!--
  Who queries this data and why? Drives grain, indexing, partitioning, and SLA choices.
  PRIORITIZE as P1 → P2 → P3. Each use case must be independently testable.
-->

### Use Case 1 — [Brief Title] (Priority: P1)

[Plain-language description of the analytics or reporting need]

**Consumer**: [e.g., "Finance team in Tableau", "Data science team via Python"]

**Why this priority**: [Business value and rationale]

**Independent Test**: [e.g., "Run the reconciliation query in quickstart.md; totals must match source system report"]

**Typical Query Pattern**:

```sql
-- Illustrative query this use case drives (not a spec requirement)
SELECT [dimension], SUM([measure])
FROM   [fact_table]
WHERE  [filter]
GROUP BY [dimension]
```

**Acceptance Scenarios**:

1. **Given** [source data state], **When** [pipeline runs / query executes], **Then** [expected result]
2. **Given** [a data quality issue], **When** [pipeline encounters it], **Then** [quarantine / alert / reject behavior]

---

### Use Case 2 — [Brief Title] (Priority: P2)

[Description of the analytics need]

**Consumer**: [Who uses this]

**Why this priority**: [Rationale]

**Independent Test**: [How to validate independently]

**Acceptance Scenarios**:

1. **Given** [state], **When** [action], **Then** [outcome]

---

[Add more use cases as needed, each with an assigned priority]

### Edge Cases

- What happens when source data arrives outside the SLA window?
- How does the pipeline handle duplicate records from the source system?
- What is the behavior when a fact row references a dimension key that doesn't exist?
- How are soft-deletes or hard-deletes in the source handled?
- What happens on full reload vs. incremental refresh?
- How are late-arriving facts processed?

---

## Dimensional Model

<!--
  Define the LOGICAL model — what each entity represents and how things relate.
  Avoid physical details (column types, indexes) — those go in the plan.
-->

### Grain Statement

> **"This fact table contains one row per [unit of measure] per [time granularity]."**

*Example: "One row per sales order line item per calendar day."*

### Fact Table(s)

| Fact Table | Grain | Fact Type | Additive Measures |
|------------|-------|-----------|-------------------|
| `[fct_sales]` | [order line / day] | [Transaction / Periodic Snapshot / Accumulating Snapshot] | [revenue, quantity, discount_amount] |

**Semi-additive or Non-additive Measures** *(if any)*:

- [e.g., "`account_balance` is semi-additive — sum across products OK, NOT across time periods"]

### Dimension Tables

| Dimension | Business Key | Conformed? | SCD Strategy |
|-----------|-------------|------------|-------------|
| `[dim_customer]` | `[customer_id]` | [Yes / No] | [Type 2 — preserve full history] |
| `[dim_product]` | `[sku]` | [Yes / No] | [Type 1 — overwrite on change] |
| `[dim_date]` | `[date_key]` | [Yes — shared] | [Static — no SCD needed] |
| `[dim_geography]` | `[geo_code]` | [Yes / No] | [Type 3 — current + prior region] |

### Relationships

```text
[fct_sales]
  → dim_customer  (many-to-one)
  → dim_product   (many-to-one)
  → dim_date      (many-to-one)
  → dim_geography (many-to-one)
```

---

## Business Rules & Transformations

<!--
  Every rule must be unambiguous and independently testable.
  These are the authoritative definitions — no ambiguity allowed.
-->

### Measure Definitions

- **`[measure_name]`**: [Full business definition and formula, e.g., "`net_revenue = gross_amount − discount_amount − tax_amount`. Excludes shipping fees."]
- **`[kpi_name]`**: [Definition, e.g., "`customer_lifetime_value = SUM(net_revenue)` for customers with `tenure_days ≥ 365`"]

### Dimension Attribute Rules

- **`[attribute]`**: [Derivation rule, e.g., "`customer_segment`: annual_spend > $10K → 'Premium'; else → 'Standard'"]
- **`[status_field]`**: [Source-to-warehouse mapping, e.g., "Source codes 'A','B' → 'Active'; 'C' → 'Inactive'"]

### Filter & Exclusion Rules

- [e.g., "Exclude orders where `customer_id` starts with `'TEST-'`"]
- [e.g., "Exclude rows where `cancellation_date < order_date` — indicates a source data integrity error"]

---

## Data Quality Requirements

<!--
  These are enforced pipeline checkpoints, not aspirational targets.
  Mandatory checks ABORT the pipeline on failure.
  Warning checks ALERT but allow the pipeline to continue.
-->

### Mandatory Checks *(Pipeline aborts on failure)*

- **DQ-001**: No NULL values in `[primary_key_column]`
- **DQ-002**: Referential integrity — every `fact.[dimension_key]` must exist in the corresponding dimension table
- **DQ-003**: No duplicate rows at the defined grain
- **DQ-004**: Row count within ±[X]% of the prior successful load

### Warning Checks *(Alert, do not fail)*

- **DQ-005**: NULL rate in `[optional_field]` exceeds [Y]% — alert data engineering team
- **DQ-006**: Measure `[revenue]` deviates more than [Z]% from 7-day rolling average — alert analytics team

### Quarantine Rules

- Records failing mandatory DQ checks MUST be routed to `quarantine.[table_name]_rejected` with a `rejection_reason` and `rejected_at` timestamp
- Quarantined records MUST be reprocessable without triggering a full reload

---

## Freshness & SLA Requirements

| Requirement | Target | Hard Limit | Escalation |
|-------------|--------|------------|------------|
| Data available by | [06:00 local business timezone] | [08:00] | [Page on-call data engineer] |
| Incremental load runtime | [< 30 minutes] | [60 minutes] | [Auto-retry + alert] |
| Full reload runtime | [< 4 hours] | [8 hours] | [Notify stakeholders] |

**Refresh Schedule**: [e.g., "Nightly at 02:00 UTC, triggered after source system close"]

---

## Requirements

<!--
  Functional requirements derived from all sections above.
  Each must be independently testable.
-->

### Functional Requirements

- **FR-001**: Pipeline MUST ingest all source records within the defined SLA window
- **FR-002**: Pipeline MUST apply all business rules in this spec before writing to the serving layer
- **FR-003**: Pipeline MUST enforce all mandatory DQ checks before promoting data to consumers
- **FR-004**: Dimension tables MUST implement the specified SCD strategy per the Dimensional Model section
- **FR-005**: Fact table MUST maintain grain integrity — zero duplicates at the defined grain
- **FR-006**: Pipeline MUST be idempotent — re-running for the same period produces identical results
- **FR-007**: All rejected records MUST be quarantined with `rejection_reason` and `rejected_at`
- **FR-008**: Each pipeline run MUST emit row counts, runtime, and DQ check results to a run log

### Key Entities

- **[FactEntity]**: [Business event it records; grain; key relationships to dimensions]
- **[DimensionEntity]**: [Business concept it describes; business key; history strategy]

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: All P1 consumer use cases return correct results as verified by business sign-off queries in `quickstart.md`
- **SC-002**: Pipeline completes within the defined SLA on at least 95% of scheduled runs over the first 30 days
- **SC-003**: Mandatory DQ check pass rate ≥ 99.5% over a 30-day production period
- **SC-004**: Zero consumer-reported data accuracy incidents in the first 30 days post-launch
- **SC-005**: Full reload completes within the hard limit at production-scale data volume

---

## Assumptions

- [e.g., "Source schema will not change without advance notice to the data engineering team"]
- [e.g., "Historical backfill is required from [START_DATE]; data quality before that date is not guaranteed"]
- [e.g., "A shared `dim_date` table already exists in the warehouse and will be reused"]
- [e.g., "Source system communicates deletes as soft-delete flags — not physical row removal"]
- [e.g., "Downstream BI tools support the proposed schema without additional semantic layer changes"]
