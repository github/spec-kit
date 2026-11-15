# Workflow Step Design

A workflow step type defines what a `type:` in workflow YAML does. This is an
extension point of the workflow engine, distinct from an agent integration:
integrations dispatch work to an agent; steps validate and execute workflow
behavior. For the overall engine, see
[Workflow API and execution model](https://github.github.io/spec-kit/workflows/api.html); for YAML usage,
see [Workflows](https://github.github.io/spec-kit/workflows/overview.html).

## Delivery and registration

| Route | Source | Registration |
|---|---|---|
| Built-in | `src/specify_cli/workflows/step/<package>/__init__.py` | Explicit import and `_register_step()` in `src/specify_cli/workflows/__init__.py` |
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

The built-in shell step preserves raw `run` interpolation by default.
Per-step `strict: true` rejects expression markers in `run` during validation
and execution. Its optional `env` mapping evaluates string templates separately,
requires NUL-free string results encodable for the process environment on
POSIX, and overrides only the child environment.
`SPECKIT_WORKFLOW_DIR` remains engine-owned. This prevents workflow expression
values from becoming shell source in strict mode; it is not a sandbox or a
guarantee that an authored script handles environment data safely.
Environment bindings and inherited settings can intentionally affect executable
lookup, module loading, and runtime startup. Strict mode does not filter them;
workflow source review must cover both `run` and `env` and referenced code.

New runs persist an execution tree. Resume replays completed occurrences into
their expression contexts without calling their implementations, then continues
at the unfinished occurrence. Selected branches, custom expansions, loop
iterations, fan-out items, and bound workflow definitions therefore remain
frozen across resume. This is intentionally forward-only: new resume inputs do
not reinterpret or repeat completed work. Legacy states enter the tree once
through their saved top-level index.

The common occurrence runner owns start, checkpoint, replay, and finalization.
Step implementations return results or expansions; they do not manage persisted
lifecycle state. Internal workflow-call and registered-step paths share the
same checked transitions and post-checkpoint notifications. Per-occurrence
activity belongs to the execution tree, never to the shared step instance.

Fan-out items have independent expression contexts. Their internal results do
not enter the shared parent context; the parent receives the qualified item
result and the fan-out step's ordered `output.results`. Fan-out item aliases are
reporting-only; a `fan-in` `wait_for` targets declared step IDs (the fan-out
step's own `id`) and reads its ordered `output.results`, never a generated item
alias. A side effect performed
before its completion checkpoint can still repeat after an interruption, so the
guarantee is at-least-once rather than exactly-once.

The registry holds one shared instance per type. Concurrent `fan-out` can
invoke that instance from multiple threads: keep execution stateless and
thread-safe, with per-run data in `config` and `context`, not on `self`.

## Workflow functions

Workflow functions are a separate project-installed extension point for
expression pipe filters. A package under
`.specify/workflows/functions/<id>/` contains `function.yml` and `__init__.py`;
the manifest selects callable attributes explicitly and declares argument
bounds. Function names share a flat namespace with the immutable built-in
filter snapshot and other loaded packages. Built-in and duplicate exports are
installation and load errors; built-ins are never mutated.

The function loader clears the previous project's custom filter registrations,
validates all manifests and collisions before importing code, then imports each
package under a synthetic package name so relative imports work. A package's
exports are registered all-or-nothing and failed imports are cleaned from
`sys.modules`. Installation validates and stages files without importing them;
run, resume, workflow add, and workflow update load functions before workflow
validation. Loading executable Python is not a sandbox or trust endorsement.

Function handlers are wrapped at registration to normalize ordinary
`Exception` failures to a `ValueError` prefixed with the export name. This is
deliberately function-specific; `BaseException` is not caught and step
implementations do not gain a new recovery policy. Return values continue
through the existing expression and persistence boundaries without a separate
type whitelist. The process-global filter table is read by concurrent fan-out
work, so handlers must be stateless and thread-safe.

## Shared package installation

Step packages and function packages share their install, registry, URL and
removal mechanics instead of each owning a copy:

- `workflows/_package_install.py` owns path and symlink safety, tree walking and
  copying (no-follow, excludes, entry/byte/depth budgets), the project lock,
  publish-with-rollback, removal, and one `install_package` flow: reject
  conflicts, validate the source before creating directories, stage, re-validate
  the staged copy, then re-run every conflict check under the lock immediately
  before publishing. It is parameterized by small value objects:
  `InstallRequest` (what to install), `PackageSpec` (naming, error type and
  limits; directory, lock and staging names derive from the noun),
  `PackageRules` (the kind's locate/registry/validate/check/entry semantics) and
  `StagingOps` (copy, publish, lock; `StagingOps.standard(spec)` by default).
  Removal uses `RemoveRequest` and `RemoveHooks`.
- `workflows/_package_registry.py` provides `PackageRegistry`, the symlink-safe,
  atomically written JSON registry with rollback of in-memory state on a failed
  write. `StepRegistry` and `FunctionRegistry` only name their file, directory,
  record key and error type.
- `workflows/_archive_install.py` is the CLI flow for `--from`: URL validation,
  the untrusted-source prompt, GitHub asset resolution, download, archive
  format agreement, safe extraction and cleanup. `_commands._print_package_error`
  renders failures, including advisory notes as warnings.

A new package kind supplies a `PackageSpec`, `PackageRules`, a registry subclass
and its manifest parser; it should not copy any of the above. The step
installer keeps its established names (`_copy_package_tree`, `_replace_install`,
`_step_install_transaction`, ...) as thin bindings and builds its spec at call
time from its module limits, so existing patch points and messages are stable.
Function-specific additions stay in `function/`: manifest parsing, export-name
checks against built-ins, the registry and the package directories on disk, and
registry metadata.

## Adding a step type

1. Implement the step in its own `step/<package>/` subpackage and register
   it explicitly with a unique `type_key`. For an external package, provide
   `step.yml` with a matching `step.type_key` and a matching subclass in
   `__init__.py`; catalog discovery alone does not register the code.
2. Test valid and invalid configurations, status/output/error behavior, and
   resume or nested/concurrent execution when relevant. Registry and engine
   coverage lives in `tests/test_workflows.py`; focused step suites may live
   under `tests/workflows/`.
3. Update the [workflow step reference](https://github.github.io/spec-kit/workflow-steps/types.html) when a
   built-in step changes the YAML users can write. Keep agent-specific CLI
   dispatch in integrations rather than duplicating it in step types.
