# Spec Kit Discovery Extension

`spec-kit-discovery` provides a `discovery` extension for Spec Kit. It adds scope-bounded commands for the technical discovery phase:

```text
/speckit.discovery.feasibility [goal or idea] [constraints] [success criteria]
/speckit.discovery.techselect [decision to make] [candidate options] [criteria or constraints]
/speckit.discovery.codebase [target area or fuzzy scope] [planned change or integration] [known concerns]
/speckit.discovery.poc [user stories] [use cases] [core design idea]
/speckit.discovery.api [integration target] [intended workflow] [constraints or risks]
/speckit.discovery.codebase-api-imp [API route, SDK method, topic, command, or capability] [known concern] [source scope]
/speckit.discovery.performance [performance concern] [target flow] [load or success criteria]
/speckit.discovery.migration [data or storage change] [current state] [migration constraints]
/speckit.discovery.ux [user workflow] [interaction concern] [success criteria]
/speckit.discovery.compatibility [compatibility target] [feature or workflow] [supported environments]
```

The extension helps teams complete technical discovery before formal planning. `feasibility`, `techselect`, and `codebase` produce decision documents; `codebase-api-imp` explains existing interface implementations from source facts; `poc` creates a bounded-scope experiment that supports feasibility, selection, or legacy-codebase risk decisions. Vertical technology decision commands provide single-decision entry points for common API, performance, migration, UX, and compatibility decisions.

Internally, the commands are organized into four capability types:

- `feasibility`: support a go/no-go continuation decision.
- `techselect`: compare general technology choices.
- `api`, `performance`, `migration`, `ux`, and `compatibility`: evaluate vertical technology decisions with scenario-specific risks.
- `codebase`, `codebase-api-imp` (API implementation overview), and `poc`: locate relevant source scope, gather source-backed evidence, record evidence levels and unknowns, explain implemented interface behavior, or run executable validation.

## Installation

From a Spec Kit project:

```bash
specify extension add --dev /path/to/spec-kit-discovery
```

From this repository during local development:

```bash
specify extension add --dev . --force
```

After installation, restart or refresh your AI coding agent if the new command does not appear immediately.

## Commands

### `speckit.discovery.feasibility`

Produces an evidence-backed feasibility study.

Typical output:

- `feasibility.md`
- decision: `feasible`, `feasible-with-risks`, `not-feasible`, or `inconclusive`

### `speckit.discovery.techselect`

Builds a technology selection matrix for candidate tools, libraries, platforms, or architectures.

Typical output:

- `tech-selection-matrix.md`
- recommendation, shortlist, or evidence gap

### `speckit.discovery.codebase`

Assesses legacy codebase risks, reusable assets, constraints, and integration hazards. When the target area is fuzzy, it first narrows likely source areas before using files, symbols, tests, configuration, and observed behavior as evidence for planning.

Typical output:

- `legacy-codebase-risk-assessment.md`
- scoped source areas or inspected paths
- source facts with file references
- evidence level per finding
- unknowns and unresolved questions
- risks rated as `low`, `medium`, `high`, or `unknown`

### `speckit.discovery.codebase-api-imp`

Explains how an already implemented API or interface works from repository facts. Use it for an HTTP/RPC route, SDK method, message topic, scheduled job, CLI command, or internal capability when engineers need implementation understanding or defect-localization guidance.

Typical output:

- `codebase-api-imp.md`
- interface match and source-backed entrance evidence
- service/system-level and module/component-level Mermaid sequence diagrams when evidence supports them
- repository-fact-backed business implementation flowcharts for key branches, dependencies, exceptions, and return paths
- evidence levels: `Proven`, `Framework inferred`, `Runtime dependent`, or `Unknown`

### `speckit.discovery.poc`

Creates a bounded-scope PoC plan and, when static evidence is insufficient and execution preconditions are met, a minimum runnable validation plus evidence report and conclusion.

Minimum input:

- User stories
- Use cases
- Core design idea

Example:

```text
/speckit.discovery.poc US: Readers can search notes by title and body. UC: Search while typing and open a result. Core design idea: Use SQLite FTS5 with a small local index.
```

The command produces:

- `poc-plan.md`
- `poc-result.md`
- `discovery/<short-name>/poc/` minimum validation code or scripts when executable evidence is required
- evidence logs or outputs
- result: `passed`, `failed`, or `inconclusive`

## Vertical Technology Decision Commands

Use vertical technology decision commands when the unknown is already tied to a common technical decision situation. Each command creates a single-decision discovery document with a command-specific `Planning Decision`, while remaining independent from the other commands. Each command sets `Evaluation Mode` to either `comparison` or `single-approach-readiness`.

### `speckit.discovery.api`

Evaluates a third-party API, SDK, webhook, service, SaaS platform, or partner integration technology decision.

Typical output:

- `api-integration-discovery.md`
- decision question, candidate approaches, contract, auth, rate-limit, failure-handling, security, validation findings, and planning decision

### `speckit.discovery.performance`

Evaluates a latency, throughput, scalability, resource, or capacity technology decision.

Typical output:

- `performance-discovery.md`
- decision question, candidate approaches, workload assumptions, success criteria, bottleneck hypotheses, measurement plan, evidence, and planning decision

### `speckit.discovery.migration`

Evaluates a data model, storage, schema, backfill, import/export, or migration technology decision.

Typical output:

- `data-migration-discovery.md`
- decision question, candidate approaches, affected data flows, rollout and rollback notes, scenario risks, validation plan, and planning decision

### `speckit.discovery.ux`

Evaluates a complex UX interaction, stateful workflow, accessibility requirement, or frontend/backend handoff technology decision.

Typical output:

- `ux-discovery.md`
- decision question, candidate approaches, user scenarios, states, edge cases, accessibility and responsiveness risks, and planning decision

### `speckit.discovery.compatibility`

Evaluates a browser, OS, device, runtime, framework, API version, or deployment compatibility technology decision.

Typical output:

- `compatibility-discovery.md`
- decision question, candidate approaches, support matrix, scenario risks, test matrix, fallback notes, and planning decision

## Repository Structure

```text
.
├── extension.yml
├── commands/
│   ├── api.md
│   ├── codebase-api-imp.md
│   ├── compatibility.md
│   ├── feasibility.md
│   ├── migration.md
│   ├── performance.md
│   ├── poc.md
│   ├── codebase.md
│   ├── techselect.md
│   └── ux.md
├── templates/
│   ├── api-integration-discovery.md
│   ├── codebase-api-imp.md
│   ├── compatibility-discovery.md
│   ├── data-migration-discovery.md
│   ├── feasibility.md
│   ├── legacy-codebase-risk-assessment.md
│   ├── performance-discovery.md
│   ├── poc-plan.md
│   ├── poc-result.md
│   ├── tech-selection-matrix.md
│   └── ux-discovery.md
├── docs/
│   └── usage.md
├── CHANGELOG.md
├── LICENSE
└── README.md
```

## Development

Validate the extension from a Spec Kit project with:

```bash
specify extension add --dev /path/to/spec-kit-discovery --force
specify extension info discovery
```

## License

MIT
