# Agent Integration Design

Integrations adapt the shared Spec Kit workflows to an AI coding agent. Their
**availability** (built-in, generic, or catalog-only) is separate from their
**output format** (commands, recipes, skills, or a custom layout). The Python
integration registry owns installation behavior; catalogs provide discovery,
not executable integration implementations. Trusted external adapter packages
are installed separately and loaded into that registry for their project.

## Availability

| Route | What ships | How users get it |
|---|---|---|
| Built-in | A registered class under `src/specify_cli/integrations/` and, for discovery, an entry in `integrations/catalog.json` | `specify init my-project --integration copilot` or, in an initialized project, `specify integration install copilot` |
| Generic | The registered `generic` integration, with a user-supplied `--commands-dir` and optional `--skills` | `specify init my-project --integration generic --integration-options="--commands-dir .agent/commands"` |
| External | A catalog entry pointing to an adapter archive | Register a trusted catalog, review the adapter, then `specify integration install sample-agent` |
| Community discovery | Metadata in the default `integrations/catalog.community.json` | Discover with `specify integration list --catalog` or `search`; review its source before configuring an install-enabled catalog |

The default community catalog is discovery-only. Listing, searching, or
fetching catalog metadata never imports catalog code. An install-enabled
catalog permits download, not execution without consent: installation prompts
before downloading/importing an adapter, or accepts explicit
`--trust-integration` authorization. Users must review external code; a catalog
listing is not a code audit or security endorsement.

## Built-in contract

Each built-in agent has one Python-safe subpackage: `copilot` lives in
`src/specify_cli/integrations/copilot/` and exposes `CopilotIntegration`.
Hyphenated keys use underscores in package names. Its class declares:

- `key`: unique user-facing identifier. CLI-backed integrations normally use
  the executable name: tool checks use the key and runtime dispatch defaults
  to it. Agents with a different executable must handle both paths explicitly;
  IDE-only agents use their canonical identifier.
- `config`: agent name, folder, commands subdirectory, install URL, and
  `requires_cli`.
- `registrar_config`: output directory, format, argument placeholder, and
  file extension.

Import and `_register()` the class in `src/specify_cli/integrations/__init__.py`
(both lists alphabetically). This registry is the source of built-in Python
integration behavior. If the agent supports non-interactive workflows, implement
`build_exec_args()` with the full base signature; `options()` declares
install-time `--integration-options`, not per-workflow runtime options.
Agent-specific native events can be declared on the integration. Set
`multi_install_safe = True` only for a static, non-overlapping agent root and
command directory; shared dynamic paths are not safe by default.

## Output flavors

Choose the smallest base class that matches the agent's native format. The
format bases render shared `templates/commands/*.md`; `IntegrationBase.setup()`
copies templates raw unless overridden. Paths below are relative to each
agent's configured root.

| Flavor | Base class | Typical output | Arguments |
|---|---|---|---|
| Markdown commands | `MarkdownIntegration` | `commands/speckit.plan.md` | `$ARGUMENTS` |
| TOML commands | `TomlIntegration` | `commands/speckit.plan.toml` | `{{args}}` |
| YAML recipes | `YamlIntegration` | `recipes/speckit.plan.yaml` | `{{args}}` |
| Agent skills | `SkillsIntegration` | `skills/speckit-plan/SKILL.md` | `$ARGUMENTS` |
| Nonstandard or dual-mode | `IntegrationBase` or a targeted override of a format base | Agent-specific files, companions, or settings | Agent-specific |

`registrar_config["args"]` selects the installed argument syntax;
`command_filename()` and `setup()` are override points when the native layout
demands them. Keep mode selection, invocation spelling, and registration in
sync. Agent-specific layouts and options belong in the integration code and
the [supported-integrations reference](../docs/reference/integrations.md).

Core templates that call scripts declare `sh`, `ps`, and `py` commands in
`scripts:` frontmatter; template processing replaces `{SCRIPT}` with the
selected variant. `py` is opt-in; non-interactive init defaults to `sh` on
POSIX or `ps` on Windows. Maintain equivalent stdout behavior across all three.
Bundled extension commands do not yet use this core-template script routing.
`__AGENT__` and command references are resolved during rendering, not by
adding per-agent wrapper scripts. For `generic`, extension registration
resolves the persisted `--commands-dir` rather than the static registry
placeholder; `--skills` emits skills into that same directory.

Core command templates also use `{PRE_HOOK_SCRIPT}` and `{POST_HOOK_SCRIPT}`.
Rendering selects the same `sh`, `ps`, or `py` variant as the command's main
script; the shared-infrastructure installer includes the selected native
pre/post entry points. The CLI validates hook configuration on write and
materializes ordered per-event JSON with a snapshot of `.specify/extensions.yml`.
CLI writers serialize publication, and each variant checks the snapshot and
generated response digest before returning hooks. Each reads the projection
in its own runtime, without depending on another variant or on runtime PyYAML;
it rejects stale, corrupt, or missing projections.
The legacy YAML resolver remains for projects not yet refreshed. The resolver
returns ordered hook metadata as JSON; agent commands themselves remain the
responsibility of the agent. The command/skill registrar resolves these
placeholders too when a preset wraps a core command.

## External adapter package contract

A standalone ZIP, tar.gz, or tgz archive needs only these root files (a single
enclosing archive directory is also accepted):

```text
integration.yml
__init__.py
```

The descriptor is adapter metadata, not an inventory of Spec Kit commands:

```yaml
schema_version: "1.0"
integration:
  id: sample-agent
  name: Sample Agent
  version: "1.0.0"
  description: Adapter for Sample Agent
requires:
  speckit_version: ">=1.1.2.dev0"
```

`integration.author`, `repository`, and `license` are optional metadata.
When present in a descriptor or catalog entry, each must be a non-empty string.
Their types are validated before importing package code and on installed reload.
`requires.tools` is an optional list of mappings with a non-empty `name`,
optional boolean `required` (default `true`), and optional PEP 440 `version`
constraint. Installation and `specify check` probe required descriptor tools on
PATH. If a CLI adapter declares no required tools, `specify check` probes its
runtime executable rather than assuming its catalog ID is an executable.
Tool version detection is adapter-specific, not a generic invocation of arbitrary
`--version` commands. The Spec Kit constraint is parsed and enforced on install
and load, including development versions. Legacy `provides.commands` and
`provides.scripts` remain accepted and validated as optional metadata, but
are neither required nor used to install core commands.

The root module exports exactly one concrete `IntegrationBase` subclass with
`key == integration.id`. It can inherit a host format base and use relative
imports from helper modules in its own package:

```python
from specify_cli.integrations.base import SkillsIntegration


class SampleIntegration(SkillsIntegration):
    key = "sample-agent"
    config = {
        "name": "Sample Agent",
        "folder": ".sample-agent",
        "commands_subdir": "skills",
        "install_url": "https://example.com/sample-agent",
        "requires_cli": False,
    }
    registrar_config = {
        "dir": ".sample-agent/skills",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": "/SKILL.md",
    }
    multi_install_safe = True
```

`config.name` must match the descriptor. An optional class `version` must match
its version. Display names are rendered as literal text in discovery and lifecycle output;
brackets and Rich-like tags are valid name content, not console formatting.
`config` and `registrar_config` must provide the fields above; the registration
directory must match `folder/commands_subdir`. Output paths
must be canonical, project-local, and outside `.git` and `.specify`.
Registration extensions must be plain dotted filename suffixes (such as
`.md`) or, for Markdown skills, `/SKILL.md`; path traversal is not allowed.
The public class attribute `invoke_separator` must be a non-empty string;
`dev_no_symlink` and `multi_install_safe` must be booleans, including when
registrar configuration supplies its own optional values.
An explicit `registrar_config.invoke_separator` takes precedence over the class
default. `dev_no_symlink` is enabled when either the class or registrar
configuration enables it. Healthy registration and persisted recovery metadata
use the same resolved configuration.
An optional `registrar_config.legacy_dir` must be a non-empty canonical
project-relative directory under the same reserved-root and symlink restrictions;
home-relative destinations are not supported for external adapters.
An adapter's primary root and optional legacy destination must not overlap,
regardless of whether it supports multi-install. Multi-install-safe adapters
also cannot overlap another integration's agent roots or legacy destinations.
Comparisons use case-folded path components on every platform so
packages remain safe on case-insensitive filesystems. Custom
setup must keep generated agent files under its declared root, track writes
with `IntegrationManifest`, and leave shared infrastructure ownership to the
host. Use the host's format bases rather than copied core templates.

CLI adapters override `build_exec_args(prompt, *, model=None,
output_json=True, integration_args=None, integration_options=None,
project_root=None)` as appropriate. Every explicitly declared host keyword
parameter must have a default; accepting omitted keywords through `**kwargs`
is also supported. Validation checks both prompt-only and complete host calls.
An adapter using only the host API and
standard library needs no pip installation or source-registry edit.
Import-side-effect registration is rejected.

Catalog entries require matching identity, name, version, and description,
plus `download_url`. Optional descriptor metadata and `requires`, when present
in the catalog, must match too. `sha256` is an optional 64-character hexadecimal
digest of the archive bytes; publishing a pinned URL and digest is recommended.
Downloads use the host authentication configuration, including authenticated
GitHub release assets. HTTPS is mandatory except for loopback HTTP development
servers. Redirects, archive format declarations, traversal, symlinks, and
bounded download/extraction limits are enforced.

### Storage, loading, and lifecycle

Trusted executable packages live in
`.specify/integrations/packages/<id>/`; their provenance, descriptor metadata,
and per-file hashes live in
`.specify/integrations/packages.json`. They are **not** generated agent files
and do not appear in `<id>.manifest.json`. The managed `.specify/.gitignore`
excludes both executable packages and their registry.
Authoritative execution consent lives in `~/.specify/integration-trust.json`,
never in project metadata. Projects containing that canonical trust path,
including a project rooted at `~/.specify`, cannot install or load adapters.
The trust path and local state are validated before importing a candidate.
Each grant binds the canonical project root,
integration ID, and the complete verified package file-hash mapping. Copying
a project, changing users, changing package bytes, or deleting a grant requires
a new local decision; a legacy project `trusted` field grants no authority.
Consent is checked before every load, including configuration-cache reuse.
The trust reader and writer share a 1 MiB byte limit. An update that would
exceed it fails before replacement, leaving the previous grants and recovery
records readable; existing grants are never evicted implicitly. The writer
persists the exact measured UTF-8 bytes, without platform newline translation.
Only recorded, locally trusted packages are loaded, and hash/descriptor
validation precedes import. Missing, modified,
incompatible, or unimportable implementations produce explicit errors.
Python source is verified again when imported, including relative helper
modules; cached bytecode is never used to execute package code.

Execution entry points load installed adapters before setup, agent configuration,
extension/preset registration, artifact resolution, status, and workflow dispatch. Fresh CLI
processes use the persisted package, not the catalog. Changing projects unloads
external registry entries, synthetic Python packages and their submodules, and
refreshes agent configuration/registrar caches in place. Built-in keys cannot
be replaced by packages.
Registry loading and configuration snapshots are synchronized. Each runtime
dispatch pins a context-local project registry and its verified Python namespaces
until dispatch finishes, including lazy relative imports. Switching another
thread to a different project cannot replace that dispatch's adapter, and
independent agent processes are not serialized by the registry lock.
Command and skill registration also pin the target project's registry for the
entire rendering operation, including implementation hooks and lazy relative
imports. A retained registrar or interleaved registration in another project
cannot substitute another project's adapter while rendering.
Catalog listing, catalog discovery, and `integration info` read metadata without
importing installed adapters. Merely checking that a directory is a Spec Kit
project does not load adapter code; registration managers load it when they
actually need the adapter's rendering configuration.
Workflow metadata inspection (`workflow status` and `workflow info`) also leaves
adapters unloaded, even if an installed package is damaged. Workflow run/resume
load adapters within their error-handling boundary and reload before dispatch.
Extension-native event refresh also loads and pins the project's trusted adapters,
including fresh-process event-only extension add/remove and enable/disable.
Adapter loading failures are reported as event-refresh failures, not skipped.

`init --integration`, `integration install`, and `integration switch` can
resolve an uninstalled adapter from an install-enabled catalog. `use` selects
an already installed adapter. `upgrade` downloads the catalog's current
version and requires a new trust decision; it still refuses modified generated
files unless `--force` is supplied. `uninstall` removes executable code and its
registration while retaining modified generated files unless forced.
Adapter lifecycle mutations are project-locked and journal operation-owned
file changes, including package code, metadata, shared infrastructure, and
generated artifacts. Initial inventories retain only names and filesystem
metadata; they do not copy agent trees, user data, or the installed package
store. Content snapshots are created lazily before the first observed mutation,
with an aggregate limit of 128 MiB of file content and 4,096 entries per
transaction. Exceeding either limit fails before the affected write or removal.
Preset and extension package installation/replacement, configuration rescue
directories, and project extension configuration participate in the journal.
Package replacements keep one bounded directory snapshot rather than duplicate
snapshots for every generated descendant. Replacement observations complete at
the actual copy/config-restore boundary, including failed copies, before command
registration or registry commit. Later observed descendant writes update that
directory's recorded identity without taking duplicate snapshots.
External init aborts its transaction when a requested preset or extension install
raises; built-in init without an external transaction retains its best-effort
optional-install behavior. Late external-init failures therefore
remove new packages and restore pre-existing package contents, not orphan sources
after their registries and agent outputs have been rolled back.
Failed setup or durable package commit restores those
changes, not entire agent directories or all of `.specify`. Independent workflow
progress and unowned user files are left untouched.
While the lifecycle journal is active, install/switch failure handlers defer
cleanup to it rather than forcing teardown or rewriting fallback state first.
This preserves pending-file conflicts and the original directory inventory.
Rollback removes newly created empty parent directories only until the first
pre-existing parent;
original empty directories are preserved in project and built-in home scopes.
This includes empty Kimi legacy directories removed during migration or teardown;
non-empty legacy directories are not snapshotted merely for parent cleanup.
This also applies when an adapter records an already-written file.
Custom writes to existing files must use `IntegrationManifest.record_file()`
or the host's before-write primitives, such as
`IntegrationBase.write_file_and_record()`. `record_existing()` alone remains
supported for new files and unchanged existing files; it cannot recover bytes
already overwritten outside the journal. Such an unobserved overwrite fails
explicitly, retains the resulting file rather than deleting it, and reports
that its original bytes cannot be restored.
Concurrent edits to a managed file are preserved and reported with retained
recovery snapshots; a later host
write refuses to overwrite an edit made after its previous write. Extensions and presets
remain independently installed and follow the active integration as before.
If a write fails before its completion is observed, changed or newly present
bytes cannot be attributed to that operation. Rollback leaves those pending
paths untouched and retains recovery snapshots, including when a previously
existing path was deleted. An unchanged pending path needs no restoration.
Host settings merges, native event updates/removal, legacy migrations, and
extension/preset rendering caches participate in the journal without becoming
uninstall-owned files. Existing built-in home-scoped destinations are journaled
only for participating built-ins; external adapters remain project-local.
Host write helpers reject symlinked destinations and ancestors before creating
directories or writing. Manifest recording validates lexical paths before
resolution, including project-local and dangling symlinks, so resolution cannot
hide a link to an unrelated project file. Removing an owned leaf symlink unlinks
the link itself without following its target; declared output directories cannot
be symlinks. Manifest cleanup validates lexical ancestors before reading or
deleting a tracked file and immediately before unlinking it, even without an
active lifecycle journal. Unsafe paths are reported as preserved files rather
than followed through a symlink.
Cancelling initialization discards the prepared adapter without installing code
or reporting success. Stable lifecycle locks are user-local and keyed by
canonical project root, so cancellation does not create target lock scaffolding;
rollback removes a newly created target root only when it remains empty.
Local consent is atomic and user-local; a grant for an explicitly authorized
package may remain after failed setup, but cannot authorize different bytes or
a different project.
Metadata changed by another operation during preparation is not overwritten;
the operation exits with an explicit retry error.
External uninstall unregisters the adapter's owned extension/preset artifacts
before unloading its code, preserves user-modified contributions, and
re-registers contributions for a remaining default integration.
If filesystem recovery itself fails, the error reports retained snapshot
paths for manual recovery rather than deleting the only backup.
`upgrade --force` and `uninstall --force` can recover a recorded adapter whose
implementation is missing, modified, incompatible, or fails to import. Recovery
excludes only that adapter, validates the others, and uses validated manifest
ownership and registrar configuration saved in the user-local trust store for
cleanup. Recovery records bind the project and adapter to the previously trusted
package identity, verified registrar configuration, and generated paths.
New records retain the verified package file-hash mapping locally, so recovery
checks the package identity against its original project, key, and hashes,
not damaged bytes or edited project metadata. The identity must still have a
local trust grant; otherwise cleanup treats ownership proof as unavailable and
preserves generated files. Older hash-less ownership records remain supported
when their package identity has a local grant.
Ownership is replaced only after the durable package loads successfully, so a
failed upgrade cannot replace the previous adapter's recovery authority.
Generated-file manifests distinguish `whole`, `partial`, and `shared`
ownership. The event dispatcher is shared; merged native event settings are
partial. Trusted host event refreshes update only their touched ownership
claims in the user-local record, and active lifecycle transactions defer those
updates until their project writes commit. Editable project manifests cannot
add unrelated cleanup authority or promote shared settings to whole-file
ownership. Damaged fallback cleanup preserves shared and partial files,
including with `--force`; manual event cleanup may be needed. Older local
records without ownership modes conservatively preserve unproven files.
Edited project configuration or forged manifest ownership is rejected, as is
cleanup overlapping another integration's root. It reports this
recovery explicitly and never bypasses catalog source policy or the replacement
package's trust decision. Ordinary selection and lifecycle operations still fail
explicitly for damaged installed implementations.
After copying a project or changing users, review the adapter and run
`specify integration upgrade <id> --force --trust-integration` using an
install-enabled catalog to establish local consent. Forced uninstall can remove
an untrusted or missing package without importing it.
Forced recovery also accepts a recorded package leaf replaced by a regular file
or a symlink: it unlinks that owned leaf without following it, while rejecting
symlinked ancestors. Failed commits restore the original damaged leaf.
When local ownership proof is unavailable, including copied projects or older
grant-only trust stores, recovery preserves old generated files from cleanup and
warns that manual cleanup may be needed. A newly trusted replacement still
renders its declared destination under normal `upgrade --force` semantics;
old-only destinations are not deleted using unverified project metadata.

See the [catalog contract](../integrations/README.md) and
[user reference](../docs/reference/integrations.md) for public commands.

## Ownership and lifecycle

An installation records its files and SHA-256 hashes in
`.specify/integrations/<key>.manifest.json`. Custom `setup()` code must track
files it creates via the manifest (`record_file()` or the base class's
write-and-record helpers). These APIs accept `ownership="whole"` (the default
for generated files), `"partial"`, or `"shared"` where applicable; recording
an existing file without a new mode retains its current mode. Do not claim
whole-file ownership merely because you merged settings into a user file:
partial and shared files are preserved by manifest-only uninstall.
`teardown()` preserves modified tracked files by default; `--force` can remove
them. Keep agent-specific settings and events consistent with that lifecycle.

The integration does **not** own agent context files such as `AGENTS.md` or
`CLAUDE.md`. The opt-in `extensions/agent-context/` owns their defaults,
configuration, and managed sections; do not add `context_file` fields or
context-file handling to the CLI. `specify init` does not enable the extension
implicitly. Extensions and presets register command or skill overrides for the
current default integration, not every installed integration.

## Integration delivery boundary

Integration-specific behavior belongs in the integration package. Its delivery
PR may also include registry wiring, catalog metadata, integration-specific
tests, documentation, and agent-specific devcontainer tooling outside that
package. File location alone does not determine whether a separate PR is needed.

If delivery requires changes to shared runtime behavior, integration base
classes, rendering, lifecycle management, CLI behavior, or core templates or
scripts, it requires **at least two PRs**: a separate prerequisite PR for the
shared behavior and a PR for the integration itself. The shared change must
have independent justification and behavioral coverage, including regression
evidence for bug fixes, and must work and be testable without the new
integration. An agent-specific workaround is not sufficient justification for
changing core behavior.

The integration PR must identify its prerequisite PRs and must not merge until
they have merged. See the
[integration PR submission requirements](../CONTRIBUTING.md#integration-pull-requests).

## Adding an agent

1. Run `specify integration scaffold my-agent --type markdown` from this
   repository (`toml`, `yaml`, and `skills` are also supported), or start with
   a custom class only when necessary.
2. Review the generated `config` and `registrar_config`; register the class
   alphabetically and add a matching entry to `integrations/catalog.json`.
3. Add focused coverage in `tests/integrations/test_integration_<package_dir>.py`
   for metadata, generated output, installation, and uninstall (including
   preservation of edited files where applicable).
4. Exercise `specify init my-project --integration <key>` and the install/uninstall
   lifecycle; update the [supported agents](../docs/reference/integrations.md)
   and devcontainer setup if the agent needs additional tooling.

The scaffold creates a package and test skeleton, **not** registry or catalog
entries. Prefer existing bases and shared processing over copied setup loops.
