# Workflow Step Design

A workflow step type defines what a `type:` in workflow YAML does. This is an
extension point of the workflow engine, distinct from an agent integration:
integrations dispatch work to an agent; steps validate and execute workflow
behavior. For the overall engine, see
[Workflow System Architecture](../workflows/ARCHITECTURE.md); for YAML usage,
see [Workflows](../docs/reference/workflows.md).

## Delivery and registration

| Route | Source | Registration |
|---|---|---|
| Built-in | `src/specify_cli/workflows/steps/<package>/__init__.py` | Explicit import and `_register_step()` in `src/specify_cli/workflows/__init__.py` |
| Installed | Package under `.specify/workflows/steps/<id>/`, containing `step.yml` and `__init__.py` | `load_custom_steps(project_root)` loads a matching `StepBase` subclass at workflow run/resume |

`STEP_REGISTRY` maps each `type_key` to a single step instance. Built-in keys
are snapshotted in `BUILTIN_STEP_TYPES` before project steps are loaded; do not
infer built-in status from the mutable registry. Installed packages can be
found through step catalogs and added with `specify workflow step add <id>`.
The default community catalog is discovery-only, not an install or trust
endorsement. Review external step code before installing it: loading a package
imports and executes its Python module.

## Step contract

Subclass `StepBase` from `src/specify_cli/workflows/base.py`, set `type_key`
to the workflow YAML `type`, and implement
`execute(config: dict[str, Any], context: StepContext) -> StepResult`.
Override `validate(config)` for step-specific errors; the base validator
requires an `id`. Omitting `type` in YAML selects the built-in `command` step.

`StepContext` supplies inputs, previous step results, workflow defaults, run
and project paths, and iteration/resume context. Return a `StepResult` with a
`StepStatus`, an output mapping, and an error message on failure. The engine
records the result for later `{{ steps.<id>.output.* }}` expressions and
persists run state. `PAUSED` stops for resume; `FAILED` normally stops the run
unless `continue_on_error: true` is set (an explicit abort always stops).
`next_steps` supplies nested steps for control flow.

The engine calls `validate()` during workflow validation but does not
automatically validate a definition passed to `execute()`. Guard invalid
configurations in `execute()` too, returning a failed result rather than a
successful default or an unhandled exception.

New runs persist an execution tree. Resume replays completed occurrences into
their expression contexts without calling their implementations, then continues
at the unfinished occurrence. Selected branches, custom expansions, loop
iterations, fan-out items, and bound workflow definitions therefore remain
frozen across resume. This is intentionally forward-only: new resume inputs do
not reinterpret or repeat completed work. Legacy states enter the tree once
through their saved top-level index.

Fan-out items have independent expression contexts. Their internal results do
not enter the shared parent context; the parent receives the qualified item
result and the fan-out step's ordered `output.results`. A side effect performed
before its completion checkpoint can still repeat after an interruption, so the
guarantee is at-least-once rather than exactly-once.

The registry holds one shared instance per type. Concurrent `fan-out` can
invoke that instance from multiple threads: keep execution stateless and
thread-safe, with per-run data in `config` and `context`, not on `self`.

## Adding a step type

1. Implement the step in its own `steps/<package>/` subpackage and register
   it explicitly with a unique `type_key`. For an external package, provide
   `step.yml` with a matching `step.type_key` and a matching subclass in
   `__init__.py`; catalog discovery alone does not register the code.
2. Test valid and invalid configurations, status/output/error behavior, and
   resume or nested/concurrent execution when relevant. Registry and engine
   coverage lives in `tests/test_workflows.py`; focused step suites may live
   under `tests/workflows/`.
3. Update the [workflow reference](../docs/reference/workflows.md) when a
   built-in step changes the YAML users can write. Keep agent-specific CLI
   dispatch in integrations rather than duplicating it in step types.
