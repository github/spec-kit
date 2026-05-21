---
description: Reverse-generate 4+1 architecture artifacts from observable repository facts.
scripts:
  sh: .specify/extensions/arch/scripts/bash/setup-arch.sh --json
  ps: .specify/extensions/arch/scripts/powershell/setup-arch.ps1 -Json
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Reverse-generate or refresh the project-level architecture SSOT for an ordinary historical repository by first recording observable repository facts, then deriving 4+1 architecture artifacts from those facts.

The workflow writes:

- Repo facts: `.specify/memory/architecture-repo-facts.md`
- Main synthesis: `.specify/memory/architecture.md`
- Scenario view: `.specify/memory/architecture-scenario-view.md`
- Logical view: `.specify/memory/architecture-logical-view.md`
- Process view: `.specify/memory/architecture-process-view.md`
- Development view: `.specify/memory/architecture-development-view.md`
- Physical view: `.specify/memory/architecture-physical-view.md`

`architecture-repo-facts.md` is the evidence layer for this reverse pass. The six architecture files remain the architecture SSOT. They must summarize architecture conclusions, not become source-code audit reports.

## Operating Boundaries

- Write only the seven files listed above.
- Do not modify source code, README files, project documentation, package files, configuration, tests, deployment files, `.specify/memory/uc.md`, `.specify/memory/constitution.md`, feature specs, plans, tasks, root `docs/`, deployment manifests, or runbooks.
- Stay at abstract architecture-design level.
- Do not write concrete classes, files, functions, endpoints, DTO fields, database table fields, framework selections, library choices, UI component details, deployment manifests, task breakdowns, test strategy, validation anchors, code notes, deployment scripts, or runbooks into the architecture views.
- If evidence is insufficient, record a specific gap in the repo facts file and affected view instead of inventing business facts, actors, use cases, components, interfaces, modules, deployment units, or numeric metrics.

## Evidence Sources

Inspect the repository for observable facts. Prefer concise inventory over exhaustive source listing.

Use these source categories when present:

- README and project documentation
- Source layout and named entry points
- Package manager files and build scripts
- Configuration and environment examples
- Tests, fixtures, examples, and sample data
- CLI commands, API routes, UI routes, scheduled jobs, workers, middleware, or event handlers
- CI/CD definitions
- Docker, Compose, Kubernetes, Terraform, or deployment configuration
- Operational scripts
- Recent Git history signals

Git history is auxiliary. It may indicate change axes, hotspots, and boundary risks, but it must not independently prove an architecture conclusion.

### Repository-First Inputs

If `.specify/memory/repository-first/` exists, inspect its markdown artifacts before deriving the architecture views. These files are optional, project-local evidence projections for repositories that already ran a repository-first analysis pass.

Treat these repository-first artifacts as evidence inputs, not as architecture artifacts:

- `.specify/memory/repository-first/technical-dependency-matrix.md`: 2nd/3rd-party dependency facts, version-source signals, version-divergence signals, and unresolved-version signals.
- `.specify/memory/repository-first/module-invocation-spec.md`: first-party module invocation governance, allowed directions, forbidden directions, and dependency-governance rules derived from matrix signals.

When present, summarize repository-first facts into `REPO_FACTS_FILE` under the repository-first projection sections. Use them primarily to support the development view and synthesis constraints. They may also support physical or process gaps when dependency evidence reveals unresolved external systems or runtime ownership ambiguity.

Repository-first content must not be copied verbatim into architecture views. The architecture views may only carry architecture-level conclusions such as stable package boundaries, allowed/forbidden dependency directions, module-governance invariants, unresolved dependency risks, and review triggers.

## Outline

1. **Setup**: Run `{SCRIPT}` from repo root and parse JSON for `ARCH_FILE`, `ARCH_DIR`, `REPO_FACTS_FILE`, `SCENARIO_VIEW`, `LOGICAL_VIEW`, `PROCESS_VIEW`, `DEVELOPMENT_VIEW`, and `PHYSICAL_VIEW`.
2. **Load templates and existing artifacts**:
   - Read the seven architecture artifacts created by setup.
   - Read the seven architecture templates under `.specify/extensions/arch/templates/`.
3. **Build repo fact inventory**:
   - Identify repository identity, entry points, visible behaviors, boundaries, state clues, runtime clues, development structure, deployment clues, and Git history signals.
   - If repository-first artifacts exist, extract first-party module edges, allowed/forbidden invocation rules, dependency matrix signals, and dependency-governance actions.
   - Assign confidence: `High`, `Medium`, or `Low`.
4. **Write repo facts**:
   - Fill `REPO_FACTS_FILE` using the repo facts template.
   - Every non-placeholder fact must name an evidence source.
5. **Derive scenario view**:
   - Derive actors, triggers, use cases, paths, branches, and acceptance semantics from repo facts.
6. **Derive logical view**:
   - Derive capability boundaries, domain objects, states, relationships, and invariants from scenario facts and repo facts.
7. **Derive process view**:
   - Derive runtime links, handoffs, retries, approvals, receipts, and failure closure from repo facts plus scenario and logical views.
8. **Derive development view**:
   - Derive architecture-level components and package boundaries from repo facts plus logical and process views.
9. **Derive physical view**:
   - Derive deployment, external systems, fact sources, observability, and operations constraints from repo facts plus process and development views.
10. **Update synthesis**:
   - Update `ARCH_FILE` using the synthesis template and all completed source artifacts.
11. **Stop and report**:
   - Report the seven updated paths and explicit unresolved architecture gaps.

## Inference Rules

- README, docs, CLI help, API route declarations, UI routes, tests, and examples primarily support scenario view.
- Package directories, module boundaries, imports, configuration ownership, and test grouping primarily support development view.
- Repository-first module invocation specs primarily support development view dependency rules, package boundary intent, synthesis constraints, and review triggers.
- Repository-first dependency matrices primarily support repo facts dependency governance signals; only signal-level conclusions should flow into architecture views.
- State fields, migrations, schema files, fixtures, domain naming, and persistence configuration may support logical view, but cannot alone prove a complete domain model.
- Workers, queues, schedulers, middleware, async jobs, transactions, retries, locks, event handlers, approvals, and receipts may support process view when evidence sources are named.
- Dockerfiles, Compose files, Kubernetes manifests, Terraform, CI/CD, environment examples, and service configuration may support physical view.
- Low-confidence facts may appear in evidence gaps or view gaps, but must not become architecture conclusions.
- Concrete class names, function names, DTO fields, database table fields, and implementation data structures may appear only as evidence sources, not architecture conclusions.

## Confidence

- `High`: multiple independent sources agree, or docs/tests and code entry points agree.
- `Medium`: one strong source is present, such as clear configuration, entry point, route declaration, or behavior test.
- `Low`: naming, directory structure, isolated code, or Git history suggests a fact but lacks behavior evidence.

## Quality Gates

- ERROR if an architecture conclusion has no repo fact source or stated external constraint source.
- ERROR if the repo facts file contains generic claims without file paths, directories, configuration, tests, or commit signals.
- ERROR if 4+1 views promote classes, functions, fields, endpoints, database structure, or implementation details into architecture conclusions.
- ERROR if repository-first dependency matrices are copied wholesale into a 4+1 architecture view instead of being summarized as architecture constraints, dependency rules, gaps, or review triggers.
- ERROR if Git history signals are used alone as architecture conclusions.
- ERROR if physical view invents deployment units not visible from repo facts.
- GAP if actors, use cases, authority boundaries, runtime processes, or deployment topology cannot be supported by repository evidence.
- GAP if the repository lacks deployment, runtime, or business documentation. Missing evidence does not block generation, but it must be explicit.

## Quality Bar

- `architecture-repo-facts.md` must contain enough evidence for every non-gap architecture conclusion.
- Every non-placeholder architecture conclusion must be grounded in a repo fact, scenario, object, runtime link, component boundary, deployment boundary, or stated external constraint.
- Use stable names consistently across repo facts, all five views, and synthesis.
- Keep uncertainty specific: record what is unknown, which view it affects, and which architecture conclusion cannot yet be made.
- Remove generic statements such as "scalable", "secure", "observable", or "modular" unless they name owner, affected view, scope, evidence source, and architecture consequence.
