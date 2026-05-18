---
description: Sync agent context files (AGENTS.md, CLAUDE.md, .github/copilot-instructions.md, GEMINI.md) from the installed agent-context.md template. Shows a diff for review before writing, keeping all agent context files in lockstep with the preset.
---

## User Input

```text
$ARGUMENTS
```

Optional flags:
- `--dry-run` — show diff but do not write any files
- `--force` — overwrite without prompting when conflicts are detected
- `--targets <list>` — comma-separated subset of targets to sync (e.g. `CLAUDE.md,AGENTS.md`)
- `--template <path>` — path to an alternate agent-context template (default: `.specify/presets/nextjs/templates/agent-context.md`)

## Pre-Execution Checks

Check for `.specify/extensions.yml`. Look for hooks under `hooks.before_docs_sync`. Apply standard hook-processing.

## Outline

Agent context files drift from the canonical template as the template evolves but the files are not updated. This command brings them back in sync, with a diff for review to ensure no custom additions are lost.

### 1. Locate the template

Read the agent context template from:
1. `--template <path>` if provided
2. `.specify/presets/nextjs/templates/agent-context.md` (installed preset location)
3. `presets/nextjs/templates/agent-context.md` (monorepo development fallback)

If none of these paths exist, abort with a clear error message.

### 2. Identify sync targets

Resolve which files to sync. Default target list:

| File | Agent | Notes |
|---|---|---|
| `AGENTS.md` | Generic / Codex | Present if project uses generic agents |
| `CLAUDE.md` | Claude Code | Present if `claude` is detected in toolchain |
| `.github/copilot-instructions.md` | GitHub Copilot | Present if `.github/` exists |
| `GEMINI.md` | Gemini CLI | Present if project uses Gemini |

Check for each file's existence. For each target file:
- **Exists** → diff against template, report change size
- **Does not exist** → mark as "new" (will be created)
- **Excluded by `--targets`** → skip silently

If `--targets` is provided, only process the listed files.

### 3. Compute diffs

For each existing target, compute a line-level diff between:
- **Current content** (what is in the file now)
- **Template content** (the canonical `agent-context.md`)

Classify each change as:
- `IDENTICAL` — no diff; skip this file (report it as up-to-date)
- `ADDITIVE` — template has new lines not in the current file (safe to apply)
- `CONFLICT` — current file has lines not in the template (manual additions that would be overwritten)
- `NEW` — file does not exist; template content will be written verbatim

### 4. Present the sync plan

Before writing anything, output the plan:

```
## Docs Sync Plan

**Template**: `.specify/presets/nextjs/templates/agent-context.md`
**Targets checked**: <N>

| File | Status | Changes |
|---|---|---|
| `CLAUDE.md` | CONFLICT | +12 lines in template, -3 custom lines in current file |
| `AGENTS.md` | ADDITIVE | +12 lines in template, current file unchanged |
| `.github/copilot-instructions.md` | IDENTICAL | up to date |
| `GEMINI.md` | NEW | will be created |

### Diffs

#### CLAUDE.md (CONFLICT — review carefully)

```diff
- <line from current file that will be removed>
+ <line from template that will be added>
```

*Custom lines in the current file that will be overwritten*:
- Line 42: `<!-- Custom: project-specific rule -->`
- ...

#### AGENTS.md (ADDITIVE)

```diff
+ <new lines from the updated template>
```

#### GEMINI.md (NEW — full content from template)

*(content preview truncated to 20 lines)*
...
```

If `--dry-run` is set, stop here and print: `Dry run complete. No files were written.`

### 5. Prompt for confirmation (unless `--force`)

If any file has `CONFLICT` status:

```
CONFLICT detected in <N> file(s). Custom content in those files will be overwritten.

Options:
- Proceed: overwrite all files (custom lines will be lost)
- Selective: list which files to sync, skip the rest
- Abort: do not write any files

How would you like to proceed?
```

If the user chooses "Selective", ask which files to include.
If `--force` is set, proceed without prompting.
If all files are `IDENTICAL`, print: `All agent context files are up to date. Nothing to write.` and exit.

### 6. Write the files

For each file approved for sync:
- Write the full template content verbatim.
- Preserve the file's trailing newline behavior (add one if template ends without one, match if it has one).
- Do not add any machine-generated header (e.g. `<!-- auto-generated -->`); the template is the canonical source and should look like it was written by a human.

### 7. Print the result

```
## Docs Sync Complete

**Files written**:
- `CLAUDE.md` — overwritten (was CONFLICT; <N> custom lines lost — consider adding them back manually or opening a PR to include them in the template)
- `AGENTS.md` — updated (ADDITIVE; <N> new lines from template)
- `GEMINI.md` — created (NEW)

**Files skipped**:
- `.github/copilot-instructions.md` — IDENTICAL (already up to date)

**Next steps**:
- Review the written files: `git diff CLAUDE.md AGENTS.md GEMINI.md`
- If custom lines were lost, re-add them below a `<!-- Project-specific additions -->` comment to make future syncs easier to review
- Commit: `git commit -m "chore: sync agent context files from agent-context.md template"`
- If the template itself needs updating, edit `.specify/presets/nextjs/templates/agent-context.md` and re-run `/speckit.docs.sync`
```

### 8. Detect outdated constitution reference (advisory)

After syncing, check whether `.specify/memory/constitution.md` exists. If it does not:

```
Advisory: No constitution found at `.specify/memory/constitution.md`.
Agent context files reference the constitution but it has not been generated yet.
Run `/speckit.constitution.scan` to produce the constitution from the repository inventory.
```

If it does exist, check the `ratification_date` field (look for `**Ratification Date**:` or `ratification_date:` in the YAML front-matter). If it is older than 90 days from today, print:

```
Advisory: The constitution was last ratified <N> days ago (<date>).
Consider re-running `/speckit.constitution.scan` to refresh it with the current repository state.
```

## Post-Execution Hooks

Check `.specify/extensions.yml` for `hooks.after_docs_sync`. Apply standard hook-processing.
