# Spec Kit Discovery Extension

`spec-kit-discovery` provides a `discovery` extension for Spec Kit. It adds scope-bounded commands for the technical discovery phase:

```text
/speckit.discovery.feasibility [goal or idea] [constraints] [success criteria]
/speckit.discovery.techselect [decision to make] [candidate options] [criteria or constraints]
/speckit.discovery.decision type: api|performance|migration|ux|compatibility [scenario] [constraints or risks]
/speckit.discovery.codebase [target area or fuzzy scope] [planned change or integration] [known concerns]
/speckit.discovery.codebase-api-imp [API route, SDK method, topic, command, or capability] [known concern] [source scope]
/speckit.discovery.poc [user stories] [use cases] [core design idea]
```

The extension helps teams complete technical discovery before formal planning. `feasibility`, `techselect`, and `codebase` produce decision documents; `decision` evaluates scenario-specific API, performance, migration, UX, and compatibility risks; `codebase-api-imp` explains existing interface implementations from source facts; `poc` creates a bounded-scope experiment that supports feasibility, selection, scenario decision, or legacy-codebase risk decisions.

Internally, the commands are organized into four capability types:

- `feasibility`: support a go/no-go continuation decision.
- `techselect`: compare general technology choices.
- `decision`: evaluate scenario-specific API, performance, migration, UX, and compatibility decisions with type-specific risks.
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

### `speckit.discovery.decision`

Evaluates a scenario-specific technical decision before formal planning. Use `type: api`, `type: performance`, `type: migration`, `type: ux`, or `type: compatibility` to select the decision frame and output template.

Typical output:

- `api-integration-discovery.md`
- `performance-discovery.md`
- `data-migration-discovery.md`
- `ux-discovery.md`
- `compatibility-discovery.md`
- type-specific `Planning Decision`

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

## Scenario-Specific Technical Decisions

Use `/speckit.discovery.decision` when the unknown is already tied to a common technical decision situation. The command creates a single-decision discovery document with a type-specific `Planning Decision`, and sets `Evaluation Mode` to either `comparison` or `single-approach-readiness`.

| Decision type | Use for | Typical output |
|---|---|---|
| `api` | Third-party API, SDK, webhook, service, SaaS platform, or partner integration decisions. | `api-integration-discovery.md` |
| `performance` | Latency, throughput, scalability, resource, capacity, or cost decisions. | `performance-discovery.md` |
| `migration` | Data model, storage, schema, backfill, import/export, or migration decisions. | `data-migration-discovery.md` |
| `ux` | Complex interaction, stateful workflow, accessibility, responsive behavior, or frontend/backend handoff decisions. | `ux-discovery.md` |
| `compatibility` | Browser, OS, device, runtime, framework, API version, or deployment compatibility decisions. | `compatibility-discovery.md` |

## Repository Structure

```text
.
├── extension.yml
├── commands/
│   ├── codebase-api-imp.md
│   ├── codebase.md
│   ├── decision.md
│   ├── feasibility.md
│   ├── poc.md
│   └── techselect.md
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
