# Architecture Reverse Command Design

## Purpose

Add a reverse architecture workflow for ordinary historical repositories that do not already use Spec Kit structure. The workflow introduces a dedicated command, `/speckit.arch.reverse`, that derives project-level 4+1 architecture artifacts from repository facts while preserving evidence traceability.

The command is separate from `/speckit.arch.generate` because the two workflows answer different questions:

- `/speckit.arch.generate` bootstraps or refreshes architecture from scenario intent and existing architecture context.
- `/speckit.arch.reverse` reconstructs architecture from observable repository facts in an existing codebase.

## Scope

The reverse workflow writes only these files:

- `.specify/memory/architecture-repo-facts.md`
- `.specify/memory/architecture.md`
- `.specify/memory/architecture-scenario-view.md`
- `.specify/memory/architecture-logical-view.md`
- `.specify/memory/architecture-process-view.md`
- `.specify/memory/architecture-development-view.md`
- `.specify/memory/architecture-physical-view.md`

The command does not modify source code, README files, project documentation, package files, configuration, tests, deployment files, `.specify/memory/uc.md`, `.specify/memory/constitution.md`, feature specs, plans, tasks, or root `docs/`.

## Architecture

The reverse workflow adds an evidence layer ahead of the existing 4+1 architecture views.

`architecture-repo-facts.md` is the fact source for the reverse pass. It records observable repository facts, evidence sources, confidence, architecture relevance, and unresolved gaps. The six existing architecture files remain the architecture SSOT. They should summarize architecture conclusions, not become source-code audit reports.

The command flow is:

1. Run the architecture setup script from the installed extension path.
2. Ensure `.specify/memory/` exists.
3. Create missing architecture files from templates, including the new repo facts template.
4. Build a repo fact inventory from README/docs, source layout, package files, configuration, tests, examples, CI, deployment files, scripts, and Git history signals.
5. Write `architecture-repo-facts.md` with facts, sources, confidence, supported architecture implications, and evidence gaps.
6. Derive scenario view from observable user-visible behavior, entry points, examples, tests, and documentation.
7. Derive logical view from scenario facts plus domain, state, and boundary clues.
8. Derive process view from runtime, handoff, retry, worker, queue, transaction, approval, and failure-closure clues.
9. Derive development view from module/package boundaries, dependency clues, configuration ownership, and test grouping.
10. Derive physical view from deployment, environment, external system, CI/CD, and operational clues.
11. Update architecture synthesis from the five completed views and the repo facts file.

## Components

### Command

Add `commands/speckit.arch.reverse.md`.

The command defines the reverse workflow, its operating boundaries, evidence requirements, derivation phases, and quality gates. It must instruct the agent to write only the seven allowed files.

### Repo Facts Template

Add `templates/architecture-repo-facts-template.md`.

The template should include:

- Repository identity
- Entry points
- User-visible behaviors
- System boundaries
- Data and state clues
- Runtime and process clues
- Development structure clues
- Physical and deployment clues
- Git history signals
- Evidence gaps

Each fact row must carry an evidence source and confidence. Confidence values are `High`, `Medium`, or `Low`.

### Setup Scripts

Update both setup scripts:

- `scripts/bash/setup-arch.sh`
- `scripts/powershell/setup-arch.ps1`

The scripts should create `architecture-repo-facts.md` from the repo facts template when missing. Their JSON output should include `REPO_FACTS_FILE` in addition to the existing architecture file paths.

### Extension Metadata

Update `extension.yml` to register both commands:

- `speckit.arch.generate`
- `speckit.arch.reverse`

### Documentation

Update user-facing documentation to distinguish the command purposes:

- Use `/speckit.arch.generate` for new or intentionally designed architecture passes.
- Use `/speckit.arch.reverse` for ordinary historical repositories where architecture must be inferred from repo facts.

## Data Flow

Repository facts feed the reverse workflow in one direction:

```text
Repository files and history
  -> architecture-repo-facts.md
  -> scenario view
  -> logical view
  -> process view
  -> development view
  -> physical view
  -> architecture.md synthesis
```

The repo facts file is not a replacement for the architecture views. It is the evidence substrate that allows architecture conclusions to be reviewed and challenged.

## Inference Rules

The reverse command must apply these rules:

- README, docs, CLI help, API route declarations, UI routes, tests, and examples primarily support scenario view.
- Package directories, module boundaries, imports, configuration ownership, and test grouping primarily support development view.
- State fields, migrations, schema files, fixtures, domain naming, and persistence configuration may support logical view, but cannot alone prove a complete domain model.
- Workers, queues, schedulers, middleware, async jobs, transactions, retries, locks, event handlers, approvals, and receipts may support process view when evidence sources are named.
- Dockerfiles, Compose files, Kubernetes manifests, Terraform, CI/CD, environment examples, and service configuration may support physical view.
- Git history is an auxiliary signal for change axes, long-lived hotspots, and boundary risks. It cannot independently prove architecture conclusions.
- Low-confidence facts may appear in evidence gaps or view gaps, but must not become architecture conclusions.
- Concrete class names, function names, DTO fields, database table fields, endpoint details, and implementation data structures may appear only as evidence sources, not architecture conclusions.

Confidence definitions:

- `High`: multiple independent sources agree, or docs/tests and code entry points agree.
- `Medium`: one strong source is present, such as clear configuration, entry point, route declaration, or behavior test.
- `Low`: naming, directory structure, isolated code, or Git history suggests a fact but lacks behavior evidence.

## Error Handling and Gaps

The command should record a specific gap rather than invent a conclusion when evidence is insufficient.

Quality gates:

- Error if an architecture conclusion has no repo fact source or stated external constraint source.
- Error if the repo facts file contains generic claims without file paths, directories, configuration, tests, or commit signals.
- Error if 4+1 views promote classes, functions, fields, endpoints, database structure, or implementation details into architecture conclusions.
- Error if Git history signals are used alone as architecture conclusions.
- Error if physical view invents deployment units not visible from repo facts.
- Gap if actors, use cases, authority boundaries, runtime processes, or deployment topology cannot be supported by repository evidence.
- Gap if the repository lacks deployment, runtime, or business documentation. Missing evidence does not block generation, but it must be explicit.

## Testing Strategy

Verification should cover the extension surface and the setup behavior:

- In a temporary ordinary repository without `.specify/`, run the setup script and verify it creates `.specify/memory/` and all seven target files.
- Verify bash setup JSON includes `REPO_FACTS_FILE`.
- Verify PowerShell setup JSON includes `REPO_FACTS_FILE`.
- Verify `extension.yml` registers both `speckit.arch.generate` and `speckit.arch.reverse`.
- Verify the reverse command document limits writes to the seven allowed files.
- Verify README or equivalent user documentation clearly distinguishes `generate` and `reverse`.
- Optionally run the reverse command manually against a small historical repository and inspect that each architecture conclusion traces to a repo facts source or becomes a gap.

## Non-Goals

The reverse workflow does not:

- Generate or modify `.specify/memory/uc.md`.
- Rewrite project documentation or source code.
- Produce implementation tasks or feature plans.
- Replace human architecture review.
- Infer business facts with no repository evidence.
- Treat C4, UML, Mermaid, PlantUML, class diagrams, or endpoint maps as architecture reasoning sources.

## Review Triggers

Refresh or review the reverse architecture artifacts when:

- Entry points or user-visible behavior change.
- Package/module boundaries are reorganized.
- Deployment topology or external systems change.
- CI/CD, runtime configuration, or environment assumptions change.
- Git history shows repeated changes crossing a stated stable boundary.
- A gap recorded in `architecture-repo-facts.md` is resolved by new evidence.
