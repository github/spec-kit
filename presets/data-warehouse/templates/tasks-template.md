---
description: "Data warehouse task list — organized by pipeline layer and consumer use case"
---

# DW Tasks: [FEATURE NAME]

**Input**: Design documents from `/specs/[###-feature-name]/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required), `data-lineage.md` (required), `data-contracts/` (if available)

**Organization**: Tasks flow through pipeline layers (Raw → Staging → Dimensions → Facts), then consumer use cases within the serving layer, then operations. Each phase has a checkpoint.

## Format: `[ID] [P?] [Layer/Story] Description — file path`

- **[P]**: Safe to run in parallel (no file or table dependencies)
- **[Layer]**: `RAW`, `STG`, `DIM`, `MART`, `DQ`, `OPS`
- **[US#]**: Which consumer use case this task enables
- Include **exact model or file paths** in every task description

<!--
  ============================================================================
  IMPORTANT: The tasks below are SAMPLE TASKS for illustration only.

  /speckit.tasks MUST replace them with actual tasks derived from:
  - Consumer use cases from spec.md (P1, P2, P3 priorities)
  - Schema and load strategy from plan.md
  - Field mappings from data-lineage.md
  - Source contracts from data-contracts/

  Tasks MUST be organized so each consumer use case (P1, P2, ...) is
  independently implementable, testable, and deliverable.

  DO NOT retain these sample tasks in the generated tasks.md file.
  ============================================================================
-->

---

## Phase 1: Environment Setup

**Purpose**: Infrastructure, schemas, project scaffolding, audit plumbing

- [ ] T001 Create warehouse schemas: `raw`, `staging`, `mart` (adjust names per plan.md layer convention)
- [ ] T002 [P] Configure source system connection credentials and test connectivity
- [ ] T003 [P] Initialize ETL project structure per plan.md source code layout
- [ ] T004 [P] Create pipeline audit table `[warehouse].pipeline_runs` per plan.md observability design
- [ ] T005 [P] Create quarantine schema and base DDL template per plan.md quarantine schema
- [ ] T006 Configure CI/CD pipeline: lint → test → deploy steps for ETL models

**Checkpoint**: Infrastructure ready; source connectivity confirmed; audit and quarantine tables exist

---

## Phase 2: Raw / Bronze Layer (Source Extraction)

**Purpose**: Land source data with zero transformation. Append-only. Exact replica of source.

**Rule**: No business logic. No type coercion beyond minimal landing schema. Every row gets `load_timestamp` and `source_file` or `source_run_id`.

- [ ] T007 [RAW] Create raw landing DDL for `raw.[source_table_1]` — file: `models/staging/[source]/schema.yml` or DDL script
- [ ] T008 [P] [RAW] Create raw landing DDL for `raw.[source_table_2]`
- [ ] T009 [RAW] Implement extractor: `[source_system]` → `raw.[source_table_1]` — file: `pipelines/extract/[source]_extractor.py`
- [ ] T010 [P] [RAW] Write unit test: extractor preserves all source columns without modification — `tests/unit/test_[source]_extractor.py`
- [ ] T011 [RAW] Validate raw row counts match source system record counts for a known batch

**Checkpoint**: Raw tables populated; row counts reconcile to source; no transformations applied

---

## Phase 3: Staging / Silver Layer (Clean, Type, Validate)

**Purpose**: Apply structural cleaning only — type casting, deduplication, NULL handling, schema enforcement. No business metric derivation.

**Rule**: Staging must quarantine records failing structural validation before any business-layer model runs.

- [ ] T012 [STG] Create staging model `stg_[source]__[entity1].sql` — `models/staging/[source]/stg_[source]__[entity1].sql`
- [ ] T013 [P] [STG] Create staging model `stg_[source]__[entity2].sql` — `models/staging/[source]/stg_[source]__[entity2].sql`
- [ ] T014 [STG] Implement deduplication logic on `[business_key]` in `stg_[source]__[entity1]`
- [ ] T015 [P] [STG] Add dbt schema tests: `not_null`, `unique`, `accepted_values` — `models/staging/[source]/schema.yml`
- [ ] T016 [STG] Implement quarantine routing: records failing structural checks → `quarantine.[entity1]_rejected`
- [ ] T017 [STG] Validate staging row count vs. raw; document expected attrition from deduplication

**Checkpoint**: Staging layer clean and tested; quarantine routing verified; ready for dimensional modeling

---

## Phase 4: Dimension Tables *(Foundational — blocks all fact loading)*

**Purpose**: Build dimension tables with stable surrogate keys. Facts cannot load until all referenced dimensions exist and are validated.

**Rule**: Write DQ tests first. Tests MUST fail before dimension implementation begins.

### Data Quality Tests — Write First, Verify They Fail

- [ ] T018 [DQ] Write `dbt unique` test on `[dim_entity1].[entity_key]` — `models/marts/schema.yml`
- [ ] T019 [P] [DQ] Write `dbt not_null` test on `[dim_entity1].[business_key]` — `models/marts/schema.yml`
- [ ] T020 [P] [DQ] Write `dbt unique` test on `[dim_entity1].[business_key]` among `is_current=TRUE` rows (SCD2 guard)

### Dimension: [dim_entity1]

- [ ] T021 [DIM] Create dimension model `dim_[entity1].sql` — `models/marts/[domain]/dim_[entity1].sql`
- [ ] T022 [DIM] Implement SCD Type [1/2/3] logic for `dim_[entity1]` per plan.md SCD table
- [ ] T023 [DIM] Add audit columns: `valid_from`, `valid_to`, `is_current`, `load_id` (SCD2 only)
- [ ] T024 [DIM] Verify historical rows are preserved correctly with SCD Type 2 test scenario

### Dimension: [dim_entity2]

- [ ] T025 [P] [DIM] Create dimension model `dim_[entity2].sql` — `models/marts/[domain]/dim_[entity2].sql`
- [ ] T026 [P] [DIM] Implement SCD logic for `dim_[entity2]`
- [ ] T027 [P] [DIM] Add dbt tests for `dim_[entity2]`

**Checkpoint**: All dimensions loaded; surrogate keys stable; SCD logic validated; dbt tests pass — fact loading can begin

---

## Phase 5: Fact Table — Consumer Use Case 1 (Priority: P1) 🎯 MVP

**Goal**: [What business questions P1 consumers can now answer]

**Independent Test**: Run the P1 sign-off query from `quickstart.md`; totals must match source system reconciliation report.

### Data Quality Tests — Write First, Verify They Fail

- [ ] T028 [DQ] [US1] Write `dbt unique` test on grain columns `([col1], [col2], [col3])` — `models/marts/schema.yml`
- [ ] T029 [P] [DQ] [US1] Write `dbt not_null` test on all foreign key columns
- [ ] T030 [P] [DQ] [US1] Write `dbt relationships` test: `fct_[name].[customer_key]` → `dim_customer.[customer_key]` (repeat per FK)
- [ ] T031 [P] [DQ] [US1] Write row count variance check macro (DQ-004: ±[X]% vs prior run)

### Implementation

- [ ] T032 [MART] [US1] Create fact model `fct_[business_process].sql` — `models/marts/[domain]/fct_[business_process].sql`
- [ ] T033 [MART] [US1] Implement grain join: fact source rows → dimension surrogate key lookups
- [ ] T034 [MART] [US1] Implement measure derivations per business rules in `spec.md` (e.g., `net_revenue`, `discount_pct`)
- [ ] T035 [MART] [US1] Add partitioning and clustering per plan.md performance section
- [ ] T036 [MART] [US1] Implement idempotent load logic: MERGE or DELETE+INSERT per plan.md idempotency design
- [ ] T037 [MART] [US1] Implement quarantine routing for mandatory DQ check failures (DQ-001/002/003)
- [ ] T038 [MART] [US1] Emit row counts and DQ results to `pipeline_runs` audit table

**Checkpoint**: Fact table loads; all mandatory DQ checks pass; P1 sign-off query returns correct results independently

---

## Phase 6: Fact Table — Consumer Use Case 2 (Priority: P2)

**Goal**: [What P2 consumers gain; may extend the existing fact or add a separate model]

**Independent Test**: Run P2 sign-off query from `quickstart.md`; P1 and P2 results remain correct independently.

### Data Quality Tests — Write First

- [ ] T039 [DQ] [US2] Add DQ tests for any new P2 tables or extensions to `schema.yml`

### Implementation

- [ ] T040 [MART] [US2] [Implement P2-specific fact extension, new aggregate, or separate fact table]
- [ ] T041 [P] [MART] [US2] Validate P2 query patterns against `quickstart.md`

**Checkpoint**: P1 AND P2 use cases independently validated; neither breaks the other

---

[Add more use case phases following the same pattern]

---

## Phase N: Orchestration, Monitoring & Operations

**Purpose**: Production readiness — scheduling, alerting, documentation, sign-off

- [ ] TXXX [OPS] Create or update DAG / workflow trigger for scheduled execution at defined refresh window
- [ ] TXXX [OPS] Configure failure alerting: pipeline abort notification → `[Slack channel / PagerDuty]`
- [ ] TXXX [P] [OPS] Configure warning check alerting: DQ-005/006 → `[Slack channel / email]`
- [ ] TXXX [OPS] Verify pipeline run metadata writes correctly to `pipeline_runs` audit table
- [ ] TXXX [P] [OPS] Create pipeline health dashboard in `[BI tool]`
- [ ] TXXX [P] [OPS] Update data catalog / data dictionary with new table and column definitions
- [ ] TXXX [OPS] Finalize `data-lineage.md` with confirmed source-to-target field mappings
- [ ] TXXX [OPS] Complete `quickstart.md` with final sign-off queries and expected row counts
- [ ] TXXX [OPS] Conduct business stakeholder sign-off using `quickstart.md` queries
- [ ] TXXX [OPS] Write runbook: re-run procedure, quarantine investigation, full reload steps

**Checkpoint**: Pipeline running on schedule; alerts wired; docs complete; stakeholder sign-off obtained

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Raw/Bronze (Phase 2)**: Requires Phase 1 complete (schemas and infrastructure exist)
- **Staging/Silver (Phase 3)**: Requires Phase 2 (raw data available to transform)
- **Dimensions (Phase 4)**: Requires Phase 3 (staging clean and validated) — **BLOCKS all fact loading**
- **Facts (Phase 5+)**: Requires Phase 4 (dimension surrogate keys stable)
- **Operations (Phase N)**: Requires all fact and dimension phases complete

### Within Each Phase

- DQ tests MUST be written and confirmed failing before any implementation begins
- Dimension tables MUST be fully loaded and validated before facts reference them
- Staging must be clean and tested before dimensions can build from it

### Parallel Opportunities

- Multiple raw source tables: all `[P]` extraction tasks can run concurrently
- Multiple staging models for different source entities: all `[P]`
- Multiple dimensions with no shared surrogate key dependency: all `[P]`
- Multiple consumer use cases (separate fact tables): can parallelize across team members once dimensions are complete
- DQ test authoring for multiple tables: all `[P]`

---

## Data Quality Validation Checklist

Before declaring any phase complete:

- [ ] All mandatory DQ checks PASS (not just run without error)
- [ ] Quarantine table inspected; rejection rate is within acceptable bounds; `rejection_reason` values are understood
- [ ] Row counts reconciled against source system or prior pipeline layer
- [ ] Grain integrity confirmed: zero duplicate rows at the defined grain
- [ ] Sample queries from `quickstart.md` return expected results

---

## Rollback Checklist

Before first production run:

- [ ] Rollback procedure documented in runbook: which tables to truncate/restore for a failed load
- [ ] Quarantine table verified: captured records include enough metadata to identify and reprocess the source rows
- [ ] Idempotency verified: pipeline executed twice for the same date → no duplicate rows in fact or dimension tables
- [ ] Full reload tested end-to-end in a non-production environment
