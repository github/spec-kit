# Bundles

Bundles compose existing Spec Kit components — extensions, presets, workflows, and steps — into a single, versioned, installable unit. Where extensions and presets are primitives, a bundle is a curated stack that declares everything a team or role needs and installs it in one step through each component's own machinery. Bundles add no new runtime behavior of their own: they are a distribution and composition layer over the primitives you already use.

A bundle is described by a `bundle.yml` manifest and is discovered through the same catalog stack as other components. Installing a bundle resolves its declared components against pinned versions, checks active-integration and shared-component-version conflicts, and applies each component idempotently with full provenance tracking so it can be cleanly removed or refreshed later.

For a concrete starting point, see the
[example bundle manifests](https://github.com/github/spec-kit/tree/main/examples/bundles)
for product managers, business analysts, security researchers, and developers.
These demonstrate packaging a role-based setup, not filled generated feature
specs; for end-to-end usage examples, see
[community walkthroughs](../community/walkthroughs.md).

## First-party Bundles

Spec Kit ships a first-party bundle catalog in `bundles/catalog.json`. These bundles are curated, marked `verified: true`, and resolve through the built-in `builtin://default` catalog source.

| Bundle    | Role        | Components                                            | Use case                                |
| --------- | ----------- | ----------------------------------------------------- | --------------------------------------- |
| `bugfix`  | `developer` | `bug` extension + `bugfix` workflow                   | Guided assess → gate → fix → test       |
| `assess`  | `developer` | `assess` extension + `assess` workflow                | Idea triage before Spec-Driven Development |

Install a first-party bundle the same way you install any bundle (`add` is an alias for `install`):

```bash
specify bundle install bugfix
specify bundle add assess
```

The first-party catalog is fetched from the repository online and falls back to the packaged wheel snapshot offline so discovery works without network access. A local bundle manifest can install bundled extensions and workflows with `--offline`. Catalog-discovered bundle manifests still resolve from their `download_url`, so `specify bundle add <id>` requires network today; fully offline catalog installation is tracked as follow-up work.

## Search Available Bundles

```bash
specify bundle search [query]
```

| Option      | Description                  |
| ----------- | ---------------------------- |
| `--offline` | Do not access the network    |
| `--json`    | Emit machine-readable JSON   |

Searches all active catalogs for bundles matching the query. Without a query, lists every available bundle with its version, role, source, and a trust indicator (`verified` for org-curated catalog entries, `community` otherwise) so you can judge trust before installing.

## Bundle Info

```bash
specify bundle info <bundle_id>
specify bundle info <bundle_id> --versions
```

| Option       | Description                       |
| ------------ | --------------------------------- |
| `--offline`  | Do not access the network         |
| `--json`     | Emit machine-readable JSON        |
| `--versions` | List the current and historical catalog releases |

Shows full metadata for a bundle along with the **fully expanded component set** it installs — every extension, preset, step, and workflow with its pinned version, plus preset priority and strategy. The output also includes a trust indicator (`verified` vs `community`) so you can judge trust before installing. This preview is the same plan `install` applies, so you can see exactly what will be added before committing. For bundles with references, text output includes a `References` summary, with each referenced bundle's own trust level (`verified` or `community`), and marks referenced components with their shortest origin chain; overridden components show the overridden version and origin. JSON adds `references` entries with `id`, `version`, resolved `source`, `install_policy`, `via`, and the referenced bundle's own `verified` and `trust`; referenced component entries add `origin` and, when applicable, `overrides`. Discovery-only references are marked `discovery-only, not installable`. Foreseeable overlaps and version conflicts with components already required by installed bundles are surfaced here as well; a bundle can require a component without having installed it.

Use `specify bundle info <bundle_id> --versions` to inspect the catalog history without downloading a bundle manifest. With `--json`, it emits the bundle ID, available versions, current version, source, and install policy.

## Install a Bundle

```bash
specify bundle install <bundle_id | path>
```

| Option           | Description                                                         |
| ---------------- | ------------------------------------------------------------------ |
| `--integration`  | Override the integration used when initializing/installing         |
| `--offline`      | Do not access the network                                          |
| `--refresh`      | Refresh owned components from the supplied bundle source           |
| `--version`      | Install an exact historical or current catalog release             |

Installs a bundle's full component set through each primitive's machinery. The argument may be a catalog bundle id, or a local path to a built `.zip` artifact, a bundle directory, or a `bundle.yml` file; local sources install directly without consulting the catalog stack.

If the current directory is not yet a Spec Kit project, `install` initializes one first so a fresh checkout reaches a working state in a single command. `--integration` selects the integration when initializing a new project, and confirms the target when a bundle pins a specific integration but the project's active integration can't be determined (missing or unreadable `.specify/integration.json`). It does **not** override an already-initialized project's active integration: if a bundle targets a different integration than the project's, install aborts with no changes. Integration-agnostic bundles inherit the project's active integration. Without `--refresh`, installation is idempotent — already-installed components matching their pins are skipped, as are bundle-owned compatible packaged patch releases with a warning (see below). Other differing or missing installed versions cannot satisfy a pin. Only `--refresh` can repair a drifted version owned exclusively by this bundle; independently installed components are skipped and never adopted or replaced. On failure, no provenance record is written (a failed install records nothing), and the components installed during that run are removed on a best-effort basis — removal errors are swallowed, so partial on-disk state may remain.

Installed-bundle records store required component pins separately from contributed components. A compatible independently installed component satisfies a bundle's requirement but remains independently owned: its pin still blocks a later bundle from installing an incompatible version, while removing the bundle does not uninstall it. An unpinned install or refresh cannot replace a component another bundle requires at a pinned version; sharing an already installed matching version without refreshing remains allowed. Shared bundles must also agree on component source and, for presets, priority and strategy before installing or refreshing the shared component. Older records without the requirement list retain their known contributed pins; reinstall or refresh the bundle to record its full requirements.

A normal install rejects a change to an already-recorded bundle's version or owned component metadata (version, source, preset priority, or strategy), including removal of an owned component. This applies even if a local manifest keeps the same bundle version. Reordering unchanged components or adding new components does not require refresh. To apply changes to a local bundle without adding it to a catalog, pass the revised source with `--refresh`:

```bash
specify bundle install ./new-release/bundle.yml --refresh
```

The source may also be a bundle directory or `.zip` artifact. Refresh uses the same primitive update path as `bundle update`, re-applies components owned by a bundle, and removes previously owned components omitted from the new manifest unless another bundle still needs them. Components installed independently remain untouched and are not adopted. The success summary includes refreshed and removed counts. The bundle record advances only after the operation succeeds; as with `bundle update`, already-installed components modified during a failed refresh are not rolled back.

A local bundle source supplies the manifest, not its component payloads. Components resolved through catalogs still require network access to refresh, even when already installed. Add `--offline` only when the components being installed or refreshed ship with Spec Kit; otherwise the command reports which component needs network access. Re-run without `--offline` to fetch that component through its catalog.

**Packaged patch compatibility.** When an extension, preset, or workflow shipped
with the CLI is a newer stable patch release within the pinned major/minor
version, installation and refresh warn and use that packaged release. For
example, a bundle pinning `bug` to `1.0.0` can use packaged `bug` `1.0.1` without
editing its manifest. Validation reports the same warning. Downgrades,
major/minor mismatches, and differing prerelease versions remain errors; an
explicit component `source` also retains exact-pin enforcement. Catalog-resolved
components still require exact matches. This exception improves compatibility
across CLI upgrades, but a patch release is not a guarantee of unchanged behavior.

Bundle records retain requested versions in `required_components` and
`contributed_components` and
store actual known installed versions under `installed_versions`, keyed by
`kind:id` (for example, `"extensions:bug": "1.0.1"`). These are also visible in
`specify bundle list --json`. Component version ranges, `latest`, and omitted
extension versions are not supported.

## Bundle References

A bundle can compose other bundles with exact, pinned references in
`provides.bundles`. A non-empty reference list requires manifest schema `1.1`;
empty or null lists are treated as no references. Each reference has a bundle
ID, an exact SemVer `version`, and an optional `source` naming the expected
winning bundle catalog (not a URL). Reference IDs are safe slugs, must be
unique within the manifest, and cannot name the parent bundle:

```yaml
schema_version: "1.1"
bundle:
  id: team
  name: Team setup
  version: 1.0.0
  role: developer
  description: A team bundle
  author: Example team
  license: MIT
requires:
  speckit_version: ">=0.1.0"
provides:
  bundles:
    - id: bugfix
      version: 1.0.1
      source: default
    - id: qa-pack
      version: 2.0.0
```

References resolve at command time through the effective bundle catalog stack.
The stack's winning entry is selected for each exact pin; an explicit `source`
is an assertion that this is the winning catalog, not a request to change
precedence; a mismatch is an error and does not fall through to another
catalog. A referenced bundle from a discovery-only source can be inspected
by `info`, but `install`, `update`, and online `validate` reject it as
non-installable. Every bundle ID may have only one version in an expansion;
cycles and a second version for the same ID are errors.

The expansion is one flat component plan. Referenced bundles are walked
recursively in declaration order (depth-first), followed by the declaring
bundle's own components, while preserving the existing extension, preset, step,
and workflow grouping. A component is installed at most once per `kind:id`.
Copies agree when their version and `source` match (omitted and set `source`
values differ); extension and preset copies must also have the same `priority`,
and preset copies must also have the same `strategy`.
Other differences between sibling references are conflicts that must be fixed
in the parent. At every level, a bundle's own declaration wins over its
references, takes the declaration's position, and emits a warning describing
the override and its origin chain.

Expansion allows at most 10 levels of reference nesting and 50 distinct
referenced bundle IDs, excluding the root. A cycle is rejected with its
reference chain. At install and update time, the Spec Kit version requirement
is checked for every bundle in the graph, and an incompatible requirement is
a hard error, while the root bundle remains the only integration gate: a
referenced bundle's differing or unknown integration is a warning.
`requires.tools` and `requires.mcp` are unioned across the graph
and rendered through the existing tool and MCP warnings.

The installed parent record contains the expanded component set and an
optional `bundle_references` JSON key listing each direct and transitive
reference once with its resolved catalog source. There are no child-bundle
records. `bundle update` follows the parent's current manifest and its pinned
references; remove and refresh retain the existing ownership and component
lifecycle rules.

Referenced manifests require network access. For a local root manifest,
`install` can identify the first reference and fail offline with that reference
named. A catalog-root `install`, `info`, or `update` can instead fail earlier
while fetching its catalog or root manifest, before any reference can be known.
`validate --offline` warns once per declared reference that it was not expanded.
`bundle build` performs only the structural checks for references and does not
resolve or embed them.

**Known limitations.**

- Offline and local resolution of referenced bundles is not supported; referenced
  manifests need network-backed catalog downloads.
- First-party bundle catalogs keep no release history, so an exact pin to a
  first-party bundle can break when that bundle publishes its next release.
- A local bundle with references cannot be previewed with `bundle info`; local
  preview is deferred.
- Broader schema versioning and CLI compatibility checks/ranges are deferred.

> **Step payloads resolve through the step catalog only.** A bundle's `provides.steps` entries still resolve exclusively through the active step catalogs. Bundle-local `steps/<id>/` payloads and relative `provides.steps[].source` overrides are **not** resolved in this release, so a step declared that way cannot be installed offline. To ship a step with a bundle today, publish it to a step catalog the bundle's users can reach.

## Catalog Release History

A catalog entry can advertise a current release and approved historical releases. Older single-version catalogs continue to work unchanged.

```json
{
  "id": "team-setup",
  "version": "1.2.0",
  "download_url": "https://example.com/team-setup-1.2.0.zip",
  "sha256": "<sha256 for 1.2.0>",
  "releases": {
    "1.1.0": {
      "download_url": "https://example.com/team-setup-1.1.0.zip",
      "sha256": "<sha256 for 1.1.0>"
    }
  }
}
```

Each historical release needs its own `download_url` and a 64-character SHA-256 digest; as with current releases, a digest may use a case-insensitive `sha256:` prefix and surrounding whitespace, and other algorithm prefixes are rejected. A release's `requires`, `provides`, and `verified` fields are not inherited from the current release: put them in that release's record, or the release has no requirements, no provided counts, and is shown as `community`. Other shared metadata, such as the name, description, and author, is inherited, and a release record may override it. A release record cannot contain `id`, `version`, or `releases`.

`specify bundle install team-setup --version 1.1.0` selects the bundle release, downloads that release's artifact, verifies its digest, and checks that its manifest declares the catalog ID and the same version as the selected release. Equivalent spellings such as `v1.1.0` and `1.1.0` match; the catalog key spelling is display-only. It never overrides component pins inside `bundle.yml`. `--version` is catalog-only, so it cannot be blank, used with a local path, or combined with `--refresh`.

Only the highest-precedence catalog that lists a bundle is consulted; a missing version does not fall through to a lower-priority catalog. Discovery-only sources remain non-installable, including exact historical releases. Duplicate JSON keys anywhere in a catalog are rejected while it is read. Historical `download_url` values must use HTTPS (or HTTP on localhost), and release keys must be strict SemVer values that are PEP 440-comparable. Version keys must be distinct, including PEP 440-equivalent spellings such as `1.0.0-rc.1` and `1.0.0-rc1`, and cannot repeat the current version. `bundle update` always selects the current release. The first-party and community catalogs currently advertise one release per bundle.

Release history is validated when its catalog source loads. A malformed `releases` mapping makes `install`, `info`, `update`, and `search` fail while that source is consulted. Resolution stops after the first source that lists the bundle, so a malformed lower-precedence source remains unobserved when a higher-precedence source supplies that ID; `search` loads every source, so a shadowed malformed entry still causes it to fail.

## Update Bundles

```bash
specify bundle update [<bundle_id>]
```

| Option           | Description                                                                                                            |
| ---------------- | --------------------------------------------------------------------------------------------------------------------- |
| `--all`          | Update every installed bundle                                                                                         |
| `--integration`  | Override the integration used when refreshing components; applied only when the project's active integration can't be determined |
| `--offline`      | Do not access the network                                                                                             |

Re-resolves a bundle and **refreshes** its components through each primitive's update path, bringing already-installed components up to the bundle's newly pinned versions (or compatible newer packaged patches, with a warning) while preserving primitive-level overrides (such as preset priority). Provide a bundle id, or use `--all` to update everything installed.

**Pinned catalog releases.** Extensions, presets, workflows, and steps with version pins select that exact release from the highest-priority active catalog entry. Historical releases must be advertised under `releases` with their own artifact URL and SHA-256 digest; the bundler never guesses an old URL from the current one or falls through to another catalog. Legacy extension and preset entries that advertise no version are an exception: the bundler uses the winning entry as-is and cannot enforce its pin or verify the installed archive's version. Publish a versioned entry to make that pin enforceable. The primitive installer uses the selected workflow or step record without re-reading the catalog, and verifies downloaded archive or workflow/step metadata against that release. A pinned workflow that ships with Spec Kit uses its bundled copy when the version matches, and the catalog release when it differs and network access is allowed. A step without a pin installs the current catalog release.

Without an explicit `source`, bundled extensions and presets take precedence over catalog releases. Validation rejects an incompatible pin even when a matching catalog release exists; compatible newer stable packaged patches produce a warning instead. Specify the winning catalog as `source` to opt into its exact release.

> **One installed version per component ID.** Bundles sharing a component must agree on its pinned version. A different or unknown pin from another bundle is rejected before installation, including during `bundle update`; refreshing one bundle cannot replace a version required by another.

A bundle may list a component ID only once per kind; duplicate references in the same manifest are invalid, even if their pins agree.

An optional `source` in a `provides.<kind>` reference names the expected winning component catalog (as displayed by `specify <kind> catalog list`, or `specify workflow step catalog list` for steps). It is **not** an artifact URL and does not override catalog priority or install policy. When specified, the component is verified against that catalog even if already installed, rather than resolved from a Spec Kit-bundled copy; a different winning catalog or a discovery-only source prevents installation. If multiple active catalogs share the named source, bundle validation and installation reject it as ambiguous; give each catalog a unique name. Verifying an explicit source requires network access. Direct primitive `--from` URLs are a separate, explicitly requested route.

## Remove a Bundle

```bash
specify bundle remove <bundle_id>
```

Uninstalls only the components this bundle contributed, leaving any component that another installed bundle still needs in place (no collateral removals). If no other bundle owns a retained component, its contribution is transferred to a remaining requiring bundle so removing that bundle later can clean it up. Independently installed components are never adopted.

## List Installed Bundles

```bash
specify bundle list
```

| Option   | Description                  |
| -------- | ---------------------------- |
| `--json` | Emit machine-readable JSON   |

Lists the bundles installed in the project with their versions, required component counts (including components supplied independently), and install timestamps. With `--json`, a reference-bearing record also includes `bundle_references`, containing each resolved direct or transitive reference and its winning catalog source.

## Initialize a Project with a Bundle

```bash
specify bundle init [<bundle_id>]
```

| Option           | Description                              |
| ---------------- | ---------------------------------------- |
| `--integration`  | Integration override                     |
| `--offline`      | Do not access the network                |

Ensures the current directory is a Spec Kit project (initializing it idempotently if needed), then optionally installs the given bundle. Useful as an explicit one-step bootstrap for a new checkout.

Repeating `bundle init` skips components already installed by the bundle and preserves their local edits. It follows the same rules as a normal [`bundle install`](#install-a-bundle): components newly added to the manifest are installed and recorded, but it fails without changing the installed bundle if the manifest changes the recorded bundle version, changes an owned component's version, source, preset priority, or strategy, or removes an owned component. To refresh components or apply such changes, use `bundle update <id>` for a catalog bundle or `bundle install <path> --refresh` for a local source.

## Validate a Bundle

```bash
specify bundle validate
```

| Option       | Description                                                          |
| ------------ | ------------------------------------------------------------------- |
| `--path`     | Bundle directory or `bundle.yml` (default: current directory)       |
| `--offline`  | Verify references against bundled/installed components only          |

Reports whether a `bundle.yml` is well-formed and whether every declared component reference resolves at its pinned version. For a reference-bearing manifest, online validation expands the complete reference graph and checks every component in the expanded plan, including structural, cycle, version, source, conflict, and install-policy checks. References are checked against matching bundled or installed components and — when online — the exact release in the winning install-allowed catalog. An explicit `source` is verified against the winning catalog instead of resolving locally. Missing releases, mismatched sources, discovery-only sources, and malformed catalog metadata fail validation; references that cannot be checked offline or because a catalog is unreachable produce warnings. In `--offline` mode, each declared bundle reference produces a warning that it was not expanded. If a higher-priority catalog is unreachable before a match is found, the lookup remains unverified; a lower-priority match cannot settle it. Validation does not evaluate `requires.speckit_version` against the running CLI; `install` and `update` enforce that runtime compatibility gate. As with installation, legacy extension and preset entries advertising no version are accepted without verifying their pins.

## Build a Bundle Artifact

```bash
specify bundle build
```

| Option      | Description                                              |
| ----------- | ------------------------------------------------------- |
| `--path`    | Bundle directory (default: current directory)           |
| `--output`  | Output directory for the artifact                       |

Produces a single versioned, distributable `.zip` artifact from a bundle directory. The artifact embeds the manifest and can be installed directly with `specify bundle install <artifact.zip>`.

## Publish a Bundle

Bundle authors validate and package bundles locally, then host the generated artifact and catalog metadata where users can access it. A bundle catalog entry points at the bundle artifact, but the components declared inside `bundle.yml` still resolve through bundled components, installed components, or active extension, preset, workflow, and step catalogs.

If your bundle references components from non-default catalogs, document those catalog URLs and test the install path from a clean project with those catalogs added. Community bundle submissions should include that dependency-resolution evidence in the [Bundle Submission](https://github.com/github/spec-kit/issues/new?template=bundle_submission.yml) issue.

### What Happens After You Submit

1. GitHub applies the `triage-must-have` verdict when the issue is opened through the Bundle Submission form. Bundle submissions join extension and preset submissions in using this intake automation; the manual triage rubric for other issues remains unchanged.
2. A maintainer reviews the issue during issue triage and applies the separate `bundle-submission` label, which starts the automated catalog validation. On this public repository, contributors cannot apply that label themselves, so there is nothing to label or re-request — the issue simply waits in triage.
3. The automated workflow validates the submission and, when validation passes, updates `bundles/catalog.community.json` and `docs/community/bundles.md` in a draft pull request
4. A maintainer reviews the generated pull request and merges it when approved
5. Your bundle becomes discoverable via `specify bundle search`

## Manage Catalog Sources

Bundles are discovered through a priority-ordered stack of catalog sources (project, user, and built-in scopes). The built-in sources are:

- `builtin://default` — first-party bundles shipped in `bundles/catalog.json` (`bugfix`, `assess`, ...), install-allowed.
- `builtin://community` — community submissions in `bundles/catalog.community.json`, discovery-only.

Each source has an install policy. `install-allowed` sources can be installed
from; `discovery-only` sources appear in `search` and `info` but refuse
installation. Inspect the active stack before installing a bundle from a
non-default source.

> **Vet both the bundle source and its component catalogs.** A project can supply its own bundle catalog and `install-allowed` component catalogs (extension, preset, workflow, and step) under `.specify/`; that project configuration existing is not evidence anything in it was reviewed. Before installing a bundle from an unfamiliar project, run `specify bundle catalog list` — and the equivalent `extension`/`preset`/`workflow catalog list` and `specify workflow step catalog list` commands for the components it pulls in — and treat any source you didn't add yourself as unvetted until you've reviewed it.

### List the Catalog Stack

```bash
specify bundle catalog list
```

Prints the active, priority-ordered catalog stack with each source's scope and install policy.

### Add a Catalog Source

```bash
specify bundle catalog add <url>
```

| Option        | Description                                              |
| ------------- | ------------------------------------------------------- |
| `--policy`    | `install-allowed` or `discovery-only`                   |
| `--priority`  | Source priority (lower = higher precedence; default 10) |
| `--id`        | Explicit source id                                      |

Registers a project-scoped catalog source and persists it.

Re-adding the same source with the same ID, URL, policy, and priority succeeds without changing the configuration; different settings are rejected.

### Remove a Catalog Source

```bash
specify bundle catalog remove <id_or_url>
```

Removes a project-scoped catalog source. Built-in default sources cannot be deleted.

> **Note:** `search` and `info` work anywhere — with no project they fall back to the built-in/user catalog stack. The remaining state-changing commands (`list`, `update`, `remove`, `catalog`) require a project already initialized with `specify init`. `install` and `init` will initialize a project on demand when run in an uninitialized directory.
