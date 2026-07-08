# Constitution

> Durable compliance and boundary rules for this repository.
> Operational workflows and agent commands are out of scope.

## I. Scope and Authority

- This constitution governs all changes merged into this repository.
- When docs, scripts, or team habits conflict with this document, this document
  wins until formally amended.
- Workflows and tooling guides MUST NOT contradict these rules.

## II. Change Boundaries

### II.1 Approved scope

- Every change MUST tie to a tracked work item (issue, ticket, or equivalent)
  unless explicitly exempted by maintainers.
- Changes MUST stay within the approved scope; scope expansion requires updating
  the work item or opening a new one.

### II.2 Impact-sensitive changes

- Changes that affect public API, shared schemas, config contracts, security
  boundaries, or cross-module behavior MUST be documented before merge.
- Breaking changes MUST include migration, rollback, or compatibility notes.

### II.3 Minimal diff

- Prefer the smallest change that satisfies the requirement; unrelated refactors
  MUST NOT ride along without justification.

## III. Quality and Verification

### III.1 Evidence before merge

- Behavior changes MUST include proportionate automated tests, self-tests, or
  documented manual verification.
- Skipped checks MUST record a concrete reason; vague deferrals are not
  acceptable.

### III.2 Regression safety

- Fixes MUST include a test or reproducible verification step when feasible.
- Release-critical paths MUST NOT be changed without evidence that existing
  behavior is preserved or intentionally replaced.

## IV. Security, Privacy, and Compliance

### IV.1 Secrets and sensitive data

- Secrets, credentials, tokens, and private keys MUST NOT be committed.
- Logs, fixtures, and sample data MUST NOT contain real personal or
  confidential information unless explicitly approved and protected.

### IV.2 Dependency and license

- New dependencies MUST be justified; copyleft or policy-restricted licenses
  MUST be reviewed before adoption.
- Known-vulnerable dependencies MUST NOT be introduced without documented
  exception and remediation plan.

## V. Repository Hygiene

### V.1 Traceability

- Pull requests MUST reference the canonical work item and summarize
  user-visible impact.
- Commit messages MUST be understandable without hidden chat context.

### V.2 Documentation

- User-facing or operator-facing behavior changes MUST update relevant docs in
  the same change set when applicable.
- Deprecated behavior MUST be marked with removal timeline or migration path
  when breaking.

## VI. Governance

- Amendments require documented rationale, semantic version bump, and
  maintainer approval.
- **MAJOR**: incompatible rule removal or redefinition.
- **MINOR**: new section or material expansion.
- **PATCH**: clarification or non-semantic wording only.

**Version**: 1.0.0 | **Last Amended**: 2026-07-07
