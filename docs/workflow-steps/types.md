# Built-in workflow step types

Step configuration selects executable behavior with `type`. Omitting `type` selects `command`. Step IDs are local expression aliases and must not contain `:`, which is reserved for generated occurrence IDs.

## Step Types

| Type         | Purpose                                          |
| ------------ | ------------------------------------------------ |
| `command`    | Invoke a Spec Kit command (e.g., `speckit.plan`) |
| `prompt`     | Send an arbitrary prompt to the AI coding agent  |
| `shell`      | Execute a shell command and capture output       |
| `github`     | Add an explicit issue or pull-request label       |
| `init`       | Bootstrap a project (like `specify init`)        |
| `slot`       | Named workflow slot; skipped when unfilled       |
| `gate`       | Pause for human approval before continuing       |
| `if`         | Conditional branching (then/else)                |
| `switch`     | Multi-branch dispatch on an expression           |
| `while`      | Loop while a condition is true                   |
| `do-while`   | Execute at least once, then loop on condition    |
| `fan-out`    | Dispatch a step for each item in a list          |
| `fan-in`     | Aggregate results from a fan-out step            |
| `workflow`   | Call an installed workflow with private inputs and declared outputs |

## Command Steps (default)

Invoke an installed Spec Kit command by name via the integration CLI:

```yaml
- id: specify
  command: speckit.specify
  input:
    args: "{{ inputs.spec }}"
  integration: claude        # Optional: override workflow default
  model: "claude-sonnet-4-20250514"   # Optional: override model
```

For positional arguments and named runtime options, see
[Per-step integration configuration](#per-step-integration-configuration). For
`reasoning_effort` and `context_size`, see
[Reasoning effort and context size](#reasoning-effort-and-context-size).

## Prompt Steps

Send an arbitrary inline prompt to an integration CLI (no command file needed):

```yaml
- id: security-review
  type: prompt
  prompt: "Review {{ inputs.file }} for security vulnerabilities"
  integration: claude
```

## Capturing Command and Prompt Output

`command` and `prompt` steps stream the integration CLI's output to the
terminal, so `steps.<id>.output.stdout` and `steps.<id>.output.stderr` are empty
strings. Set `capture: true` to retain that output in the step result instead,
where later steps can read it:

```yaml
- id: verdict
  type: prompt
  prompt: "Reply with exactly READY or BLOCKED for {{ inputs.spec }}"
  capture: true
  capture_max_bytes: 4096   # Optional: per-stream limit (default 1048576)
  timeout: 120              # Optional: seconds before the CLI is killed

- id: branch
  type: if
  condition: "{{ steps.verdict.output.stdout | contains('READY') }}"
  then:
    - id: plan
      command: speckit.plan
```

| Field               | Applies to          | Meaning                                                                                             |
| ------------------- | ------------------- | --------------------------------------------------------------------------------------------------- |
| `capture`           | `command`, `prompt` | `true` captures stdout and stderr instead of streaming them. Must be a literal boolean; default `false`. |
| `capture_max_bytes` | `command`, `prompt` | Limit for each captured stream: a positive integer, or `-1` for no limit. Default `1048576` (1 MiB). Requires `capture: true`. |
| `timeout`           | `command`, `prompt` | Seconds before the CLI is killed; with `capture: true`, its process group (POSIX) or job object (Windows) is killed, which includes the processes it started unless they detached from it, as a daemonising helper can. For `command` it applies only with `capture: true` (default `600`); a streaming `command` step has no timeout. For `prompt` it always applies (default `300`). |

A captured step prints nothing while it runs. Its output gains these fields:

| Output field       | Meaning                                                                    |
| ------------------ | -------------------------------------------------------------------------- |
| `stdout`, `stderr` | The captured text.                                                         |
| `stdout_truncated` | `true` when stdout exceeded `capture_max_bytes` and the rest was discarded. |
| `stderr_truncated` | The same for stderr.                                                       |
| `timed_out`        | `true` when the CLI and its processes were killed at `timeout`; `exit_code` is `-1`. |
| `interrupted`      | `true` when the run was interrupted (Ctrl+C); `exit_code` is `130`.        |

**What the text is.** Capture requests the integration CLI's normal text
output, the same output a streaming step prints. It is not a structured format:
it can include progress or tool-use lines as well as the final answer, it
differs between integrations, and it is valid JSON only if the agent printed
nothing but JSON.

**Limits and encoding.** `capture_max_bytes` counts raw bytes on each stream
before decoding. Bytes past the limit are read and discarded so the CLI is never
blocked, and the matching `*_truncated` field is set. Output is decoded as
UTF-8: invalid bytes become U+FFFD, and a character split by the limit, a
timeout, or an interruption is dropped rather than replaced. Line endings are
normalised to `\n`.

With `capture_max_bytes: -1` nothing is discarded and both `*_truncated` fields
stay `false`. The whole output is then held in memory and written to run state,
so an agent that prints a large amount grows both without bound. Use it only
for output you know is small.

**Check completeness before using the output.** Filters such as `from_json` do
not look at these fields; they parse whatever text is there. Output is
incomplete when `stdout_truncated` is `true`, and also when `timed_out` or
`interrupted` is `true` — a stopped CLI leaves partial output even with no size
limit. Guard the use:

```yaml
- id: parse
  type: if
  condition: "{{ steps.verdict.output.exit_code == 0 and not steps.verdict.output.stdout_truncated }}"
  then:
    - id: use
      type: shell
      run: "echo parsed"
```

**Failures.** A non-zero exit, a timeout, or an interruption fails the step and
keeps whatever was captured in `output.stdout` and `output.stderr`. The step's
error is a short summary (`Command exited with code 2`,
`Prompt timed out after 120 seconds.`), never the captured text. A failed step
stops the run, so set `continue_on_error: true` on the capturing step when a
later step needs to inspect the failure:

```yaml
- id: verdict
  type: prompt
  prompt: "Reply with exactly READY or BLOCKED"
  capture: true
  timeout: 120
  continue_on_error: true

- id: on-timeout
  type: if
  condition: "{{ steps.verdict.output.timed_out }}"
  then:
    - id: review
      type: gate
      message: "The verdict step timed out. Approve to continue without it."
```

> ⚠️ **Captured output is stored in plain text and is not redacted.** It is
> written to the run's `state.json` so that `specify workflow resume` can replay
> it, and it stays there after the run. Anything the agent prints — including
> secrets it read from files or the environment — is persisted. Captured text is
> not printed to the terminal and is not written to `log.jsonl`. Do not enable
> capture on a step whose output may contain credentials unless the run
> directory is protected accordingly.

Captured text is agent output and therefore untrusted; see
[Interpolation and shell safety](../workflows/expressions.md#interpolation-and-shell-safety) before using
it in a `shell` step.

## Per-Step Integration Configuration

Command steps may pass structured runtime configuration to integrations that
support it:

```yaml
- id: implement-with-docker-agent
  type: command
  command: speckit.implement
  integration: docker-agent
  integration_args:
    - "{{ inputs.agent_config }}"
  integration_options:
    agent: root
    safety: balanced
  model: "openai/gpt-5"
  input:
    args: "{{ inputs.spec }}"
```

`integration_args` is an ordered list of strings. `integration_options` is a
mapping with string keys. Values in both fields are resolved with the workflow
expression mechanism and validated by the selected integration; unsupported,
unknown, or malformed values fail with an actionable error. Docker Agent uses
its single positional argument as the agent configuration reference and accepts
`agent` and `safety` as named integration options. Configure its model through
the command step's top-level `model` field.

When Docker Agent `integration_args` supplies an agent reference for a command
step, it takes precedence over `SPECKIT_INTEGRATION_DOCKER_AGENT_EXTRA_ARGS`;
the entire legacy environment value is ignored for that step. Without a per-step
agent reference, the legacy environment behavior is unchanged.

Resolved runtime configuration is recorded in workflow run state. When a failed
or paused command is resumed, the complete dispatch configuration is re-resolved
from the current inputs, so values supplied with `workflow resume --input` take
effect consistently. A resume without updated inputs reproduces the same values.

A command step's `options` mapping, merged over `workflow.options`, is recorded
as `steps.<id>.output.options` but is not passed to the integration CLI. To
change the invocation, use `integration_args`, `integration_options`, `model`,
or [`reasoning_effort` and `context_size`](#reasoning-effort-and-context-size).

## Reasoning Effort and Context Size

`command` and `prompt` steps can set `reasoning_effort` and `context_size` for
the integration CLI they invoke. `workflow.reasoning_effort` and
`workflow.context_size` set defaults for both step types:

```yaml
workflow:
  id: plan-and-review
  name: Plan and review
  reasoning_effort: "medium"   # Default for command and prompt steps

inputs:
  review_effort:
    type: string
    default: ""                # Empty: the review step sends no effort

steps:
  - id: plan
    command: speckit.plan
    reasoning_effort: "high"   # Overrides the workflow default
    context_size: "200000"     # Quoted: values are strings

  - id: review
    type: prompt
    prompt: "Review the plan for gaps"
    reasoning_effort: "{{ inputs.review_effort }}"
```

**Resolution.** Each setting resolves like `model`: the step's value, then the
workflow default, then unset. The step value and the default can both be
expressions. A step value that is missing, `null`, or `""` inherits the
default. An expression that resolves to `""` or null unsets the setting for
that step, without falling back to the default; this is how a step opts out of
a default. In the example, `review` sends no reasoning effort unless the run
supplies `--input review_effort=<value>`.

**Values.** Values are strings. Quote numbers and words that YAML reads as
booleans, such as `on`, `off`, `yes`, and `no`: write `context_size: "200000"`,
not `context_size: 200000`. An expression must resolve to a string too, so
read a number from an input declared with `type: string`, not `type: number`.
A value must be 1 to 64 letters, digits, `.`, `_`, or `-`, starting with a
letter or digit. Literal values are checked when the workflow is validated, and
expression results when the step runs. An error about a malformed value reports
only its type and length, not its text. Spec Kit passes the value to the
integration unchanged. Its meaning and accepted values are defined by the
integration's CLI, and an integration can reject a value before the CLI runs.

**Support.** An integration translates a setting only if it declares support
for it. Otherwise the step fails before the CLI runs, with an error that names
the setting, its source (the step or the workflow default), and any
integrations that support it. Workflow defaults are not exempt: a default fails
each inheriting step whose integration does not support it. No built-in
integration supports these settings yet; see
[Workflow CLI dispatch](../integrations/cli.md#workflow-cli-dispatch) for how
integrations opt in.

**CLI rejections.** When the CLI rejects a value and exits with a non-zero code,
the step fails like any other CLI failure. The step error reports the exit
code, and the CLI's message appears on the terminal, or in `output.stderr` with
[`capture: true`](#capturing-command-and-prompt-output).

**Recording and resume.** The resolved values are recorded in
`steps.<id>.output.reasoning_effort` and `steps.<id>.output.context_size`, which
are `null` when unset. When `specify workflow resume` re-executes a step, it
resolves both again from the current inputs, so values supplied with `--input`
take effect.

**Extra arguments.** An integration that supports these settings adds their
flags after any arguments from `SPECKIT_INTEGRATION_<KEY>_EXTRA_ARGS`. If both
set the same CLI flag, the CLI decides which value wins, so set each flag in
only one place.

**Compatibility.** Spec Kit versions without this feature ignore these fields,
including the workflow defaults, and run steps without them.
`requires.speckit_version` does not prevent this: it is advisory and is not
enforced.

## Shell step

`type: shell` executes `run` through the platform shell, retaining support for
pipes, redirects, and multiple commands. Set `strict: true` to reject `{{`
expression markers anywhere in `run`, including inside quotes. This is checked
both during validation and immediately before execution. `strict` must be a
boolean; omitted or `false` preserves existing raw interpolation behavior.

Use an `env` mapping to bind dynamic values without inserting them into shell
source. For example, on POSIX:

```yaml
- id: display-result
  type: shell
  strict: true
  env:
    RESULT: "{{ steps.plan.output.stdout }}"
  run: 'printf "%s\n" "$RESULT"'
```

For cross-platform scripts, read the environment in the program itself, such
as `os.environ["RESULT"]` in Python. See
[Shell Step Environment Variables](#shell-step-environment-variables) for the
binding contract and [Interpolation and shell safety](../workflows/expressions.md#interpolation-and-shell-safety)
for the remaining trust boundary.

> **Security note:** a `shell` step runs a local command with **your** privileges. There is no capability sandbox — `requires` is an advisory pre-condition block (spec-kit version, integrations), not a runtime gate, so it does **not** restrict what a step can do. In particular there is no `requires.permissions` capability gate: it is rejected by validation precisely because it would imply a sandbox that does not exist. Review any catalog or downloaded workflow before running it, and use a `gate` step to require explicit approval before sensitive or destructive shell commands.

Shell `timeout` must be a positive number and defaults to `300` seconds. A timeout kills the command and fails the step. Shell output is captured for later expressions.

Set `output_format: json` to parse stdout into typed `output.data`. Invalid JSON,
including bare `NaN`, `Infinity`, and `-Infinity` constants, fails the step while
preserving `stdout`, `stderr`, and `exit_code`. Quoted strings such as `"NaN"`
remain valid. Without `output_format`, stdout remains raw text with no `data` field.

## Shell Step Environment Variables

Shell steps automatically receive the following environment variables:

| Variable | Description |
| -------- | ----------- |
| `SPECKIT_WORKFLOW_DIR` | Resolved absolute path to the workflow source directory (same value as `{{ context.workflow_dir }}`). Not set when the workflow has no source path. |

An optional per-step `env` mapping is available in both strict and non-strict
mode. Names must match `[A-Za-z_][A-Za-z0-9_]*`; names are literal, not
expressions. Values must be strings and may contain workflow expressions.
Each value is evaluated once and must resolve to a string without NUL
characters. On POSIX, the string must also be encodable for the process
environment using the filesystem encoding and its error handler.
Invalid bindings fail the step before launching a process.

Single-expression bindings preserve the expression's result type:
`COUNT: "{{ inputs.count }}"` rejects a number, boolean, null, list, or mapping
instead of converting it to text. Mixed templates use standard expression
interpolation: `COUNT: "n={{ inputs.count }}"` produces `n=42` for integer
`42`; embedded null becomes empty text, and other values use their string
representation. To serialize structured data explicitly, use `to_json`.

Bindings override inherited environment values for that subprocess only;
they do not modify the parent process or subsequent steps. An empty string is
valid. `SPECKIT_WORKFLOW_DIR` is reserved (case-insensitively) and cannot be
overridden. Keep environment names and executable-loading settings under the
workflow author's control: environment binding is a data channel, not a sandbox.

### Reviewing shell execution

Before installing or running an unfamiliar workflow, audit each shell step's
`run` **and** `env`, including nested branches and fan-out templates. Review
referenced scripts and resources, called workflows, and active overlay YAML
that can replace or insert steps. Apply the same review to workflow components
of bundles, and repeat it when definitions, overlays, or referenced code change.
Custom step packages require their own source review because loading them
executes Python code.

An environment value can control execution rather than merely supply data.
For example, `PATH` selects executables, `PYTHONPATH` affects Python imports,
`BASH_ENV` can select Bash startup code, and `NODE_OPTIONS` can change Node.js
startup behavior. Native loaders and other programs have their own settings;
these examples are not an exhaustive list. A fixed `run` can therefore execute
different code even with `strict: true` and no `eval`. Strict mode neither
filters execution-controlling bindings nor cleans the inherited environment.
Keep those settings literal and author-vetted, or constrain dynamic values to
an approved set of trusted paths/options. Use unconstrained input or agent
output only for application-data variables whose consumers handle it as data.

When a shell step invokes Specify itself, catalog overrides such as
`SPECKIT_WORKFLOW_CATALOG_URL` can also change where child commands discover
or install components. Vet those bindings alongside the
[active catalog sources](../overview/catalogs.md#discovery-and-trust).

Workflow validation checks configuration, not whether environment settings or
commands are safe. `specify workflow info` shows metadata and step identities;
`specify workflow resolve` shows layer and step attribution. Neither displays
the complete `run`/`env` configuration or replaces reading the contributing
source files. Catalog install permission, bundle installation, and strict mode
are not security endorsements.

## GitHub step

`type: github` uses the installed `gh` CLI and its active authentication.
Specify the GitHub repository as `owner/repo`; no Git remote or source checkout
is required. Requests go to GitHub's `api.github.com` REST endpoint for that
repository. The active token needs permission to read the issue or pull request
and to write its labels (for example, `issues: write` for issues or
`pull-requests: write` for PRs when using `GITHUB_TOKEN` in Actions). The step
uses only the existing token: it does not request or elevate permissions. It
does not inspect issue contents for instructions or make a maintainer decision.

```yaml
- id: mark-ready
  type: github
  operation: add-label
  repository: owner/repo
  target: issue
  number: "{{ inputs.issue_number }}"
  label: ready-for-review
```

`target` is `issue` or `pull_request`; `number` must resolve to a positive
integer. `label` is one explicit label name (up to 50 characters) and must
already exist in the repository. `repository`, `number`, and `label` may use
workflow expressions. The repository must resolve to a single `owner/repo`
name, not a URL or Git remote. The step checks the target type and its existing
labels, skips the write when the label is already present, and verifies GitHub's
response after adding it.
The output includes `repository`, `target`, `number`, `label`, and `added`
(`true` only when a label was added). Repeated execution and fan-out items
are safe to retry: an already-present label is left unchanged. This first
version does not post comments, restore artifacts, check out PRs, or infer
which label a maintainer would choose.

## Init Steps

Bootstrap a project the same way `specify init` does — scaffolding
templates, scripts, shared infrastructure, and the selected coding agent
integration. Runs non-interactively (defaults to `--ignore-agent-tools`)
and resolves the integration from the step config or the workflow default:

```yaml
- id: bootstrap
  type: init
  here: true                 # or: project: my-project
  integration: copilot       # Optional: defaults to workflow integration
  integration_options: "--skills"  # Optional: extra options for the integration
  script: sh                 # Optional: sh, ps, or py
  force: true                # Optional: required when target directory already exists
  preset: healthcare-compliance   # Optional preset ID
```

## Workflow Slots

Declare a named workflow slot that downstream projects can fill with a
workflow overlay. The slot is skipped when unfilled; its `id` is the overlay
anchor and `name` is a required human-readable label:

```yaml
- id: post-implement
  type: slot
  name: "Post-implementation checks"
```

See [Workflow slots](../workflows/overlays.md#workflow-slots-upstream-extension-points)
for filling a slot, preserving its outputs, and fan-out limitations.

## Gate Steps

Prompt for human review on an interactive terminal, or pause for a later
`specify workflow resume`. A verdict input can decide without prompting:

```yaml
- id: review-spec
  type: gate
  message: "Review the generated spec before planning."
  options: [approve, edit, reject]
  on_reject: abort
```

## Gate Verdict Inputs

`verdict_input` binds a gate's verdict to a named workflow input. The input must
be declared in the workflow's `inputs` block; workflow validation during `add`
or `run` reports an undeclared reference.

`verdict_input` is not supported inside a `fan-out` template. Fan-out items
share workflow inputs, while workflow state can represent only one paused
gate. Place a gate before the fan-out to approve the whole batch, or after a
fan-in to review the aggregated results.

**Input value semantics:**

| Value | Behavior |
|---|---|
| Non-empty string, matches an option (case-insensitive) | Gate auto-decides; `output.choice` is set to the configured option spelling |
| Non-empty string, no match | Gate fails immediately |
| Non-string | Gate fails immediately |
| Missing or empty | Gate prompts on a TTY; pauses otherwise |

**Default value semantics:** A non-empty `default` is consumed as a verdict on the first run — matching an option auto-decides the gate, not matching fails it immediately.

```yaml
inputs:
  spec_verdict:
    type: string
    default: ""
steps:
  - id: review-spec
    type: gate
    message: "Approve the specification?"
    options: [approve, reject]
    on_reject: retry
    verdict_input: spec_verdict
```

Supply a verdict when resuming:

```bash
specify workflow resume <run_id> --input spec_verdict=approve
```

For `on_reject: retry`, a bound reject verdict is consumed before the gate
pauses: the named stored input is reset to `""`. A later resume therefore
prompts or pauses again until another verdict is supplied. Approve, abort, and
skip outcomes leave the input unchanged.

Because of that reset, a verdict input used with `on_reject: retry` must accept
`""`. If it declares an `enum`, include the empty string — otherwise the reset
value violates the input's own `enum` and the run can no longer be resumed with
any input. `specify workflow add` reports this as a validation error.

```yaml
inputs:
  spec_verdict:
    type: string
    enum: ["", approve, reject]
    default: ""
```

## If/Then/Else Steps

Conditional branching based on an expression:

```yaml
- id: check-scope
  type: if
  condition: "{{ inputs.scope == 'full' }}"
  then:
    - id: full-plan
      command: speckit.plan
  else:
    - id: quick-plan
      command: speckit.plan
      options:
        quick: true
```

## Switch Steps

Multi-branch dispatch on an expression value:

```yaml
- id: route
  type: switch
  expression: "{{ steps.review.output.choice }}"
  cases:
    approve:
      - id: plan
        command: speckit.plan
    reject:
      - id: log
        type: shell
        run: "echo 'Rejected'"
  default:
    - id: fallback
      type: gate
      message: "Unexpected choice"
```

## While Loop Steps

Repeat steps while a condition is truthy:

```yaml
- id: retry
  type: while
  condition: "{{ steps.run-tests.output.exit_code != 0 }}"
  max_iterations: 5
  steps:
    - id: fix
      command: speckit.implement
```

## Do-While Loop Steps

Execute steps at least once, then repeat while condition holds:

```yaml
- id: refine
  type: do-while
  condition: "{{ steps.review.output.choice == 'edit' }}"
  max_iterations: 3
  steps:
    - id: revise
      command: speckit.specify
```

## Fan-Out Steps

Dispatch a step template for each item in a collection. The default
`max_concurrency: 1` is sequential; higher values run items concurrently,
with independent item contexts and ordered results:

```yaml
- id: parallel-impl
  type: fan-out
  items: "{{ steps.tasks.output.task_list }}"
  max_concurrency: 3
  step:
    id: impl
    command: speckit.implement
```

## Fan-In Steps

Aggregate results from fan-out steps:

```yaml
- id: collect
  type: fan-in
  wait_for: [parallel-impl]
  output: {}
```

`wait_for` references declared step IDs. For a fan-out, use the fan-out step's
own `id` (`parallel-impl` above); its ordered item results are available as
`steps.<fan-out-id>.output.results`. Generated item aliases such as
`fan:template:0` are reporting-only and are not valid `wait_for` targets.

## Workflow composition

A `workflow` step executes an installed, enabled workflow in the current project
as a private scope of the same run. Targets can be literal IDs or expressions;
the resolved string must match the ID exactly, including case and whitespace.

```yaml
inputs:
  target: {type: string, required: true}
  report: {type: string, required: true}
steps:
  - id: investigate
    type: workflow
    workflow: "{{ inputs.target }}"
    input:
      report: "{{ inputs.report }}"
```

The included workflow sees only declared inputs passed through `input` and its
own step results. It does not inherit the caller's `inputs`, step results,
fan-out `item`/`fan_in` values, or workflow defaults. Unknown input names,
missing required values, and invalid types/enums fail the call. Existing child
defaults and `integration: auto` resolution apply. Values cross back only
through explicit declarations:

```yaml
outputs:
  report:
    value: "{{ steps.analyze.output.stdout }}"
```

The caller reads `{{ steps.investigate.output.report }}`. Output includes
`workflow` and `status`; failures include `error` when the failed operation
reported one, and an abort includes `aborted: true`. These names and
`integration`, `model`, `options`, and `input` are reserved. Returned values
must be JSON-safe. Private inputs, step records, and logs are not part of the
return value. No separate child run is created.

`continue_on_error: true` on a workflow call handles a returned child failure
and call-boundary contract failures, such as an unavailable target, invalid
mapped input, cycle, depth limit, or invalid declared output. It does not catch
step exceptions, expression errors (including `from_json` errors in `input:` or
`outputs:`), interruptions, or checkpoint failures; those propagate exactly as
they do at the root. An unavailable step implementation is terminal where the
step occurs; at a workflow call it is a reported child failure, whether it is
detected while binding the target or later. Pauses and explicit aborts always
stop execution.

Nested composition is allowed, but repeated workflow IDs on the active call
path are cycles. Diamonds are allowed. The maximum included depth is 16, with
the root at depth zero.

## Calling a Child Gate

Only root-declared inputs can be supplied to `workflow resume --input`. Map a
root input through each workflow boundary when a child gate uses it as a
`verdict_input`:

```yaml
# Parent workflow
inputs:
  approval:
    type: string
    default: ""
steps:
  - id: review-release
    type: workflow
    workflow: release-notes
    input:
      approval: "{{ inputs.approval }}"
```

```yaml
# Installed release-notes workflow
inputs:
  approval:
    type: string
    default: ""
steps:
  - id: review
    type: gate
    message: "Approve the release notes?"
    options: [approve, reject]
    verdict_input: approval
```

The initial run pauses if `approval` is empty. Its structured status identifies
the nested gate and its enclosing call with `gate.scope_path`. Resume the root
run, not the child, to continue it:

```bash
specify workflow status <run-id> --json
specify workflow resume <run-id> --input approval=approve
```

A gate with `verdict_input` is not supported inside a fan-out item, including
through one or more workflow calls. The `inside_fan_out` runtime condition is
preserved across workflow boundaries.

## Defaults and Errors at the Call Boundary

Parent `integration`, `model`, `options`, `reasoning_effort`, and
`context_size` defaults apply only to steps in the parent workflow. A child
uses its own defaults or automatic resolution. To make a value common to both,
declare it as a child input and map it explicitly.
The call result intentionally has an empty `input` field and does not expose
the child's private inputs, step records, or logs.

An initial binding or output-finalization contract failure can be handled with
`continue_on_error`. A failure while rebinding an incomplete call during
`workflow resume --input` is different: it propagates. For a previously bound
call, resume discards the prior `result`, `outcome`, and `error` while
preserving its binding and child subtree, so it can be retried with corrected
root inputs. A call whose initial binding failed returns to `ready` and retries
target resolution and binding.

## See also

- [Workflow step overview](overview.md)
- [Workflow YAML and execution semantics](../workflows/api.md)
- [Expressions](../workflows/expressions.md)
- [Overlays and workflow slots](../workflows/overlays.md)
- [Developing custom step packages](developing.md#custom-step-packages)
- [Step management CLI](cli.md#step-management)
