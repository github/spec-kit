---
description: Detect the agent hosting this conversation, discover its actually configured models from first-party runtime evidence, assign primary and fallback models by task difficulty, and write models.json.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty). Supported overrides include `--global`, pasted model-picker output, a manual model list, and explicit assignments such as `manager=X`, `high=X,Y`, `medium=A,B`, or `low=C,D`.

## Goal

Create a `models.json` containing only models that the agent hosting **this conversation** can select now, plus a verified execution route for each assigned model. Assign an ordered candidate chain to every difficulty: the first model is the primary executor and the remaining models are alternatives used when a model is unavailable, rate-limited, out of usage/tokens, or exceeds its context limit.

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
- `tier`: derived implementation capability (`max`, `high`, `medium`, or `low`) assigned in the next step; this is an assessment, not discovery evidence

### 3. Assess difficulty suitability

Classify every discovered model for `high`, `medium`, and `low` work. Use model metadata returned by discovery, reliable capability information available in the runtime, and explicit user guidance. Consider reasoning strength, coding capability, context size, speed, cost, quota, and specialization.

Do not rank opaque or unfamiliar model IDs from their names alone. Ask the user for guidance when the available evidence cannot support a meaningful ranking.

Assignment rules:

- `manager`: the strongest model for specification, planning, decomposition, and orchestration. It does not normally implement tasks.
- `high`: architecture, difficult debugging, security-sensitive logic, broad refactors, and tasks requiring deep reasoning or large context.
- `medium`: normal feature implementation, localized refactors, and substantive tests.
- `low`: documentation, configuration, renames, formatting, and mechanical edits.
- Each difficulty maps to an **ordered non-empty list**: primary first, then alternatives in fallback order.
- Prefer alternatives with an independent provider/quota route when capability is adequate, so exhausting one model's allowance does not exhaust every fallback.
- Keep each fallback capable of completing that difficulty. Never add a weak model merely to make the list longer.
- Reserve the manager from implementation when enough other models exist. Small catalogs may reuse the same model across roles and difficulties.
- Apply explicit user assignments after validating that every assigned ID exists in the discovered catalog.

Before writing, show the detected environment, discovery evidence, catalog, proposed manager, and ordered candidates for each difficulty. Ask the user to confirm or adjust the assignments. Skip this confirmation only when the user already supplied complete explicit assignments for `manager`, `high`, `medium`, and `low`.

### 4. Resolve and verify an executor for every assigned model

Discover execution capabilities from the **runtime**, not from the product name. Inspect the task/subagent tool schemas and agent configuration already loaded by the host. Never assume that a model picker implies programmatic per-task model selection.

All task execution must remain inside the agent or CLI hosting this conversation. A model connected to OpenCode must run through OpenCode; a model connected to Claude Code must run through Claude Code; and so on. Never launch another agent CLI, and never start a second process of the current CLI, to execute a task or fallback. Native model commands may be used only to inspect the current host's configured catalog.

Each assigned model must resolve to one of these executor modes:

- `native_subagent`: the runtime can invoke a named subagent whose loaded configuration pins the exact model.
- `current_session`: the current conversation is already running that exact model, but cannot select it for a separate worker.
- `manual`: no verified programmatic route exists; the user must switch/select the model and continue manually.

Use the following runtime-specific procedure. These are verification branches, not claims that every installed version supports the feature:

#### OpenCode

1. Read the merged OpenCode configuration and inspect project/global agents. A subagent is selectable only when its definition has `mode: subagent` (or `all`) and `model: <exact provider/model-id>`.
2. Inspect the task tool schema exposed to this conversation. If it accepts only `subagent_type` and not `model`, select a configured agent name; do not claim direct model selection.
3. For each candidate without a matching agent, propose a stable agent such as `speckit-high-1` or `speckit-medium-2` in `.opencode/agents/<name>.md`, with `mode: subagent`, the exact `model`, a concise description, and only the permissions needed for implementation.
4. Ask before creating or updating OpenCode agent files. Preserve unrelated configuration. After writing, mark the executor `pending_restart`; OpenCode loads configuration at startup, so tell the user to restart and rerun `__SPECKIT_COMMAND_MODELS__` to verify it before marking it `verified`.

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
2. If there is no verified per-task selector, do not create guessed config files or commands. Use `current_session` only for the exact active model and `manual` for other picker entries.
3. Ask the user for vendor-specific instructions only when they want automation that the runtime cannot demonstrate.

#### Coverage of built-in Spec Kit integrations

Apply the branches above to every built-in integration. The registry's `requires_cli` value only controls installation checks; it is a starting hint, not proof of model selection or dispatch support.

- CLI-hosted integrations: `agy` (Antigravity), `amp`, `auggie`, `claude`, `codebuddy`, `codex`, `devin`, `droid`, `forge`, `gemini`, `goose`, `grok`, `hermes`, `junie`, `kimi`, `kiro-cli`, `omp`, `opencode`, `pi`, `qodercli`, `qwen`, `rovodev`, `shai`, `tabnine`, `vibe`, and `zcode`. For each one, discover its connected models through its native picker/configuration, then inspect the task/subagent API available inside the current session. Do not spawn the CLI as a worker.
- IDE-hosted integrations: `bob`, `cline`, `copilot`, `cursor-agent`, `firebender`, `kilocode`, `lingma`, `trae`, and `zed`. Inspect the host's native task/agent API and configured named agents. Never hand work to a companion CLI.
- `generic`: rely entirely on runtime evidence and user-provided execution instructions; never infer a command from the integration key.
- Whether the host itself is an IDE or CLI does not change the rule: implementation stays inside that host. If native per-task model selection is unavailable, use `current_session` or `manual`.

Verification and safety rules:

- Ask before creating agent configuration or running a native verification task that may consume paid quota.
- Verification prompts must be minimal, read-only, and contain no project secrets.
- `verified: true` requires a successful probe in the current environment. Configuration written during this run but not loaded yet is `verified: false` with `status: pending_restart`.
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
      "tier": "<max | high | medium | low>",
      "availability": "<restriction if known>",
      "note": "<variant or specialization if known>"
    }
  ],
  "manager": "<model id>",
  "by_complexity": {
    "high": ["<primary>", "<fallback 1>", "<fallback 2>"],
    "medium": ["<primary>", "<fallback 1>"],
    "low": ["<primary>", "<fallback 1>"]
  },
  "executors": {
    "<model id>": {
      "mode": "native_subagent",
      "agent": "speckit-high-1",
      "verified": true,
      "status": "ready"
    },
    "<other model id>": {
      "mode": "manual",
      "instructions": "Select <other model id> in this host's native model picker, then continue with the saved handoff.",
      "verified": true,
      "status": "manual_only"
    }
  }
}
```

Omit unknown optional model fields instead of filling them with guesses.

Validate before writing:

- `runtime.agent`, `discovery.source`, and `discovery.mechanism` are non-empty.
- `catalog` is non-empty and contains unique exact IDs.
- Every catalog entry has one valid `tier`: `max`, `high`, `medium`, or `low`.
- `manager` and every ID in `by_complexity` exist in `catalog`.
- `high`, `medium`, and `low` each contain at least one model and no duplicate IDs.
- Every assigned ID has exactly one `executors` entry with mode `native_subagent`, `current_session`, or `manual`.
- A `native_subagent` executor has a non-empty `agent` and is not autonomous unless `verified` is true and `status` is `ready`.
- A `current_session` executor matches the model currently hosting the conversation.
- A `manual` executor has non-empty native picker/switch instructions and uses `status: manual_only`.
- The target contains valid JSON after writing.

### 6. Fallback contract used by implementation

The list order is the complete dispatch policy; no separate load-balancing strategy is implied.

1. Start each task with the first candidate for its difficulty.
2. Resolve the candidate's executor. Dispatch automatically only when it is `native_subagent` with `verified: true` and `status: ready`, or when it is the matching `current_session` executor.
3. On a model-level availability failure (usage/token exhaustion, rate limit, unavailable model, provider outage, or context limit), preserve the task state and retry with the next candidate that has a ready executor.
4. Pass the next candidate the original task plus the latest verified progress, changed files, test results, and remaining work so it continues rather than blindly restarting.
5. Never retry the same failed candidate in a loop. If the next candidate is `manual`, pause with exact switch/continuation instructions. Stop after the ordered list is exhausted and report every attempted model and failure.
6. Do not hide code/test failures by switching models. Diagnose ordinary implementation failures normally; fallback is for model availability/capacity failures.

### 7. Completion report

Report:

- Written path and project/global scope
- Runtime agent, installed integration, and any mismatch
- Discovery source and mechanism
- Number of models discovered
- Manager and rationale
- Primary and ordered alternatives for `high`, `medium`, and `low`
- Executor mode and verification state for every assigned model
- Configuration files created, restart requirements, and any manual-only fallback
- Reminder to rerun `__SPECKIT_COMMAND_MODELS__` whenever agent configuration or model availability changes
