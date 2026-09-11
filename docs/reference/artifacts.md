# Artifacts

An **artifact** is any command, template, script, or hook Spec Kit exposes in a project, regardless of which layer contributes it — built-in assets, an installed preset, an installed extension, or a project-local override in `.specify/templates/overrides/`.

The `specify artifact` command group is the read-only introspection surface for that inventory. `specify preset resolve <name>` answers "which file wins for this preset-managed name?"; `specify artifact` answers "what exists at all, and what is the full composition stack behind it?" — including built-in artifacts that no preset touches.

Both subcommands currently require `--json`. Omitting it exits with code `2` and prints a usage message on stderr; no stdout is produced. Text rendering is deliberately deferred so the JSON shapes below are the only contract, and adding a default text renderer later stays a non-breaking, additive change.

## List Artifacts

```bash
specify artifact list --json
```

| Option   | Description                                              |
| -------- | -------------------------------------------------------- |
| `--json` | Required. Emit the inventory as a JSON array on stdout.  |

Prints the full inventory of every visible artifact — one row per `(kind, name)` pair, including its composition `stack`. Named artifacts are sorted by kind (`command`, then `template`, then `script`) and name. Hook rows follow them, sorted by event and then by the first declaration's priority.

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
        "lookupId": null,
        "sourcePath": null
      }
    ]
  },
  {
    "id": "script:setup-plan",
    "name": "setup-plan",
    "kind": "script",
    "description": "Setup implementation plan for a feature.",
    "stack": [
      {
        "id": "script:setup-plan",
        "layer": null,
        "sourceId": null,
        "presetId": null,
        "presetName": null,
        "strategy": "replace",
        "active": true,
        "hidden": false,
        "manifestPath": null,
        "lookupId": null,
        "sourcePath": null
      }
    ]
  }
]
```

| Field         | Description                                                               |
| ------------- | ------------------------------------------------------------------------- |
| `id`          | `{kind}:{name}` — the shorthand `artifact info` accepts as its argument    |
| `name`        | Logical artifact name (commands use the `speckit.<stem>` namespace)        |
| `kind`        | One of `command`, `template`, `script`, `hook`                             |
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
| `--kind <kind>`  | Narrow the lookup to `command`, `template`, `script`, or `hook`      |

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
      "lookupId": "preset:compliance:command:speckit.specify",
      "sourcePath": ".github/skills/speckit-specify/SKILL.md"
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
      "lookupId": null,
      "sourcePath": null
    }
  ]
}
```

The top-level `id`, `name`, `kind`, `description`, and `stack` fields match the corresponding row on `artifact list --json`.

### Stack semantics

For command, template, and script artifacts, `stack` is ordered by resolution precedence: index `0` is the winning layer. Hook stacks are additive rather than winner-based: multiple entries may be active, and their declaration ordering is described in [Hook artifacts](#hook-artifacts). Each row describes one contributing layer:

| Field          | Description                                                                     |
| -------------- | -------------------------------------------------------------------------------- |
| `id`           | `{kind}:{name}` — the source-agnostic round-trip key, identical on every row of the same artifact's stack |
| `layer`        | `project`, `preset`, or `extension`; `null` for built-in layers                    |
| `sourceId`     | Source component of `lookupId`, or `null` when the layer has no provenance         |
| `presetId`     | Preset pack directory id; `null` on built-in, `project`, and `extension` rows       |
| `presetName`   | Preset display name when its manifest declares one, else the pack id; `null` when `presetId` is `null` |
| `strategy`     | `replace`, `wrap`, `prepend`, `append`, or `additive`                              |
| `active`       | Whether the layer is active; for named artifacts this is `true` only at index `0` |
| `hidden`       | `true` when a lower-index `replace` layer cuts this layer out of the composition |
| `manifestPath` | Project-relative path to the declaring manifest, or `null` when none applies      |
| `lookupId`     | Deterministic `{layer}:{sourceId}:{kind}:{name}` identifier, or `null` for built-in layers |
| `sourcePath`   | Project-relative POSIX path to the concrete file backing the layer, or `null` for built-in/synthetic layers |

`active` and `hidden` are independent labels, not opposites. For command, template, and script artifacts, `active` identifies the highest-precedence layer selected by the existing Spec Kit layer-resolution order; it does not validate that the layer content can be read or composed. This preserves the diagnostic behavior of `specify preset resolve`, which reports the discovered layer chain even when content composition later produces a warning. Composing strategies (`wrap`, `prepend`, `append`) keep lower layers in the composed output, so an inactive layer is not necessarily hidden: only layers below the first `replace` layer are marked `hidden`. Built-in rows have no provenance: `layer`, `sourceId`, and `lookupId` are `null` — but `id` is always populated, even on built-in rows. `id` is the round-trip key: `specify artifact info` accepts it as input (for example, `specify artifact info command:speckit.specify --json`), and it resolves the same artifact whether the caller passes the bare name or the `id`.

Lookup IDs are derived by the artifact command from the resolved layer and its existing preset or extension manifest. Manifest-declared layers use the manifest's `id`; convention-only layers use the installed preset or extension directory id. Project-local overrides carry a synthetic `project:_:{kind}:{name}` ID, while built-in layers have no `lookupId`. These values are artifact-stack provenance, not the round-trip key — use `id` for that. `sourcePath` is populated only when the layer maps to a concrete installed preset/extension file or a tracked agent materialization; core, project-override, and other synthetic rows report `null`.

### Hook artifacts

Hook rows project hook declarations from extensions included by the standard preset and extension resolver. The round-trip shorthand is:

```text
hook:{encodedEventName}:{encodedTargetCommand}
```

For example, both of these select the same hook artifact:

```bash
specify artifact info hook:before_specify:speckit.compliance.pre-check --json
specify artifact info before_specify:speckit.compliance.pre-check --kind hook --json
```

Hook event and target-command components are UTF-8 percent-encoded using URL quoting: ASCII letters, digits, `-`, `.`, `_`, and `~` remain literal, while all other bytes are encoded. This encoding is limited to the hook components in the artifact `id`, `name`, and `lookupId`; hook manifests, runtime bindings, `eventName`, and `targetCommand` are unchanged. For example, an event named `custom:after` targeting `/skill:speckit-test-ext-hello` has the artifact ID:

```text
hook:custom%3Aafter:%2Fskill%3Aspeckit-test-ext-hello
```

Hook rows add three top-level fields:

| Field           | Description                                                                    |
| --------------- | ------------------------------------------------------------------------------ |
| `eventName`     | Hook event that triggers the declaration                                       |
| `targetCommand` | Command invoked by the hook declaration                                        |
| `registered`    | `true` when at least one declaring stack entry has an enabled runtime binding  |

Each hook stack entry also includes the declaration's normalized `priority` and `optional` values. Hook entries always use `strategy: "additive"` and `hidden: false`: multiple extensions may declare and register the same event-command pair, and every enabled declaration remains active. Stack entries are sorted by hook priority, with the resolver's deterministic declaration order used as the tiebreaker. This ordering describes the declaration inventory; it is not a promise that equal-priority hooks execute in the same order at runtime.

For hooks, `active` reports registration state from `.specify/extensions.yml`, not condition evaluation. A declaration is active only when the runtime configuration contains an enabled binding with the same extension id, event, and command. Conditions are evaluated later when the hook executes. Missing, malformed, or unreadable runtime configuration therefore leaves declarations visible with `registered: false` and `active: false`.

Declared-but-unregistered hooks remain visible when their extension is included by the normal resolver. Registry-disabled extensions are excluded entirely, consistently with their other contributions. Invalid individual extension manifests are also omitted by the existing resolver and remain diagnosable through extension inspection and validation commands.

Hook lookup IDs use the artifact-private `{layer}:{sourceId}:hook:{encodedEventName}:{encodedTargetCommand}` grammar. Hook provenance is restricted to `preset` and `extension` layers; hooks never receive a built-in/core layer. The current manifest API exposes extension hook declarations, so current rows use the `extension` layer. The `preset` layer remains reserved by the hook identifier grammar for preset-provided hooks without requiring artifact IDs to be added to preset or extension manifest APIs.

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
| `artifact resolution failed`                        | The extension registry could not be read, or an error prevented the artifact layer stack from being collected |

Exit code `2` is reserved for usage errors — a missing `--json` flag or an invalid `--kind` value — and emits a plain-text message on stderr rather than a JSON envelope.
