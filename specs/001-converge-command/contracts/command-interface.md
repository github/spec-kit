# Contract: Command Interface

Defines the user-facing invocation contract for `/speckit.converge`.

## Invocation

```
/speckit.converge [feature-name]
```

- `feature-name` (optional positional argument): the feature to assess. When omitted, the
  command resolves the active feature via the standard mechanism
  (`SPECIFY_FEATURE_DIRECTORY` → `.specify/feature.json` → branch-prefix fallback), the
  same resolution used by `analyze` and `implement`.
- Invocation convention follows the agent's separator: `/speckit.converge` (dot agents) or
  `/speckit-converge` (skills/hyphen agents). This is produced automatically from the
  `__SPECKIT_COMMAND_CONVERGE__` token — no per-agent code required.

## Frontmatter scripts contract

The command template MUST declare:

```yaml
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
```

- The script MUST be run once; its JSON output provides `FEATURE_DIR` and `AVAILABLE_DOCS`.
- If `plan.md` or `tasks.md` is missing, the script exits non-zero with a message naming
  the prerequisite command; converge MUST surface that and stop (FR-013).

## Preconditions

| Condition | Behavior |
|-----------|----------|
| `plan.md` missing | Stop with message: run the plan command first. |
| `tasks.md` missing | Stop with message: run the tasks command first. |
| Constitution is unfilled template | Proceed; skip constitution checks gracefully. |
| Little/no implementation yet | Treat entire specified scope as remaining work (edge case). |

## Outputs

| Output | Form |
|--------|------|
| In-session findings summary | Human-readable table/list, severity-graded (not written to a file). |
| Appended Convergence tasks | New phase at the bottom of `tasks.md` (see `tasks-output.md`). |
| Next-step suggestion | `converged` → proceed to review/PR; `tasks_appended` → run implement. |

## Guarantees (read-only boundaries)

- MUST NOT modify `spec.md` or `plan.md`.
- MUST NOT modify or delete existing tasks.
- MUST NOT modify application code.
- The ONLY write is appending to `tasks.md`.
