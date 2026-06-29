# Spec Kit Repository Governance

Generate project-governance projections for the active Spec Kit agent platform target.

## Output

- Active agent platform target from safe `context_file` override or Spec Kit integration metadata.
- Generated `PROJECT GOVERNANCE` projection file.

## Scope

- Generate the resolved active agent platform target when missing.
- Update existing active target project-governance projections.
- Distill detected repository areas into action rules.
- Capture repository facts as vertical SSOT evidence and routing input.
- Structure generated instructions with Copilot-like repository-wide, path-scope, and agent-harness layers.
- Project agent platform adapter rules from Spec Kit integration metadata.
- Build a scenario capability index for repository-local skills and MCP-backed external tool evidence.
- Analyze repository areas to depth 2 only.
- Include hidden and cache directories in repository area governance.
- Enforce one primary responsibility per directory.
- Overwrite the active agent platform target on generation.
- Do not generate Copilot `.github/instructions/*.instructions.md` companion files.
- Generate repository evidence from the current repository state on every run.
- Review only the active agent platform target.
- Remove legacy managed sections only from non-active context files enumerated by `CONTEXT_FILES`.

## Install

```bash
specify extension add repository-governance --from https://github.com/bigsmartben/spec-kit-agent-governance/archive/refs/tags/v3.0.1.zip
```

Local development:

```bash
specify extension add --dev /path/to/spec-kit-agent-governance
```

## Run

```text
/speckit.repository-governance.generate
```

Helper:

```bash
uv run python .specify/extensions/repository-governance/scripts/generate_repository_governance.py
```

## Build

```bash
uv run python tools/build_repository_governance_zip.py
```

## Files

- `extension.yml`
- `commands/speckit.repository-governance.generate.md`
- `scripts/generate_repository_governance.py`
- `templates/repository-governance-template.md`

## Vertical SSOT Coverage

- Architecture SSOT evidence from source roots, extension source assets, route files, API contracts, and deployment directories.
- Engineering SSOT evidence from CI workflows, release/version files, command/template governance contracts, manifests, lockfiles, task runners, extension assets, build config, runtime config, Docker, and compose files.
- Code Style SSOT evidence from formatter, lint, type-check, and test configuration.
- Directory Structure SSOT evidence from repository areas scanned to depth 2.
- Agent Harness SSOT evidence from active agent context files, Spec Kit metadata, repository-local skills, and MCP config candidates.

## Instruction Layers

- Repository-wide instructions summarize authority, active-target scope, write boundaries, validation commands, and handoff expectations.
- SSOT routing maps task types and path families to Architecture, Engineering, Code Style, Directory Structure, and Agent Harness SSOT entries.
- Path and task scope rules keep generated guidance deterministic without expanding the write surface.
- Agent harness instructions cover adapter behavior, repository-local skills, MCP discovery, external tools, permissions, and failure handling.
- Copilot's instruction model is a structural reference only; this extension still emits one active target file.

## Evidence Coverage

- Repository fact evidence from README files, project docs, repository policy files, feature specs, source/test paths, and runtime/build configuration.
- Development command evidence from package scripts or Python/uv test conventions.

## Agent Adapter

- Repository Capability: abstract repository-local skill specs and MCP evidence into scenario-level capabilities.
- Spec Kit Agent Adapter: map the active integration to the active agent platform target and supported discovery behavior.
- Platform Projection: emit only rules the active agent platform target can safely apply.

Repository-local `SKILL.md` files are indexed by declared name, description, trigger, and source path. MCP config files are reported as candidates and evidence only; active servers, resources, and tools must be enumerated from the agent platform runtime before use.

## Verify

```bash
uv run --locked python -m py_compile scripts/generate_repository_governance.py tools/build_repository_governance_zip.py tests/test_governance_domains.py
uv run --locked pytest -q
```
