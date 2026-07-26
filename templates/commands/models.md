---
description: Detect the full model catalog available to the current AI agent, classify models by capability, and write the models.json file required by all other Spec Kit commands.
handoffs:
  - label: Create Specification
    agent: speckit.specify
    prompt: Define what you want to build now that models are configured...
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty). The user may pass overrides such as `--global` (write to the user-level file instead of the project), a manual model list, or explicit role assignments (e.g. "manager=X", "high=Y,Z").

## Goal

Produce a `models.json` file describing **every model available to the agent currently running this command**, classified by complexity tier. This file is a prerequisite: all other Spec Kit commands (except `__SPECKIT_COMMAND_CONSTITUTION__`) refuse to run without it.

- Project-level file: `.specify/models.json` (default; wins when both exist)
- Global file: `~/.specify/models.json` (written when the user passes `--global`; used as fallback by other commands)

## Execution Steps

### 1. Identify the running agent

Determine which AI agent/CLI is executing this command (e.g. Claude Code, GitHub Copilot, Codex CLI, Cursor, Gemini CLI, Qwen Code, opencode, Windsurf...). State it explicitly. If the agent runs behind a gateway/proxy (custom `ANTHROPIC_BASE_URL`, LiteLLM, OpenRouter, etc.), note that too — the catalog must reflect what THIS session can actually select, which is what the agent's own model picker shows.

### 2. Enumerate the FULL model catalog

Collect **every** selectable model, not just the well-known ones. There may be dozens (60+ behind some gateways). In priority order:

1. **Programmatic discovery** — if the agent exposes its model list programmatically and you have permission to query it (e.g. a gateway `${BASE_URL}/v1/models` endpoint when a custom base URL + model discovery is configured), fetch it and use the complete list.
2. **Agent knowledge** — if the agent knows its own selectable models (the set offered by its model picker / `--model` flag), enumerate them all, including variants (thinking / no-thinking, extended context like `[1m]`, fast modes, specialized models such as review- or plan-tuned ones).
3. **Ask the user** — if neither works, ask the user to paste the output of their agent's model picker (e.g. `/model` in Claude Code, the model dropdown in Copilot). Do NOT guess or invent models.

For each model record the attributes you can determine (omit unknowns rather than inventing them):

- `id` — the exact string usable to select the model (for subagents / `--model`)
- `thinking` — whether it is a reasoning/thinking variant
- `context` — context window if known (e.g. `200k`, `1M`)
- `tier` — your capability judgment: `max` | `high` | `medium` | `low`
- `note` — anything special (fast mode, review-specialized, extended context...)

### 3. Classify by complexity

Assign roles using these rules:

- **`manager`** — the single most capable model available (prefer thinking + largest context). The manager ONLY defines the main idea, specification and plan. It never implements tasks.
- **`by_complexity` map** — which model(s) implement tasks of each complexity level:
  - `high` — complex logic, architecture-heavy tasks, large refactors → most capable *non-manager-reserved* tier (thinking models).
  - `medium` — standard implementation, code edits, tests → balanced models.
  - `low` — docs, renames, config, mechanical chores → fastest/cheapest models.
  - Optional extra keys for specialized models (e.g. `review` for a review-tuned model).
- **`max`-tier models are used in very few cases**: reserve them for the `manager` role and, at most, exceptionally hard `high` tasks. Do NOT map the whole `high` tier to a `max` model — prefer the next tier down.
- Apply any explicit user overrides from the arguments; user choices always win.

### 4. Confirm with the user

Show a compact table: catalog size, manager, and the by_complexity mapping. Ask the user to confirm or adjust before writing. Skip confirmation only if the user passed explicit assignments covering manager and all three complexity levels.

### 5. Write models.json

Write to `.specify/models.json` (or `~/.specify/models.json` with `--global`), creating the directory if needed:

```json
{
  "version": 1,
  "agent": "<agent name>",
  "detected_at": "<YYYY-MM-DD>",
  "source": "gateway /v1/models | agent picker | user-provided",
  "catalog": [
    { "id": "<model id>", "thinking": true, "context": "200k", "tier": "high", "note": "" }
  ],
  "manager": "<model id>",
  "by_complexity": {
    "high": ["<model id>"],
    "medium": ["<model id>"],
    "low": ["<model id>"]
  }
}
```

Validation before writing:
- `manager` and every id in `by_complexity` MUST exist in `catalog`.
- `high`, `medium`, `low` MUST each have at least one model (they may repeat a model if the catalog is small — even a single-model catalog is valid: that model fills every role).

### 6. Completion report

Output:
- Path of the written file and whether it is project or global scope
- Catalog size (total models detected)
- Manager model and one-line rationale
- The by_complexity mapping
- Reminder: other Spec Kit commands will now use this file; re-run `__SPECKIT_COMMAND_MODELS__` whenever the available models change.

Context for model detection: {ARGS}
