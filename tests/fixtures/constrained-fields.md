# Constrained-field command regression scenarios

These are agent-executed fixtures for `templates/commands/tasks.md` and
`templates/commands/analyze.md`, not inputs to a test-only analyzer. Scaffold
tests protect the instructions; an agent must check the outcomes below.

## Common feature artifacts

Use the following `spec.md`, `plan.md`, and `data-model.md` with each task variant.
Only the absent-model and unconstrained-model cases replace the data model.

### spec.md

```markdown
# Feature Specification: Request validation

## User Scenarios & Testing

### User Story 1 - Validate requests (Priority: P1)

A contributor can submit a request that follows its canonical field rules.

Acceptance: Valid requests succeed; invalid field values are rejected.

## Requirements

- **FR-001**: Validate request and audit fields using the canonical data model.

## Success Criteria

- **SC-001**: All accepted requests satisfy the canonical field constraints.
```

### plan.md

```markdown
# Implementation Plan: Request validation

## Summary

Implement request validation and audit recording in src/request.py and
src/audit.py using data-model.md. Test valid and invalid inputs.

## Technical Context

Python library; existing validation helpers and pytest; no new dependencies.

## Constitution Check

Use the project's existing principles; no exceptions are needed.
```

### data-model.md

```markdown
# Data Model

## Request

| Field | Type | Constraints |
|-------|------|-------------|
| SuspendReason | nvarchar(200) | Nullable; trim whitespace; if supplied, must not be empty after trimming. |
| Remark | nvarchar(200) | Required. |
| Status | enum | Required; allowed values: open, suspended. |
| RetryCount | integer | Nullable; inclusive range 0 through 3. |
| Code | string | Required; minimum length 3, maximum length 8; uppercase letters only. |

## Audit

| Field | Type | Constraints |
|-------|------|-------------|
| Remark | string | Required; maximum length 40. |
```

There are six constrained fields. `Request.SuspendReason` and `Request.Remark`
are the two 200-character lineage fields; `Audit.Remark` deliberately repeats a
field name with a different restriction.

## Task-generation scenario

Generate tasks from the common artifacts using the actual tasks command.
Expect every field to have an explicit `data-model.md` `Entity.field` reference
in at least one implementing task. Preserve checklist IDs, paths, and story
grouping. A shared implementation task may cover several fields. Constraint
values must not be restated when unchanged; cite their canonical definitions.

As a second generation case, add an operation-specific rule requiring a
SuspendReason when suspending a request, while the general model permits null.
Expect the relevant task to retain its `data-model.md` `Request.SuspendReason`
citation and state only the operation-specific narrowing. It must not repeat
the unchanged length/trim rules or contradict the canonical definition.

## Analysis baseline

Start with these complete, citation-only tasks. Each variant below changes only
the specified lines; keep the other baseline lines unchanged.

```markdown
# Tasks: Request validation

## User Story 1

- [ ] T001 [US1] Implement request validation in src/request.py using data-model.md `Request.SuspendReason`, `Request.Remark`, `Request.Status`, `Request.RetryCount`, and `Request.Code`.
- [ ] T002 [US1] Implement audit validation in src/audit.py using data-model.md `Audit.Remark`.
- [ ] T003 [US1] Test valid and invalid requests and audit entries in tests/test_request.py.
```

Run each case independently. Count only constrained-field findings; ordinary
analysis may separately report shortcomings of this deliberately small feature.
Every missing citation is HIGH Coverage; every contradiction is HIGH
Inconsistency unless an existing CRITICAL escalation applies. Findings identify
the exact field, task IDs and source locations when available; contradictions
include both canonical and task-stated restrictions. Analysis must not edit files.

### A01 - Citation-only, shared implementing task

Use the analysis baseline unchanged.

**Expected**: Six covered fields, zero constrained-field findings. No demand to
repeat values. Multiple fields in T001 are independently covered.

### A02 - Omitted lineage field

Remove only `` `Request.SuspendReason`, `` from T001. Leave the field defined in
the data model.

**Expected**: One Coverage finding for `Request.SuspendReason`; five of six
fields covered. Mentioning `Request.Remark` does not cover the other 200-character
field.

### A03 - Generic document/entity reference

Replace T001:

```markdown
- [ ] T001 [US1] Implement Request validation from data-model.md in src/request.py.
```

**Expected**: Five missing-field Coverage findings for Request fields; one of six
fields covered. The document name and entity name alone do not count.

### A04 - Unresolved field reference

Replace `Request.SuspendReason` with `Request.SuspensionReason` in T001.

**Expected**: A Coverage finding for the unresolved `Request.SuspensionReason`
citation and a Coverage finding for the uncovered `Request.SuspendReason`.
Five of six fields covered; no guessed alias resolution.

### A05 - Cited but conflicting length

Append to T001: `Set Request.SuspendReason maximum length to 500.`

**Expected**: Six covered fields and one Inconsistency finding naming
`Request.SuspendReason`, canonical 200, task-stated 500, and T001. A valid
citation does not neutralize contradictory prose.

### A06 - Uncited and conflicting length

Apply A02, then append to T001:
`Set Request.SuspendReason maximum length to 500.`

**Expected**: Five of six fields covered, one missing-citation finding and one
200-versus-500 Inconsistency finding for `Request.SuspendReason`. Uncited prose
is still compared when its field identity is clear.

### A07 - Matching paraphrase

Append to T001:
`Request.SuspendReason may be omitted; when supplied, strip surrounding whitespace and reject an empty result; allow at most 200 characters.`

**Expected**: Six covered fields, zero constrained-field findings. Equivalent
wording is not a mismatch and need not repeat every other field's constraints.

### A08 - Conflicting required status

Append to T001: `Request.SuspendReason is mandatory and cannot be null.`

**Expected**: One Inconsistency finding for canonical nullable versus task
required/non-null. All six fields remain covered.

### A09 - Conflicting allowed values

Append to T001: `Request.Status also accepts archived.`

**Expected**: One Inconsistency finding for canonical allowed values
`open, suspended` versus the additional `archived` value.

### A10 - Conflicting validation

Append to T001: `Accept Request.RetryCount values through 9.`

**Expected**: One Inconsistency finding for canonical inclusive maximum 3
versus task maximum 9.

### A11 - Same field name on another entity

Remove `Request.Remark` from T001 but keep T002's `Audit.Remark`.

**Expected**: One Coverage finding for `Request.Remark`; five of six fields
covered. `Audit.Remark` must not cover `Request.Remark`.

### A12 - Test-only reference

Apply A02 and append to T003: `Check data-model.md Request.SuspendReason.`

**Expected**: One missing implementation-citation finding for
`Request.SuspendReason`; a test-only reference does not satisfy coverage.

### A13 - Missing optional data model

Omit `data-model.md`. Keep the baseline tasks.

**Expected**: Constrained-field checks are not applicable; no invented canonical
fields, missing-model error, or constrained-field findings. Ordinary analysis
still runs.

### A14 - No constrained fields

Replace `data-model.md` with:

```markdown
# Data Model

Request and Audit have no defined fields or restrictions yet.
```

Replace T001 and T002 with one entity-level implementation task.

**Expected**: Constrained-field checks are not applicable; zero constrained-field
findings. Ordinary underspecification findings may still be appropriate.

### A15 - Bare field names with matching copied values

Replace T001:

```markdown
- [ ] T001 [US1] Implement SuspendReason (nullable, trimmed, 200 characters), Remark (required, 200 characters), Status (open or suspended), RetryCount (0 through 3), and Code (3 through 8 uppercase letters) in src/request.py.
```

**Expected**: Five missing-field Coverage findings; copied values and bare field
names do not replace explicit document/qualified-field citations. No supported
contradiction is present.

### A16 - Conflicting minimum length

Append to T001: `Accept Request.Code values containing one uppercase letter.`

**Expected**: One Inconsistency finding for canonical minimum length 3 versus
task minimum 1.

### A17 - Links instead of plain document references

Replace T002:

```markdown
- [ ] T002 [US1] Implement [Audit.Remark](data-model.md#audit) validation in src/audit.py.
```

**Expected**: Six covered fields, zero constrained-field findings. A link is
valid when the document and exact field identity are explicit.

### A18 - Ambiguous canonical restriction

Change only the canonical RetryCount restriction to
`Nullable; range still to be decided.` Append to T001:
`Use Request.RetryCount maximum 9.`

**Expected**: Do not invent a canonical numeric range or report a supported
numeric mismatch for RetryCount. The ordinary ambiguity/underspecification
pass may flag the undecided range.

### A19 - Document-only reference

Replace T001:

```markdown
- [ ] T001 [US1] Implement field validation from data-model.md in src/request.py.
```

**Expected**: Five missing-field Coverage findings for Request fields; one of six
fields covered by the unchanged audit task. Naming the document without field
identities provides no Request field coverage.

### A20 - Entity-only reference

Replace T001:

```markdown
- [ ] T001 [US1] Implement Request validation in src/request.py.
```

**Expected**: Five missing-field Coverage findings for Request fields; one of six
fields covered by the unchanged audit task. Naming the entity without document
and field references provides no Request field coverage.

In A06, the separate sentence stating a 500-character limit is a field mention,
not an instruction to follow that field's canonical definition. Its qualified
name must not become a citation merely because other fields in the same task
are explicitly cited from data-model.md. The task has both a missing citation
and a contradiction.

## Reproducible review record

For each agent run, record the command/template revision, actual generated
tasks or field findings, comparison with these expectations, and whether any
input changed. Keep limitations explicit: pytest scaffold checks do not execute
these agent scenarios or guarantee model behavior.
