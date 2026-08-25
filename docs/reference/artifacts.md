# Artifacts

An **artifact** is any command, template, or script Spec Kit exposes in a project, regardless of which layer contributes it — built-in assets, an installed preset, an installed extension, or a project-local override in `.specify/templates/overrides/`.

The `specify artifact` command group is the read-only introspection surface for that inventory. `specify preset resolve <name>` answers "which file wins for this preset-managed name?"; `specify artifact` answers "what exists at all, and what is the full composition stack behind it?" — including built-in artifacts that no preset touches.

Both subcommands currently require `--json`. Omitting it exits with code `2` and prints a usage message on stderr; no stdout is produced. Text rendering is deliberately deferred so the JSON shapes below are the only contract, and adding a default text renderer later stays a non-breaking, additive change.

## List Artifacts

```bash
specify artifact list --json
```

| Option   | Description                                              |
| -------- | -------------------------------------------------------- |
| `--json` | Required. Emit the inventory as a JSON array on stdout.  |

Prints the full inventory of every visible artifact — one row per `(kind, name)` pair, including its composition `stack` — sorted by kind (`command`, then `template`, then `script`) and then by name.

```json
[
  {
    "id": "command:speckit.specify",
    "name": "speckit.specify",
    "kind": "command",
    "description": "Create or update the feature specification.",
    "stack": [
      {
        "id": "command:speckit.specify",
        "layer": null,
        "sourceId": null,
        "presetId": null,
        "presetName": null,
        "strategy": "replace",
        "active": true,
        "hidden": false,
        "manifestPath": null,
        "lookupId": null
      }
    ]
  },
  {
    "id": "script:create-new-feature",
    "name": "create-new-feature",
    "kind": "script",
    "description": "Create a new feature branch and spec directory.",
    "stack": [
      {
        "id": "script:create-new-feature",
        "layer": null,
        "sourceId": null,
        "presetId": null,
        "presetName": null,
        "strategy": "replace",
        "active": true,
        "hidden": false,
        "manifestPath": null,
        "lookupId": null
      }
    ]
  }
]
```

| Field         | Description                                                               |
| ------------- | ------------------------------------------------------------------------- |
| `id`          | `{kind}:{name}` — the shorthand `artifact info` accepts as its argument    |
| `name`        | Logical artifact name (commands use the `speckit.<stem>` namespace)        |
| `kind`        | One of `command`, `template`, `script`                                     |
| `description` | Description from the highest-precedence layer that declares one, else `""` |
| `stack`       | Composition stack for this artifact, using the same row shape as `artifact info` |

Built-in artifacts always appear, even when nothing overrides them. Descriptions come from the highest-priority layer that has one — a preset or project override that hides a built-in command reports its own description, not the hidden built-in text. Skills (`.github/skills/**/SKILL.md`) are excluded: they are integration-specific output, not a shipped asset family.

## Artifact Info

```bash
specify artifact info <name> --json
```

| Option           | Description                                                        |
| ---------------- | ------------------------------------------------------------------- |
| `--json`         | Required. Emit the composition stack as a JSON object on stdout.    |
| `--kind <kind>`  | Narrow the lookup to `command`, `template`, or `script`             |

`<name>` accepts either a bare name (`speckit.specify`) or the `kind:name` shorthand (`command:speckit.specify`). When both the shorthand and `--kind` are supplied they must agree.

```json
{
  "id": "command:speckit.specify",
  "name": "speckit.specify",
  "kind": "command",
  "description": "Create or update the feature specification.",
  "stack": [
    {
      "id": "command:speckit.specify",
      "layer": "preset",
      "sourceId": "compliance",
      "presetId": "compliance",
      "presetName": "Compliance Preset",
      "strategy": "replace",
      "active": true,
      "hidden": false,
      "manifestPath": ".specify/presets/compliance/preset.yml",
      "lookupId": "preset:compliance:command:speckit.specify"
    },
    {
      "id": "command:speckit.specify",
      "layer": null,
      "sourceId": null,
      "presetId": null,
      "presetName": null,
      "strategy": "replace",
      "active": false,
      "hidden": true,
      "manifestPath": null,
      "lookupId": null
    }
  ]
}
```

The top-level `id`, `name`, `kind`, `description`, and `stack` fields match the corresponding row on `artifact list --json`.

### Stack semantics

`stack` is ordered by resolution precedence: index `0` is the layer that wins. Each row describes one contributing layer:

| Field          | Description                                                                     |
| -------------- | -------------------------------------------------------------------------------- |
| `id`           | `{kind}:{name}` — the source-agnostic round-trip key, identical on every row of the same artifact's stack |
| `layer`        | `project`, `preset`, or `extension`; `null` for built-in layers                    |
| `sourceId`     | Source component of `lookupId`, or `null` when the layer has no provenance         |
| `presetId`     | Preset pack directory id; `null` on built-in, `project`, and `extension` rows       |
| `presetName`   | Preset display name when its manifest declares one, else the pack id; `null` when `presetId` is `null` |
| `strategy`     | `replace`, `wrap`, `prepend`, or `append`                                         |
| `active`       | `true` only for index `0` — the layer whose content is served                     |
| `hidden`       | `true` when a lower-index `replace` layer cuts this layer out of the composition |
| `manifestPath` | Project-relative path to the declaring manifest, or `null` when none applies      |
| `lookupId`     | Deterministic `{layer}:{sourceId}:{kind}:{name}` identifier, or `null` for built-in layers |

`active` and `hidden` are independent labels, not opposites. Composing strategies (`wrap`, `prepend`, `append`) keep lower layers in the composed output, so an inactive layer is not necessarily hidden: only layers below the first `replace` layer are marked `hidden`. Built-in rows have no provenance: `layer`, `sourceId`, and `lookupId` are `null` — but `id` is always populated, even on built-in rows. `id` is the round-trip key: `specify artifact info` accepts it as input (for example, `specify artifact info command:speckit.specify --json`), and it resolves the same artifact whether the caller passes the bare name or the `id`.

Lookup IDs use the same grammar as [preset contribution identifiers](presets.md#contribution-identifiers), so a `lookupId` from this command joins directly to `PresetManifest.iter_contributions()` / `ExtensionManifest.iter_contributions()` for manifest-declared layers. Project-local overrides carry a synthetic `project:_:{kind}:{name}` ID that intentionally matches no manifest contribution. `lookupId` is manifest-backed layer provenance, not the round-trip key — use `id` for that.

## JSON Errors

On failure, nothing is written to stdout. A single-key JSON envelope is written to stderr and the process exits with code `1`:

```json
{ "error": "unknown artifact command:nope" }
```

| Message                                             | Cause                                                            |
| --------------------------------------------------- | ---------------------------------------------------------------- |
| `not a Spec Kit project: no .specify/ directory found` | Run outside an initialized project                             |
| `unknown artifact <name>`                           | No artifact matches the requested name (and kind, when given)     |
| `ambiguous artifact <name>: matches kinds [...]`    | The bare name matches more than one kind — re-run with `--kind`   |
| `artifact resolution failed`                        | The preset/extension registries could not be read, or artifact content could not be composed |

Exit code `2` is reserved for usage errors — a missing `--json` flag or an invalid `--kind` value — and emits a plain-text message on stderr rather than a JSON envelope.
