# Workflow step API reference

This reference describes the supported Python contract for both built-in
(embedded) workflow steps and installed custom step types. They implement the
same `StepBase` methods and use the same `StepContext`, `StepResult`, and
`StepStatus` types. Workflow definitions and engine-owned execution semantics
remain in the [workflow API reference](../workflows/api.md).

## Delivery routes

Built-in steps ship with Specify CLI and need no separately installed
`step.yml` package. Source registration is an internal contributor concern,
not a step implementation API.

Installed custom steps use the same execution contract, plus the package
metadata, matching type identity, and installation requirements documented in
[Developing steps](developing.md). Neither delivery route authorizes a step
to mutate the engine's registry or checkpoint state.

## Step Python API

Import `StepBase`, `StepContext`, `StepResult`, and `StepStatus` from `specify_cli.workflows.base`.

| API | Contract |
| --- | --- |
| `StepBase.type_key` | Matches YAML `type`; installed custom steps must also match their package identity |
| `validate(config) -> list[str]` | Validation errors; empty means valid |
| `execute(config, context) -> StepResult` | Stateless, thread-safe execution |
| `can_resume(state) -> bool` | Base method returning true; the current engine does not call it as a resume gate |
| `StepContext` | Inputs, previous results, defaults, paths, run ID, fan-out item and resume context |
| `StepResult.status` | `pending`, `running`, `completed`, `failed`, `skipped`, or `paused`; default `completed` |
| `StepResult.output` | Output mapping, default empty |
| `StepResult.next_steps` | Nested expansion, default empty |
| `StepResult.error` | Error message for failure, otherwise null |

`config` is the step's YAML mapping. The base `validate()` checks for an `id`;
an override should preserve that check with `super().validate(config)` and add
its own errors. Execution does not automatically call the validator, so guard
invalid configuration in `execute()` too.

### StepContext fields

| Field | Type | Meaning |
| --- | --- | --- |
| `inputs` | `dict[str, Any]` | Resolved workflow inputs |
| `steps` | `dict[str, dict[str, Any]]` | Previous step result records, keyed by authored step ID; outputs are under each record's `output` |
| `item` | `Any` | Current fan-out item, otherwise `None` |
| `inside_fan_out` | `bool` | Whether execution is inside a fan-out template |
| `fan_in` | `dict[str, Any]` | Aggregated fan-in context |
| `default_integration` | `str \| None` | Workflow integration default |
| `default_model` | `str \| None` | Workflow model default |
| `default_options` | `dict[str, Any]` | Workflow dispatch defaults |
| `project_root` | `str \| None` | Project directory |
| `run_id` | `str \| None` | Current run ID |
| `is_resume` | `bool` | Whether this execution is a resume attempt |
| `workflow_dir` | `str \| None` | Source directory of the current workflow definition |

Mappings default to empty dictionaries, boolean flags to false, and optional
paths/identifiers to `None`. Paths are strings, not `Path` objects. Use
`workflow_dir` for resources relative to the workflow and `project_root` for
project-local operations; they need not be the same directory.

Treat inputs and previous result records as context, not as a way to rewrite
run state. Return outputs through `StepResult`. Fan-out items have independent
result contexts; workflow calls have their own inputs and defaults.

### Results and failures

Use `StepStatus` values rather than arbitrary status strings. A normal
successful step returns `COMPLETED`; `SKIPPED` records a skipped step,
`PAUSED` requests a pause, and `FAILED` records an error. `PENDING` and
`RUNNING` also exist in the enum, but returning either does not leave the
occurrence pending or running: the engine treats it as completed. Return
`PAUSED` to stop for a later resume, not a progress status.

Return serializable output values, since the engine persists outputs and
exposes them to later `{{ steps.<id>.output.* }}` expressions. `next_steps`
is a list of nested step-definition mappings for a control-flow expansion,
not a list of step instances.

For expected failures, return `StepResult(status=StepStatus.FAILED,
error=...)`, with relevant diagnostics in `output`. This lets the engine
apply `continue_on_error`. An unhandled exception stops the run regardless of
that flag; do not turn invalid configuration or failed operations into a
successful default.

```python
from specify_cli.workflows.base import StepBase, StepContext, StepResult, StepStatus


class GreetingStep(StepBase):
    type_key = "greeting"

    def validate(self, config: dict) -> list[str]:
        errors = super().validate(config)
        if not isinstance(config.get("name"), str) or not config["name"].strip():
            errors.append("'name' must be a non-empty string.")
        return errors

    def execute(self, config: dict, context: StepContext) -> StepResult:
        errors = self.validate(config)
        if errors:
            return StepResult(
                status=StepStatus.FAILED,
                error="; ".join(errors),
            )
        return StepResult(output={"message": f"Hello, {config['name']}!"})
```

## Execution and resume contract

A step instance may be called concurrently. Keep execution stateless and
thread-safe: derive per-run values from `config` and `context`, not mutable
attributes on `self`.

The engine owns checkpoints and lifecycle transitions. Completed occurrences
are replayed on resume without calling their implementations again. Selected
branches and nested expansions remain fixed; unfinished occurrences continue
under the [workflow resume rules](../workflows/api.md#execution-identity-and-resume).
Do not use `can_resume()` as an authorization or safety check; it is not an
enforced engine gate.

A side effect performed before its completion checkpoint can repeat after an
interruption. Make external operations idempotent or otherwise safe to retry;
execution is not an exactly-once guarantee. Workflow snapshots freeze
definitions, not step package code or external resources.

## Installed type discovery

Each installed step records only the *kind* of its source — `catalog`
(optionally with the catalog name), `local`, or `url`. Local paths and source
URLs are never persisted. Use `specify workflow step list` and
`specify workflow step info <id>` to discover installed types and provenance;
do not mutate the host's internal Python registry.

## State and Configuration Locations

| Component | Location | Format | Purpose |
| --- | --- | --- | --- |
| Custom steps | `.specify/workflows/steps/{id}/` | Package | Installed step manifest and Python |
| Step registry | `.specify/workflows/steps/step-registry.json` | JSON | Installed step metadata |
| Step catalog cache | `.specify/workflows/steps/.cache/*.json` | JSON | Cached step catalog entries |
| Project step catalogs | `.specify/step-catalogs.yml` | YAML | Project-level step sources |
| User step catalogs | `~/.specify/step-catalogs.yml` | YAML | User-level step sources |

## See also

- [Developing custom steps](developing.md)
- [Built-in step configuration](types.md)
- [Step CLI](cli.md)
- [Step catalogs](catalogs.md)
- [Workflow YAML and execution semantics](../workflows/api.md)
