# Changelog

## Unreleased

## v1.2.2 - 2026-06-25

- Use CLI-compatible command names such as `/speckit.arch.scenario-generate` and `/speckit.arch.scenario-reverse`.
- Add `/speckit.arch.full-generate` for one-command forward generation of all 4+1 views and synthesis.
- Add `/speckit.arch.full-reverse` for one-command reverse generation of repo facts, all 4+1 views, and synthesis.
- Clarify command bootstrap boundaries, synthesis readiness checks, reverse repo-facts merge behavior, and source traceability expectations.
- Replace the two broad architecture commands with ten `.arch`-namespaced commands: forward and reverse generation for scenario, logical, process, development, and physical views.
- Keep synthesis refresh optional for per-view commands so each command owns one primary 4+1 artifact.
- Add reverse commands for repo-facts-first generation of architecture artifacts from ordinary historical repositories.
- Teach reverse commands to consume optional `.specify/memory/repository-first/` evidence, with dependency matrix interpretation owned by development-view governance rather than treated as an independent view or equal input to every 4+1 view.
- Require the Development View commands to produce a `Dependency Matrix` section as part of the development-view artifact.
- Add a schema-backed architecture artifact contract for JSON-compatible working models before Markdown rendering.
- Add bash and PowerShell readiness validators that emit `ready_gate` and stable architecture blocker codes for synthesis refresh decisions.
- Separate command, schema, validator, and template responsibilities: commands now own extraction, classification, merge policy, and write routing; schemas own working-model structure; validators own rendered-artifact readiness and blocker codes; templates only define Markdown layout.
- Keep this repository scoped to extension-owned architecture commands, templates, schemas, scripts, and contract tests.

## v1.0.0

- Publish the 4+1 architecture workflow as an external Spec Kit extension.
- Provide `/speckit.arch.generate` with Bash and PowerShell setup helpers.
- Include architecture synthesis, scenario, logical, process, development, and physical view templates.
