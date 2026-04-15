# Extension Behavior & Deployment — RFC Addendum

## Overview

Extension commands can declare two new frontmatter sections:

1. **`behavior:`** — agent-neutral intent vocabulary
2. **`agents:`** — per-agent escape hatch for fields with no neutral equivalent

Deployment target is fully derived from `behavior.execution` — no separate manifest field is needed.

---

## `behavior:` Vocabulary

```yaml
behavior:
  execution: command | isolated | agent
  capability: fast | balanced | strong
  effort: low | medium | high | max
  tools: none | read-only | write | full | <custom>
  invocation: explicit | automatic
  visibility: user | model | both
  color: red | blue | green | yellow | purple | orange | pink | cyan
```

### Per-agent translation

| behavior field | value | Claude | Copilot | Codex | Others |
|---|---|---|---|---|---|
| `execution` | `isolated` | `context: fork` | `mode: agent` | — | — |
| `execution` | `agent` | routing only (see Deployment section) | `mode: agent` | — | — |
| `capability` | `fast` | `model: claude-haiku-4-5-20251001` | — | — | — |
| `capability` | `balanced` | `model: claude-sonnet-4-6` | — | — | — |
| `capability` | `strong` | `model: claude-opus-4-6` | — | — | — |
| `effort` | any | `effort: {value}` | — | `effort: {value}` | — |
| `tools` | `read-only` | `allowed-tools: Read Grep Glob` | `tools: [read_file, list_directory, search_files]` | — | — |
| `tools` | `write` | `allowed-tools: Read Write Edit Grep Glob` | — | — | — |
| `tools` | `none` | `allowed-tools: ""` | — | — | — |
| `tools` | `full` | — (no restriction, all tools available) | — | — | — |
| `tools` | `<custom string>` | `allowed-tools: <value>` (literal passthrough) | — | — | — |
| `tools` | `<yaml list>` | `allowed-tools: <space-joined items>` | — | — | — |
| `invocation` | `explicit` | `disable-model-invocation: true` | — | — | — |
| `invocation` | `automatic` | `disable-model-invocation: false` | — | — | — |
| `visibility` | `user` | `user-invocable: true` | — | — | — |
| `visibility` | `model` | `user-invocable: false` | — | — | — |
| `visibility` | `both` | — | — | — | — |
| `color` | any valid value | `color: {value}` | — | — | — |

Cells marked `—` mean "no concept, field omitted silently."

> **Note:** For Claude agent definitions (`execution: agent`), the `allowed-tools` key is automatically remapped to `tools` by spec-kit during deployment. The table above shows the `allowed-tools` form used in skill files (SKILL.md); the agent definition example below shows the resulting `tools` key after remapping.

### `tools` presets and custom values (Claude)

The `tools` field accepts four named presets or a custom value:

| value | `allowed-tools` written | use case |
|---|---|---|
| `none` | `""` (empty — no tools) | pure reasoning, no file access |
| `read-only` | `Read Grep Glob` | read/search, no writes |
| `write` | `Read Write Edit Grep Glob` | file reads + writes, no shell |
| `full` | _(key omitted)_ | all tools including Bash |

For anything outside these presets, pass a **custom string** or **YAML list** — it is written verbatim as `allowed-tools`:

```yaml
# Custom string (space-separated)
behavior:
  tools: "Read Write Bash"

# YAML list (joined with spaces)
behavior:
  tools:
    - Read
    - Write
    - Bash
```

> Custom values bypass preset lookup entirely and are not validated. Use named presets whenever possible.

### `color` (Claude Code only)

Controls the UI color of the agent entry in the Claude Code task list and transcript. Accepted values: `red`, `blue`, `green`, `yellow`, `purple`, `orange`, `pink`, `cyan`. The value is passed through verbatim to the agent definition frontmatter — no translation occurs. Other agents ignore this field.

---

## `agents:` Escape Hatch

For fields with no neutral equivalent, declare them per-agent:

```yaml
agents:
  claude:
    paths: "src/**"
    argument-hint: "Path to the codebase"
  copilot:
    someCustomKey: someValue
```

Agent-specific overrides win over `behavior:` translations.

---

## Deployment Routing from `behavior.execution`

Deployment target is fully derived from `behavior.execution` in the command file — no separate manifest field needed.

| `behavior.execution` | Claude | Copilot | Codex | Others |
|---|---|---|---|---|
| `command` (default) | `.claude/skills/{name}/SKILL.md` | `.github/agents/{name}.agent.md` | `.agents/skills/{name}/SKILL.md` | per-agent format |
| `isolated` | `.claude/skills/{name}/SKILL.md` + `context: fork` | `.github/agents/{name}.agent.md` + `mode: agent` | per-agent format | per-agent format |
| `agent` | `.claude/agents/{name}.md` | `.github/agents/{name}.agent.md` + `mode: agent` + `tools:` | not supported | not supported |

### Agent definition format (Claude, `execution: agent`)

Spec-kit writes a Claude agent definition file at `.claude/agents/{name}.md`.
The body becomes the **system prompt**. Frontmatter is minimal — no
`user-invocable`, `disable-model-invocation`, `context`, or `metadata` keys.

```markdown
---
name: speckit-revenge-analyzer
description: Codebase analyzer subagent
model: claude-opus-4-6
tools: Read Grep Glob
---
You are a codebase analysis specialist...
```

### Deferred: `execution: isolated` as agent definition

It is theoretically possible to want a command that runs in an isolated
context (`context: fork`) AND is deployed as a named agent definition
(`.claude/agents/`). These two concerns are orthogonal — isolation is a
runtime concern, agent definition is a deployment concern.

This combination is **not supported** in this implementation. `execution:
isolated` always deploys as a skill file. Decoupling runtime context from
deployment target is deferred until a concrete use case requires it.

---

## Full Example: Orchestrator + Reusable Subagent

**`extension.yml`** (no manifest `type` field — deployment derived from command frontmatter):
```yaml
provides:
  commands:
    - name: speckit.revenge.extract
      file: commands/extract.md

    - name: speckit.revenge.analyzer
      file: commands/analyzer.md
```

**`commands/extract.md`** (orchestrator skill — no `execution:` → deploys to skills):
```markdown
---
description: Run the extraction pipeline
behavior:
  invocation: automatic
agents:
  claude:
    argument-hint: "Path to codebase (optional)"
---
Orchestrate extraction for $ARGUMENTS...
```

**`commands/analyzer.md`** (reusable subagent — `execution: agent` → deploys to `.claude/agents/`):
```markdown
---
description: Analyze codebase structure and extract domain information
behavior:
  execution: agent
  capability: strong
  tools: read-only
  color: green
agents:
  claude:
    paths: "src/**"
---
You are a codebase analysis specialist.
Analyze $ARGUMENTS and return structured domain findings.
```

The deployed `.claude/agents/speckit-revenge-analyzer.md` will contain:

```markdown
---
name: speckit-revenge-analyzer
description: Analyze codebase structure and extract domain information
model: claude-opus-4-6
tools: Read Grep Glob
color: green
---
You are a codebase analysis specialist.
...
```

### `tools: write` example

Use `write` when an agent needs to create or modify files but does not need shell access (Bash):

```yaml
behavior:
  execution: agent
  capability: strong
  tools: write       # Read Write Edit Grep Glob — no Bash
  color: yellow
```

### `tools: full` example

Use `full` when an agent needs unrestricted access including Bash (running tests, git commands, CLI tools):

```yaml
behavior:
  execution: agent
  capability: strong
  tools: full        # all tools; no allowed-tools key injected
  color: red
```
