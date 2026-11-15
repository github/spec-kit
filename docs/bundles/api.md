# Bundle API reference

This page defines the declarative bundle manifest, reference expansion, and
installed-record contracts. Bundles compose existing components; they do not
provide a separate execution API.

## Manifest

The UTF-8 `bundle.yml` file is a YAML mapping. Bundle ZIPs must contain it at
the archive root. The developing guide provides complete examples.

| Field | Requirement |
| --- | --- |
| `schema_version` | Required; `"1.0"` or `"1.1"` |
| `bundle` | Required metadata mapping |
| `requires.speckit_version` | Required nonempty Spec Kit version constraint |
| `requires.tools` | Optional list of tool names; defaults to empty |
| `requires.mcp` | Optional list of MCP server names; defaults to empty |
| `integration` | Optional mapping with a nonempty `id` |
| `provides` | Optional component/reference mapping |
| `tags` | Optional list of strings |

An absent or null `requires`/`provides` mapping is treated as empty, although
the required Spec Kit constraint must still be supplied. A present non-mapping
value is invalid. String-list fields cannot be bare strings or contain
non-string members.

### Metadata

All fields in `bundle` are required and nonempty:

| Field | Meaning |
| --- | --- |
| `id` | Filesystem-safe bundle identifier |
| `name` | Human-readable name |
| `version` | Exact semantic version |
| `role` | Role, team, or persona served |
| `description` | Description of the setup |
| `author` | Author or organization |
| `license` | License identifier |

IDs match `^[a-z0-9](?:[a-z0-9._-]*[a-z0-9])?$`: start and end with a
lowercase letter or digit, with lowercase letters, digits, dots, underscores,
and hyphens between. Path separators and traversal IDs are invalid.

Bundle and component versions use full `MAJOR.MINOR.PATCH` SemVer, optionally
with prerelease/build metadata and a leading `v` or `V`. Component ranges and
`latest` are not accepted. The Spec Kit requirement is instead a constraint,
such as `">=0.9.0,<2.0.0"`; it is evaluated during installation/update, not
against the running version by `bundle validate`.

`requires.tools` and `requires.mcp` generate requirement warnings. They do not
install tools, provision MCP servers, or verify those dependencies are present.

### Integration

```yaml
integration:
  id: copilot
```

Omitting `integration` or setting it to null makes a bundle
integration-agnostic. A mapping without a nonempty ID is invalid.

The root bundle must agree with the project's active integration. It does not
switch integrations. Referenced bundle integration differences or an
indeterminate effective integration are warnings rather than additional
integration gates.

### Component references

`provides.extensions`, `provides.presets`, `provides.steps`, and
`provides.workflows` are lists of mappings. Omitted or null lists are empty.
Each `(kind, id)` may appear only once in a manifest, even with identical pins.
The same ID in different component kinds is distinct.

| Field | Extensions | Presets | Steps | Workflows |
| --- | --- | --- | --- | --- |
| `id` | Required | Required | Required | Required |
| `version` | Required | Required | Optional | Required |
| `source` | Optional catalog name | Optional catalog name | Optional catalog name | Optional catalog name |
| `priority` | Optional; default `10` | Required integer, at least `1` | Not used | Not used |
| `strategy` | Not used | Required | Not used | Not used |

Explicit extension priority must also be at least `1`. Preset strategies are
`replace`, `prepend`, `append`, and `wrap`; their effects are defined by the
[preset composition contract](../presets/api.md).

`source` asserts the expected winning component catalog. It does not select a
lower-priority catalog, bypass a discovery-only policy, accept a direct
artifact URL, or refer to bundle-local payloads. Explicit sources are checked
even for already installed components, require network access, and reject
ambiguous catalog names.

Without `source`, packaged extensions and presets take precedence over their
catalogs. Packaged workflows may also be used. The CLI reference explains
stable packaged patch compatibility and catalog pin enforcement.

### Bundle references

A nonempty `provides.bundles` list requires schema `"1.1"`. An empty or null
list has no references and is also accepted under schema `"1.0"`.

```yaml
provides:
  bundles:
    - id: qa-pack
      version: 2.0.0
      source: team-catalog
```

| Field | Requirement |
| --- | --- |
| `id` | Required safe slug; unique in this manifest and different from the parent ID |
| `version` | Required exact SemVer |
| `source` | Optional expected winning bundle catalog ID, not a URL |

References are resolved at command time through the same effective bundle
catalog stack as the parent. An explicit source is an assertion, not a
precedence override. A mismatch fails without falling through to another
catalog.

## Reference expansion

The result is a single flat component plan, not nested installations.

### Ordering and conflict rules

References are walked depth-first in declaration order, followed by the
declaring bundle's own components. The final plan preserves component grouping:
extensions, presets, steps, then workflows.

Each component is installed at most once per `(kind, id)`. Repeated declarations
agree when versions and sources match; omitted and explicit sources differ.
Extensions and presets must also agree on priority, and presets on strategy.
An omitted extension priority equals its default of `10`.

Conflicting sibling references fail unless the declaring bundle resolves them
with its own component declaration. At every level, a bundle's own declaration
wins over its references, takes its own declaration position, and emits an
override warning with the replaced declarations' origin chains.

One bundle ID can have only one version in an expansion. A second version is
an error, not another installation. Choose compatible referencing releases to
resolve that conflict.

### Limits and gates

- Cycles are rejected with their reference chain.
- At most `10` levels of reference nesting are allowed.
- At most `50` distinct referenced bundle IDs are allowed, excluding the root.
- Install and update enforce the Spec Kit version requirement for every bundle
  in the graph.
- The root is the only integration gate. Referenced integration differences
  generate warnings.
- Tools and MCP requirements are unioned across the graph for warnings.

`info` can expand discovery-only references for inspection. Install, update,
and online validate reject them as non-installable. `validate --offline` does
not expand references and warns once per declared reference. `build` performs
structural checks only; it neither resolves nor embeds referenced bundles.

Referenced manifests require network-backed catalog downloads. Local/offline
reference resolution and local `bundle info` previews are not supported.
First-party bundle catalogs keep no release history, so a first-party reference
can become unavailable when the catalog advances. Broader schema compatibility
negotiation is not implemented.

## Installed records and ownership

The project stores provenance in `.specify/bundle-records.json`:

```json
{
  "schema_version": "1.0",
  "updated_at": "2026-01-01T00:00:00Z",
  "bundles": [
    {
      "bundle_id": "team-setup",
      "version": "1.0.0",
      "installed_at": "2026-01-01T00:00:00Z",
      "required_components": [
        {"kind": "extensions", "id": "bug", "version": "1.0.0"}
      ],
      "contributed_components": [
        {"kind": "extensions", "id": "bug", "version": "1.0.0"}
      ],
      "installed_versions": {
        "extensions:bug": "1.0.1"
      }
    }
  ]
}
```

| Record field | Meaning |
| --- | --- |
| `bundle_id`, `version` | Installed root bundle identity |
| `installed_at` | Original installation time, preserved across refresh/update |
| `required_components` | Every required component in the expanded plan, including independently supplied components |
| `contributed_components` | Components attributed to the bundle; always a subset of its requirements |
| `installed_versions` | Optional known actual versions keyed by plural `kind:id`, distinct from requested pins |
| `bundle_references` | Optional list of direct/transitive bundle references, each with `id`, `version`, and resolved catalog `source` |

Record component entries use plural `kind` names and contain `id`, `version`,
and any declared `source`, `priority`, and `strategy`. For a reference-bearing
bundle, only the parent has an installed record; child references are recorded
once, not installed as separate bundle records.

Required pins participate in cross-bundle conflict checks even when the
component was independently installed. Compatible independently installed
components are not adopted, refreshed, or uninstalled by the bundle. Components
already owned by other bundles can be shared.

Shared requirements must agree on version and source, extension/preset
priority, and preset strategy. A bundle update cannot replace a pin another
bundle requires. When removing a bundle or dropping a component during refresh,
components another bundle still needs are retained; ownership transfers to a
remaining requiring bundle if necessary.

Older records without `required_components` retain their known contributed
pins. A successful reinstall/refresh records the full requirements. Missing
records are treated as no bundles, but malformed records and incompatible
schema major versions are errors, not an empty installation.

Record writes happen after successful component operations. They do not make
installation, update, refresh, or removal globally transactional; see the CLI
reference for failure and rollback boundaries.

## See also

- [Developing bundles](developing.md)
- [CLI output and lifecycle behavior](cli.md)
- [Catalog entry and release contracts](catalogs.md)
- [Publishing bundles](publishing.md)
- [Bundle overview](overview.md)
