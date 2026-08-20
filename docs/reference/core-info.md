# Core Info

The `specify core` command group exposes read-only information about Spec Kit's baked-in ("core") baseline — the commands, templates, and helper scripts that ship inside the CLI package itself. Presets, extensions, integrations, and project-scoped assets are intentionally **not** included; use their dedicated commands (`specify preset`, `specify extension`, `specify integration`) for those.

Core info output is deterministic and byte-identical across runs, so downstream tools can safely diff, hash, or cache it.

## Inspect Core Info

```bash
specify core info --json
```

| Option        | Description                                                          |
| ------------- | -------------------------------------------------------------------- |
| `--json`      | **Required.** Emit core info as JSON on stdout.                      |

The `--json` flag is mandatory. A human-readable table format is intentionally not offered — the command is designed for programmatic consumption by external tools and other Spec Kit surfaces. Invoking `specify core info` without `--json` exits non-zero with a hint pointing at the flag.

### Output shape

The response is a JSON object with three top-level arrays, always in this order and always sorted alphabetically by `name` within each array:

```json
{
  "commands":  [ /* baseline slash-commands (e.g. speckit.plan) */ ],
  "templates": [ /* markdown templates (spec, plan, tasks, ...) */ ],
  "scripts":   [ /* helper scripts (bash/powershell/python)      */ ]
}
```

Every entry carries a stable identifier suitable for cross-referencing:

- `id`: `core:_:<kind>:<name>` (`<kind>` is `command`, `template`, or `script`)
- `name`: the logical artifact name. Commands are namespaced as `speckit.<stem>`; templates use their filename stem; scripts use a hyphenated stem (for example, `setup-plan`, not `setup_plan`).
- `description`: short human-readable summary
- `sourcePath`: package-relative, forward-slash path (e.g. `templates/commands/plan.md`)

Kind-specific fields:

- **`commands[]`** also include `artifact` (string or `null`), `optional` (boolean, defaults to `false`), and `handoffs` (list of downstream command identifiers, may be empty).
- **`scripts[]`** also include `runtimes`: a sorted list of the runtimes that ship a variant of that script, drawn from `bash`, `powershell`, and `python`. Every script has at least a `bash` variant — that is the canonical source.

### Example

```bash
specify core info --json | jq '.commands[] | select(.name == "speckit.plan")'
```

```json
{
  "id": "core:_:command:speckit.plan",
  "name": "speckit.plan",
  "description": "Execute the implementation planning workflow using the plan template to generate design artifacts.",
  "sourcePath": "templates/commands/plan.md",
  "artifact": null,
  "optional": false,
  "handoffs": ["speckit.tasks", "speckit.checklist"]
}
```

## When to Use It

- Building tools that need to know what the shipped baseline contains without unpacking the wheel by hand.
- Auditing which commands, templates, or scripts a given Spec Kit release ships.
- Cross-referencing baseline artifacts against extension- or preset-provided ones.

## Determinism Guarantees

- Alphabetical ordering by `name` within each section.
- Fixed top-level key order: `commands`, `templates`, `scripts`.
- Fields inside each entry are emitted in a fixed order.
- Path separators are always forward-slashes, even on Windows.

## Failure Modes

The command fails fast on packaging errors it can detect at read time — unparseable frontmatter, a mistyped field, or a script missing its canonical bash variant — rather than silently emitting a malformed inventory. On any such error it exits with code `1` and prints a JSON error envelope on stderr. Note that templates and scripts are enumerated from whatever files are present on disk, so an asset that is missing entirely from the installation is simply omitted from the output rather than raised as an error.

```json
{
  "error": "core_inventory.frontmatter_parse",
  "message": "Could not parse YAML frontmatter of command 'plan': ...",
  "artifact": { "kind": "command", "name": "plan", "sourcePath": "templates/commands/plan.md" }
}
```

Common `error` codes:

| Code                                | Meaning                                                        |
| ----------------------------------- | -------------------------------------------------------------- |
| `core_inventory.assets_missing`     | Neither the wheel-shipped `core_pack/` nor the source checkout was found. |
| `core_inventory.frontmatter_parse`  | YAML frontmatter on a baseline file could not be parsed, or a field has the wrong type. |
| `core_inventory.missing_description`| A baseline command, template, or script has no usable description. |
| `core_inventory.missing_canonical`  | A script ships a non-bash variant but no canonical bash one.   |
| `core_inventory.invalid_source_path`| An emitted `sourcePath` failed the shape check (absolute or contained a backslash). |

These conditions represent packaging bugs and should be reported.
