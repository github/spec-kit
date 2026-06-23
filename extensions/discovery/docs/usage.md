# Usage

Use the `discovery` extension before formal planning when a product idea, technical direction, technology choice, legacy integration, or scenario-specific technical decision risk has important unknowns.

The extension provides six source-backed discovery commands:

- `/speckit.discovery.feasibility`: feasibility study.
- `/speckit.discovery.techselect`: technology selection matrix.
- `/speckit.discovery.decision`: scenario-specific API, performance, migration, UX, or compatibility technical decision.
- `/speckit.discovery.codebase`: scope-located, evidence-graded legacy codebase assessment.
- `/speckit.discovery.codebase-api-imp`: source-backed implementation overview for an existing API or interface.
- `/speckit.discovery.poc`: proof-of-concept experiment.

Think of the command set as four capability types:

- `feasibility`: support a go/no-go continuation decision.
- `techselect`: compare general technology choices.
- `decision`: evaluate API, performance, migration, UX, and compatibility decisions with scenario-specific risks.
- `codebase`, `codebase-api-imp`, and `poc`: locate relevant source scope, gather source-backed evidence, record evidence levels and unknowns, explain implemented interface behavior, or run executable validation.

PoC input should stay bounded-scope:

- User stories: what the user wants to accomplish.
- Use cases: key scenarios or typical flows.
- Core design idea: the proposed algorithm, technical path, architecture idea, or implementation approach.

The command derives the validation question, hypothesis, success criteria, minimal executable experiment, sample inputs, expected observations, and risk focus from those inputs.

Good discovery candidates include:

- A third-party API or SDK integration.
- A performance or scalability assumption.
- A UX interaction that may be difficult to implement cleanly.
- A storage, migration, or data modeling decision.
- A cross-platform compatibility risk.

## Scenario-Specific Technical Decision Selection

Use `/speckit.discovery.decision` when the user already knows the shape of the technical decision:

| Situation | Decision type | Typical output |
|---|---|---|
| External API, SDK, webhook, SaaS, partner, or service dependency | `type: api` | `api-integration-discovery.md` |
| Latency, throughput, load, scalability, resource, or cost assumption | `type: performance` | `performance-discovery.md` |
| Schema, model, storage, backfill, import/export, or data migration risk | `type: migration` | `data-migration-discovery.md` |
| Complex interaction, stateful workflow, accessibility, responsive behavior, or handoff risk | `type: ux` | `ux-discovery.md` |
| Browser, OS, device, runtime, dependency, deployment, or version support risk | `type: compatibility` | `compatibility-discovery.md` |

The command sets a type-specific `Planning Decision`. It sets `Evaluation Mode` to `comparison` when evaluating multiple candidates, or `single-approach-readiness` when evaluating one approach against acceptance criteria. Use follow-up commands only when the decision assessment recommends them.

## Source-Backed Codebase Command Selection

Use these commands when existing source facts affect planning:

| Situation | Command | Typical output |
|---|---|---|
| Fuzzy existing module, reusable asset, integration hazard, or legacy risk | `/speckit.discovery.codebase` | `legacy-codebase-risk-assessment.md` |
| Existing API route, SDK method, topic, command, job, or capability implementation | `/speckit.discovery.codebase-api-imp` | `codebase-api-imp.md` |

## Example

Feasibility:

```text
/speckit.discovery.feasibility Goal: Add webhook retry support. Constraints: Existing worker queue, no duplicate side effects, must ship in two weeks. Success: retries are reliable and auditable.
```

Technology selection:

```text
/speckit.discovery.techselect Decision: choose search implementation. Candidates: SQLite FTS5, Meilisearch, Postgres full-text search. Criteria: local-first fit, setup cost, query quality, maintenance burden.
```

Legacy codebase assessment:

```text
/speckit.discovery.codebase Target: webhook retry/delivery area, not sure exact module. Planned change: add retries. Concerns: idempotency, test coverage, existing event schema.
```

Codebase API implementation overview:

```text
/speckit.discovery.codebase-api-imp Target: POST /webhooks/stripe. Concern: duplicate event handling and retry behavior. Scope: payment service.
```

PoC:

```text
/speckit.discovery.poc US: Operators can retry failed webhook deliveries. UC: A duplicate retry should not create duplicate side effects. Core design idea: Use an idempotency key derived from provider event ID plus delivery attempt.
```

API integration:

```text
/speckit.discovery.decision type: api Target: Stripe webhooks. Workflow: mark invoices paid after payment_succeeded. Risks: retries, duplicate events, signature verification, local replay tests.
```

Performance:

```text
/speckit.discovery.decision type: performance Concern: search must respond under 200ms p95. Target flow: note search while typing. Load: 50k local notes and 10 concurrent queries.
```

Data migration:

```text
/speckit.discovery.decision type: migration Change: split customer address into normalized table. Current: address JSON on customer records. Constraints: zero downtime, rollback within one release.
```

UX:

```text
/speckit.discovery.decision type: ux Workflow: bulk edit selected records. Concern: partial failures, undo, keyboard access, and responsive toolbar behavior. Success: operators can recover from failed rows.
```

Compatibility:

```text
/speckit.discovery.decision type: compatibility Target: Safari and Chromium browsers. Feature: offline note sync. Environments: latest two major versions on desktop and mobile.
```

PoC expected result:

- A `poc-plan.md` file.
- A single-hypothesis validation question, hypothesis, success criteria, and minimal executable experiment.
- A small runnable PoC under `discovery/<short-name>/poc/` when executable evidence is required and execution preconditions are met.
- Evidence logs, outputs, screenshots, or metrics.
- A `poc-result.md` file with result set to `passed`, `failed`, or `inconclusive`.

## Recommended Flow

1. Run `/speckit.discovery.decision` when the decision shape is obvious, such as `type: api` or `type: performance`.
2. Run `/speckit.discovery.feasibility` when the main question is whether the idea supports a go/no-go continuation decision.
3. Run `/speckit.discovery.techselect` when a general technology choice needs an explicit comparison, or when `/speckit.discovery.decision` finds multiple tools or architectures that need broader comparison.
4. Run `/speckit.discovery.codebase` when the existing code scope is unclear, source facts may affect the plan, or unknowns need to be confirmed before planning.
5. Run `/speckit.discovery.codebase-api-imp` when the source scope is an existing API or interface and engineers need the implementation path, key branches, dependencies, exceptions, or runtime boundaries explained.
6. Run `/speckit.discovery.poc` when an assumption needs executable evidence.
7. Continue with `/speckit.specify`, `/speckit.plan`, `/speckit.tasks`, and `/speckit.implement` once discovery evidence is strong enough for formal planning.
