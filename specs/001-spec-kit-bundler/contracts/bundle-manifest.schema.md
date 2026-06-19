# Contract: Bundle Manifest (`bundle.yml`)

**Feature**: Spec Kit Bundler | **Date**: 2026-06-19

The manifest is the hand-written source of truth for a bundle (no scaffold generates it, FR-007). `specify bundle validate` enforces this contract; `specify bundle build` packages a manifest that satisfies it.

## Shape

```yaml
schema_version: "1.0"

bundle:
  id: "security-researcher"            # required, slug, unique within a catalog source
  name: "Security Researcher"          # required
  version: "1.0.0"                     # required, semver
  role: "security-researcher"          # required, open-ended metadata (not a closed enum)
  description: "One-stop SDD setup..."  # required
  author: "acme-platform-team"         # required
  license: "MIT"                       # required

requires:
  speckit_version: ">=0.9.0"           # required, version constraint (evaluated with `packaging`)
  tools: []                            # optional, required external tools
  mcp: []                              # optional, required MCP servers

# Optional. Absent => "agnostic" bundle: inherits the project's active integration (FR-004/FR-014).
integration:
  id: "claude"

provides:
  extensions:                          # optional; each pinned
    - id: "ci-guard"
      version: "1.2.0"
      source: null                     # optional: catalog id / URL / path; null => active stack
  presets:                             # optional; priority + strategy passed through to preset machinery
    - id: "security-compliance"
      version: "1.1.0"
      priority: 5                      # lower number wins in the preset stack
      strategy: "append"               # one of replace | prepend | append | wrap
  steps: []                            # optional; may stay empty until the step catalog lands
  workflows:                           # optional; each pinned
    - id: "secure-sdd"
      version: "1.0.0"

tags: ["security", "compliance"]        # optional
```

## Field rules (validation)

| Path | Required | Rule |
|------|----------|------|
| `schema_version` | yes | Must be a supported value |
| `bundle.id` | yes | Non-empty slug; unique within its catalog source |
| `bundle.name` | yes | Non-empty |
| `bundle.version` | yes | Valid semver |
| `bundle.role` | yes | Non-empty string; not validated against a fixed list (FR-031) |
| `bundle.description` | yes | Non-empty |
| `bundle.author` | yes | Non-empty |
| `bundle.license` | yes | Non-empty |
| `requires.speckit_version` | yes | Valid version constraint; install/update refuse if installed version is lower (FR-016) |
| `integration.id` | no | If present, must reference a known integration; conflict handled at install (FR-019) |
| `provides.extensions[].id/version` | id yes | Each installable ref pinned to a version; reference must resolve (FR-005) |
| `provides.presets[].id/version` | id yes | Pinned; `priority` integer required; `strategy` in {replace,prepend,append,wrap} |
| `provides.steps[]` | no | May be empty; forward-compatible with the future step catalog |
| `provides.workflows[].id/version` | id yes | Pinned; reference must resolve |
| `tags` | no | List of strings |

## Validation outcomes (`specify bundle validate`)

- **PASS**: well-formed YAML, schema-valid, all required fields present, every `provides.*` reference resolves against the active catalog stack (or pinned URL/path), `requires.speckit_version` parses.
- **FAIL** (each names the specific problem):
  - Missing required field → name the field.
  - Unresolved component reference → name the offending `id@version`/source.
  - Invalid version/constraint → name the field and value.
  - Invalid preset strategy/priority → name the entry.

## Invariants

- A manifest expands deterministically to a concrete component set; `specify bundle info` shows exactly that set, and `specify bundle install` adds exactly that set (transparency, SC-002).
- The manifest declares **at most one** integration. Multiple bundles stacked in a project may each declare an integration, but only one can be active — the install-time conflict guard enforces this (FR-019).
- Presets carry priority/strategy that are **passed through** to the preset machinery; the bundle introduces no additional resolution.
