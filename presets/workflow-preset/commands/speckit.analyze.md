---
description: Wrap core analysis with behavior-first vertical consistency checks.
strategy: wrap
---

## Behavior Vertical Consistency

Analyze whether the feature artifacts close the `spec -> BDD/UIF intent -> contracts -> tasks` loop. This command checks planning consistency only; it does not inspect implementation code or infer interaction flows from built code.

Check:

- spec.md user stories have BDD coverage.
- BDD Given steps map to fixtures.
- BDD When steps map to UIF events or API requests.
- BDD Then steps map to feedback or behavior assertions.
- behavior/uif.intent.json is formalized into contracts/uif/*.expected.json.
- behavior drafts exist but formal contracts are missing, without a matching `N/A or blocker` explanation tied to `behavior/open-questions.json`.
- UIF API calls exist in contracts/api/.
- behavior contracts cover scenarios, fixtures, and assertions.
- tasks.md covers BDD, UIF, API, fixtures, and quickstart validation paths.

Report missing, inconsistent, or stale links by source artifact and target artifact. Keep findings actionable and separate blockers from warnings.

{CORE_TEMPLATE}

## Behavior Analysis Reporting

Before finishing, report whether the vertical consistency chain is closed and list blockers that should be resolved before implementation continues.
