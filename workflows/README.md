# Workflows

Workflows are multi-step, resumable automation pipelines defined in YAML. They orchestrate Spec Kit commands across integrations, evaluate control flow, and pause at human review gates — enabling end-to-end Spec-Driven Development cycles without manual step-by-step invocation.

## How It Works

A workflow definition declares a sequence of steps. The engine executes them in order, dispatching commands to AI integrations, running shell commands, evaluating conditions for branching, and pausing at gates for human review. State is persisted after each step, so workflows can be resumed after interruption.

```yaml
steps:
  - id: specify
    command: speckit.specify
    input:
      args: "{{ inputs.feature_name }}"

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

# Install a workflow from the catalog
specify workflow add sdd-pipeline

# Run a workflow with inputs
specify workflow run sdd-pipeline --input feature_name="user-auth"

# Check run status
specify workflow status

# Resume after a gate pause
specify workflow resume <run_id>

# Get detailed workflow info
specify workflow info sdd-pipeline

# Remove a workflow
specify workflow remove sdd-pipeline
```

## Running Workflows

### From an Installed Workflow

```bash
specify workflow add sdd-pipeline
specify workflow run sdd-pipeline --input feature_name="user-auth"
```

### From a Local YAML File

```bash
specify workflow run ./my-workflow.yml --input feature_name="user-auth"
```

### Multiple Inputs

```bash
specify workflow run sdd-pipeline \
  --input feature_name="user-auth" \
  --input scope="backend-only"
```

## Step Types

Workflows support 9 built-in step types:

### Command Steps (default)

Dispatch a Spec Kit command to an AI integration:

```yaml
- id: specify
  command: speckit.specify
  input:
    args: "{{ inputs.feature_name }}"
  integration: claude        # Optional: override workflow default
  model: "claude-sonnet-4-20250514"   # Optional: override model
```

### Shell Steps

Run a shell command and capture output:

```yaml
- id: run-tests
  type: shell
  run: "cd {{ inputs.project_dir }} && npm test"
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

Parallel dispatch over a collection:

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

Aggregate results from parallel steps:

```yaml
- id: collect
  type: fan-in
  wait_for: [parallel-impl]
  output: {}
```

## Expressions

Workflow definitions use `{{ expression }}` syntax for dynamic values:

```yaml
# Access inputs
args: "{{ inputs.feature_name }}"

# Access previous step outputs
args: "{{ steps.specify.output.file }}"

# Comparisons
condition: "{{ steps.run-tests.output.exit_code != 0 }}"

# Filters
message: "{{ status | default('pending') }}"
```

Supported filters: `default`, `join`, `contains`, `map`.

## Input Types

Workflow inputs are type-checked and coerced from CLI string values:

```yaml
inputs:
  feature_name:
    type: string
    required: true
    prompt: "Feature name"
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
