"""CLI-specific orchestrator dispatch blocks.

Every workflow command template (``templates/commands/*.md``) contains a
``__SPECKIT_DISPATCH_BLOCK__`` placeholder where the model-dispatch procedure
goes.  The orchestrator concept (5 complexity levels, dynamic classification,
ordered fallback) is identical across every CLI — but *how* a task is handed to
the model of its level is CLI-specific:

* OpenCode pins a model by invoking a **named subagent** (``subagent_type``).
* Hermes Agent has no in-session per-task selector, so it spawns its **own CLI**
  one-shot with the model pinned by flag (``hermes chat -q -m <id>``).
* Other CLIs fall back to the generic multi-mode block that reads ``executors``.

Each integration returns the block dedicated to its CLI from
:meth:`IntegrationBase.dispatch_block`.  At install time,
:meth:`IntegrationBase.process_template` substitutes the placeholder with that
block, so the skills written to disk speak only their own CLI's mechanism.

The fallback contract is the same everywhere: start with the first model in the
level's ordered list; if that model cannot be reached (rate limit, quota
exhausted, provider outage, context overflow, non-zero exit), move to the next
model in the list — carrying the task state forward — until the list is
exhausted.
"""

from __future__ import annotations

# The placeholder every command template carries.
DISPATCH_PLACEHOLDER = "__SPECKIT_DISPATCH_BLOCK__"

# Placeholder in the `models` command for the CLI-specific "resolve an executor"
# section (executor modes + runtime branch + models.json executor example).
EXECUTOR_PLACEHOLDER = "__SPECKIT_EXECUTOR_BLOCK__"


# ---------------------------------------------------------------------------
# Generic (default) — reads every executor mode from models.json
# ---------------------------------------------------------------------------

GENERIC_DISPATCH_BLOCK = """\
Before performing ANY substantive step, run this procedure and show its output:

1. **Classify** the step you are about to perform: level `5` critical -> `1` trivial.
2. **Resolve the model**: `model = by_complexity["<level>"][0]` from the loaded `models.json`.
3. **Resolve the executor**: `exec = executors[model]`. Read `exec.mode` and the field it needs — `native_subagent` -> `exec.agent`; `cli_subprocess` -> `exec.command`; `current_session` -> run in this session only if `model` is the current runtime model; `manual` -> pause with `exec.instructions`.
4. **Announce the dispatch** on its own line, verbatim: `DISPATCH n<level> -> <model>`.
5. **Dispatch the worker by executor mode**, passing a prompt containing only the context that worker needs:
   - `native_subagent`: call the task tool with the agent parameter pinned to `exec.agent`. Never call the task tool with only a prompt — an unpinned worker runs on the manager's model and defeats the orchestrator.
   - `cli_subprocess`: run `exec.command` (which pins the model via the host CLI's own model flag) as a one-shot subprocess of the **same** CLI hosting this conversation, with the worker prompt appended.
   - `current_session`: perform the step in this conversation only when `model` equals the current runtime model.
   - `manual`: stop and surface `exec.instructions`; never claim automatic dispatch.
6. **Check the result**: if the invocation fails (unknown/rejected agent, non-zero subprocess exit, or model unavailable), treat that candidate as failed, take the next model in that level's list, and repeat from step 3. When the list is exhausted, say so explicitly and only then continue in-session.\
"""


# ---------------------------------------------------------------------------
# OpenCode — named subagents pinned to a model (subagent_type)
# ---------------------------------------------------------------------------

OPENCODE_DISPATCH_BLOCK = """\
Before performing ANY substantive step, run this procedure and show its output:

1. **Classify** the step you are about to perform: level `5` critical -> `1` trivial.
2. **Resolve the model**: `model = by_complexity["<level>"][0]` from the loaded `models.json`.
3. **Resolve the agent name**: `agent = executors[model].agent`. This exact string is required — never a guess, never a description. (OpenCode pins a model by dispatching to a named subagent, so every executor here is `native_subagent`.)
4. **Announce the dispatch** on its own line, verbatim: `DISPATCH n<level> -> <model>` (append `via <agent>` when helpful).
5. **Call the task tool** with the agent parameter pinned to that string (`subagent_type: "<agent>"`) and a prompt containing only the context that worker needs. Never call the task tool with only a prompt — an unpinned worker runs on the manager's own model and silently defeats the whole orchestrator.
6. **Check the result and fall back down the list**: if the runtime reports an unknown agent, a rejected agent name, a fallback to a default agent, or the model is unavailable (rate limit, quota exhausted, provider outage, context overflow), treat that candidate as failed, take the **next model in that level's list**, and repeat from step 3 — carrying the task state forward so the fallback continues rather than restarting. Never retry the same failed candidate in a loop. When the list is exhausted, say so explicitly and only then continue in-session.\
"""


# ---------------------------------------------------------------------------
# Hermes Agent — spawn the same CLI with the model pinned by -m flag
# ---------------------------------------------------------------------------

HERMES_DISPATCH_BLOCK = """\
Before performing ANY substantive step, run this procedure and show its output:

1. **Classify** the step you are about to perform: level `5` critical -> `1` trivial.
2. **Resolve the model**: `model = by_complexity["<level>"][0]` from the loaded `models.json`.
3. **Resolve the command**: `command = executors[model].command` — a `hermes chat -q -m <model-id>` invocation that pins that exact model. This exact string is required — never a guess. (Hermes has no in-session per-task model selector: `delegate_task` inherits the manager's model. Spawning the Hermes CLI with `-m` **is** the native per-task selector — use it, do not fall back to `manual` while a `command` exists.)
4. **Announce the dispatch** on its own line, verbatim: `DISPATCH n<level> -> <model>` (append `via <command>` when helpful).
5. **Run the worker as a one-shot Hermes subprocess**: execute `executors[model].command` with the worker prompt appended as its query (e.g. `hermes chat -q -m <model-id> "<prompt>"`), passing only the context that worker needs. The `-m` flag pins the model, so the work runs on the level's model, not the manager's. Only ever spawn Hermes itself — never a different vendor's CLI.
6. **Check the result and fall back down the list**: if the subprocess fails (non-zero exit, model unavailable, rate limit, quota exhausted, provider outage, context overflow, or connection refused), treat that candidate as failed, take the **next model in that level's list**, and repeat from step 3 — carrying the task state forward (progress, changed files, test results, remaining work) so the next model continues rather than restarting. Never retry the same failed candidate in a loop. When the list is exhausted, say so explicitly and only then continue in-session.\
"""


# ---------------------------------------------------------------------------
# Executor-resolution block for the `models` command (section 4 + JSON example)
# ---------------------------------------------------------------------------

GENERIC_EXECUTOR_BLOCK = """\
All task execution must remain inside the agent or CLI hosting this conversation. Discover the real per-task execution route from the runtime — do not assume a model picker implies programmatic per-task model selection.

Each assigned model resolves to one of these executor modes:

- `native_subagent`: the runtime invokes a named subagent whose configuration pins the exact model. Requires passing that agent's exact name to the host's task/subagent tool.
- `cli_subprocess`: the host has no in-session per-task selector, but its own CLI pins a model per invocation. Dispatch runs a fresh **same-CLI** one-shot process with the model flag set (recorded in `executors[model].command`).
- `current_session`: the conversation is already running that exact model but cannot select it for a separate worker.
- `manual`: no programmatic route exists; the user switches the model and continues manually.

Prefer an in-session per-task selector when the host has one; otherwise use `cli_subprocess` when the host CLI exposes a per-invocation model flag; fall back to `current_session`/`manual`. Never launch a *different* vendor's CLI.

The `executors` map in models.json records, per assigned model, the resolved mode plus its field (`agent` / `command` / `instructions`). Every model in `by_complexity` must have an executor entry.\
"""


HERMES_EXECUTOR_BLOCK = """\
Hermes has **no in-session per-task model selector**: its `delegate_task` subagent inherits the manager's model and cannot pin a different one per task. Do **not** mark models `manual` — that silently kills level->model routing. Hermes' native per-task route is its own CLI's `-m` flag.

Resolve every assigned model to a `cli_subprocess` executor:

1. Discover the connected catalog from the runtime: inspect the Hermes model picker, or query the configured gateway's `GET /v1/models` when the session provably routes through it. Preserve exact selectable IDs (including provider prefixes such as `cc/` or `kimi/`).
2. Give every assigned model a `cli_subprocess` executor whose `command` is `hermes chat -q -m <exact-model-id>` (add `--provider <p>` only when the id needs it). Dispatch appends the worker prompt as the query; the `-m` flag pins the model. This is same-CLI — the intended mechanism, not a forbidden second agent.
3. Use `current_session` only for the exact model already hosting this conversation. Use `manual` only if the Hermes CLI cannot be invoked from the session at all. Never create agent-definition files — Hermes has no per-agent model-pinning file mechanism.

Write each model's executor into models.json like:

```json
"executors": {
  "<hermes model id>": {
    "mode": "cli_subprocess",
    "command": "hermes chat -q -m <hermes model id>"
  },
  "<current session model>": {
    "mode": "current_session"
  }
}
```

Validation: every model in `by_complexity` has exactly one executor; each `cli_subprocess` has a non-empty `command` that pins its exact model id via `hermes chat -q -m ...`; a `current_session` executor matches the model hosting this conversation. No agent config is created and no restart is needed — the subprocess route works immediately. Ask before running a probe invocation that consumes paid quota.\
"""


OPENCODE_EXECUTOR_BLOCK = """\
OpenCode pins a model per task by dispatching to a **named subagent**. Every assigned model resolves to a `native_subagent` executor.

1. Read the merged OpenCode configuration and inspect project/global agents. A subagent is selectable only when its definition has `mode: subagent` (or `all`) and `model: <exact provider/model-id>`.
2. Inspect the task tool schema. If it accepts only `subagent_type` and not `model`, select a configured agent name; do not claim direct model selection.
3. For each assigned model without a matching agent, propose a stable agent such as `speckit-n3-1` in `.opencode/agent/<name>.md` (project) or `~/.config/opencode/agent/<name>.md` (global), with `mode: subagent`, the exact `model`, a concise description, and only the permissions needed. The directory is **`agent/` (singular)** — a plural `agents/` is silently ignored. Confirm with `opencode agent list`.
4. Ask before creating/updating agent files; preserve unrelated config. OpenCode loads agents at startup, so tell the user to restart. Do not gate dispatch on this: if a worker agent is not loaded yet when invoked, the fallback chain moves to the next candidate.

Write each model's executor into models.json like:

```json
"executors": {
  "<opencode model id>": {
    "mode": "native_subagent",
    "agent": "speckit-n3-1"
  }
}
```

Validation: every model in `by_complexity` has exactly one executor; each `native_subagent` has a non-empty `agent`. Dispatch is optimistic — a failed invocation falls through to the next candidate. Ask before creating agent configuration or running a probe that consumes paid quota.\
"""
