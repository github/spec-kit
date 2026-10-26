# Mistral Vibe

Install [Mistral Vibe](https://github.com/mistralai/mistral-vibe) before setup.
The integration key is `vibe`. The skills layout requires Mistral Vibe
v2.0.0 or newer.

## Multi-Install Safety

This integration is declared multi-install safe. See the
[shared multi-install rules](cli.md#can-i-install-multiple-integrations-in-the-same-project).

## Setup

```bash
specify init my-project --integration vibe
```

For an existing Spec Kit project, use `specify integration install vibe`.
See [integration management](cli.md) for activation, upgrades, and removal.

## Installed Skills

Skills are installed as `.vibe/skills/speckit-<command>/SKILL.md`.
Invoke them in the agent's chat, for example `/speckit-specify` or
`/speckit-bug-assess` for the installed bug extension.

Generated skills are both user- and model-invocable. The optional
`--integration-options="--skills"` flag restates the default.

## Runtime Events

Native events use `.vibe/hooks.toml`. Vibe supports only `pre_tool_use`,
`post_tool_use`, and `stop`, mapped to `pre_tool`, `post_tool`, and `post_agent`.
Session-start, session-end, and prompt-submit events are not emitted for Vibe;
unsupported handlers are skipped with a warning.
`--integration-options="--events false"` disables Spec Kit event handlers.
See [runtime events](cli.md#runtime-events).

Spec Kit refreshes and removes only the `[[hooks]]` entries it wrote, which
carry `speckit_marker = true`. Each entry ends after its last TOML line and the
blank lines right after it, so a comment that follows a Spec Kit entry stays in
the file. If removing Spec Kit's entries leaves only comments and blank lines,
Spec Kit deletes `.vibe/hooks.toml`.

## Workflow Dispatch

Workflow steps use `vibe -p <prompt>` and request `--output json` for structured
output. The adapter ignores the workflow `model` setting. Select the model with
Vibe's `active_model` configuration or `VIBE_ACTIVE_MODEL` instead.
