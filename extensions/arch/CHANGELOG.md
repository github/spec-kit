# Changelog

## Unreleased

- Add `/speckit.arch.reverse` for repo-facts-first reverse generation of architecture artifacts from ordinary historical repositories.
- Teach `/speckit.arch.reverse` to consume optional `.specify/memory/repository-first/` dependency matrices and module invocation specs as evidence for development-view governance.
- Add the `arch-governance` preset to wrap only the core `/speckit.plan` workflow with architecture SSOT grounding.
- Keep `/speckit.arch.generate` independent from core workflow commands by removing downstream planning language from architecture artifacts.

## v1.0.0

- Publish the 4+1 architecture workflow as an external Spec Kit extension.
- Provide `/speckit.arch.generate` with Bash and PowerShell setup helpers.
- Include architecture synthesis, scenario, logical, process, development, and physical view templates.
