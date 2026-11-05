# Workflow overlays

Workflow overlays let a project extend or override an installed workflow without editing the installed `workflow.yml`.  This keeps local customizations safe across `specify bundle update` or `specify workflow add` upgrades.

When `specify workflow run <workflow-id>` loads a workflow, the engine composes the base workflow with all enabled overlays for that workflow id.  The result is validated like any other workflow definition.

## How Overlays Work

An overlay is a YAML file that declares a set of edit operations against the step list of a base workflow. Overlays use lower-wins precedence: higher priority numbers are applied first and lower numbers last. Equal-priority overlays are applied alphabetically by ID, with the last ID winning conflicts.

Project overlay files live at:

| Location | Purpose |
| --- | --- |
| `.specify/workflows/overlays/<id>/*.yml` | Project-local customizations |

## Overlay File Format

The recommended edit format uses the operation name as the key and the anchor step id as the value:

```yaml
id: "my-overlay"
extends: "speckit"
priority: 10
enabled: true
edits:
  - insert_after: implement
    step:
      id: run-lint
      type: shell
      run: "ruff check src/"

  - replace: review-spec
    step:
      id: review-spec
      type: gate
      message: "Review the generated spec (overlay override)."
      options: [approve, reject]
      on_reject: abort
```

The explicit form is also supported:

```yaml
edits:
  - operation: insert_after
    anchor: implement
    step:
      id: run-lint
      type: shell
      run: "ruff check src/"
```

### Fields

| Field | Required | Description |
| --- | --- | --- |
| `id` | yes | Identifier for this overlay. Used in `specify workflow overlay *` commands. Must be lowercase letters, digits, and hyphens only; no dots, underscores, path separators, or `overlays`. |
| `extends` | yes | The workflow id this overlay applies to. Uses the same safe-id format as `id`; `overlays`, `runs`, and `steps` are reserved. |
| `priority` | no | Integer; defaults to `10`. Lower values have higher precedence and win conflicts. Missing or invalid values fall back to `10`. |
| `enabled` | no | Boolean. Defaults to `true`. Disabled overlays are ignored. |
| `edits` | yes | Non-empty list of edit operations. |

### Edit Operations

| Operation | `step` required | Effect |
| --- | --- | --- |
| `insert_after` | yes | Insert `step` immediately after the anchor step. |
| `insert_before` | yes | Insert `step` immediately before the anchor step. |
| `replace` | yes | Replace the anchor step with `step`. |
| `remove` | no | Remove the anchor step from the list. |

The `anchor` is the `id` of a step in the base workflow.  Anchors are resolved recursively inside `then`, `else`, `steps`, `cases.*`, and `default` blocks, so nested base steps can also be targeted.  Fan-out templates (`step` inside a `fan-out` step) are **not** valid anchors.

Step ids must not contain `:` — that character is reserved for engine-generated nested ids.

## Manage overlays

Use the [overlay CLI commands](cli.md#overlay-management) to add, list, prioritize, enable, disable, and remove overlays, or inspect composition with `specify workflow resolve <workflow-id>`.

## Example: Adding Automated Linting after Implementation

Given the built-in `speckit` workflow, create `project-overlay.yml`:

```yaml
id: "add-lint"
extends: "speckit"
priority: 10
edits:
  - insert_after: implement
    step:
      id: run-lint
      type: shell
      run: "ruff check src/"
```

Install it:

```bash
specify workflow overlay add project-overlay.yml --priority 10
```

Run the workflow:

```bash
specify workflow run speckit -i spec="Build a kanban board"
```

The composed workflow will now run the full SDD cycle and execute `ruff check src/` automatically after the `implement` step.

## Example: Replacing a Gate

```yaml
id: "skip-plan-review"
extends: "speckit"
priority: 5
edits:
  - replace: review-plan
    step:
      id: review-plan
      type: command
      command: speckit.plan
      input:
        args: "{{ inputs.spec }}"
```

Lower priority values have higher precedence. This overlay's `priority: 5`
wins conflicts with a priority-10 overlay. It replaces the `review-plan` gate
with another plan command, so the existing plan command still runs too.

## Workflow slots (upstream extension points)

Workflow authors can declare a named, no-op workflow slot with `type: slot`:

```yaml
- id: post-implement
  type: slot
  name: "Post-implementation checks"
```

The step `id` is the unique overlay anchor; `name` is a required non-blank,
human-readable label only. An unfilled slot completes as a `skipped` step with
`output: {slot: <name>}`, so subsequent steps continue normally.

Fill a slot with a schema-valid overlay `replace` edit anchored on the step
`id`, not its `name`:

```yaml
id: fill-post-implement
extends: my-workflow
edits:
  - replace: post-implement
    step:
      id: post-implement
      type: shell
      run: "echo Run project-specific checks"
```

Reuse the slot's `id` when later expressions or `fan-in.wait_for` refer to it.
The replacement must also preserve every output key those later steps consume:
an unfilled workflow slot supplies only `steps.<id>.output.slot`. Slot steps are
not supported inside `fan-out.step` templates because runtime-multiplied
templates cannot be overlay anchors.

## Interaction with Bundles and Updates

`specify workflow add <local-directory>` installs the complete local workflow
package into `.specify/workflows/<id>/`. Archive installs preserve the same
package contents.

When an installed workflow is refreshed or reinstalled, project overlays in `.specify/workflows/overlays/<id>/` are preserved because they live outside the installed workflow directory.

## Limitations

- Overlays operate on the step list only. They cannot change workflow metadata,
  inputs, outputs, `requires`, or workflow-level defaults. To change an
  expression in a step, replace that step.
- Fan-out templates cannot be used as anchors.
- An overlay that targets a step id that does not exist in the base workflow will raise a validation error when the workflow is resolved.
- Overlays cannot target steps added by other overlays.
- Overlays cannot add new inputs or change the input schema of the base workflow.

## See also

- [Workflow CLI](cli.md#overlay-management)
- [Step types](../workflow-steps/types.md)
