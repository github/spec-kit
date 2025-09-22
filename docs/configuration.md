# Configuration

Spec Kit supports external configuration that all slash commands read at startup to locate your constitution and any supplemental documents. Configuration is optional — projects work out of the box with a minimal default.

## Lookup Order

When a command runs, it loads configuration in this order:
- `.specify.yaml` at the repository root (if present)
- `config-default.yaml` at the repository root (fallback)

If neither file is present, commands rely on hardcoded defaults in templates where applicable.

## Files

- `.specify.yaml` — Your project‑specific configuration. Commit this to your repo if you want to customize behavior.
- `config-default.yaml` — Ships with Spec Kit. Contains:
  - A minimal active default (sets only the constitution path) to keep projects zero‑config.
  - A commented, full example demonstrating how to reference architecture docs, front‑end specs, and other documents. This example is an enhancement/extension and is not required.

## Schema Overview

Configuration is defined under the top‑level `spec-kit` key. The canonical structure is a YAML sequence where each item is a single section object:

```yaml
spec-kit:
  - constitution:
      path: "CONSTITUTION.md"
      documents:
        - path: "docs/architecture.md"
          context: "Documents the architecture of the project and should be considered a primary source of truth."
        - path: "docs/ui-architecture.md"
          context: "Documents the UI architecture of the project and should be considered a primary source of truth."
  - specify:
      documents:
        - path: "docs/prd.md"
          context: "Documents the product requirements and should be considered a primary source of truth."
        - path: "docs/front-end-spec.md"
          context: "Documents the front-end specifications and should be considered a primary source of truth."
  - plan:
      technical_context:
        - "**Coding Standards**: [NEEDS CLARIFICATION]"
      additional_research:
        - "Analyse the architecture documents and prepare a summary of the relevant sections as they relate to the implementation of the plan."
      documents:
        - path: "docs/architecture.md"
          context: "Documents the architecture of the project and should be considered a primary source of truth."
        - path: "docs/ui-architecture.md"
          context: "Documents the UI architecture of the project and should be considered a primary source of truth."
        - path: "docs/front-end-spec.md"
          context: "Documents the front-end specifications and should be considered a primary source of truth."
  - tasks:
      documents:
        - path: "docs/architecture.md"
          context: "Documents the architecture of the project and should be considered a primary source of truth."
        - path: "docs/ui-architecture.md"
          context: "Documents the UI architecture of the project and should be considered a primary source of truth."
        - path: "docs/front-end-spec.md"
          context: "Documents the front-end specifications and should be considered a primary source of truth."
  - implement:
      documents:
        - path: "docs/work-flow.md"
          context: "Documents the implementation work-flow for the project and should be considered a primary source of truth."
```

Notes:
- Paths are resolved relative to the repository root.
- Missing optional files are noted and skipped by the agent.
- The commented example above mirrors the structure demonstrated in `config-default.yaml` and is meant as an enhancement; you do not need to include any of it to use Spec Kit.

## Keys and Their Roles

- `constitution.path`
  - Absolute or repo‑relative path to your constitution Markdown file.
  - Default (from `config-default.yaml`): `/memory/constitution.md`.

- `specify.documents[]`
  - Additional documents the `/specify` phase should consider (e.g., PRD, UX notes).
  - Each item has:
    - `path`: repo‑relative file path
    - `context`: short description of how to use the document

- `plan.documents[]`
  - Design references the `/plan` phase should read (architecture, UI specs, etc.).
  - Same item shape as `specify.documents`.

- `plan.technical_context[]`
  - Lines appended to the “Technical Context” section of the plan template. Keep `[NEEDS CLARIFICATION]` markers where appropriate to drive targeted research.

- `plan.additional_research[]`
  - Independent, plain‑text research instructions executed during Phase 0 of the `/plan` command.
  - As defined in the plan template (see `templates/plan-template.md`, Phase 0, step 5), each instruction is run separately and its output is appended to `research.md` under a top‑level heading `## Additional Research`.
  - For each instruction, the agent derives a concise section title from the output (do not repeat the instruction verbatim) and writes a section using the following structure:
    - `### {Concise Title Derived From Output}`
    - Summary and details produced by the instruction
    - References or source notes (if applicable)
  - Why this is useful: these focused, instruction‑driven sections turn open questions or context gathering (“unknowns”) into explicit, documented findings that inform the rest of Phase 1 (design & contracts) and later `/tasks` generation. For example, the instruction:
    - "Analyse the architecture documents and prepare a summary of relevant sections as they relate to the implementation plan."
    will typically yield a section such as:
    - `### Architecture Implications for Plan`
      - Key components and boundaries impacting the design
      - Constraints (e.g., services, data flows, performance goals)
      - Direct links into tasks (e.g., required services or integration points)

- `tasks.documents[]`
  - Supplemental references for `/tasks` generation (data model, contracts, UI specs, etc.).

- `implement.documents[]`
  - Additional references for `/implement` (workflow guides, operations runbooks, etc.).

## Command Behavior and Configuration

Every command loads configuration at the start, extracts the `spec-kit` section into an internal structure, and prints the effective configuration for visibility.

- `/constitution`
  - Reads `constitution.path` and optional `constitution.documents[]`.
  - Treats the existing constitution (if found) as a primary source of truth.

- `/specify`
  - Reads `specify.documents[]` to inform specification writing.

- `/plan`
  - Reads `plan.documents[]`, `plan.technical_context[]`, and `plan.additional_research[]`.
  - Uses `constitution.path` to perform the “Constitution Check”.

- `/tasks`
  - Reads `tasks.documents[]` plus the design artifacts generated in Phase 1 (contracts, data‑model, quickstart).

- `/implement`
  - Reads `implement.documents[]` and the artifacts produced in previous phases.

## Examples

Minimal (zero‑config) project — rely on defaults:
```yaml
spec-kit:
  - constitution:
      path: "/memory/constitution.md"
```

Product team with architecture & frontend specs:
```yaml
spec-kit:
  - constitution:
      path: "CONSTITUTION.md"
      documents:
        - path: "docs/architecture.md"
          context: "Primary architecture reference"
        - path: "docs/ui-architecture.md"
          context: "UI architecture reference"
  - specify:
      documents:
        - path: "docs/prd.md"
          context: "Product requirements"
        - path: "docs/front-end-spec.md"
          context: "Front‑end specifications"
  - plan:
      technical_context:
        - "**Testing**: pytest; CI required"
        - "**Performance**: p95 < 200ms"
      additional_research:
        - "Benchmark ORM options vs raw SQL for our scale"
      documents:
        - path: "docs/architecture.md"
          context: "Architecture reference"
        - path: "docs/front-end-spec.md"
          context: "Front‑end specifications"
```

## Best Practices

- Start minimal; add documents only when they materially improve decision quality.
- Keep `context` fields concise but directive — explain how the document should influence decisions.
- Retain `[NEEDS CLARIFICATION]` markers in `plan.technical_context` to drive targeted research tasks.
- Store stable, versioned references (e.g., link to in‑repo docs, not ephemeral sources).

## Common Pitfalls

- Confusing example with requirement: The commented full example in `config-default.yaml` is optional and not required.
- Incorrect paths: All paths are resolved relative to the repo root; ensure files exist.
- Overloading technical context: Keep entries crisp; lengthy prose belongs in dedicated docs referenced via `documents`.

## Verification

When you run a command, look for the printed `SPEC_KIT_CONFIG` in your agent’s output to confirm that your `.specify.yaml` was loaded. If you don’t see your changes reflected:
- Verify `.specify.yaml` is at the repository root.
- Validate YAML formatting (indentation, list markers).
- Confirm there are no filename typos in `path` values.
