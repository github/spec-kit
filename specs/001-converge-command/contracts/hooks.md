# Contract: Lifecycle Hooks

`/speckit.converge` registers two extension hook points, consistent with the hook pattern
used by `analyze` (`before_analyze` / `after_analyze`) and `implement`.

## Hook keys

| Key | When it runs | Purpose |
|-----|-------------|---------|
| `before_converge` | Before the assessment scan begins. | Extensions may load extra context or check preconditions. |
| `after_converge` | After the result is produced and any tasks are appended. | CI gates, PR generation, status updates, notifications. |

## Discovery and execution

- The command MUST check for `.specify/extensions.yml` and read entries under
  `hooks.before_converge` and `hooks.after_converge`.
- Parsing/format errors MUST be handled silently (skip hook checking, continue).
- Hooks with `enabled: false` are skipped; missing `enabled` defaults to enabled.
- The command MUST NOT evaluate non-empty `condition` expressions itself — those are left
  to the hook executor; hooks with a non-empty `condition` are skipped by the command.
- Mandatory hooks (`optional: false`) emit an `EXECUTE_COMMAND:` directive; optional hooks
  emit a suggestion block. This mirrors the exact pre/post-hook blocks in `analyze.md`.

## Outcome passed to `after_converge`

The `after_converge` hook MUST be able to distinguish the two outcomes (FR-015):

| Outcome | Meaning |
|---------|---------|
| `converged` | No remaining work; `tasks.md` unchanged. |
| `tasks_appended` | One or more Convergence tasks were appended. |

This lets an extension branch — e.g. generate a PR description on `converged`, or trigger
another implement pass on `tasks_appended`.

## Non-goals

- Hooks do not gate the append itself; converge appends as part of its normal run.
- Hooks are optional infrastructure — the command works fully with no
  `.specify/extensions.yml` present.
