---
description: Wrap core analysis with behavior-first vertical consistency checks.
strategy: wrap
---

## Change Scope Granularity

Check that tasks preserve the planned `M + U` scope. Report missing, widened, or ambiguous scope boundaries as blockers.

## Behavior Vertical Consistency

Analyze whether the feature artifacts close the `spec -> BDD/UIF intent -> contracts -> tasks` loop. This command checks planning consistency only; it does not inspect implementation code or infer interaction flows from built code.

## Analysis Performance Guardrails

Keep analysis bounded to the existing planning artifacts.

- Build a one-pass artifact inventory before deep reading. Record which expected files and directories exist, then short-circuit missing artifact branches as source artifact -> target artifact blockers.
- Use stable IDs as the primary consistency surface: `CASE-`, `SCN-`, `UIF-`, `FIX-`, `AST-`, and `BLK-`. Compare ID sets and declared method/path references before prose-level interpretation.
- Read `tasks.md` and `quickstart.md` once for ID, contract path, API method/path, and validation path evidence. Do not repeatedly scan them per scenario when a single evidence map can answer coverage.
- Read surrounding prose only when a required ID, source section, or blocker explanation is missing or ambiguous.
- Stop expanding a branch after the first blocker that proves the downstream link cannot be closed. Report the blocker with the source artifact and target artifact instead of continuing speculative checks.
- Do not create new analysis artifacts, workflow runners, or external-tool requirements.

Check:

- spec.md user stories have BDD coverage.
- BDD Given steps map to fixtures.
- BDD When steps map to UIF events or API requests.
- BDD Then steps map to feedback or behavior assertions.
- behavior/uif.intent.json is formalized into contracts/uif/*.expected.json.
- behavior drafts exist but formal contracts are missing, without a matching `N/A or blocker` explanation tied to the source draft and missing planning input.
- UIF API calls exist in contracts/api/.
- behavior contracts cover scenarios, fixtures, and assertions.
- tasks.md covers BDD, UIF, API, fixtures, and quickstart validation paths.
- case coverage is closed from checklist through implementation tasks.
- Required case types in `checklists/behavior-testability.md` map to behavior draft scenarios, formal behavior contracts, tasks, and quickstart validation paths.
- positive, negative, boundary, permission, validation, and state_conflict case types are either covered or have `N/A or blocker` evidence.
- failure scenarios declare error code, failure feedback, and state invariant, rollback, or compensation assertion.
- quickstart validation paths cover Required failure scenarios.

Report missing, inconsistent, or stale links by source artifact and target artifact. Keep findings actionable and separate blockers from warnings.

{CORE_TEMPLATE}

## Behavior Analysis Reporting

Before finishing, report whether the vertical consistency chain is closed and list blockers that prevent implementation from continuing.
