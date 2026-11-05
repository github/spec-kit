# Developing workflow steps

Custom step types are installed with `specify workflow step`. A step is a
directory package containing metadata and executable Python.

## Custom step packages

```text
my-step/
├── step.yml        # required, at the package root
├── __init__.py     # required, at the package root
└── helpers.py      # optional nested modules and data files
```

`step.yml` declares the step's identity. `step.type_key` must exactly match the
`<step_id>` passed on the command line — the ID is never inferred from package
content:

```yaml
step:
  type_key: my-step
  name: My Step
  version: 0.1.0
  author: you
  description: What this step does
```

`__init__.py` must define a `StepBase` subclass whose `type_key` matches:

```python
from specify_cli.workflows.base import StepBase, StepResult


class MyStep(StepBase):
    type_key = "my-step"

    def execute(self, config, context):
        return StepResult(output={"ok": True})
```

### Package validation

Every source is validated identically before anything is committed:

- `step.yml` and `__init__.py` must be regular, non-symlink files at the package
  root.
- The package tree is copied recursively (relative imports, nested helper
  modules, and data files are supported). A symlinked package root, any
  descendant symlink, and any filesystem object that is not a regular file or
  directory are rejected.
- `.git`, `__pycache__`, and `.DS_Store` entries are skipped without being
  inspected: they are not copied, excluded directories are not entered, and
  they do not count toward any limit.
- The installed-package policy permits at most **512 retained entries** (files
  and directories combined), at most **32 levels** of directory nesting, and
  **50 MiB** of retained content.
- Archive URLs also pass transport/extraction safety limits before package
  validation: at most 512 archive entries, 50 MiB downloaded or extracted, and
  10 MiB per archive member. Catalog files have a 50 MiB per-response bound.
- Installation validates and copies the package but does **not** import or
  execute `__init__.py`. Installed custom step modules are loaded during startup
  of `workflow add`, `workflow run`, and `workflow resume`, before any particular
  custom step necessarily executes.

> **Security note:** Loading a custom step runs its Python with **your**
> privileges. Only install and retain step packages from sources you trust.

## Implement a custom step

Subclass `StepBase`, give the package and implementation the same `type_key`, and return explicit status, outputs, and errors. Override `validate()` and guard invalid configuration in `execute()` too: execution does not automatically call the validator.

The registry shares a single instance of each type. Concurrent fan-out can call it from several threads, so keep execution stateless and thread-safe; store per-run data in `config` and `context`, not `self`. Let the engine own checkpoints and lifecycle transitions.

Use `specify workflow step add my-step --dev ./my-step` for local iteration and `--force` after editing. See the [step installation reference](cli.md#step-management) for source validation and replacement failure behavior.

## Test locally

Test valid and invalid configuration, returned statuses, outputs, and errors.
Exercise the type through a small workflow, including relevant resume,
nested-step, and concurrent execution paths. Use a disposable initialized
project when the package or workflow can produce side effects.

## Bundle-local limitation

A bundle's `provides.steps` still resolves only through the active step
catalogs. Bundle-local `steps/<id>/` payloads and relative
`provides.steps[].source` overrides are **not** resolved in this release, so
such steps are not installable offline. See the [bundle offline limits](../bundles/cli.md#offline-limits).

## See also

- [Step overview](overview.md)
- [Python API and registry](api.md)
- [Step installation CLI](cli.md)
- [Publishing steps](publishing.md)
- [Community step submission](../community/workflow-steps.md)
- [Workflow execution and resume](../workflows/api.md#execution-model)
- [Contributor step design](https://github.com/github/spec-kit/blob/main/design/workflow-step.md)
