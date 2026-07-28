---
description: Detect the agent hosting this conversation, discover its actually configured models from first-party runtime evidence, classify them into 5 complexity levels using live OpenRouter data (benchmark, speed, cost, context), and write models.json.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty). Supported overrides include `--global`, pasted model-picker output, a manual model list, and explicit assignments such as `manager=X`, `n5=X,Y`, `n4=A,B`, `n3=C,D`, `n2=E,F`, or `n1=G,H`.

## Goal

Create a `models.json` containing only models that the agent hosting **this conversation** can select now, plus an execution route for each assigned model. Classify every discovered model into one of **5 complexity levels** using live OpenRouter data (never a static table — recalculate every run), and assign an ordered candidate chain to every level: the first model is the primary executor and the remaining models are alternatives used when a model is unavailable, rate-limited, out of usage/tokens, or exceeds its context limit.

- Project file: `.specify/models.json` (default and highest precedence)
- User file: `~/.specify/models.json` (with `--global`; fallback for other commands)

Every other Spec Kit command except `__SPECKIT_COMMAND_CONSTITUTION__` requires this file.

## Execution Steps

### 1. Establish where the conversation is running

Determine these facts before discovering any model:

1. **Project root**: resolve the current working directory and locate the nearest project root containing `.specify/` or the repository root where `.specify/` will be created.
2. **Runtime agent**: identify the exact application or CLI hosting this conversation from runtime/system context, available tools, process/environment evidence, or explicit user input.
3. **Installed Spec Kit integration**: if `<project-root>/.specify/integration.json` exists, read its active integration. Record it separately from the runtime agent. It indicates where Spec Kit commands were installed; it does **not** prove which agent is hosting this conversation.
4. **Provider route**: identify any configured gateway, proxy, provider, or custom base URL used by this session without exposing credentials.

If runtime evidence conflicts with `.specify/integration.json`, use the **runtime agent** for model discovery and report the mismatch. If the runtime agent cannot be identified reliably, STOP and ask the user which agent/CLI is hosting the conversation. Do not infer it from command-file syntax, folder names, or the installed integration alone.

### 2. Discover configured models from the runtime agent

Do **not** derive a catalog from the agent name, provider name, executable name, public vendor documentation, memory, or commonly available models. A model is eligible only when first-party evidence shows that this runtime can select it.

Use the strongest available discovery mechanism in this order:

1. Invoke the runtime agent's native model-list command, API, or picker through the tools exposed by the host and capture the result.
2. Query the configured gateway's model endpoint only when runtime configuration proves that this session uses that gateway. Treat the returned identifiers as selectable only if the agent supports gateway discovery.
3. Observe the runtime agent's actual model picker. If it is an interactive chat command or UI that cannot be invoked by the agent itself, ask the user to open it and paste or share the complete output.
4. Accept an explicit model list supplied by the user and record the source as `user_provided`.

Rules:

- A help page showing only a `--model` option is not a model catalog.
- Do not execute an interactive slash command as a shell command.
- Do not substitute a vendor's public `/v1/models` response for the agent's configured picker.
- Preserve exact selectable IDs, including provider prefixes and variants.
- Capture the discovery command/mechanism and enough non-secret evidence to explain the result.
- If no trustworthy list can be obtained, STOP and request the picker output. Never create `models.json` from guesses.

For each discovered model, record only supported facts:

- `id`: exact selectable model identifier (required)
- `provider`: provider or gateway namespace when shown
- `context`: context window when shown
- `reasoning`: reasoning/thinking capability when shown
- `availability`: relevant usage, quota, or access restriction when shown
- `note`: selectable variant or specialization shown by the source
- `tier`: derived level (`5`, `4`, `3`, `2`, or `1`) assigned in the next step; this is an assessment, not discovery evidence

### 3. Classify models into 5 levels with OpenRouter data

Classify every discovered model into 5 complexity levels using **live data from OpenRouter**. Never use a static table, never rank from model names alone — recalculate every run. This classification is CLI-agnostic; the incorporation into each CLI happens in step 4.

**3.1 Fetch model data (3 lightweight JSON calls, no browser, no scraping):**

| Data | Endpoint | Field used |
|---|---|---|
| Price + context | `https://openrouter.ai/api/v1/models` | `pricing.prompt` / `pricing.completion`, `context_length` |
| Intelligence | `https://openrouter.ai/api/frontend/v1/rankings/benchmarks` | `data.aaData.percentilesBySlug[slug].intelligence` (Artificial Analysis percentile 0-100) |
| Speed | `https://openrouter.ai/api/frontend/v1/rankings/performance` | `p50_throughput` (tok/s), `p50_latency` (ms) |

If an endpoint is unreachable, fall back to model metadata from discovery plus explicit user guidance, and record that data-driven classification was degraded.

**3.2 Match each discovered model to its OpenRouter slug:**

- Normalize: strip provider prefixes, variant suffixes (`-review`, `-highspeed`, `-thinking`, `-free`), date suffixes (`-20251001`), and leading `~`.
- Variants inherit the base model's data.
- Keep a small manual alias table for slugs that differ (e.g. `kimi-latest` → the current flagship slug it points to).
- Do not rank opaque or unfamiliar model IDs from their names alone. If a model has no OpenRouter match and no benchmark, apply the unmeasured rule below; ask the user when evidence cannot support any classification.

**3.3 Compute per model:**

- `intel`: intelligence percentile (0-100). It is **relative** — it drops as newer better models appear.
- `speed`: best `p50_throughput` across providers.
- `price blend`: `0.75 × input price + 0.25 × output price` (agentic usage is input-dominated).
- `cost-benefit`: `intel ÷ max(blend, 0.05)`.

**3.4 Assign the level by benchmark** (capability defines the ceiling of what the model can solve):

- **N5 (critical)**: intel ≥ 94 — full architecture, irreversible decisions, security. Used rarely.
- **N4 (complex)**: intel 85–93 — design decisions, large features, non-obvious debugging.
- **N3 (moderate)**: intel 60–84 — the workhorse; most real work lands here.
- **N2 (simple)**: intel 40–59 — single-file changes, obvious bugs, mechanical work.
- **N1 (trivial)**: intel < 40 — direct questions, lookups, formatting.
- **Unmeasured models** (no benchmark): price ≤ $0.30/M → N1; fast (>100 tok/s) and < $1/M → N2; otherwise N3.

**3.5 Order each level's list:**

- Order candidates within a level by cost-benefit, preferring ~1M context. Beware high cost-benefit with low benchmark: cheap does not help if the model cannot solve the task.
- Prefer alternatives with an independent provider/quota route when capability is adequate, so exhausting one model's allowance does not exhaust every fallback.
- Keep each fallback capable of completing that level. Never add a weak model merely to make the list longer.

Assignment rules:

- `manager`: the communicator/orchestrator model — the single entry point. It receives every command, classifies each task/step's level (1-5) itself, and delegates. It NEVER implements; classifying is part of its communicator role. Choose the strongest model for specification, planning, decomposition, and orchestration.
- Each level maps to an **ordered non-empty list**: primary first, then alternatives in fallback order.
- Reserve the manager from implementation when enough other models exist. Small catalogs may reuse the same model across roles and levels.
- Apply explicit user assignments after validating that every assigned ID exists in the discovered catalog.

Before writing, show the detected environment, discovery evidence, catalog, proposed manager, and ordered candidates for each level (N1-N5), including the benchmark percentile, blended price, and cost-benefit behind each classification. Ask the user to confirm or adjust the assignments. Skip this confirmation only when the user already supplied complete explicit assignments for `manager`, `n5`, `n4`, `n3`, `n2`, and `n1`.

### 4. Resolve an executor for every assigned model

Discover execution capabilities from the **runtime**, not from the product name. Inspect the task/subagent tool schemas and agent configuration already loaded by the host. Never assume that a model picker implies programmatic per-task model selection.

All task execution must remain inside the agent or CLI hosting this conversation. A model connected to OpenCode must run through OpenCode; a model connected to Claude Code must run through Claude Code; and so on. Never launch another agent CLI, and never start a second process of the current CLI, to execute a task or fallback. Native model commands may be used only to inspect the current host's configured catalog.

Each assigned model must resolve to one of these executor modes:

- `native_subagent`: the runtime can invoke a named subagent whose loaded configuration pins the exact model.
- `current_session`: the current conversation is already running that exact model, but cannot select it for a separate worker.
- `manual`: no programmatic route exists; the user must switch/select the model and continue manually.

When the runtime supports named agents whose configuration pins an exact model (agent definition files, JSON agent entries, or an equivalent mechanism), you MUST propose creating them for every assigned model that lacks a matching agent. `manual` is allowed only when no such configuration mechanism exists or the user explicitly declines creation. Marking every executor `manual` while a pinned-agent mechanism exists violates this contract: it silently disables autonomous dispatch and the ordered fallback chain.

Use the following runtime-specific procedure. These are verification branches, not claims that every installed version supports the feature:

#### OpenCode

1. Read the merged OpenCode configuration and inspect project/global agents. A subagent is selectable only when its definition has `mode: subagent` (or `all`) and `model: <exact provider/model-id>`.
2. Inspect the task tool schema exposed to this conversation. If it accepts only `subagent_type` and not `model`, select a configured agent name; do not claim direct model selection.
3. For each candidate without a matching agent, you MUST propose a stable agent such as `speckit-n3-1` or `speckit-n5-1` in `.opencode/agents/<name>.md`, with `mode: subagent`, the exact `model`, a concise description, and only the permissions needed for implementation. Do not skip this step and record `manual` instead; `manual` is only acceptable here when the user explicitly declines agent creation.
4. Ask before creating or updating OpenCode agent files. Preserve unrelated configuration. OpenCode loads agent files at startup, so tell the user to restart for the new agents to become dispatchable. Do not gate dispatch on this: if a worker agent is not loaded yet when invoked, the fallback chain simply moves to the next candidate.

#### Claude Code

1. Inspect the runtime task/subagent schema and configured agents. Use `native_subagent` only if the task call can select a named agent that pins the exact model or explicitly accepts the exact model.
2. Do not start another `claude` process to execute work. If the loaded task interface cannot select the model, use `current_session` for the active model and `manual` for alternatives.
3. Do not treat `/model` as a shell command. It may be used interactively to inspect or switch the current host only.

#### Codex CLI

1. Inspect the task/subagent capabilities exposed inside the current Codex session and any native agent configuration already loaded by it.
2. Do not use `codex exec` or start another Codex process to execute work.
3. A skill invocation alone does not prove that a spawned task can change models. Without native per-task selection, use `current_session` or `manual`.

#### Gemini CLI, Qwen Code, Kiro CLI, Goose, and other CLI agents

1. Inspect only the native task/subagent interface and agent configuration exposed inside the current host session.
2. A native model-list command may provide catalog evidence, but it does not prove per-task model selection.
3. Never start another CLI process to execute a task. Without native per-task selection, use `current_session` for the active model or `manual` for alternatives.

#### GitHub Copilot, Cursor, and agents with both IDE and CLI surfaces

1. Use only the execution surface hosting this conversation. Models connected to an IDE session must not be executed by launching its companion CLI.
2. Use a runtime-native named agent pinned to the model when the host exposes one.
3. If only the model dropdown is available, use `manual` and record the UI action required.

#### IDE-only or unknown agents

1. Inspect the runtime's actual subagent/task interface and project agent configuration.
2. If there is no per-task selector, do not create guessed config files or commands. Use `current_session` only for the exact active model and `manual` for other picker entries.
3. Ask the user for vendor-specific instructions only when they want automation that the runtime cannot demonstrate.

#### Coverage of built-in Spec Kit integrations

Apply the branches above to every built-in integration. The registry's `requires_cli` value only controls installation checks; it is a starting hint, not proof of model selection or dispatch support.

- CLI-hosted integrations: `agy` (Antigravity), `amp`, `auggie`, `claude`, `codebuddy`, `codex`, `devin`, `droid`, `forge`, `gemini`, `goose`, `grok`, `hermes`, `junie`, `kimi`, `kiro-cli`, `omp`, `opencode`, `pi`, `qodercli`, `qwen`, `rovodev`, `shai`, `tabnine`, `vibe`, and `zcode`. For each one, discover its connected models through its native picker/configuration, then inspect the task/subagent API available inside the current session. Do not spawn the CLI as a worker.
- IDE-hosted integrations: `bob`, `cline`, `copilot`, `cursor-agent`, `firebender`, `kilocode`, `lingma`, `trae`, and `zed`. Inspect the host's native task/agent API and configured named agents. Never hand work to a companion CLI.
- `generic`: rely entirely on runtime evidence and user-provided execution instructions; never infer a command from the integration key.
- Whether the host itself is an IDE or CLI does not change the rule: implementation stays inside that host. If native per-task model selection is unavailable, use `current_session` or `manual`.

Verification and safety rules:

- Ask before creating agent configuration or running a native probe task that may consume paid quota.
- Probe prompts must be minimal, read-only, and contain no project secrets.
- A `manual` executor is valid but cannot be used for autonomous fallback.
- Every model appearing in `by_complexity` must have an executor entry, even when its mode is `manual`.

### 5. Write models.json

Write `.specify/models.json`, or `~/.specify/models.json` with `--global`, creating its parent directory when needed:

```json
{
  "version": 1,
  "runtime": {
    "agent": "<runtime agent>",
    "integration": "<active Spec Kit integration or null>",
    "project_root": "<absolute project root>",
    "provider_route": "<direct, gateway name/base URL, or unknown>"
  },
  "discovery": {
    "source": "agent_command | agent_picker | gateway_endpoint | user_provided",
    "mechanism": "<command, API, or UI used>",
    "detected_at": "<ISO-8601 timestamp>"
  },
  "catalog": [
    {
      "id": "<exact selectable model id>",
      "provider": "<provider if known>",
      "context": "<context if known>",
      "reasoning": true,
      "tier": "<5 | 4 | 3 | 2 | 1>",
      "intel": "<benchmark percentile 0-100 or null>",
      "blend_price": "<0.75*input + 0.25*output $/M or null>",
      "availability": "<restriction if known>",
      "note": "<variant or specialization if known>"
    }
  ],
  "manager": "<model id>",
  "by_complexity": {
    "5": ["<primary>", "<fallback 1>", "<fallback 2>"],
    "4": ["<primary>", "<fallback 1>"],
    "3": ["<primary>", "<fallback 1>"],
    "2": ["<primary>", "<fallback 1>"],
    "1": ["<primary>", "<fallback 1>"]
  },
  "executors": {
    "<model id>": {
      "mode": "native_subagent",
      "agent": "speckit-n3-1"
    },
    "<other model id>": {
      "mode": "manual",
      "instructions": "Select <other model id> in this host's native model picker, then continue with the saved handoff."
    }
  }
}
```

Omit unknown optional model fields instead of filling them with guesses.

Validate before writing:

- `runtime.agent`, `discovery.source`, and `discovery.mechanism` are non-empty.
- `catalog` is non-empty and contains unique exact IDs.
- Every catalog entry has one valid `tier`: `5`, `4`, `3`, `2`, or `1`.
- `manager` and every ID in `by_complexity` exist in `catalog`.
- `5`, `4`, `3`, `2`, and `1` each contain at least one model and no duplicate IDs. When the catalog is too small to fill every level with a distinct model, reuse capable models across levels rather than leaving a level empty.
- Every assigned ID has exactly one `executors` entry with mode `native_subagent`, `current_session`, or `manual`.
- A `native_subagent` executor has a non-empty `agent`. No verification state is stored: dispatch is optimistic and a failed invocation falls through to the next candidate.
- A `current_session` executor matches the model currently hosting the conversation.
- A `manual` executor has non-empty native picker/switch instructions.
- The target contains valid JSON after writing.

### 6. Fallback contract used by implementation

The list order is the complete dispatch policy; no separate load-balancing strategy is implied.

1. The manager (communicator) classifies each task/step's level (1-5) using the level criteria, then looks up that level's ordered list.
2. Start each task with the first candidate for its level.
3. Resolve the candidate's executor and dispatch immediately when it is `native_subagent` or the matching `current_session` executor. There is no verification gate: if the invocation itself fails (agent not loaded yet, unknown agent name, model unavailable), treat it as an availability failure and continue with the next candidate.
4. On a model-level availability failure (connection failure, usage/token exhaustion, rate limit, unavailable model, provider outage, or context limit), preserve the task state and retry with the next candidate that has a ready executor.
5. Pass the next candidate the original task plus the latest verified progress, changed files, test results, and remaining work so it continues rather than blindly restarting.
6. Never retry the same failed candidate in a loop. If the next candidate is `manual`, pause with exact switch/continuation instructions. Stop after the ordered list is exhausted and report every attempted model and failure.
7. Do not hide code/test failures by switching models. Diagnose ordinary implementation failures normally; fallback is for model availability/capacity failures.

### 7. Completion report

Report:

- Written path and project/global scope
- Runtime agent, installed integration, and any mismatch
- Discovery source and mechanism
- Number of models discovered
- Manager (communicator) and rationale
- Primary and ordered alternatives for every level N1-N5, with the benchmark percentile and cost-benefit behind each classification
- Executor mode for every assigned model
- Configuration files created, restart reminder for hosts that load agents at startup, and any manual-only fallback
- Reminder to rerun `__SPECKIT_COMMAND_MODELS__` whenever agent configuration or model availability changes (benchmark percentiles are relative — classification must be recalculated, never cached as a static table)
