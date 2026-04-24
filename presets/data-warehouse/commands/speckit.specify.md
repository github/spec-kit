---
description: Create a data warehouse feature specification and store it in spec.md.
handoffs:
  - label: Build DW Technical Plan
    agent: speckit.plan
    prompt: Create a data warehouse implementation plan for this spec. Platform is...
  - label: Clarify DW Requirements
    agent: speckit.clarify
    prompt: Clarify data warehouse specification requirements
    send: true
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Pre-Execution Checks

Check for extension hooks (`before_specify`) by reading `.specify/extensions.yml` if it exists, following the standard hook execution rules. If not present, skip silently.

## Outline

Given the user's feature description, do the following:

### 1. Generate a Feature Short Name

Create a 2–4 word slug for the feature (action-noun, lowercase, hyphenated).

Examples: `customer-dim-scd2`, `sales-fact-daily`, `product-etl-pipeline`, `revenue-mart-rebuild`

### 2. Create the Spec Directory and File

- Determine the feature directory following the standard resolution order:
  1. Explicit `SPECIFY_FEATURE_DIRECTORY` if provided
  2. Auto-generate under `specs/` using sequential (`NNN`) or timestamp prefix per `.specify/init-options.json`
- `mkdir -p SPECIFY_FEATURE_DIRECTORY`
- Copy `templates/spec-template.md` to `SPECIFY_FEATURE_DIRECTORY/spec.md`
- Write `.specify/feature.json`:
  ```json
  { "feature_directory": "<resolved feature dir>" }
  ```

### 3. Collect and Fill DW-Specific Information

Parse the feature description to extract — and make informed defaults for anything unspecified:

**Data Sources**
- What source systems feed this feature? (CRM, ERP, event stream, flat files, APIs?)
- What is the refresh frequency and estimated row volume?
- Are there known data quality issues in the source?

**Dimensional Model**
- What is the **grain**? (one row per what, per what time period?) — this is the most critical question; if unclear, propose the most natural grain and flag it
- What fact table(s) are needed? What type (transaction, periodic snapshot, accumulating snapshot)?
- What dimension tables are needed? Which are conformed (shared) vs. local?
- What SCD strategy applies to each dimension? (Type 1 overwrite / Type 2 history / Type 3 prior+current / static)

**Consumer Use Cases**
- Who will query this data? (BI team in Tableau, data scientists, application APIs?)
- What business questions does it answer?
- What is the priority order of consumers/use cases?

**Business Rules**
- How are key measures calculated? (formulas, exclusions, rounding rules)
- Are there filter or exclusion rules? (test data, cancelled records, etc.)
- Are there derived dimension attributes? (segments, tiers, regions mapped from codes?)

**Data Quality**
- What mandatory checks should abort the pipeline on failure?
- What warning checks should alert without blocking?
- How should rejected records be quarantined?

**Freshness & SLA**
- What time must data be available by each day?
- What is the acceptable load duration?

Mark critical unknowns with `[NEEDS CLARIFICATION: specific question]`. Limit to **3 markers maximum** — make informed defaults for everything else and document them in the Assumptions section.

**Prioritize clarifications by impact**: grain definition > source availability > consumer SLA > business rule ambiguity.

**Common DW defaults** (do not ask, just apply):
- Date dimension: assume a shared `dim_date` already exists unless stated otherwise
- Surrogate keys: system-generated BIGINT
- Audit columns: `created_at`, `updated_at`, `source_system`, `load_id` on every table
- Default SCD for customer/product dimensions with no stated strategy: Type 1 (overwrite)
- Row count variance threshold: ±10% of prior load

### 4. Write the Specification

Fill `spec.md` using the DW spec template structure. Replace all placeholders with concrete content derived from the feature description. Preserve all section headings.

Ensure every section is actionable:
- **Grain Statement**: must be a single unambiguous sentence
- **Consumer Use Cases**: each must have an independent test described
- **Business Rules**: every measure formula must be written out explicitly
- **DQ Requirements**: numbered DQ-001, DQ-002, … with clear pass/fail criteria
- **SLA table**: concrete times, not vague "daily"

### 5. Specification Quality Validation

After writing the spec, validate against these DW-specific criteria:

**Create** `SPECIFY_FEATURE_DIRECTORY/checklists/requirements.md`:

```markdown
# DW Specification Quality Checklist: [FEATURE NAME]

**Purpose**: Validate completeness before planning begins
**Created**: [DATE]
**Feature**: [Link to spec.md]

## Dimensional Modeling Completeness
- [ ] Grain statement is present and unambiguous (one sentence)
- [ ] All fact tables have a Fact Type defined (transaction / snapshot / accumulating)
- [ ] All dimension tables have an SCD strategy documented
- [ ] Conformed dimensions are identified (shared vs. local)
- [ ] Semi-additive or non-additive measures are called out explicitly

## Data Source Completeness
- [ ] All source systems are listed with format, frequency, and estimated volume
- [ ] Source data quality baseline is documented (known issues, latency, history availability)

## Consumer Use Cases
- [ ] Each use case has a priority (P1, P2, ...)
- [ ] Each use case has an independent test described
- [ ] At least one illustrative query pattern is included per use case

## Business Rules
- [ ] Every measure formula is written out explicitly (no "standard calculation" placeholders)
- [ ] All filter and exclusion rules are documented
- [ ] Derived dimension attributes have their derivation logic stated

## Data Quality & SLA
- [ ] Mandatory DQ checks are numbered (DQ-001, ...) with clear pass/fail criteria
- [ ] Warning checks are distinguished from mandatory (abort) checks
- [ ] Quarantine behavior is described
- [ ] SLA table has concrete times (not vague "daily")

## General Quality
- [ ] No implementation details (no SQL, no framework names, no column types)
- [ ] No [NEEDS CLARIFICATION] markers remain
- [ ] Assumptions section covers all defaults applied
- [ ] Success criteria are measurable and technology-agnostic

## Notes

[Document any remaining issues or items requiring stakeholder input]
```

**Run validation**: Check the spec against every checklist item.

- If all pass: mark checklist complete
- If items fail: fix the spec and re-validate (up to 3 iterations)
- If `[NEEDS CLARIFICATION]` markers remain: present up to 3 questions to the user using the standard Q&A format (options A/B/C/Custom table), wait for answers, update spec, re-validate

### 6. Report Completion

Report to the user:
- `SPECIFY_FEATURE_DIRECTORY` — the feature directory path
- `spec.md` location
- Grain statement (repeat it explicitly — this is the most important output)
- Checklist results summary
- Any assumptions made (list them)
- Next step: `/speckit.plan`

### 7. Post-Execution Hooks

Check `.specify/extensions.yml` for `after_specify` hooks and execute per standard hook rules.

---

## DW Specification Quick Guidelines

- Focus on **WHAT** data is needed, **WHY** consumers need it, and **HOW FRESH** it must be
- **Never** include implementation details: no SQL dialects, no framework names (dbt, Spark, Airflow), no column data types, no index strategies
- The grain statement is the most critical artifact — it determines everything else. If it isn't clear from the input, derive the most natural grain and mark it for confirmation.
- Business rules belong here. If a measure formula can't be written unambiguously, it's a clarification item.
- SCD strategy decisions belong in the spec (business decision), not the plan (implementation detail)
