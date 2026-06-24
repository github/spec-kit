# Changelog

## Unreleased

- Use CLI-compatible command names such as `/speckit.arch.scenario-generate` and `/speckit.arch.scenario-reverse`.
- Clarify command bootstrap boundaries, synthesis readiness checks, reverse repo-facts merge behavior, and source traceability expectations.
- Replace the two broad architecture commands with ten `.arch`-namespaced commands: forward and reverse generation for scenario, logical, process, development, and physical views.
- Keep synthesis refresh optional for per-view commands so each command owns one primary 4+1 artifact.
- Add reverse commands for repo-facts-first generation of architecture artifacts from ordinary historical repositories.
- Teach reverse commands to consume optional `.specify/memory/repository-first/` dependency matrices and module invocation specs as evidence for development-view governance.
- Add a schema-backed architecture artifact contract and require commands to validate JSON-compatible working models before Markdown rendering.
- Separate command and template responsibilities: commands now own extraction, classification, validation, merge policy, and write boundaries; templates only define Markdown layout.
- Add the `arch-governance` preset to wrap only the core `/speckit.plan` workflow with architecture SSOT grounding.
- Keep architecture generation commands independent from core workflow commands by removing downstream planning language from architecture artifacts.

## v1.0.0

- Publish the 4+1 architecture workflow as an external Spec Kit extension.
- Provide `/speckit.arch.generate` with Bash and PowerShell setup helpers.
- Include architecture synthesis, scenario, logical, process, development, and physical view templates.
