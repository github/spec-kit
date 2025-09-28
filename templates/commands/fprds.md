---
description: Decompose a PPRD into one or more Feature PRDs (FPRDs) and create feature folders using the repository’s declarative layout.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --paths-only
  ps: scripts/powershell/check-prerequisites.ps1 -Json -PathsOnly
---

The user input to you can be provided directly by the agent or as a command argument - you MUST consider it before proceeding with the prompt (if not empty).

User input:

{ARGS}

Goal: From a portfolio/product PRD (PPRD), identify concrete features and create corresponding Feature PRDs (FPRDs) with correct folders/filenames based on the layout configuration. Confirm the feature list with the user before creating files.

Execution steps:

1) Run `{SCRIPT}` from the repository root once and parse `REPO_ROOT` (JSON). All subsequent paths are absolute.
2) Resolve the FPRD layout template path by running `scripts/bash/resolve-template.sh --json spec` (or PowerShell variant) and reading `TEMPLATE_PATH`.
3) Determine PPRD source:
   - If user passed a PPRD path in arguments, use it.
   - Else search `REPO_ROOT/.specs/.specify/pprd/*.md` for the most recent file.
   - If none found, ask the user to specify the PPRD path or create one with `/pprd`.
4) Read the PPRD. Propose a list of 3–7 FPRDs with titles and one‑line scope each. Include optional epic/product attribution if present in PPRD (and surface inferred `SPECIFY_EPIC` / `SPECIFY_PRODUCT` values).
5) Ask the user to confirm/edit the feature list before creation. Do not create files until the user confirms.
6) For each confirmed feature (in order):
   - Compute environment hints from PPRD if possible:
     * If the PPRD defines a product/epic, set them as `SPECIFY_PRODUCT` and `SPECIFY_EPIC` for this feature creation.
   - Create the feature folder + branch and seed the FPRD file by running (from REPO_ROOT):
     - POSIX example: `SPECIFY_PRODUCT="<product>" SPECIFY_EPIC="<epic>" .specs/.specify/scripts/bash/create-new-feature.sh --json "<Feature Title>"`
     - PowerShell example: `$env:SPECIFY_PRODUCT="<product>"; $env:SPECIFY_EPIC="<epic>"; .specs/.specify/scripts/powershell/create-new-feature.ps1 -Json "<Feature Title>"`
   - Parse JSON: `BRANCH_NAME`, `SPEC_FILE`.
   - Load the FPRD layout (from `TEMPLATE_PATH`). Populate the new FPRD file (SPEC_FILE) using the PPRD as upstream context:
     * Bring forward relevant Personas/JTBD, guardrails, and constraints.
     * Write a concise “Context & Goals” preface linking back to the PPRD.
     * Draft initial User Scenarios and Functional Requirements at feature level.
     * Mark ambiguities in the FPRD with `[NEEDS CLARIFICATION: ...]` to be resolved later via `/clarify`.
   - Save SPEC_FILE atomically after writing.
7) Output a summary table with: Feature Title, Branch, SPEC_FILE path.
8) Recommend next steps: run `/clarify` on each feature, then `/plan` and `/tasks`.

Behavior rules:
- Never overwrite an existing SPEC_FILE; if it exists with non‑empty content, append a minimal header noting linkage and skip template re‑seeding.
- Keep the PPRD unchanged; this command only creates FPRDs.
- For layout routing (flat/epic/product), rely on environment variables set per feature as described above; do not write layout files.

Context for feature decomposition: {ARGS}

