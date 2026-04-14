---
description: Generate the data warehouse implementation task list and store it in tasks.md.
---

## User Input

```text
$ARGUMENTS
```

## Outline

### 1. Load Context

- Read `.specify/feature.json` to get the feature directory path
- Read `<feature_directory>/spec.md` — consumer use cases (with priorities), DQ requirements, SLAs
- Read `<feature_directory>/plan.md` — schema design, load strategies, SCD decisions, project structure
- Read `<feature_directory>/data-lineage.md` — field-level source-to-target mappings
- Read `<feature_directory>/data-contracts/` — source system contracts (if present)
- Read `.specify/memory/constitution.md` — to ensure tasks enforce constitutional requirements

### 2. Understand the Scope

Before writing any tasks, extract and confirm:

**From spec.md**:
- Consumer use cases and their priorities (P1, P2, P3 …)
- DQ check identifiers (DQ-001, DQ-002 …) and their failure actions
- SLA and refresh schedule

**From plan.md**:
- Every table: fact and dimension tables with their load type and idempotency strategy
- SCD type per dimension attribute
- Data quality tool (dbt tests / Great Expectations / custom macros / etc.)
- Project structure (dbt models path / Python pipeline path / etc.)
- Orchestration tool (Airflow DAG / dbt Cloud job / etc.)

**From data-lineage.md**:
- Source tables that need raw landing tables
- Complex transformations that need intermediate staging models

### 3. Generate Tasks

Create `<feature_directory>/tasks.md` using the DW tasks template structure. Replace all sample tasks with actual tasks derived from the spec and plan. Follow these rules:

**Task ID format**: Sequential integers, zero-padded to 3 digits (T001, T002, …)

**Layer prefix in every task**:
- `[RAW]` — raw/bronze extraction tasks
- `[STG]` — staging/silver cleaning tasks
- `[DIM]` — dimension table tasks
- `[MART]` — fact table and mart tasks
- `[DQ]` — data quality test writing tasks
- `[OPS]` — orchestration, monitoring, documentation tasks

**Every task must include the exact file path** of the model, script, test file, or config being created or modified.

**DQ test tasks come BEFORE implementation tasks** within each phase. Tests must be written first and verified as failing before implementation begins.

**Phase structure** (replicate from tasks template):

1. **Phase 1 — Environment Setup**: Schemas, project scaffold, audit table, quarantine DDL, CI/CD
2. **Phase 2 — Raw/Bronze**: One extraction task per source table from `data-lineage.md`; unit test for each extractor; row count validation
3. **Phase 3 — Staging/Silver**: One staging model per source entity from `plan.md`; deduplication; DQ tests for structural checks; quarantine routing; row count reconciliation
4. **Phase 4 — Dimensions**: DQ tests first (write and confirm failure); then one implementation block per dimension from `plan.md`; SCD logic per constitution; audit columns; SCD correctness test scenario
5. **Phase 5 — Facts / Consumer Use Case 1 (P1)**: DQ tests first; grain join; measure derivations per spec business rules; partitioning/clustering; idempotent load; quarantine routing; audit table emit — **checkpoint: P1 sign-off query passes**
6. **Phase 6+ — Facts / Consumer Use Cases 2, 3, ... (P2, P3, …)**: One phase per consumer use case, following the same DQ-first pattern
7. **Phase N — Operations**: DAG/scheduler, failure alerting, warning alerting, audit table, data catalog, data lineage finalization, quickstart sign-off, runbook

**Parallelism marking**: Mark `[P]` on any task that can run concurrently with other tasks in the same phase — specifically tasks that operate on different tables/files with no shared dependencies.

**Typical parallel opportunities**:
- Multiple raw source tables: all parallel
- Multiple staging models for different entities: all parallel
- Multiple dimensions with no FK dependency between them: all parallel
- DQ test authoring for different tables: all parallel
- Multiple use case fact tasks (after dimensions complete): parallelizable across developers

### 4. Write tasks.md

Write all tasks to `<feature_directory>/tasks.md`. The generated file MUST:
- Contain only real tasks (no sample/template placeholders)
- Include concrete file paths for every task
- Have a clear checkpoint after each phase
- List the Dependencies & Execution Order section showing phase dependencies
- Include the DQ Validation Checklist section
- Include the Rollback Checklist section

### 5. Report Completion

Report to the user:
- `tasks.md` location
- Task count per phase
- Which tasks are marked `[P]` (parallelizable)
- P1 MVP scope: exactly which tasks deliver the first independently testable use case
- Suggested starting point: "Start with Phase 1 (Setup), then Phase 2 (Raw) in parallel"

---

## DW Task Generation Quick Guidelines

- **DQ tests before implementation** — this is non-negotiable per the constitution. If a phase has no DQ tests, add them.
- **Dimensions before facts** — always. Fact tasks must be in a later phase than the dimensions they reference.
- **Exact file paths** — every task must name the exact model file, test file, or config that will be created or modified. "Create a staging model" is insufficient; "Create `models/staging/salesforce/stg_salesforce__accounts.sql`" is correct.
- **Idempotency task is mandatory** — every fact table implementation block must include a task that verifies re-running the pipeline for the same date produces no duplicates.
- **Checkpoint queries** — every use-case phase must end with a task to run the corresponding sign-off query from `quickstart.md`.
- **Rollback and runbook tasks belong in the Operations phase** — do not skip them.
