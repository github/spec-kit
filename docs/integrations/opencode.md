# opencode

Install [opencode](https://opencode.ai/) before setup.
The integration key is `opencode`.

## Multi-Install Safety

This integration is declared multi-install safe. See the
[shared multi-install rules](cli.md#can-i-install-multiple-integrations-in-the-same-project).

## Setup

```bash
specify init my-project --integration opencode
```

For an existing Spec Kit project, use `specify integration install opencode`.
See [integration management](cli.md) for activation, upgrades, and removal.

## Installed Commands

Markdown commands are installed under `.opencode/commands/`.
Invoke them in the agent's chat using dotted notation, for example
`/speckit.specify` or `/speckit.bug.assess` for the installed bug extension.

Legacy `.opencode/command/` installations remain a registration fallback when
the canonical directory does not exist.

## Runtime Events and Workflow Dispatch

Native events use `.opencode/plugin/speckit-events.ts` rather than a JSON hook
map; Spec Kit merges its plugin reference into `opencode.json`.
`--integration-options="--events false"` disables Spec Kit event handlers.
See [runtime events](cli.md#runtime-events).

Workflow steps use `opencode run`. Slash-prefixed prompts become
`--command <name>` with the remaining text as the message; other prompts are
passed as message text. The adapter forwards a configured model with `-m` and
requests `--format json` for structured output.

## Hidden Spec Kit Files

opencode 1.18.31 and 1.19.3 on darwin arm64 discover files with a glob tool that calls ripgrep without `--hidden`. In a temporary Spec Kit tree, `opencode debug rg files --glob '.specify/**/*'` (the same `Ripgrep.glob` call the glob tool makes, with no model involved) returned no paths. `**/*.md` on that same command returned only a visible `README.md`, and missed `.specify/memory/constitution.md`, `.specify/templates/spec-template.md`, `.specify/templates/plan-template.md`, and `.specify/scripts/bash/check-prerequisites.sh`. After the project root `.ignore` contained:

```text
!.specify/
!.specify/**
```

those patterns returned the constitution, both templates, and the script. A catch-all `**/*` already listed `.specify` files before the exceptions. `!.specify/**` alone still returned no `.specify/**/*` matches; the directory rule is what re-includes the hidden directory on this ripgrep path. Cloud-model fallback prompts and opencode 2.x were outside this check.

Opt in at install or upgrade:

```bash
specify init my-project --integration opencode --integration-options="--configure-ignore-file"
specify integration upgrade opencode --integration-options="--configure-ignore-file"
```

The flag appends whichever of those two rules is not already an exact line, placing them at the end of the root `.ignore`, followed by `.specify/**/local-config.yml`, `.specify/**/*-config.local.yml` and `.specify/workflows/runs/` unless those exact lines already come after the last `!` line. ripgrep ranks `.ignore` above `.gitignore`, so these lines keep per-machine extension overrides, which can hold credentials, out of ripgrep searches that pass no matching glob, at any depth, including the copies extension removal keeps under `.specify/extensions/.backup/`. The `.specify/workflows/runs/` line does the same for workflow run state (`state.json`, `inputs.json`, `log.jsonl`), which holds resolved inputs and captured command output. They do not hide those files from opencode's glob tool: ripgrep lets a `--glob` pattern that matches a file override every ignore file, so with ripgrep 15.2.0, `rg --files --glob '.specify/**/*'` and `rg --files --glob '**/*.yml'` list `local-config.yml` and `*-config.local.yml` files under `.specify` once the exceptions are in place, while `rg --files` with no glob omits them. Before the exceptions, `**/*` already listed them. Keep credentials out of files under `.specify` (use `SPECKIT_{EXTENSION}_*` environment variables instead) if opencode should not see their paths. A later exclusion of a `local-config.yml` or `*-config.local.yml` file, of `.specify/extensions/.backup/`, or of anything under `.specify/workflows/runs/`, is allowed. A later line that excludes `.specify`, a parent directory such as `.specify/memory`, or a file under it (including a template or script init has not created yet, such as `.specify/templates/plan-template.md`) is rejected; move `!.specify/` and `!.specify/**` below it and rerun. A root `.rgignore`, or a `.ignore` or `.rgignore` anywhere under `.specify` (such as `.specify/memory/.ignore`), that excludes one of those paths is rejected the same way, because ripgrep ranks `.rgignore` above `.ignore` and a nearer ignore file above the root one; remove that line and rerun. A `!` line in any of those files that re-includes a private config or workflow run state (such as `!.specify/**/local-config.yml` in a root `.rgignore`, or `!local-config.yml` in `.specify/extensions/jira/.ignore`) is rejected too, since it would override the appended exclusions; remove that line and rerun. Bundled scripts are checked only for the `--script` variant being installed, plus any script already under `.specify/scripts`. `specify integration install`, `switch` and `upgrade` run this check before they write shared templates or scripts, so a rejected `.ignore` leaves the project unchanged, including with `--force`. A child exception does not uncover a file while its parent directory stays excluded. Bytes already in the file stay as a prefix, including UTF-8 non-ASCII text, CRLF, and a missing final newline. Non-UTF-8 content is rejected before command files are written; convert the file to UTF-8 and rerun, because ripgrep stops at the first invalid byte. Default installs leave `.ignore` untouched. The file is recorded with partial ownership, so `specify integration uninstall` and `specify integration uninstall --force` both leave it in place, exceptions included. Upgrades still compare its hash: adding a user rule blocks a plain `specify integration upgrade opencode` until that change is resolved or `--force` is used, and `--force` also overwrites edited command files. Deleting the two lines is not a lasting opt-out while the stored flag remains, because the next upgrade restores them. Clear the stored flag with `specify integration upgrade opencode --integration-options=""` before removing the lines.

`.ignore` is a shared ignore file. opencode's glob tool sees the rules because it searches with ripgrep, and other tools that read `.ignore` (including fd) can start showing `.specify` as well. `specify integration upgrade opencode` replays the stored flag. Passing `--integration-options` replaces the whole stored set (repeat `--configure-ignore-file` alongside any other flags, such as `--events false`); `--integration-options=""` clears it.
