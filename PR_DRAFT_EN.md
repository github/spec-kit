feat(templates): add /speckit.ui blueprint, fail-fast scripts, JSON Schema, and smoke CI

Summary
- Add optional command /speckit.ui and companion templates/scripts to generate a framework-agnostic UI blueprint: design tokens, component API spec, state/flow diagram, semantic HTML skeleton, BDD stories, and data contracts.
- Fix release path rewrites for idempotency (avoid ".specify.specify/").
- Add cross-platform smoke CI to prevent silent empty files and validate packaged projects end-to-end.

Motivation
- Problem: Relying on natural language for UI/UX leaves too much interpretation for agents, causing drift in style, structure, interaction, and data contracts.
- Goals: Strengthen Spec-Driven Development by turning UI decisions into structured, machine-readable artifacts; keep technology-neutral; make results reproducible across agents and OSs.

Changes
- Scripts (fail-fast + dual-root resolution + full JSON output)
  - scripts/bash/setup-ui.sh
  - scripts/powershell/setup-ui.ps1
  - Behavior: resolve template root from ".specify/templates/ui" or "templates/ui"; if templates are missing, exit with a clear error; emit absolute paths as JSON keys: UI_DIR, TOKENS_FILE, COMPONENTS_SPEC, FLOWS_FILE, HTML_SKELETON, BDD_FILE, TYPES_SCHEMA, TYPES_TS, README_FILE.
- Packaging idempotency
  - .github/workflows/scripts/create-release-packages.sh: add guard rules to collapse repeated ".specify/" prefixes during path rewriting.
- Command template
  - templates/commands/ui.md: rely only on script JSON keys (no hard-coded paths). Data contracts default to JSON Schema (types.schema.json) with TypeScript (types.ts) as optional.
- UI templates (technology-neutral)
  - templates/ui/*: README.md, tokens.json (with breakpoints/zIndex/opacity/motion), components.md, flows.mmd, skeleton.html, stories.feature, types.ts, types.schema.json.
- Docs
  - README.md: add /speckit.ui row and a short "UI Command Usage" section (feature branch or SPECIFY_FEATURE; only use JSON keys; prefer JSON Schema).

Compatibility
- Non-breaking; CLI core untouched.

How to Verify
- Local (no init, Bash)
  - export SPECIFY_FEATURE=001-ui-blueprint
  - bash scripts/bash/setup-ui.sh | tee /tmp/ui.json
  - Example JSON (real output on my machine):
    {"UI_DIR":"/abs/specs/001-ui-blueprint/ui","TOKENS_FILE":"/abs/specs/001-ui-blueprint/ui/tokens.json","COMPONENTS_SPEC":"/abs/specs/001-ui-blueprint/ui/components.md","FLOWS_FILE":"/abs/specs/001-ui-blueprint/ui/flows.mmd","HTML_SKELETON":"/abs/specs/001-ui-blueprint/ui/skeleton.html","BDD_FILE":"/abs/specs/001-ui-blueprint/ui/stories.feature","TYPES_TS":"/abs/specs/001-ui-blueprint/ui/types.ts","TYPES_SCHEMA":"/abs/specs/001-ui-blueprint/ui/types.schema.json","README_FILE":"/abs/specs/001-ui-blueprint/ui/README.md"}
  - Validate keys exist and files are non-empty.
- Packaged project (Linux)
  - bash .github/workflows/scripts/create-release-packages.sh v0.0.5
  - unzip -p .genreleases/spec-kit-template-claude-sh-v0.0.5.zip .claude/commands/speckit.ui.md | grep -qv '.specify.specify/'
  - Extract and run packaged .specify/scripts/*/setup-ui.*; repeat JSON + file checks.
- CI
  - .github/workflows/ui-smoke.yml (Ubuntu + Windows): builds packages, checks for no ".specify.specify/", runs create-new-feature + setup-ui, validates JSON keys/files, jq-validates JSON, and runs shellcheck/PSScriptAnalyzer (warnings not blocking).

Risks & Rollback
- Minimal: small tweak to path rewriting and one new CI workflow. Revert this PR to roll back; alternatively keep UI templates/command while removing the idempotency tweak/CI if necessary.

Docs & Workflows
- README updated (commands list and usage notes).
- No changes to the core CLI or CHANGELOG required.

Performance & Security
- N/A for runtime; templates/scripts only.
- No credentials introduced; paths are local absolute paths for generation/editing.

AI Disclosure
- Authored by me with AI assistance for drafting. All scripts and templates were reviewed and verified locally and via packaging.

Review
- Suggested reviewer: @localden
- Focus areas: robustness of using only JSON keys in the command; fail-fast behavior; technology neutrality via JSON Schema preference.
