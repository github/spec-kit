# Workflows

Workflows are multi-step, resumable automation pipelines defined in YAML. They orchestrate Spec Kit commands across integrations, evaluate control flow, and pause at human review gates — enabling end-to-end Spec-Driven Development cycles without manual step-by-step invocation.

## How It Works

A workflow definition declares a sequence of steps. The engine executes them in order, dispatching commands to AI integrations, running shell commands, evaluating conditions for branching, and pausing at gates for human review. State is persisted after each step, so workflows can be resumed after interruption.

```yaml
steps:
  - id: specify
    command: speckit.specify
    input:
      args: "{{ inputs.spec }}"

  - id: review
    type: gate
    message: "Review the spec before planning."
    options: [approve, reject]
    on_reject: abort

  - id: plan
    command: speckit.plan
```

For detailed architecture and internals, see [ARCHITECTURE.md](ARCHITECTURE.md).

## Quick Start

```bash
# Search available workflows
specify workflow search

# Install the built-in SDD workflow
specify workflow add speckit

# Or run directly from a local YAML file
specify workflow run ./workflow.yml --input spec="Build a user authentication system with OAuth support"

# Run an installed workflow with inputs
specify workflow run speckit --input spec="Build a user authentication system with OAuth support"

# Check run status
specify workflow status

# Resume after a gate pause
specify workflow resume <run_id>

# Get detailed workflow info
specify workflow info speckit

# Remove a workflow
specify workflow remove speckit
```

## Running Workflows

### From an Installed Workflow

```bash
specify workflow add speckit
specify workflow run speckit --input spec="Build a user authentication system with OAuth support"
```

### From a Local YAML File

```bash
specify workflow run ./my-workflow.yml --input spec="Build a user authentication system with OAuth support"
```

### Multiple Inputs

```bash
specify workflow run speckit \
  --input spec="Build a user authentication system with OAuth support" \
  --input scope="backend-only"
```

## Step Types

Workflows support 11 built-in step types:

### Command Steps (default)

Invoke an installed Spec Kit command by name via the integration CLI:

```yaml
- id: specify
  command: speckit.specify
  input:
    args: "{{ inputs.spec }}"
  integration: claude        # Optional: override workflow default
  model: "claude-sonnet-4-20250514"   # Optional: override model
```

### Prompt Steps

Send an arbitrary inline prompt to an integration CLI (no command file needed):

```yaml
- id: security-review
  type: prompt
  prompt: "Review {{ inputs.file }} for security vulnerabilities"
  integration: claude
```

### Shell Steps

Run a shell command and capture output:

```yaml
- id: run-tests
  type: shell
  run: "cd {{ inputs.project_dir }} && npm test"
  timeout: 1800   # Optional: max seconds before the command is killed (default 300)
```

`timeout` is the maximum time in seconds the command may run before it is
killed and the step fails; it must be a positive number and defaults to
`300` (five minutes) when omitted. Raise it for long-running gates such as
full builds, linter aggregators, or integration-test targets.

### Init Steps

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
  script: sh                 # Optional: sh or ps
  force: true                # Optional: required when target directory already exists
  preset: healthcare-compliance   # Optional preset ID
```

### Gate Steps

Pause for human review. The workflow resumes when `specify workflow resume` is called:

```yaml
- id: review-spec
  type: gate
  message: "Review the generated spec before planning."
  options: [approve, edit, reject]
  on_reject: abort
```

### If/Then/Else Steps

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

### Switch Steps

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

### While Loop Steps

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

### Do-While Loop Steps

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

### Fan-Out Steps

Dispatch a step template for each item in a collection (sequential):

```yaml
- id: parallel-impl
  type: fan-out
  items: "{{ steps.tasks.output.task_list }}"
  max_concurrency: 3
  step:
    id: impl
    command: speckit.implement
```

### Fan-In Steps

Aggregate results from fan-out steps:

```yaml
- id: collect
  type: fan-in
  wait_for: [parallel-impl]
  output: {}
```

## Error Handling

By default, any step that returns `StepResult(status=StepStatus.FAILED, ...)`
at runtime halts the entire run — most commonly a `shell` or
`command` step exiting non-zero. Set `continue_on_error: true` on
a step to record its result and continue to the next sibling step
instead. When the failure was a non-zero exit, the exit code
remains available on `steps.<id>.output.exit_code` so a downstream
`if` or `switch` can branch on it (or a `gate` can surface it to
the operator via `{{ }}` interpolation in `message`):

```yaml
- id: heavy-thing
  type: command
  integration: claude
  command: speckit.heavy-thing
  continue_on_error: true

- id: check-result
  type: if
  condition: "{{ steps.heavy-thing.output.exit_code != 0 }}"
  then:
    - id: review
      type: gate
      message: "Step failed (exit {{ steps.heavy-thing.output.exit_code }}). Approve to run the recovery path, or reject to leave the failure recorded and move on."
      on_reject: skip
    - id: recover
      type: if
      condition: "{{ steps.review.output.choice == 'approve' }}"
      then:
        - id: rerun
          command: speckit.recovery
  else:
    - id: next-thing
      command: speckit.next-thing
```

A few things worth knowing about that example:

- Both gate options (`approve`, `reject`) return `StepStatus.COMPLETED`;
  `on_reject: skip` controls only whether the engine aborts on reject
  (it doesn't, with `skip`) — it does **not** auto-skip subsequent
  sibling steps in the `then:` list. Downstream branching is the
  workflow author's responsibility: read
  `{{ steps.<gate-id>.output.choice }}` in a follow-up `if`, `switch`,
  or expression, as the `recover` step above does.
- `on_reject` has three values: `abort` (default — reject → `StepStatus.FAILED`
  with `output.aborted = True`, halts the run), `skip` (reject →
  `StepStatus.COMPLETED`, author handles branching as shown), and `retry`
  (reject → `StepStatus.PAUSED` so the next `specify workflow resume` re-runs
  the gate).
- Gates do not automatically re-run the failed step. To express a
  retry path, either define custom gate options and branch on the
  choice downstream, or wrap the failing step in your own loop.

**Notes:**

- The field must be a literal boolean (`true` / `false`); coerced
  strings like `"true"` are rejected at validation time.
- **Scope: returned failures only.** The flag applies to step results
  with `status=StepStatus.FAILED`. Unhandled exceptions raised out of a step's
  `execute()` method are caught one level up by `WorkflowEngine.execute()`,
  logged as `workflow_failed`, and abort the run regardless of
  `continue_on_error`. If a step author wants the flag to cover an
  exceptional path, the step must catch the exception internally and
  return `StepResult(status=StepStatus.FAILED, ...)` with the failure encoded in
  `output` (e.g. `exit_code`, `stderr`, or a custom field).
- Gate aborts (`on_reject: abort` chosen by the operator) always halt
  the run — `continue_on_error` does not override them. The flag is
  for transient/expected step failures, not for overriding deliberate
  operator decisions.
- Structural validation runs up-front: `specify workflow run` rejects
  invalid workflow definitions before the run is created, so
  validation failures never reach this code path.
- When the flag is omitted, behaviour is byte-equivalent to before
  this feature.

## Expressions

Workflow definitions use `{{ expression }}` syntax for dynamic values:

```yaml
# Access inputs
args: "{{ inputs.spec }}"

# Access previous step outputs
args: "{{ steps.specify.output.file }}"

# Comparisons
condition: "{{ steps.run-tests.output.exit_code != 0 }}"

# Filters
message: "{{ status | default('pending') }}"
```

Supported filters: `default`, `join`, `contains`, `map`, `from_json`.

### Runtime Context

`{{ context.* }}` exposes engine-managed runtime metadata for the
current run:

| Variable | Description |
|----------|-------------|
| `context.run_id` | The current workflow run id (the same value Spec Kit prints as `Run ID:` at the end of `workflow run`). Auto-generated runs are 8-character hex from `uuid4`; operator-supplied ids may be any alphanumeric string with hyphens or underscores. Empty string outside a run context. |
| `context.workflow_dir` | The resolved absolute path to the directory containing the workflow source file. For file-loaded workflows this is the parent directory of the YAML file; for installed-by-ID workflows it is the absolute path to the installation directory (e.g. `<project>/.specify/workflows/<id>/`); for string-loaded workflows it is an empty string. On resume the original source directory is preserved from the first execution. |

```yaml
# Stamp telemetry events with the run id for cross-system join.
- id: emit-event
  type: shell
  run: 'echo "{\"run_id\":\"{{ context.run_id }}\",\"event\":\"started\"}" >> events.jsonl'

# Per-run scratch directory.
- id: prep-scratch
  type: shell
  run: 'mkdir -p /tmp/run-{{ context.run_id }}'

# Pass run id into a command for artifact metadata.
- id: tag-artifact
  command: speckit.specify
  input:
    args: "{{ context.run_id }}"

# Reference a sibling file shipped alongside the workflow definition.
- id: apply-config
  type: shell
  run: 'cp "{{ context.workflow_dir }}/defaults.yml" ./config.yml'
```

## Input Types

Workflow inputs are type-checked and coerced from CLI string values:

```yaml
inputs:
  spec:
    type: string
    required: true
    prompt: "Describe what you want to build"
  task_count:
    type: number
    default: 5
  dry_run:
    type: boolean
    default: false
  scope:
    type: string
    default: "full"
    enum: ["full", "backend-only", "frontend-only"]
```

| Type | Accepts | Example |
|------|---------|---------|
| `string` | Any string | `"user-auth"` |
| `number` | Numeric strings → int/float | `"42"` → `42` |
| `boolean` | `true`/`1`/`yes` → `True`, `false`/`0`/`no` → `False` | `"true"` → `True` |

## State and Resume

Every workflow run persists state to `.specify/workflows/runs/<run_id>/`:

```bash
# List all runs with status
specify workflow status

# Check a specific run
specify workflow status <run_id>

# Resume a paused run (after approving a gate)
specify workflow resume <run_id>

# Resume a failed run (retries from the failed step)
specify workflow resume <run_id>
```

Run states: `created` → `running` → `completed` | `paused` | `failed` | `aborted`

## Catalog Management

Workflows are discovered through catalogs. By default, Spec Kit uses the official and community catalogs:

> [!NOTE]
> Community workflows are independently created and maintained by their respective authors. GitHub and the Spec Kit maintainers may review pull requests that add entries to the community catalog for formatting and structure, but they do **not review, audit, endorse, or support the workflow definitions themselves**. Review workflow source before installation and use at your own discretion.

```bash
# List active catalogs
specify workflow catalog list

# Add a custom catalog
specify workflow catalog add https://example.com/catalog.json --name my-org

# Remove a catalog
specify workflow catalog remove <index>
```

## Creating a Workflow

1. Create a `workflow.yml` following the schema above
2. Test locally with `specify workflow run ./workflow.yml --input key=value`
3. Verify with `specify workflow info ./workflow.yml`
4. See [PUBLISHING.md](PUBLISHING.md) to submit to the catalog

## Environment Variables

| Variable | Description |
|----------|-------------|
| `SPECKIT_WORKFLOW_CATALOG_URL` | Override the catalog URL (replaces all defaults) |
| `SPECKIT_WORKFLOW_DIR` | Set automatically for shell steps; contains the resolved absolute path to the workflow source directory (same value as `{{ context.workflow_dir }}`). Not set when the workflow has no source path (string-loaded workflows). |

## Configuration Files

| File | Scope | Description |
|------|-------|-------------|
| `.specify/workflow-catalogs.yml` | Project | Custom catalog stack for this project |
| `~/.specify/workflow-catalogs.yml` | User | Custom catalog stack for all projects |

## Repository Layout

```
workflows/
├── ARCHITECTURE.md                         # Internal architecture documentation
├── PUBLISHING.md                           # Guide for submitting workflows to the catalog
├── README.md                               # This file
├── catalog.json                            # Official workflow catalog
├── catalog.community.json                  # Community workflow catalog
└── speckit/                                # Built-in SDD cycle workflow
    └── workflow.yml
```
