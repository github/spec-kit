# Workflow Steps

Workflow steps provide reusable units of executable behavior. A workflow selects
a step type with `type:` and supplies its configuration; the workflow engine
owns sequencing, execution state, checkpoints, and resume.

## Built-in and custom types

Built-in types ship with Spec Kit. They invoke commands and prompts, run shell
tasks, pause at review gates, and express branching, loops, and fan-out. Omitting
`type` selects `command`. A `workflow` call composes another installed workflow
within the same run.

Custom step packages add types implemented in Python. Each package provides one
type key and is installed separately from the workflows that use it. Use a
custom type when reusable executable behavior does not fit an existing type;
use a workflow when composing existing steps is sufficient.

## Before installing a custom step

Review the source, dependencies, and side effects before installation and use.
Installation validates and copies a package without importing its Python.
Later `specify workflow add`, `run`, and `resume` load installed step packages,
executing import-time code with your privileges even before a particular step
is selected for execution.

Community catalog listings are discovery metadata, not code audits,
endorsements, or installation permission. Inspect active sources with
`specify workflow step catalog list`.

## Use a step in a workflow

After reviewing and installing a custom type, select its exact type key:

```yaml
steps:
  - id: check
    type: my-step
```

Additional configuration and outputs depend on the type. The workflow engine
runs the step; there is no separate step-run command.

## See also

- [Built-in step types](types.md)
- [Step management CLI](cli.md)
- [Developing custom steps](developing.md)
- [Python API reference](api.md)
- [Step catalogs](catalogs.md)
- [Publishing steps](publishing.md)
- [Community workflow step types](../community/workflow-steps.md)
- [Workflow composition and execution](../workflows/overview.md)
