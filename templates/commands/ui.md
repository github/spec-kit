---
description: Create or update the UI design blueprint (tokens, components API, flows, skeleton HTML, BDD, data contracts).
scripts:
  sh: scripts/bash/setup-ui.sh
  ps: scripts/powershell/setup-ui.ps1
---

## User Input

```text
$ARGUMENTS
```

You MUST consider the user input before proceeding (if not empty). Treat it as UI intent or additional constraints (e.g., layout style, accessibility priorities, design system hints).

## Outline

1. Run `{SCRIPT}` from repo root and parse its JSON for absolute paths:
   - `UI_DIR`, `TOKENS_FILE`, `COMPONENTS_SPEC`, `FLOWS_FILE`, `HTML_SKELETON`, `BDD_FILE`, `TYPES_SCHEMA`, `TYPES_TS`, `README_FILE`
   - Only run the script once; reuse the JSON printed to the terminal.

2. Open the UI template README using the path from the script JSON output (`README_FILE`). Do not infer or reconstruct the path.

3. Populate the six artifacts using the absolute paths from the script JSON (do not guess paths):
   - Design Tokens (`tokens.json`):
     - Ensure all color, spacing, radius, typography values are declared here.
     - DO NOT hard-code hex colors, pixel values, or fonts in other files.
   - Component API Spec (`components.md`):
     - Define component props/state/events via markdown tables with explicit types and defaults.
     - Keep interfaces minimal and testable; document required vs optional clearly.
   - Flows/States (`flows.mmd`):
     - Draw precise states and transitions (Mermaid stateDiagram-v2); avoid ambiguous labels.
   - Structural Skeleton (`skeleton.html`):
     - Provide a low-fidelity semantic layout with ARIA roles/labels; avoid styling or hard-coded values.
     - Include placeholders that map to components from components.md.
   - BDD Stories (`stories.feature`):
     - Write Given-When-Then scenarios for core flows; ensure they are verifiable and technology-agnostic.
   - Data Contracts (`types.schema.json` or `types.ts`):
     - Prefer JSON Schema (`types.schema.json`) for technology neutrality; alternatively provide TypeScript interfaces (`types.ts`).
     - Document field semantics and error shape.

4. Consistency checks (fix issues in-place):
   - Every visual decision must trace to a token in `tokens.json`.
   - Components referenced in `skeleton.html` must appear in `components.md`.
   - Flows and BDD scenarios should align on states and naming.
   - Data contracts should cover the payloads implied by events and results.

5. Report completion with the absolute paths above and a brief summary of what changed.

## Quality Rules

- Tokens-only styling: all colors/spacing/typography come from tokens.
- Framework-agnostic: keep markup portable; add notes for framework mapping as comments if needed.
- Accessibility-first: include roles/labels/aria-live where applicable.
- Tables: ensure markdown tables render (pipes, headers, separators formatted correctly).
 - Pathing: Always use the script JSON output keys (`UI_DIR`, `TOKENS_FILE`, `COMPONENTS_SPEC`, `FLOWS_FILE`, `HTML_SKELETON`, `BDD_FILE`, `TYPES_SCHEMA`/`TYPES_TS`, `README_FILE`).
