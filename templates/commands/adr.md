---
description: Review existing ADRs and create new ones for architecturally significant decisions made during planning.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json
  ps: scripts/powershell/check-prerequisites.ps1 -Json
---

The user input to you can be provided directly by the agent or as a command argument - you **MUST** consider it before proceeding with the prompt (if not empty).

User input:

$ARGUMENTS

ADR Review Gate - Post-Planning Checkpoint

Goal: Analyze the current feature plan and research to (a) reference relevant existing ADRs in `docs/adr/`, and (b) create new ADRs only when architecturally significant decisions were made during planning.

Execution Flow

1. Run `{SCRIPT}` once from repo root and parse JSON for FEATURE_DIR and AVAILABLE_DOCS. Derive absolute paths:
   - PLAN = FEATURE_DIR/plan.md
   - RESEARCH = FEATURE_DIR/research.md (if exists)
   - DATA_MODEL = FEATURE_DIR/data-model.md (if exists)
   - CONTRACTS_DIR = FEATURE_DIR/contracts/ (if exists)
   Abort with an error explaining to run `/plan` first if `plan.md` does not exist.

2. Load planning artifacts and extract architecturally significant decisions (frameworks, patterns, integration approaches, storage, security, performance strategies). Build a concise decisions list with location references (file, section).

3. Scan `docs/adr/` for existing ADRs. For each decision, determine:
   - Covered by existing ADR → record reference and compliance
   - Conflicts with ADR → record conflict and recommend remediation
   - Not covered → mark as ADR candidate

4. Apply significance test before creating any ADR:
   - Impacts how engineers write or structure software?
   - Has notable tradeoffs/alternatives?
   - Likely to be revisited or questioned later?
   Only create ADRs that pass this bar.

5. For each ADR candidate that passes significance:
   - Call `scripts/bash/create-adr.sh --title "<Title>" --feature "$(basename "$FEATURE_DIR")" --spec "$FEATURE_DIR/spec.md" --plan "$PLAN" --context "<Context>" --decision "<Decision>" --positive "<Positives>" --negative "<Negatives>" --alternatives "<Alternatives>" --json` to create the ADR deterministically.
   - Capture returned `id` and `path` and print them in the summary.

6. Produce an ADR Review Report (DO NOT edit plan.md):
   - Print a table: Decision → Existing ADR | New ADR | Conflict
   - List newly created ADR files with absolute paths
   - Recommend refreshing `docs/adr/index.md` (if present) or generating one

7. Next step guidance:
   - If no blocking conflicts: proceed to `/tasks`
   - If conflicts exist: resolve or supersede ADRs before implementation

Quality Checklist before finalizing:
- Decision is architecturally significant
- Context and rationale are clear
- Alternatives and consequences recorded
- Traceable to spec/plan requirements
- Team can review and accept (immutable once Accepted)

Error Handling:
- If `plan.md` missing → "Run /plan to generate planning artifacts before /adr"
- If no significant decisions → "No new ADRs needed; referencing existing ADRs where applicable"
- If conflicts with existing ADRs → output WARN and recommend resolution before implementation
