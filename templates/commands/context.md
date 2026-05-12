---
description: Ingest existing project documentation and convert it into operational Spec Kit guidance for brownfield or team projects.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty). Treat it as the
scope for documentation discovery, prioritization, or specific files to analyze.

## Goal

Create or refresh operational project context for Spec Kit by reading existing
documentation, preserving it as the detailed source of truth, and synthesizing concise
guidance into:

- `.specify/memory/constitution.md` for authoritative, non-negotiable project rules
- `__CONTEXT_FILE__` for agent-facing documentation map and instruction priority
- `.specify/memory/project-context.md` when longer synthesized guidance is useful

This workflow is intended for brownfield repositories and team projects that already
have README files, architecture documents, ADRs, onboarding notes, runbooks, or other
source material.

## Safety Rules

- **Do not overwrite user-authored documentation blindly.** Existing docs such as
  `README.md`, files under `docs/`, ADRs, runbooks, and design notes are references;
  preserve them unless the user explicitly asks you to edit them.
- **Do not replace detailed source documents with summaries.** Summaries belong in
  Spec Kit memory or the agent context file; detailed docs remain linked as references.
- **Do not invent policy.** If docs are missing, stale, conflicting, duplicated, or
  ambiguous, report the issue and ask for clarification when it affects implementation
  choices.
- **Keep `__SPECKIT_COMMAND_CONSTITUTION__` focused.** This workflow may update
  `.specify/memory/constitution.md`, but the constitution remains the concise source of
  authoritative principles and rules, not a full documentation dump.
- **Preserve production behavior.** Existing behavior in code or production docs takes
  precedence over assumptions. Warn before suggesting changes that could alter live
  behavior.

## Execution Steps

### 1. Establish Scope

1. Parse the user input for explicit paths, documentation categories, domains, or
   exclusions.
2. If no scope is provided, inspect the repository for likely documentation sources:
   - `README.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `SECURITY.md`
   - `docs/`, `documentation/`, `adr/`, `adrs/`, `architecture/`, `design/`
   - `.github/`, `.gitlab/`, issue or PR templates, workflow notes
   - `.specify/memory/constitution.md`, `.specify/memory/project-context.md`
   - Existing agent context files, including `__CONTEXT_FILE__`
3. Build and maintain a list of every file considered. Distinguish files that were read
   from files skipped due to irrelevance, size, binary format, or uncertainty.

### 2. Discover and Classify Documentation

For each relevant document, classify its primary purpose. Use multiple labels when
appropriate:

- **Authoritative policy**: mandatory rules, compliance, security, governance
- **Architecture**: system boundaries, modules, layering, data flow, integrations
- **Domain model**: business concepts, terminology, invariants, workflows
- **Operations**: deployment, runbooks, environments, monitoring, incident response
- **Development workflow**: setup, testing, coding conventions, branching, releases
- **Product context**: users, goals, non-goals, roadmap, support commitments
- **Historical decision**: ADRs, deprecated approaches, migration notes
- **Reference only**: detailed background that should be linked, not copied wholesale

Record for each document:

- Path
- Purpose classification
- Freshness signals, such as dates, version references, deprecated warnings, or links to
  removed files
- Key facts that affect future Spec Kit work
- Conflicts, duplicates, ambiguity, or stale content

### 3. Extract Operational Guidance

Synthesize only guidance that agents can act on during specification, planning, and
implementation:

- Rules that must be followed
- Architecture boundaries and ownership rules
- Required technologies, services, data stores, or integration patterns
- Testing, release, migration, or operational constraints
- Domain vocabulary and invariants that prevent wrong assumptions
- Known hazards, deprecated paths, and production compatibility requirements

Prefer concise bullets with source links. Example constitution entry:

```markdown
## Backend Architecture

- MUST keep domain logic in the application/service layer; adapters may translate I/O
  but must not own business decisions. See: docs/backend/ddd.md
- MUST preserve existing public API behavior unless a spec explicitly calls out a
  migration plan. See: docs/api/compatibility.md
```

### 4. Update `.specify/memory/constitution.md`

Update the constitution only with concise, authoritative rules that are stable enough to
govern future work.

1. Read the current `.specify/memory/constitution.md` if it exists.
2. Add or revise sections for project-specific rules discovered from docs.
3. Keep details brief; link to source docs with `See: path/to/doc.md`.
4. Do not copy long explanatory text, onboarding instructions, or transient project
   status into the constitution.
5. Preserve existing constitution governance and versioning conventions. If the current
   constitution uses a version, update it consistently and explain the bump.
6. If source docs conflict on a rule, do not silently choose one unless precedence is
   clear. Add a TODO or ask for clarification and report the conflict.

### 5. Update `__CONTEXT_FILE__`

Update the agent context file with operational navigation guidance. If the file does not
exist, create it with a clear Spec Kit section. If it already contains a managed Spec Kit
section, update only the relevant section. Preserve user-authored content outside managed
or clearly identified Spec Kit blocks.

Include these sections when possible:

```markdown
## Project Documentation Map

- Architecture: docs/architecture.md — service boundaries, data flow, integration rules
- Backend DDD: docs/backend/ddd.md — domain/application/adapter layering rules
- Operations: docs/runbooks/ — deployment, monitoring, incident response

## Instruction Priority

1. User request
2. `.specify/memory/constitution.md`
3. Relevant documentation listed in Project Documentation Map
4. Existing code patterns
5. Default agent assumptions

When sources conflict, ask for clarification before changing behavior. Existing
production behavior and compatibility constraints must be preserved unless the user
explicitly requests a migration.
```

### 6. Optionally Create or Update `.specify/memory/project-context.md`

Create or refresh `.specify/memory/project-context.md` when the documentation inventory
or synthesized guidance is too detailed for the constitution or agent context file.

Recommended contents:

- Documentation inventory table
- Purpose classification for each doc
- Longer synthesized architecture, domain, operations, and workflow notes
- Conflict and freshness register
- Links to source documents

Do not create this file if the useful context is small enough to fit clearly in the
constitution and `__CONTEXT_FILE__`; report that it was not needed.

### 7. Preserve References and Flag Problems

Before writing changes, prepare a review list containing:

- **Stale docs**: outdated dates, references to missing files, obsolete tooling, retired
  services, or contradicted implementation details
- **Conflicting docs**: incompatible rules across sources
- **Duplicated docs**: multiple documents with the same purpose where one may be older
- **Ambiguous docs**: unclear ownership, optional versus mandatory language, undefined
  acronyms, or missing scope
- **Risky assumptions**: inferred guidance that is not directly supported by a source

For each item, include the exact file path and the reason it needs attention.

### 8. Write Changes Carefully

Allowed writes:

- `.specify/memory/constitution.md`
- `__CONTEXT_FILE__`
- `.specify/memory/project-context.md` when justified

Do not modify source documentation unless the user explicitly requested that in the input.
When updating files, preserve unrelated existing content and prefer appending or replacing
clearly marked Spec Kit sections rather than rewriting entire files.

### 9. Final Report

Return a concise report with:

- Scope used, including user-provided paths or inferred discovery roots
- Exact files read
- Exact files changed
- Constitution sections added or updated
- Whether `.specify/memory/project-context.md` was created or updated
- Stale, conflicting, duplicated, ambiguous, or risky documentation findings
- Any clarification questions or recommended follow-up work

If no files were changed, explain why and list the information still needed.
