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

Prints the full inventory of every visible artifact — one row per `(kind, name)` pair, including its composition `stack` — sorted by kind (`command`, then `template`, then `script`, then `hook`) and then by name.

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
| `id`          | `{kind}:{name}` — the shorthand `artifact info` accepts as its argument (for hooks, `hook:{eventName}:{targetCommand}`) |
| `name`        | Logical artifact name (commands use the `speckit.<stem>` namespace; hooks use `{eventName}:{targetCommand}`) |
| `kind`        | One of `command`, `template`, `script`, `hook`                             |
| `description` | Description from the highest-precedence layer that declares one, else `""` |
| `stack`       | Composition stack for this artifact, using the same row shape as `artifact info` |

Hook rows carry additional top-level scalar fields that mirror the priority-sorted winner of the composition stack — see [Hook artifacts](#hook-artifacts) below.

Built-in artifacts always appear, even when nothing overrides them. Descriptions come from the highest-priority layer that has one — a preset or project override that hides a built-in command reports its own description, not the hidden built-in text. Skills (`.github/skills/**/SKILL.md`) are excluded: they are integration-specific output, not a shipped asset family.

## Artifact Info

```bash
specify artifact info <name> --json
```

| Option           | Description                                                        |
| ---------------- | ------------------------------------------------------------------- |
| `--json`         | Required. Emit the composition stack as a JSON object on stdout.    |
| `--kind <kind>`  | Narrow the lookup to `command`, `template`, `script`, or `hook`     |

`<name>` accepts either a bare name (`speckit.specify`) or the `kind:name` shorthand (`command:speckit.specify`). For hooks, the shorthand is `hook:{eventName}:{targetCommand}` — the bare hook name (`{eventName}:{targetCommand}`) is also accepted. When both the shorthand and `--kind` are supplied they must agree.

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

## Hook artifacts

Hook rows extend the shape above with a few fields that only apply to hooks. A hook row's public identifier is `hook:{eventName}:{targetCommand}` — that string is the round-trip key that `artifact info` accepts, and `name` is the same value with the `hook:` prefix stripped.

```json
{
  "id": "hook:before_specify:speckit.compliance.pre-check",
  "name": "before_specify:speckit.compliance.pre-check",
  "kind": "hook",
  "description": "Compliance pre-check guard",
  "eventName": "before_specify",
  "targetCommand": "speckit.compliance.pre-check",
  "optional": false,
  "priority": 5,
  "registered": true,
  "stack": [
    {
      "id": "hook:before_specify:speckit.compliance.pre-check",
      "layer": "extension",
      "sourceId": "compliance",
      "strategy": "replace",
      "active": true,
      "lookupId": "extension:compliance:hook:before_specify:speckit.compliance.pre-check",
      "priority": 5,
      "optional": false
    }
  ]
}
```

### Top-level fields

| Field           | Description                                                                                     |
| --------------- | ----------------------------------------------------------------------------------------------- |
| `eventName`     | The event whose fires trigger this hook (`before_specify`, `after_plan`, …)                     |
| `targetCommand` | The command the hook proposes to run when the event fires                                        |
| `optional`      | Mirrors the active winner's `optional` scalar — the value the runtime will actually see          |
| `priority`      | Mirrors the active winner's `priority` scalar                                                    |
| `registered`    | `true` when a matching `.specify/extensions.yml` binding exists and is not `enabled: false`      |

`optional` and `priority` on the row always agree with the entry marked `active: true` on the stack — they are the values the runtime will actually execute for this `(eventName, targetCommand)` pair. Per-contributor `priority` / `optional` remain visible on every stack entry so callers can audit why one contributor won.

### Hook stack entries

Hook stack entries drop `presetId`, `presetName`, `hidden`, and `manifestPath` (all of which are meaningless for hooks) and add per-contributor `priority` and `optional`. `strategy` is always `"replace"` — the runtime has no composable hook-strategy vocabulary today, so the field is present for shape parity but carries no semantics beyond "this hook overrides earlier hooks in the same slot".

| Field       | Description                                                                                 |
| ----------- | -------------------------------------------------------------------------------------------- |
| `id`        | The row-shorthand `hook:{eventName}:{targetCommand}`, identical on every entry               |
| `layer`     | Always `preset` or `extension` (never `null`, never `project`, never the built-in tier)      |
| `sourceId`  | The contributing pack's manifest id                                                          |
| `strategy`  | Always `"replace"` — see note above                                                          |
| `active`    | `true` only on the priority-sorted winner (index `0`)                                        |
| `lookupId`  | The manifest identifier: `{layer}:{sourceId}:hook:{eventName}:{targetCommand}`               |
| `priority`  | Per-contributor priority (ascending = higher precedence; falls back to the runtime default)  |
| `optional`  | Per-contributor optional flag                                                                |

### `registered` semantics

`registered` reflects the project's runtime binding state under `.specify/extensions.yml` and MUST match the runtime's own execution decision. It is `true` when at least one entry in the event's binding array (a) names one of the row's contributing sources via `extension` and (b) is not explicitly `enabled: false`. A binding entry with a matching `extension` but no `command` field counts as a wildcard — same rule the runtime's `enable_hooks` / `disable_hooks` apply.

A declared hook whose contributors have **no** matching binding entry still appears in the inventory with `registered: false`. This is intentional: `artifact list --json` describes what an extension declares, and `registered` tells you whether the runtime will actually invoke it. A structurally invalid `.specify/extensions.yml` (parse error, wrong top-level type, missing `hooks:` key) is silently normalized to an empty bindings map — every declared hook then reports `registered: false` and no error is raised to callers.

### Layer invariant

Hooks only appear on `preset` or `extension` stack entries. There is no built-in ("core") hook tier — the identifier grammar itself refuses to build hook IDs on any other layer, and `derive_hook_id` will raise `IdentifierComponentError` for a `layer` outside `{preset, extension}`. In practice, no built-in preset today emits hooks; extensions are the only source. Even so, the grammar reserves the preset layer for forward compatibility.

Runtime bindings under `.specify/extensions.yml` that name an extension or command no installed extension has declared do **not** synthesize a phantom row — the inventory is manifest-driven, and orphan bindings only influence the `registered` flag on rows that already exist.

### Sort order

Hooks appear after all `command` / `template` / `script` rows in `artifact list --json`. Within the hook block, rows are sorted primarily by `eventName` (alphabetical) and secondarily by the winner's `priority` (ascending). Two rows in the same event at the same priority preserve their original insertion order — matching the runtime's stable-sort tiebreak in `HookExecutor.get_hooks_for_event`.

## JSON Errors

On failure, nothing is written to stdout. A single-key JSON envelope is written to stderr and the process exits with code `1`:

```json
{ "error": "unknown artifact hook:before_specify:absent.cmd" }
```

| Message                                             | Cause                                                            |
| --------------------------------------------------- | ---------------------------------------------------------------- |
| `not a Spec Kit project: no .specify/ directory found` | Run outside an initialized project                             |
| `unknown artifact <name>`                           | No artifact matches the requested name (and kind, when given) — same envelope for unknown hooks (`hook:{event}:{command}`) |
| `ambiguous artifact <name>: matches kinds [...]`    | The bare name matches more than one kind — re-run with `--kind`   |
| `artifact resolution failed`                        | The preset/extension registries could not be read, or artifact content could not be composed |

Exit code `2` is reserved for usage errors — a missing `--json` flag or an invalid `--kind` value (accepted: `command`, `template`, `script`, `hook`) — and emits a plain-text message on stderr rather than a JSON envelope.
