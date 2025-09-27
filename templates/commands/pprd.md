---
description: Generate a Portfolio/Product PRD (PPRD) Markdown document using the PPRD template.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --paths-only
  ps: scripts/powershell/check-prerequisites.ps1 -Json -PathsOnly
---

The user input to you can be provided directly by the agent or as a command argument - you MUST consider it before proceeding with the prompt (if not empty).

User input:

$ARGUMENTS

Goal: Create a new PPRD file by resolving the layout template (assets override if present) and saving it at the canonical specs root defined by the layout. Prefer a single file named per `files.pprd` (e.g., `specs/pprd.md`) unless the repository uses a multi-PPRD convention.

Execution steps:

1. Run `{SCRIPT}` from the repository root ONCE and parse its JSON for `REPO_ROOT`. All subsequent paths are absolute.
2. Determine the canonical specs root: run `scripts/bash/spec-root.sh` (or PowerShell variant) and capture its absolute output as `SPEC_ROOT`.
3. Resolve the PPRD layout: run `scripts/bash/resolve-template.sh --json pprd` (or PowerShell) and parse `TEMPLATE_PATH`.
4. Load the layout from `TEMPLATE_PATH`.
5. Parse the user input to extract fields:
   - Required: `PPRD_ID` (e.g., `001`, `2025Q1-01`) and `TITLE` (short, human-readable).
   - Optional links: `VIS` (e.g., `VIS-123`), `STR` (e.g., `STR-42`), `ROAD` (e.g., `ROAD-2025Q1`).
   - Flexible parsing rules:
     * Accept formats like: `ID=123 Title=Payments Revamp VIS=VIS-10 STR=STR-7 ROAD=ROAD-2025Q1`
     * Or quoted: `ID="123" Title="Payments Revamp"`
     * Or a simple line: `<ID>: <Title>`
   - If `PPRD_ID` or `TITLE` cannot be determined from input, STOP and ask the user to provide the missing value(s) succinctly.
6. Read the layout file name for PPRD (`files.pprd` in `.specs/.specify/layout.yaml`) if present. Otherwise default to `pprd.md`.
7. Compute `PPRD_PATH`:
   - Single-file convention: `PPRD_PATH = SPEC_ROOT + '/' + files.pprd` (preferred for most repositories)
   - Multi-PPRD convention (only if explicitly chosen by the user): derive a slug and place under `SPEC_ROOT/pprd/` with a disambiguating file name.
8. Populate the template:
   - Replace the heading line `# PPRD-[ID]: [Portfolio / Product PRD Title]` with `# PPRD-<PPRD_ID>: <TITLE>`.
   - Replace the **Links** line with available values: `**Links:** Vision (VIS-###), Strategy (STR-###), Roadmap entry (ROAD-YYYYQX)` -> `**Links:** Vision (<VIS or N/A>), Strategy (<STR or N/A>), Roadmap entry (<ROAD or N/A>)`.
   - Leave the remaining sections intact as structured prompts to be filled by the product team.
9. Write the completed document to `PPRD_PATH` (create directories as needed). If the file already exists and is non-empty, do not overwrite; append a minimal header noting the attempted creation and exit.
10. Output a short report including: `PPRD_ID`, `TITLE`, `PPRD_PATH`.

Notes:
- PPRD documents are portfolio/product-level; they are not tied to a feature branch. Do NOT modify feature spec files or branch state.
- Always use absolute paths in file operations to avoid context issues.
- If links are omitted, insert `N/A` placeholders to make the document valid and easy to update later.

Context for PPRD creation: {ARGS}
