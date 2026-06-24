# Spec Kit Repository Governance

Generate the active Repository Governance Framework SSOT section.

## Output

- Active target file from Spec Kit integration metadata.
- Managed `SPECKIT GOVERNANCE` section.

## Scope

- Generate missing target governance file.
- Update existing target governance file.
- Distill detected repository areas into action rules.
- Capture repository facts as vertical SSOT evidence.
- Project agent platform adapter rules from Spec Kit integration metadata.
- Build a scenario capability index for repository-local skills and MCP-backed external tool evidence.
- Analyze repository areas to depth 2 only.
- Include hidden and cache directories in repository area governance.
- Enforce one primary responsibility per directory.
- Preserve user-authored content outside managed markers.
- Preserve managed markers verbatim.
- Keep `.specify/memory/repository-governance.md` internal.
- Review only the active target file.

## Install

```bash
specify extension add repository-governance --from https://github.com/bigsmartben/spec-kit-agent-governance/archive/refs/tags/v2.0.6.zip
```

Local development:

```bash
specify extension add --dev /path/to/spec-kit-agent-governance
```

## Run

```text
/speckit.repository-governance.refresh
```

Helper:

```bash
uv run python .specify/extensions/repository-governance/scripts/refresh_repository_governance.py
```

## Build

```bash
uv run python tools/build_repository_governance_zip.py
```

## Files

- `extension.yml`
- `commands/speckit.repository-governance.refresh.md`
- `scripts/refresh_repository_governance.py`
- `templates/repository-governance-template.md`

## SSOT Coverage

- Architecture SSOT evidence from source roots, extension source assets, route files, API contracts, and deployment directories.
- Engineering SSOT evidence from CI workflows, release/version files, command/template governance contracts, manifests, and task runners.
- Code Style SSOT evidence from formatter, lint, type-check, and test configuration.
- Directory Structure SSOT evidence from repository areas scanned to depth 2.
- Toolchain SSOT evidence from manifests, lockfiles, extension assets, build config, runtime config, Docker, compose, and task runner files.
- Agent Harness SSOT evidence from active agent context files, Spec Kit metadata, repository-local skills, and MCP config candidates.
- Repository fact evidence from README files, project docs, repository policy files, feature specs, source/test paths, and runtime/build configuration.
- Development command evidence from package scripts or Python/uv test conventions.

## Agent Adapter

- Repository Capability: abstract repository-local skill specs and MCP evidence into scenario-level capabilities.
- Spec Kit Agent Adapter: map the active integration to the context target and supported discovery behavior.
- Platform Projection: emit only rules the active agent context file can safely apply.

Repository-local `SKILL.md` files are indexed by declared name, description, trigger, and source path. MCP config files are reported as candidates and evidence only; active servers, resources, and tools must be enumerated from the agent platform runtime before use.

## Verify

```bash
uv run --locked python -m py_compile scripts/refresh_repository_governance.py tools/build_repository_governance_zip.py tests/test_governance_domains.py
uv run --locked pytest -q
```
