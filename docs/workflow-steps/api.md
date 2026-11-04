# Workflow step API reference

This reference describes the Python extension contract and the registry that
provides built-in and installed types. Workflow definitions and engine-owned
execution semantics remain in the workflow API reference.

## Custom step Python API

Import `StepBase`, `StepContext`, `StepResult`, and `StepStatus` from `specify_cli.workflows.base`.

| API | Contract |
| --- | --- |
| `StepBase.type_key` | Matches YAML `type` and installed package identity |
| `validate(config) -> list[str]` | Validation errors; empty means valid |
| `execute(config, context) -> StepResult` | Stateless, thread-safe execution |
| `can_resume(state) -> bool` | Optional resume capability hook; base implementation returns true |
| `StepContext` | Inputs, previous results, defaults, paths, run ID, fan-out item and resume context |
| `StepResult.status` | `pending`, `running`, `completed`, `failed`, `skipped`, or `paused`; default `completed` |
| `StepResult.output` | Output mapping, default empty |
| `StepResult.next_steps` | Nested expansion, default empty |
| `StepResult.error` | Error message for failure, otherwise null |

Implementations must guard invalid configuration during execution as well as validation. The engine persists results and controls lifecycle state; steps do not own checkpoint transitions.

## Step Registry

Built-in step types register into `STEP_REGISTRY` via
`_register_builtin_steps()` in `src/specify_cli/workflows/__init__.py`.
Installed packages are loaded through `load_custom_steps(project_root)`.
The registry maps `type_key` strings to shared step instances:

```python
STEP_REGISTRY: dict[str, StepBase]  # e.g., {"command": CommandStep(), "gate": GateStep(), ...}
```

Built-in registration is explicit: each class is imported and instantiated.
Installed packages must declare one matching `type_key` and a `StepBase`
subclass. `BUILTIN_STEP_TYPES` snapshots built-in keys before custom loading;
do not infer built-in status from the mutable registry.

## Registry provenance

Each installed step records only the *kind* of its source — `catalog`
(optionally with the catalog name), `local`, or `url`. Local paths and source
URLs are never persisted. `specify workflow step info <id>` shows the source.

## State and Configuration Locations

| Component | Location | Format | Purpose |
| --- | --- | --- | --- |
| Custom steps | `.specify/workflows/steps/{id}/` | Package | Installed step manifest and Python |
| Step registry | `.specify/workflows/steps/step-registry.json` | JSON | Installed step metadata |
| Step catalog cache | `.specify/workflows/steps/.cache/*.json` | JSON | Cached step catalog entries |
| Project step catalogs | `.specify/step-catalogs.yml` | YAML | Project-level step sources |
| User step catalogs | `~/.specify/step-catalogs.yml` | YAML | User-level step sources |

## Implementation map

| Source under `src/specify_cli/workflows/` | Responsibility |
| --- | --- |
| `__init__.py` | Explicit step registry and group registration |
| `base.py` | Step and run contracts |
| `step/<package>/` | Built-in implementations |
| `step/installer.py`, `step/catalog/` | Custom-step packages and catalogs |

## See also

- [Developing custom steps](developing.md)
- [Built-in step configuration](types.md)
- [Step CLI](cli.md)
- [Step catalogs](catalogs.md)
- [Workflow YAML and execution semantics](../workflows/api.md)
- [Contributor step design](https://github.com/github/spec-kit/blob/main/design/workflow-step.md)
