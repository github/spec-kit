# Docker Agent

Install [Docker Agent](https://docs.docker.com/ai/docker-agent/) before setup.
The integration key is `docker-agent`. Spec Kit detects either the standalone
`docker-agent` binary or the Docker CLI plugin (`docker agent`).

## Multi-Install Safety

This integration is not declared multi-install safe because its skills directory
is shared with other integrations. See the
[shared multi-install rules](cli.md#can-i-install-multiple-integrations-in-the-same-project).

## Setup

```bash
specify init my-project --integration docker-agent
```

For an existing Spec Kit project, use `specify integration install docker-agent`.
See [integration management](cli.md) for activation, upgrades, and removal.

## Installed Skills and Agent Configuration

Skills are installed as `.agents/skills/speckit-<command>/SKILL.md`, the same
directory used by Codex and Zed. In the selected agent YAML, enable local skills
with `skills: true` and provide filesystem read access. Invoke the skills in the
agent's chat as `/speckit-specify` or `/speckit-bug-assess` for the installed bug
extension.

The optional `--integration-options="--skills"` setup flag restates the
default; this integration always scaffolds skills. Spec Kit does not edit the
selected agent YAML or expose its hooks through Spec Kit's native-event system.

## Workflow Configuration

Workflow dispatch requires an agent configuration reference. Prefer the command
step's structured runtime fields:

```yaml
- id: specify
  type: command
  command: speckit.specify
  integration: docker-agent
  integration_args:
    - ./agent.yaml
  integration_options:
    agent: root
    safety: balanced
  input:
    args: "Describe the feature"
```

`integration_args` accepts at most one non-empty reference, which must not start
with `-`; Docker Agent validates the referenced local file or registry entry.
Supported `integration_options` are `agent` and `safety`; safety must be
`strict`, `balanced`, `restricted`, or `autonomous`. Set a model using the
step's top-level `model`, not `integration_options.model`. Unknown or malformed
runtime options fail explicitly.

The legacy `SPECKIT_INTEGRATION_DOCKER_AGENT_EXTRA_ARGS=./agent.yaml` environment
variable remains supported when no per-step reference is supplied. A per-step
reference overrides the entire legacy value, including any flags it contains.
Dispatch uses `run --exec`, adds requested `--json` and `--model` flags, and
places the prompt after `--` so prompt text cannot become CLI options.
See [per-step integration configuration](../reference/workflows.md#per-step-integration-configuration).
