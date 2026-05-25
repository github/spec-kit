---
description: "Generate or update the active repository governance file"
---

# Repository Governance Generate/Update

## Input

$ARGUMENTS

## Output

- Active repository governance file.
- Managed `SPECKIT GOVERNANCE` section.
- `.specify/memory/repository-governance.md`: internal cache.

## Procedure

1. Require `.specify/`.
2. Resolve target:
   - `.specify/init-options.json` `context_file`
   - `.specify/integration.json` `default_integration` or `integration`
   - `AGENTS.md`
3. Create internal cache when missing.
4. Generate target file when missing.
5. Update only the managed section when target exists.
6. Use existing managed section as refresh source.
7. Distill detected repository areas into action rules.
   - depth: 2
   - include hidden and cache directories
8. Capture repository facts as vertical SSOT evidence.
   - Architecture evidence
   - Engineering evidence
   - Code Style evidence
   - Directory Structure evidence
   - Toolchain evidence
   - Agent Harness evidence
9. Preserve content outside managed markers.
10. Preserve managed markers verbatim.
11. Run:

   ```bash
   uv run python .specify/extensions/repository-governance/scripts/refresh_repository_governance.py
   ```

## Report

- target governance file
- generated or updated
- review target
- internal cache status
- captured evidence when cache is created
