# Extension Architecture

This document defines the implemented architecture of Spec Kit extensions.
Extensions are project-local content packages that contribute commands, skills,
templates, scripts, hooks, runtime events, and configuration without adding
Python code to the extension runtime.

The implementation and executable tests are the source of truth for this
document. The command adapter conventions in
[Specify CLI Command Architecture](cli.md), the multi-adapter boundary in
[Shared Command Application Architecture](shared.md), MCP exposure in
[Specify MCP Command Architecture](mcp.md), and agent output formats in
[Agent Integration Design](integration.md) remain authoritative for those
respective concerns.

## Responsibilities and boundaries

The extension domain under `src/specify_cli/extensions/` owns:

- parsing and validating `extension.yml`;
- compatibility and command-namespace validation;
- project-local installation, enablement, disablement, update, and removal;
- the installed-extension registry and catalog stack;
- registration and cleanup of extension commands and generated skills;
- layered extension configuration;
- declarative hook registration; and
- extension lifecycle CLI commands.

Adjacent domains own behavior that extensions participate in:

- integrations render extension commands or skills into the active agent's
  native layout and refresh those outputs when the active integration changes;
- presets and artifacts resolve extension-provided commands, templates, and
  scripts as layers in the composed artifact stack;
- events validate and project extension-declared runtime events into supported
  agent-native event configuration;
- bundles install and remove extension components by calling the extension
  manager rather than reimplementing extension lifecycle behavior; and
- shared download, archive, authentication, file-change, and path-safety
  helpers provide common infrastructure.

An extension is declarative content. It does not register Python plugins,
replace CLI handlers, or import executable package code. External executable
agent adapters are integrations and follow
[the separate integration trust model](integration.md#external-adapter-package-contract).

## Manifest contract

Every extension root contains `extension.yml` with schema version `1.0`. The
required top-level mappings are:

```yaml
schema_version: "1.0"
extension:
  id: example
  name: Example
  version: "1.0.0"
  description: Example extension
requires:
  speckit_version: ">=1.0"
provides:
  commands:
    - name: speckit.example.run
      file: commands/speckit.example.run.md
```

`extension.id` is a lowercase alphanumeric-and-hyphen slug. The version is
parsed as a PEP 440 version, and `requires.speckit_version` is enforced against
the installed CLI. Optional extension metadata includes authoring,
categorization, effect, repository, license, tags, and support information.
Most optional metadata is descriptive; it does not grant trust or filesystem
access.

An extension must provide at least one command, hook, event, template, or
script. Supported behavioral declarations are:

- `provides.commands`: canonical `speckit.<extension-id>.<command>` names,
  source files, descriptions, and optional aliases;
- `provides.templates`: named template files;
- `provides.scripts`: named script entries with optional runtime declarations
  from `bash`, `powershell`, and `python`;
- `provides.config`: templates scaffolded into the installed extension
  directory without overwriting existing files;
- `hooks`: one or more command bindings for a Spec Kit workflow event; and
- `events`: validated agent-runtime event bindings handled by the events
  domain.

Manifest paths are relative to the extension root. Absolute paths, traversal,
and unsafe command or alias output names are rejected. Templates and scripts
always have `replace` semantics when they participate in artifact resolution;
extensions cannot author preset composition strategies.

Primary command names must use the extension's namespace. Installation rejects
names and aliases that exactly match a name from another installed extension,
and rejects names whose normalized agent output form conflicts with a core
command. Installed-extension comparisons are not normalized, so differently
spelled names can still converge on the same output path for a particular
renderer. A small set of legacy two-segment command names is normalized to the
canonical form with a warning; hook and event command references are rewritten
consistently.

## Project state and filesystem layout

Extension state is project-local:

```text
.specify/
├── extension-catalogs.yml          # optional project catalog stack
├── extensions.yml                  # installed IDs and declarative hook bindings
└── extensions/
    ├── .registry                   # installed lifecycle and output ownership metadata
    ├── .cache/                     # catalog metadata and downloaded archives
    ├── .backup/                    # removed config and update rollback material
    ├── .rescue-staging-<hash>/     # temporary durable kept-config rescue
    └── <extension-id>/
        ├── extension.yml
        ├── commands/
        ├── templates/
        ├── scripts/
        └── *-config.yml
```

The JSON `.registry` is the lifecycle source of truth for installed
extensions. Each valid entry records version, source provenance, manifest
hash, enablement, priority, installation time, registered command outputs,
registered skills, and, where needed, hashes proving ownership of generic
integration artifacts. Lower numeric priority has higher precedence; ties are
ordered by extension ID.

`.specify/extensions.yml` is a separate YAML projection used by declarative
hooks. It contains a normalized installed list, hook bindings, and settings.
It does not replace `.registry`.

Catalog configuration resolves in this order:

1. `SPECKIT_CATALOG_URL`, which replaces the whole stack;
2. `.specify/extension-catalogs.yml`;
3. `~/.specify/extension-catalogs.yml`; then
4. the built-in installable catalog followed by the discovery-only community
   catalog.

Extension configuration merges, from lowest to highest precedence:

1. the top-level `defaults` and `config.defaults` in `extension.yml`, merged
   with `config.defaults` winning on conflicting keys;
2. `.specify/extensions/<id>/<id>-config.yml`;
3. `.specify/extensions/<id>/local-config.yml`; and
4. `SPECKIT_<NORMALIZED_EXTENSION_ID>_*` environment variables.

Configuration files are treated as data. Invalid or unreadable YAML degrades
to an empty layer. Environment variables are nested by underscore-separated
keys, and longer installed extension IDs win ambiguous prefix matches.

Removal and force-reinstallation preserve only top-level files named
`*-config.yml` or `*-config.local.yml`. The runtime `local-config.yml`
override matches the first suffix and is covered by that preservation
convention.

## Lifecycle and data flow

### Discovery

`specify extension search` and `info` merge active catalogs in ascending
priority order. The first catalog defining an extension ID wins. Fetch
failures are isolated per catalog; the operation fails only when no active
catalog can be fetched. Catalog caches are project-local and expire after one
hour; malformed or unreadable cache entries are ignored and refetched.

The built-in community catalog is discovery-only. Its entries may be listed
and inspected but cannot be installed until the user chooses a direct URL or
places the extension in an install-enabled catalog they control.

### Installation

Installation accepts:

- a bundled extension shipped with the current Spec Kit distribution;
- a local directory, including development mode;
- an install-enabled catalog entry; or
- an explicitly trusted HTTPS archive URL.

All routes converge on `ExtensionManager.install_from_directory()` after safe
archive extraction when applicable. The manager:

1. validates the manifest, compatibility, priority, command namespace, and
   install conflicts;
2. when the generic integration is active, validates its registration
   settings, command sources, and unsafe existing output collisions;
3. preserves eligible configuration before any destructive force reinstall;
4. copies the extension under `.specify/extensions/<id>/`, honoring
   `.extensionignore`;
5. renders commands or skills for the active integration;
6. registers hooks and the installed projection in `extensions.yml`;
7. commits lifecycle and ownership metadata to `.registry`;
8. restores executable bits for project scripts.

Configuration scaffolding is a caller-owned follow-up rather than a shared
manager step. `extension add`, `extension enable`, and bundle installation call
`scaffold_config()` without overwriting existing targets. Extension
installation during `init` and extension update paths do not scaffold declared
configuration templates.

Development installs may use symlinks to rendered caches where the selected
integration and platform support them. Integrations that prohibit such
symlinks receive ordinary files instead.

### Enablement and integration changes

Disabled extensions remain installed and are excluded from registry-driven
artifact resolution, hook and event projection, and future integration
registration. Enable and disable update registry state and hook bindings. For
the generic integration, disablement also removes owned invocation artifacts
after proving ownership. Other integrations retain already-generated command
and skill files until an integration switch, uninstall, or other reconciliation
removes them, so those stale files may remain invocable while the extension is
disabled.

An extension install targets the active integration recorded in project state.
Projects predating that state may fall back to detected agent directories;
present but invalid active-integration state fails closed and registers no
agent outputs. Selecting, switching, upgrading, or removing integrations
reconciles enabled extension outputs for the affected active agent through the
integration lifecycle. Those post-commit reconciliation steps are
best-effort and surface warnings rather than rolling back a successful
integration operation.

### Update

Update discovery compares the installed registry version with the winning
install-enabled catalog release and any required bundled copy. It does not
filter candidates for Spec Kit compatibility, so an incompatible release may
still be offered. Exact catalog releases remain bound to the winning catalog
source.

After selection and before mutation, the update command preflights the
replacement archive, including manifest and Spec Kit compatibility checks, and
backs up the extension directory, registry entry, eligible configuration, hook
projection, command files, skills, and symlinks. A failed destructive update
attempts to restore the prior package and all tracked outputs. Backup
directories are unique per attempt; cleanup failures leave an isolated backup
and produce a warning rather than contradicting a committed or restored state.

Update orchestration currently lives in CLI-private
`_command_update_*` modules. It is not a shared typed operation.

### Removal

Removal unregisters tracked command and skill outputs, removes hook bindings,
and deletes the registry entry. By default it copies eligible top-level config
files to `.specify/extensions/.backup/<id>/` before deleting the package.
`--keep-config` leaves those eligible files in the extension directory and
writes a provenance marker so a later install can distinguish intentional
preservation from a partial failed installation.

## Command, skill, hook, and event delivery

Extension command source is agent-neutral Markdown. The active integration's
registrar converts it to the agent's command, recipe, TOML, YAML, or
`SKILL.md` layout, rewrites extension-relative asset paths to the installed
extension directory, resolves command references, and records the generated
outputs in `.registry`. The output formats and integration ownership rules are
defined in [Agent Integration Design](integration.md).

Native registration follows the selected integration's output flavor. It
renders primary names and aliases, so integrations whose native command format
is `SKILL.md` create separate primary and alias skill directories. Non-generic
native registration writes its selected destination and may replace an
existing file; the generic integration applies its ownership checks first.

Command-backed integrations configured to use skills take a separate
supplemental path. That path renders only primary commands as
`speckit-<extension>-<command>/SKILL.md`. A normal install skips an existing
unverified skill file or directory, while an expected development symlink or a
forced integration refresh may be replaced.

Hooks are declarative AI-agent follow-up instructions, not direct subprocess
execution. `HookExecutor` is a helper API that filters enabled bindings,
evaluates the limited `config.*` and `env.*` condition grammar, orders hooks by
priority, and renders the invocation syntax for the active integration.
`execute_hook()` returns execution metadata; the calling AI agent performs the
command.

The shipped core command templates do not call `HookExecutor`. They read
`.specify/extensions.yml` directly, preserve configured YAML order, skip
disabled hooks, and skip every hook with a non-empty condition rather than
evaluating it. For remaining hooks they emit optional or mandatory agent
instructions, and the active AI agent performs any mandatory command.

Runtime `events` are a distinct mechanism. The events domain validates their
shape, merges enabled extension declarations with integration defaults and
project overrides, and writes supported agent-native event configuration.
Event dispatch resolves the declared command template and may execute its
frontmatter script under the project process user's permissions with path
confinement and timeouts.

## Artifact registration and resolution

Extensions contribute to the same artifact inventory and resolver used by
presets and core assets. For commands, templates, and scripts, the resolution
order is:

1. project overrides;
2. installed presets;
3. enabled extensions in registry priority order; then
4. core assets.

A successfully loaded and validated extension manifest declaration is
authoritative. A declared but missing or unsafe file is not silently replaced
by a conventionally named file. For legacy compatibility, an absent,
unreadable, or invalid manifest reopens conventional lookup, as does a valid
manifest that does not declare the requested artifact. Commands and scripts
are searched under `commands/` and `scripts/`; templates are searched under
`templates/` and at the extension root. Consequently, an undeclared root-level
template can precede a core template.

Extension layers always use `replace` semantics. Artifact listing and info
project their manifest provenance, active stack entry, concrete source path,
and hook bindings without changing resolver behavior. A corrupt extension
registry causes artifact resolution to fail closed.

When the registry is healthy, the legacy resolver also admits safe
unregistered extension directories at default priority `10`. This compatibility
path is not equivalent to installation: it has no lifecycle or generated
output ownership metadata.

## Bundled extensions and bundles

First-party bundled extensions live under `extensions/<id>/` in the source
tree and are copied into `specify_cli/core_pack/extensions/<id>/` when the
wheel is built. Source and packaged lookup use the same asset resolver.
`extensions/catalog.json` advertises bundled identity and version; contract
tests require catalog and manifest versions to agree so updates are neither
hidden nor repeatedly offered.

A Spec Kit bundle may reference an extension component. The bundle installer
delegates to `ExtensionManager` for bundled or catalog installation,
configuration scaffolding, refresh, and removal. Bundles do not define a
second extension format or lifecycle.

## Trust and security boundaries

Extension content is trusted project content once installed. Commands run in
the AI agent's context, and runtime event scripts run with the permissions of
the invoking process. Manifest validation and path confinement reduce unsafe
packaging and output writes; they are not a sandbox.

Network and package trust rules are:

- catalog and archive URLs require HTTPS, except loopback HTTP for local
  development;
- catalog redirects are validated at every hop;
- configured authentication providers may add credentials for matching hosts,
  and redirect handling does not forward them to untrusted hosts;
- catalog responses and downloads are size-bounded;
- archives reject traversal, links, and unsupported layouts during extraction;
- a catalog `sha256`, when present, must match the downloaded archive;
- direct URL installation is default-deny and requires interactive
  confirmation or the explicit initialization trust flag; and
- catalog `install_allowed` controls whether metadata is an install source,
  but does not certify extension safety.

Guarded archive, package, integration, removal, and refresh paths validate
containment or prove ownership with registry records, generated frontmatter,
hashes, or expected symlink targets before mutating user-adjacent artifacts.
This is not a universal property of registry persistence:
`ExtensionRegistry._save()` does not itself validate containment of the
`.specify/extensions` root. Without an active integration file-change observer,
a symlinked root is followed and `.registry` can be written outside the
project.

## Failure and transactional guarantees

Expected manifest, compatibility, catalog, and lifecycle failures use
`ValidationError`, `CompatibilityError`, or `ExtensionError`; CLI adapters map
them to user-facing messages and non-zero exits.

The implementation provides targeted transactional guarantees rather than one
global filesystem transaction:

- manifest, compatibility, priority, namespace, conflict, and generic
  active-output checks precede destructive force removal. `.extensionignore`
  is loaded afterward, so an unreadable or invalid ignore file can still fail
  after the prior package has been removed;
- kept configuration is durably staged and restored across copy failures and
  interrupted retries;
- generic integration registration rolls back generated outputs, hooks, and
  registry state on commit failure;
- update backs up every tracked lifecycle surface before mutation and restores
  it on failure; and
- corrupted registries fail closed in artifact resolution even though registry
  construction normalizes malformed content so repair-oriented lifecycle
  commands can continue.

Best-effort cleanup may leave backups or caches after a successful commit or
rollback. Such leftovers are not treated as active extension state.

## Supported external surfaces

The supported extension surfaces are:

- `specify extension ...` and `specify extension catalog ...`;
- repeated `specify init --extension ...` inputs;
- extension components in bundle manifests;
- `specify artifact list`, `info`, and `lookup` for composed extension
  contributions;
- installed command or skill outputs consumed through the selected agent
  integration; and
- the declarative `extension.yml` package format.

Extension lifecycle operations do not currently have shared typed application
operations or first-class MCP adapters. The experimental MCP server registers
version and artifact tools; its artifact list and info tools can report
extension contributions, but extension add, update, remove, enablement,
catalog, and configuration lifecycle remain CLI-only. This is the implemented
boundary, independent of the broader adapter rules in
[the MCP design](mcp.md).

The Python classes in `specify_cli.extensions` are internal domain APIs used by
Spec Kit itself. They are not a separately versioned third-party SDK.

## Non-goals

The implemented extension system does not:

- execute arbitrary Python plugins from extension packages;
- sandbox command prompts or event scripts;
- treat catalog inclusion as a security endorsement;
- allow extensions to replace core CLI or MCP registration;
- define preset-style append, prepend, or wrap composition strategies;
- install dependencies or arbitrary tools declared in manifest metadata;
- make every manifest metadata field an enforced runtime contract; or
- guarantee all lifecycle operations are globally atomic across every
  filesystem and agent integration.
