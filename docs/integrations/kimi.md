# Kimi Code

Install [Kimi Code](https://code.kimi.com/) before setup.
The integration key is `kimi`.

## Multi-Install Safety

This integration is not declared multi-install safe. See the
[shared multi-install rules](cli.md#can-i-install-multiple-integrations-in-the-same-project).

## Setup

```bash
specify init my-project --integration kimi
```

For an existing Spec Kit project, use `specify integration install kimi`.
See [integration management](cli.md) for activation, upgrades, and removal.

## Installed Skills

Skills are installed as `.kimi-code/skills/speckit-<command>/SKILL.md`.
Invoke them in Kimi's chat using the skill-colon prefix, for example
`/skill:speckit-specify` or `/skill:speckit-bug-assess` for the installed bug
extension.

The optional `--integration-options="--skills"` flag restates the default;
this integration always scaffolds skills.

## Legacy Migration

Pass `--integration-options="--migrate-legacy"` when upgrading an old
installation to move skills from `.kimi/skills/` to `.kimi-code/skills/`.
Migration also converts dotted skill names such as `speckit.xxx` to hyphenated
names such as `speckit-xxx`:

```bash
specify integration upgrade kimi --integration-options="--migrate-legacy"
```

Setup writes the new skills first. A legacy directory is moved only if its
new target does not exist. If a target already exists, the old directory is
removed only when both `SKILL.md` files are byte-identical and the legacy
directory has no additional files. Differing legacy content and extra user
files are retained for manual reconciliation. Symlinked legacy paths are
skipped; symlinked destination components are rejected.

## Legacy Cleanup on Uninstall

Normal manifest-tracked files use the shared modified-file protection. In
addition, teardown removes legacy `.kimi/skills/speckit-*` and `speckit.*`
directories identified by generated `metadata.author` and `metadata.source`.
That legacy cleanup does not compare recorded hashes or require `--force`;
back up edited legacy skills and additional files inside those directories
before uninstalling.

## Workflow Dispatch

Workflow steps use `kimi -p <prompt>` with `/skill:speckit-<command>`
invocations and forward a configured `--model`. Structured-output requests use
`--output-format stream-json` (JSONL events), not the unsupported `json` value.
