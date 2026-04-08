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
  tools: none | read-only | full
  invocation: explicit | automatic
  visibility: user | model | both
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
| `tools` | `none` | `allowed-tools: ""` | — | — | — |
| `tools` | `full` | — | — | — | — |
| `invocation` | `explicit` | `disable-model-invocation: true` | — | — | — |
| `invocation` | `automatic` | `disable-model-invocation: false` | — | — | — |
| `visibility` | `user` | `user-invocable: true` | — | — | — |
| `visibility` | `model` | `user-invocable: false` | — | — | — |
| `visibility` | `both` | — | — | — | — |

Cells marked `—` mean "no concept, field omitted silently."

> **Note:** For Claude agent definitions (`execution: agent`), the `allowed-tools` key is automatically remapped to `tools` by spec-kit during deployment. The table above shows the `allowed-tools` form used in skill files (SKILL.md); the agent definition example below shows the resulting `tools` key after remapping.

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
agents:
  claude:
    paths: "src/**"
---
You are a codebase analysis specialist.
Analyze $ARGUMENTS and return structured domain findings.
```
