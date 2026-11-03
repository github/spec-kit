# Workflow CLI reference

The `specify workflow` group manages workflow packages and run state. Most commands require an initialized Spec Kit project; local YAML runs are the exception. Options are command-specific: `--json` is not a group-wide flag.

## Run a Workflow

```bash
specify workflow run <source>
```

| Option              | Description                                              |
| ------------------- | -------------------------------------------------------- |
| `-i` / `--input`    | Pass input values as `key=value` (repeatable)            |
| `--json`            | Emit the run outcome as a single JSON object             |

Runs an installed, enabled workflow ID or a local YAML file. Install a catalog
workflow or URL with `specify workflow add` before running it by ID. Inputs
declared by the workflow can be provided via `--input` or prompted interactively.

Example:

```bash
specify workflow run speckit -i spec="Build a kanban board with drag-and-drop task management"
```

Input values follow the [input type contracts](api.md#input-types).

With `--json`, a single machine-readable object is printed instead of formatted text (the default output is unchanged when the flag is omitted):

```bash
specify workflow run my-pipeline.yml --json
```

```json
{
  "run_id": "662bf791",
  "workflow_id": "build-and-review",
  "status": "paused",
  "current_step_id": "review",
  "current_step_index": 0
}
```

`workflow_id` is the `workflow.id` declared inside the YAML, not the file name. The object is printed exactly as shown — pretty-printed with two-space indentation, on plain stdout with no Rich markup — so it always parses. While the workflow runs under `--json`, any progress a step would print (for example a gate prompt, or output from a prompt step's CLI subprocess) is redirected to stderr, so stdout carries only the JSON object. Read the object from stdout; leave stderr attached to the terminal or capture it separately.

For `failed` and `aborted` runs, the payload includes an `error` field carrying the terminal step's error message:

```json
{
  "run_id": "662bf791",
  "workflow_id": "build-and-review",
  "status": "failed",
  "current_step_id": "boom",
  "current_step_index": 0,
  "error": "Command exited with code 3"
}
```

`completed` and `paused` runs omit the `error` field. The error is persisted in the run's `state.json`, so `specify workflow status <run_id> --json` surfaces the same message after the fact.

Adapter-load failures before creating or loading run state use a pre-run
failure envelope: a new run has no run ID, while resume retains the supplied
run ID but has no workflow or step context. After run state exists, adapter
failures from per-step reloads or verified lazy imports retain the actual run,
workflow, and current-step fields, just like execution I/O failures. If
saving state fails, the on-disk status may still reflect the last successful
save rather than the reported I/O failure.

> **Note:** Most workflow commands require a project already initialized with `specify init`. The exception is `specify workflow run <local-file.{yml,yaml}>`, which can run outside a project; in that case, run state is stored under the current directory's `.specify/workflows/runs/<run_id>/`.
>
## Resume a Workflow

```bash
specify workflow resume <run_id>
```

| Option              | Description                                              |
| ------------------- | -------------------------------------------------------- |
| `-i` / `--input`    | Updated input values as `key=value` (repeatable)         |
| `--json`            | Emit the resume outcome as a single JSON object          |

Resumes a paused or failed workflow run from its persisted execution state. A
`running` run is not resumable. Resume replays completed work into its
expression contexts without running step implementations again, then continues
at the unfinished occurrence. This lets a run continue with information that
only became available after it paused, or with a corrected value after a
failure.

Supplied `--input` values are merged over the run's stored root inputs and
re-validated against the workflow's input types. Unknown root input names are
ignored. Updated values affect only unfinished work; completed steps and calls
are not reinterpreted or repeated:

```bash
specify workflow resume <run_id> --input cmd="exit 0"
```

## Workflow Status

```bash
specify workflow status [<run_id>]
```

| Option              | Description                                              |
| ------------------- | -------------------------------------------------------- |
| `--json`            | Emit run status (or the runs list) as a JSON object      |

Shows the status of a specific run, or lists all runs if no ID is given. Run states: `created`, `running`, `completed`, `paused`, `failed`, `aborted`.

## Workflow Definition

```bash
specify workflow definition <run_id> --json
```

| Option   | Description                                                      |
| -------- | ---------------------------------------------------------------- |
| `--json` | Required. Emit the run's workflow definition as a JSON object    |

Returns the workflow definition a run was **started with**, so an integration can render a run (for example the gates it declares and their messages) without drifting from what the engine actually executes. It reads only the run's own persisted data and never the installed workflow: editing or removing the installed workflow does not change the output. Runtime progress and the active gate come from [`specify workflow status --json`](#workflow-status).

Omitting `--json` exits with code `2` and prints a usage message on stderr; no stdout is produced. A text renderer is deferred, so the JSON shape below is the only contract.

```json
{
  "run_id": "662bf791",
  "definition": {
    "schema_version": "1.0",
    "workflow": { "id": "spec-review", "name": "Spec review", "version": "1.0.0" },
    "steps": [
      { "id": "draft", "type": "command", "command": "speckit.specify" },
      { "id": "approve", "type": "gate", "message": "Review the specification." }
    ]
  },
  "workflow_scopes": []
}
```

- **`definition`** is the workflow as persisted for the run, verbatim and with overlays already applied, so it reflects the steps as executed. Every key is passed through (including `requires`, `outputs` and unknown keys). Nothing is added, renamed or filled in: an omitted field, such as a gate's `options`, means the engine default applies at run time. Expressions (`{{ ... }}`) are not evaluated. The structure follows the [workflow YAML schema](api.md#workflow-yaml-schema), so `schema_version` is the version of this interface and a schema change is a change to it; because `definition` is emitted as authored, an omitted `schema_version` defaults to `"1.0"` and the engine compares `str(schema_version)` (so unquoted `schema_version: 1.0` in YAML appears as the JSON number `1.0`). Keys may be added to the top-level response envelope (`run_id`, `definition`, `workflow_scopes`) in future versions, but existing envelope keys are never removed or renamed.
- **Plain JSON.** YAML-native values that JSON cannot represent, such as an unquoted date, appear as strings. Binary values (`!!binary`) are not emitted: each appears as a `"<binary: N bytes>"` placeholder, and the value itself stays in the run's snapshot. A set (`!!set`) appears as a list sorted by its JSON form, so the output does not depend on hash randomization. Non-string mapping keys and non-finite numbers are stringified too. Two mapping keys that collapse to the same JSON property name (for example `1` and `"1"`) make the command fail rather than emit lossy JSON. JSON cannot share a reference, so a reused YAML alias (anchor) is duplicated; a recursive alias, or a non-recursive alias graph that expands past a fixed node or output-size budget, fails instead of consuming unbounded CPU, memory and stdout. The budget applies to each definition separately (the root and every entry in `workflow_scopes`), so a run with many bound workflow calls is not rejected for its total size. A separate, much larger limit (32 MiB) caps the whole response, so a loop or fan-out that repeats a large definition fails instead of multiplying it. A non-string mapping key longer than 256 characters once stringified is rejected for the same reason.
- **`workflow_scopes`** (always present) holds the frozen definition of every [workflow call](steps.md#workflow-composition) that has been reached, in execution order. Each entry is `{ "scope_path", "workflow_id", "definition" }`, with `scope_path` and `workflow_id` identical to the values in `status --json`. A call step inside `definition` stays as authored; the callee is never expanded in place. A call that has not been reached yet, or whose target could not be resolved, has no entry, and its definition is never read from the installed workflow. The list grows as calls are reached, and a call inside a loop or fan-out has one entry per iteration or item.
- **Not included: dynamically generated steps.** The output contains the authored root definition and the frozen definitions of bound workflow calls. Steps that a custom step type generates at run time through `StepResult.next_steps` are persisted in the run's execution state but are not exported, so a gate created that way has no definition in this output. The built-in `if`, `switch`, `while`, `do-while` and `fan-out` steps take their steps from the authored definition and are covered.
- **`scope_path`** is a list of strings from the root: the authored `id` of every enclosing step (`step-<index>` for a step without an `id`). Containers such as `if`, `switch`, loops and fan-out are elements; each loop iteration and fan-out item adds its index as a string, including the first (`["loop", "0", "call"]`). `workflow_scopes` is always present here, while `status --json` includes it only when the run has workflow calls.

### Matching a gate to its definition

`status --json` reports an active gate as `gate.step_id` and `gate.scope_path`. To find the gate's definition:

1. Read `gate.scope_path` as `[]` when it is missing: `status --json` omits it for a gate directly in the root workflow. Then take the `workflow_scopes` entry with the longest `scope_path` that is a prefix of `gate.scope_path`. If there is none, use the root `definition`. Do not require an exact match: `gate.scope_path` lists every enclosing step, including `if`, `switch`, loops and fan-out containers, while an entry's `scope_path` ends at the call step. A gate in an `if` named `wrap` inside a workflow called by `call`, itself in an `if` named `route`, reports `["route", "call", "wrap"]`, and its entry has `["route", "call"]`.
2. In that definition, find the step whose `id` equals the authored step ID. In later loop iterations and in fan-out items `step_id` is qualified as `<container>:<id>:<n>` (for example `fan:g:0`); the authored ID is the second-to-last `:`-separated segment, because `:` is not allowed in authored step IDs. Step IDs are unique within a definition except across fan-out templates, which have their own ID namespace: a root step and a fan-out template step may share an ID. If `gate.scope_path` runs through a fan-out step, look only inside that step's `step` template; otherwise ignore fan-out templates. For example, a root shell `g` and a gate `g` in the template of fan-out `fan` both exist, and `fan:g:0` with `scope_path` `["fan", "0"]` is the template's gate, not the root shell.

A gate generated at run time by a custom step has no definition to match; see the note on dynamically generated steps above.

`status --json` does not report per-step status for steps inside called workflows.

### Errors

Failures write a single `{"error": "<message>"}` object to stderr, leave stdout empty and exit with code `1`: not a Spec Kit project, an invalid `SPECIFY_INIT_DIR`, unsafe (including symlinked) workflow storage, an invalid or unknown run ID, an unreadable or too deeply nested run state, a run with no persisted definition (for example one created before definitions were persisted), a corrupt definition or execution state, a definition whose mapping keys collapse to the same JSON property name, and a definition with recursive or too-large-to-expand YAML aliases. Usage errors with `--json` also use this JSON error contract and exit with code `2`.

## List Installed Workflows

```bash
specify workflow list
```

Lists workflows installed in the current project.

## Install a Workflow

```bash
specify workflow add <source>
```

| Option          | Description                                            |
| --------------- | ------------------------------------------------------ |
| `--dev`         | Install from a local YAML file, package directory, or archive |
| `--from <url>`  | Install from a custom URL (`<source>` names the expected workflow ID) |
| `--version <version>` | Install an exact advertised catalog release (`<source>` must be a workflow ID) |

Installs a workflow from the catalog, an HTTPS URL, a local YAML file, a
directory containing `workflow.yml`, or a `.zip`, `.tar.gz`, or `.tgz`
archive. Archives may contain `workflow.yml` at the root or inside one
top-level directory.

Directory and archive installs preserve the complete workflow package,
including scripts and other companion files. ZIP, `.tar.gz`, and `.tgz`
archives follow the same validation and installation behavior.

For exact-version catalog selection and its digest requirements, see [Catalog releases](catalogs.md#workflow-releases).

## Update Workflows

```bash
specify workflow update [workflow_id]
```

Updates one installed catalog workflow — or all of them when no ID is given — to the latest catalog version. Prompts for confirmation and keeps the installed copy if a download or validation fails.

## Enable or Disable a Workflow

```bash
specify workflow enable <workflow_id>
specify workflow disable <workflow_id>
```

Disabled workflows stay installed and listed (marked `[disabled]`) but refuse to run until re-enabled.

## Remove a Workflow

```bash
specify workflow remove <workflow_id>
```

Removes an installed workflow from the project.

## Search Available Workflows

```bash
specify workflow search [query]
```

| Option     | Description       |
| ---------- | ----------------- |
| `--tag`    | Filter by tag     |
| `--author` | Filter by author  |

Searches all active catalogs for workflows matching the query.

## Workflow Info

```bash
specify workflow info <workflow_id>
specify workflow info <workflow_id> --versions
```

Shows detailed information about a workflow, including its steps, inputs, and requirements.
`--versions` lists the current catalog version followed by advertised historical
versions and indicates whether the winning catalog is installable or
discovery-only (not installable). It also works when a different version is
installed locally.

## Resolve a Workflow

```bash
specify workflow resolve <workflow-id>
```

Shows the base/overlay stack and step source attribution. It does not display complete shell commands or environment bindings; review the contributing source files before execution.

## Overlay Management

### Add a Project Overlay

```bash
specify workflow overlay add <path-to-overlay.yml> --priority <n>
```

Validates the overlay file and copies it to `.specify/workflows/overlays/<extends>/<id>.yml`. `--priority` defaults to `10` and overrides the `priority` field in the file.

### List Overlays

```bash
specify workflow overlay list <workflow-id>
```

Shows all overlays for the workflow, ordered by resolver precedence. Disabled overlays are marked as disabled in the listing and are ignored during workflow resolution.

### Change Priority

```bash
specify workflow overlay set-priority <workflow-id> <overlay-id> <n>
```

### Enable or Disable

```bash
specify workflow overlay disable <workflow-id> <overlay-id>
specify workflow overlay enable <workflow-id> <overlay-id>
```

### Remove

```bash
specify workflow overlay remove <workflow-id> <overlay-id>
```

Removes the project overlay file.

## Step Management

Custom steps contain executable Python. Review their source before installation and use. See [Developing custom step packages](developing.md#custom-step-packages) for the package contract.

```bash
specify workflow step list
specify workflow step search [query]
specify workflow step info <step_id>
specify workflow step info <step_id> --versions
```

`list` shows installed custom step types; `search` searches active step catalogs; `info` shows installed or catalog metadata and source provenance. `--versions` lists releases from the winning catalog.

### Install from a local directory

```bash
specify workflow step add my-step --dev /path/to/my-step
```

`--dev` takes a **directory** (not an archive, not a bare `step.yml`) that is a
complete package. This needs no catalog, server, or network, which makes it the
supported local-authoring loop:

```bash
specify workflow step add my-step --dev ./my-step
specify workflow step list
specify workflow step info my-step
# edit ./my-step, then replace the installed copy:
specify workflow step add my-step --dev ./my-step --force
specify workflow step remove my-step
```

### Install from an archive URL

```bash
specify workflow step add my-step --from https://example.com/my-step.zip
```

`--from` accepts a `.zip`, `.tar.gz`, or `.tgz` archive (a bare `step.yml`
URL is **not** a package). The archive may place `step.yml` and `__init__.py`
at its root or under exactly one top-level directory; unrelated top-level
siblings are rejected. Because a step package contains executable Python, a
direct URL install shows a default-deny trust confirmation before any network
request; declining cancels with no request and no error. HTTPS is required
(HTTP is permitted only for loopback hosts), redirects must remain secure, and
downloads are size-bounded.

### Install from the catalog

```bash
specify workflow step add my-step
```

Catalog installs resolve individual file URLs from the active step catalogs and
then go through the same validation and commit path as `--dev` and `--from`.
Discovery-only catalogs cannot be installed from.

To submit a custom step type to the discovery-only community catalog, follow
[Community Workflow Steps](../community/workflow-steps.md). Submissions use
tag-pinned individual file URLs and per-file digests; maintainers validate
metadata and distribution evidence, not submitted code.

See [Step releases](catalogs.md#step-releases) for catalog history and exact-version selection.

### Replacement and force

```bash
specify workflow step add my-step --dev ./my-step --force
specify workflow step add my-step --from https://example.com/my-step.zip --force
```

`--force` first stages and validates the replacement before touching the
existing installation, and can replace both a registered install and a leftover
unregistered directory. Validation and staging failures leave the previous
package untouched. If removing the old directory fails, the replacement is not
published. If publishing the replacement or updating the registry fails after
the old directory has been removed, the installation may be left incomplete:
rerun the command with the original source and `--force` to reinstall. No
automatic rollback is attempted.

### Listing, running, and removing

Installed custom steps appear in `specify workflow step list` and are loaded
automatically by `workflow add`, `workflow run`, and `workflow resume`. Remove
one with:

```bash
specify workflow step remove my-step
```

## Catalog Management

Workflow and step catalogs are independent stacks.

### List Catalogs

```bash
specify workflow catalog list
specify workflow step catalog list
```

Shows all active catalog sources.

### Add a Catalog

```bash
specify workflow catalog add <url> [--name <name>]
specify workflow step catalog add <url> [--name <name>]
```

| Option          | Description                      |
| --------------- | -------------------------------- |
| `--name <name>` | Optional name for the catalog    |

Adds a custom catalog URL to the project's `.specify/workflow-catalogs.yml`
or, for step types, `.specify/step-catalogs.yml`. New entries allow installation
and receive a priority after existing entries. Only add vetted sources.
Configure discovery-only sources by editing the catalog configuration.

Re-adding the same workflow or step catalog URL with the same name succeeds without changing the configuration; a different name is rejected.

### Remove a Catalog

```bash
specify workflow catalog remove <index>
specify workflow step catalog remove <index>
```

Removes a project catalog by its index in the corresponding priority-ordered `catalog list`.
Sources supplied by `SPECKIT_WORKFLOW_CATALOG_URL` or `SPECKIT_STEP_CATALOG_URL` cannot be removed this way; unset the variable to manage project sources.

## See also

- [Workflow overview](overview.md)
- [Workflow API](api.md)
- [Built-in step types](steps.md)
- [Overlay format](overlays.md)
- [Catalog schemas and trust](catalogs.md)
