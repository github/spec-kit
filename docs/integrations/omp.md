# Oh My Pi

Install [Oh My Pi](https://www.npmjs.com/package/@oh-my-pi/pi-coding-agent) before setup.
The integration key is `omp`.

## Multi-Install Safety

This integration is declared multi-install safe. See the
[shared multi-install rules](cli.md#can-i-install-multiple-integrations-in-the-same-project).

## Setup

```bash
specify init my-project --integration omp
```

For an existing Spec Kit project, use `specify integration install omp`.
See [integration management](cli.md) for activation, upgrades, and removal.

## Installed Commands

Markdown slash commands are installed under `.omp/commands/`.
Invoke them in the agent's chat using dotted notation, for example
`/speckit.specify` or `/speckit.bug.assess` for the installed bug extension.

## Workflow Dispatch

Workflow steps use `omp --print <prompt>`; `--print` enables one-shot mode
and the prompt is positional. The adapter forwards a configured `--model` and
uses `--mode json`, not `--output-format`, for structured output.
There are no integration-specific setup options; see Runtime Options below.

## Runtime Options

Command steps can pass per-step runtime configuration to `omp --print` (see
[Per-Step Integration Configuration](../reference/workflows.md#per-step-integration-configuration)):

| `integration_options` key | OMP flag     | Value                                                                    |
| ------------------------- | ------------ | ------------------------------------------------------------------------ |
| `profile`                 | `--profile`  | Isolated OMP profile name                                                |
| `thinking`                | `--thinking` | One of `off`, `minimal`, `low`, `medium`, `high`, `xhigh`, `max`, `auto` |
| `tools`                   | `--tools`    | Comma-separated list of tools to select (not an exclusive allowlist)     |

```yaml
- id: plan-with-omp
  type: command
  command: speckit.plan
  integration: omp
  integration_args:
    - "--no-session"
  integration_options:
    profile: work
    thinking: high
    tools: "read,bash"
  model: "gpt-5"
```

`tools` selects which tools OMP enables; it is not an exclusive allowlist or a
security boundary. OMP can still enable discovered custom and
extension-registered tools that are absent from the list, so `tools: read`
does not guarantee read-only access.

Option values must be non-empty strings; unknown keys and unsupported
`thinking` values fail before OMP is launched. Select the model with the step's
top-level `model` field: `integration_options.model` and a `--model` flag in
`integration_args` are both rejected.

`integration_args` is passed to OMP as raw flags, but OMP's parser lets some
tokens consume or reorder the generated options and prompt, so each value must
be one of:

- a known valueless flag such as `--no-session`, `--no-title` or `--yolo`; or
- a self-contained `--name=value` token such as `--system-prompt=...` or
  `--resume=<id>`.

Bare value-taking flags (`--system-prompt`, `--resume`), the `--` terminator
and `--=` forms (which OMP normalizes to `--`), positional text, `@file`
references, short flags, and `--help`/`--version`/`--print`/`--export`/`--alias`/`--mode` fail before OMP is
launched.

Arguments are passed to `omp --print` in this order, so later sources follow
earlier ones on the command line:

1. `SPECKIT_INTEGRATION_OMP_EXTRA_ARGS`
2. `integration_args`
3. `integration_options` flags
4. `--model` from the step's `model` field
5. `--mode json` (or `--mode text` when JSON output is off), then the prompt
