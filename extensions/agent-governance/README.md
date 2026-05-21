# Spec Kit Agent Governance

Generate the active agent platform governance SSOT section.

## Output

- Active target file from Spec Kit integration metadata.
- Managed `SPECKIT GOVERNANCE` section.

## Scope

- Generate missing target governance file.
- Update existing target governance file.
- Distill detected repository areas into action rules.
- Analyze repository areas to depth 2 only.
- Include hidden and cache directories in repository area governance.
- Enforce one primary responsibility per directory.
- Preserve user-authored content outside managed markers.
- Preserve managed markers verbatim.
- Keep `.specify/memory/agent-governance.md` internal.
- Review only the active target file.

## Install

```bash
specify extension add agent-governance --from https://github.com/bigsmartben/spec-kit-agent-governance/archive/refs/tags/v1.2.0.zip
```

Local development:

```bash
specify extension add --dev /path/to/spec-kit-agent-governance
```

## Run

```text
/speckit.agent-governance.refresh
```

Helper:

```bash
uv run python .specify/extensions/agent-governance/scripts/refresh_agent_governance.py
```

## Files

- `extension.yml`
- `commands/speckit.agent-governance.refresh.md`
- `scripts/refresh_agent_governance.py`
- `templates/agent-governance-template.md`

## Verify

```bash
uv run pytest -q
```
