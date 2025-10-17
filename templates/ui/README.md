# UI Blueprint Templates

Purpose: Provide framework-agnostic, machine-readable UI design blueprints to reduce ambiguity during AI-assisted implementation.

What’s included (six artifacts):
- Design Tokens (`tokens.json`): central color, spacing, radius, and typography values.
- Component API Spec (`components.md`): props/state/events for key components using tables.
- Flows/States (`flows.mmd`): Mermaid state/flow diagram scaffold.
- Structural Skeleton (`skeleton.html`): low-fidelity, semantic HTML skeleton with ARIA hints.
- BDD Stories (`stories.feature`): Given-When-Then acceptance stories.
- Data Contracts (choose one):
  - `types.schema.json` (preferred; JSON Schema for technology neutrality)
  - `types.ts` (TypeScript interfaces)

Guidelines:
- Always reference tokens (no hard-coded hex colors, spacing, or fonts).
- Keep the skeleton semantic (landmarks, headings, ARIA attributes).
- Keep APIs testable and minimal; document default values explicitly.
- BDD must be verifiable and technology-agnostic.
- Prefer interfaces that map 1:1 to user actions.
 - Sizing guidance: consider mapping `px` to `rem` in implementations (e.g., body 16px → 1rem) to improve accessibility and zoom behavior.

Paths:
- Use the absolute paths printed by the setup script (`README_FILE`, `TOKENS_FILE`, `COMPONENTS_SPEC`, `FLOWS_FILE`, `HTML_SKELETON`, `BDD_FILE`, `TYPES_SCHEMA`/`TYPES_TS`). Do not reconstruct paths manually.

How it’s used:
- The `/speckit.ui` command copies these templates into `specs/<feature>/ui/` and prints absolute paths as JSON for downstream automation.
