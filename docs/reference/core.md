# Core Commands

The core `specify` commands handle project initialization, project uninstall, system checks, and version information.

## Initialize a Project

```bash
specify init [<project_name>]
```

| Option                   | Description                                                              |
| ------------------------ | ------------------------------------------------------------------------ |
| `--integration <key>`    | AI coding agent integration to use (e.g. `copilot`, `claude`, `gemini`). See the [integration directory](../integrations/index.md) for all available keys |
| `--integration-options`  | Options for the integration (e.g. `--integration-options="--commands-dir .myagent/cmds"`) |
| `--script sh\|ps\|py`    | Script type: `sh` (bash/zsh), `ps` (PowerShell), or `py` (Python)       |
| `--here`                 | Initialize in the current directory instead of creating a new one        |
| `--force`                | Force merge/overwrite when initializing in an existing directory         |
| `--allow-symlinks`       | Persist permission for contained symlinks in migrated FileHelper operations; default is deny |
| `--ignore-agent-tools`   | Skip checks for AI coding agent CLI tools                                |
| `--preset <id>`          | Install a preset during initialization                                   |

Creates a new Spec Kit project with the necessary directory structure, templates, scripts, and AI coding agent integration files.

> [!NOTE]
> Git repository initialization and branching are managed by the **git extension**, which is not installed by default. Run `specify extension add git` after init to enable git workflows.

Use `<project_name>` to create a new directory, or `--here` (or `.`) to initialize in the current directory. If the directory already has files, use `--force` to merge without confirmation.

When `--integration` is omitted, interactive terminals prompt you to choose an integration. Non-interactive sessions, such as CI or piped runs, default to GitHub Copilot; pass `--integration <key>` to choose a different integration explicitly, or set `SPECKIT_INTEGRATION_DEFAULT` to change the fallback (see [Environment Variables](#environment-variables)).

### Persisted filesystem policy

Only `init` accepts `--allow-symlinks`. It records `allow_symlinks: true` in
`.specify/init-options.json`; omitting it records `false`, including on re-init.
Project-scoped CLI commands read the current value on each invocation, so a
manual edit takes effect immediately. A missing file or key means deny; the
value must be a JSON boolean, not a string, number or null. Invalid/unreadable
configuration is an error, not a fallback. Unrelated recorded init options are
preserved.

The configuration bootstrap hierarchy (`.specify` and `init-options.json`)
must always be non-symlinked below the trusted project root, even in allow mode.
Help, version, check and projectless tool/catalog operations do not gain a
project requirement. Init uses its explicit target, not `SPECIFY_INIT_DIR`.
`check` can consume installed project integrations: it validates any present
policy at its selected cwd or `SPECIFY_INIT_DIR` boundary before loading them
or checking tools. It still works in a projectless cwd without `.specify` or
init options. Help and version do not read project policy.

**Migration limit:** policy is enforced by FileHelper operations, currently
including init-options bootstrap I/O. Loading policy does not yet route all
other command filesystem operations through FileHelper. Shared infrastructure,
registration, managed storage, scripts and runtime operations retain their
existing behavior until migrated. See [FileHelper design](../../design/file-helper.md)
for the boundary and handoff contract.

### Examples

```bash
# Create a new project with an integration
specify init my-project --integration copilot

# Initialize in the current directory
specify init --here --integration copilot

# Force merge into a non-empty directory
specify init --here --force --integration copilot

# Use PowerShell scripts (Windows/cross-platform)
specify init my-project --integration copilot --script ps

# Install a preset during initialization
specify init my-project --integration copilot --preset compliance
```

### Environment Variables

| Variable          | Description                                                              |
| ----------------- | ------------------------------------------------------------------------ |
| `SPECKIT_INTEGRATION_DEFAULT` | Override the fallback integration used by `specify init` when `--integration` is omitted (interactive prompt default and non-interactive fallback). Set it to any registered integration key (e.g. `gemini`, `claude`). An unrecognized value is ignored with a warning and the built-in default (`copilot`) is used. An explicit `--integration <key>` always takes precedence. |
| `SPECIFY_INIT_DIR` | Target a member project from outside its directory (e.g. a monorepo root) without `cd`, for non-interactive / CI use. Set it to the **project root** — the directory *containing* `.specify/` (relative paths resolve against the current directory). The path must exist and contain `.specify/`, otherwise the command errors and does **not** fall back to the current directory. Resolved once in the core root helper (`get_repo_root` in Bash, `Get-RepoRoot` in PowerShell), so it is honored by the core feature scripts (`/speckit.plan`, `/speckit.tasks`, …) and the Git extension's feature-branch creation, which inherit it. The `specify` CLI applies the **same** validation rules to every project-scoped subcommand (`specify integration …`, `specify extension …`, `specify workflow …`, `specify preset …`, and the rest that operate on a `.specify/` project), so those can target a member project too. When unset, Bash/PowerShell helpers keep their existing upward search; the `specify` CLI keeps its project-scoped resolver cwd-only unless a command explicitly defines broader detection (for example, bundle commands). |
| `SPECIFY_FEATURE_DIRECTORY` | Override the active feature directory (takes precedence over `.specify/feature.json`). A relative path is joined to the project root without a containment check, so a value like `../shared-feature` still resolves outside it; an absolute path is used as-is and may likewise point outside the project root. The project root still identifies the Spec Kit project and its command/configuration context, but the selected feature directory itself is not required to live under it. Combine with `SPECIFY_INIT_DIR` to pick both the project and the feature non-interactively. |
| `SPECIFY_FEATURE` | Explicitly override the active feature **label** (e.g. `001-photo-albums`) — the identifier the core helpers report as the current feature/branch (`get_current_branch` in Bash, `Get-CurrentBranch` in PowerShell). Those helpers never inspect Git: when the variable is set they return it verbatim, and when it is unset they return an empty string. The basename fallback happens later — `get_feature_paths` / `Get-FeaturePathsEnv` substitute the resolved feature directory's basename so the reported label is still usable — so calling the named helpers directly does **not** give you that fallback. You set it yourself: the Bash and Python feature scripts only **print** a commented `export SPECIFY_FEATURE=…` / `$env:SPECIFY_FEATURE = …` hint for you to run, because a child process cannot change its parent's environment, and `/speckit.specify` persists `feature_directory` to `.specify/feature.json` instead of setting this variable. (The PowerShell feature scripts do assign `$env:SPECIFY_FEATURE`, but that only reaches you when the script runs inside your current PowerShell session.) It does **not** locate the feature directory: with only `SPECIFY_FEATURE` set, `get_feature_paths` fails with *"Feature directory not found. Set `SPECIFY_FEATURE_DIRECTORY` or run the specify command to create `.specify/feature.json`."* Use `SPECIFY_FEATURE_DIRECTORY` (above) or `.specify/feature.json` to select the directory. |
| `SPECIFY_FEATURE_NO_PERSIST` | Set to `1` or `true` to stop every core script from writing `.specify/feature.json`, even when it would otherwise persist `SPECIFY_FEATURE_DIRECTORY` on read. Useful when multiple agents run concurrently against the same checkout, each with its own `SPECIFY_FEATURE_DIRECTORY`: without it, each invocation's persist step can overwrite another agent's pinned feature directory. |

> **Two resolution axes.** `SPECIFY_INIT_DIR` selects the **project** (which directory contains `.specify/`); `SPECIFY_FEATURE_DIRECTORY` / `.specify/feature.json` select the **feature** — its default location is under `specs/` in that project, but an explicitly selected feature directory is not restricted to living inside it. They are independent — project first, then feature.
>
> **Version control.** `specify init` scaffolds a managed `.specify/.gitignore` that excludes machine-local state — `feature.json` (the current-feature pointer, rewritten on every feature switch) and per-machine extension `extensions/*/local-config.yml` overrides — while leaving everything else under `.specify/` (constitution, templates, scripts, extension config) shareable so teams stay aligned. Like the rest of `.specify/`'s shared scripts and templates, the file is tracked in the shared-infrastructure manifest: your edits are preserved on re-init and `specify init --here --force` restores the managed content. It is intentionally left in place by `specify integration uninstall`, which only removes the uninstalled agent's own files.
>
> **Symlinked project roots.** An explicitly established project-root alias is
> trusted, including OS ancestors above it. The configuration hierarchy below
> that root is always checked in deny mode: `.specify/` and `init-options.json`
> cannot be symlinks. Unmigrated operations elsewhere in the project retain
> their existing symlink behavior.

## Uninstall Spec Kit from a Project

```bash
specify destroy --dry-run
specify destroy --yes
```

`destroy` uninstalls the project's integrations first, then removes its remaining
Spec Kit infrastructure, not the Specify CLI itself. It removes recorded integration
commands/skills, registered extension/preset artifacts, **all `.specify/` contents
including the constitution**, and the **project-local `specs/` directory** by default.
Project source and unrelated agent files remain untouched. Nonempty agent directories
are never removed wholesale.

Use preservation flags to retain SDD artifacts while removing the tooling:

```bash
specify destroy --yes --preserve-constitution
specify destroy --yes --preserve-specs
specify destroy --yes --preserve-all
# --preserve-all is equivalent to --preserve-constitution --preserve-specs
```

Preserved artifacts keep their original bytes, including when an integration manifest
tracks them. Both individual flags can be combined; combining either with
`--preserve-all` is harmless. `--force` never overrides preservation.
Preservation recognizes alternate case spellings on case-insensitive filesystems,
including the constitution's parent directories, without following a preserved link.

| Option | Description |
| --- | --- |
| `--project <path>` | Explicit project root; otherwise use `SPECIFY_INIT_DIR` or the current directory |
| `--dry-run` | Preview file and directory cleanup, managed settings updates, and declared home-scoped outputs without modifying anything |
| `--yes`, `-y` | Explicitly confirm destructive cleanup; required for unattended use |
| `--force` | Also delete modified or unverified whole-owned agent artifacts |
| `--json` | Emit a result on stdout or one structured error on stderr; never prompt |
| `--preserve-constitution` | Keep `.specify/memory/constitution.md` and its parent directories |
| `--preserve-specs` | Keep project-local `specs/` without traversing or modifying it |
| `--preserve-all` | Keep both supported SDD artifact groups above; still remove integrations, tooling, and configuration |

**Back up specifications and custom content first.** Confirmation authorizes
removing its templates, scripts, installed packages, workflows, caches, and
project-local configuration, including your custom files, constitution, and `specs/`
unless explicitly preserved. Preview the exact file and directory list before confirming.
Only the literal project-local `specs/` directory is removed: feature-directory
overrides, including `SPECIFY_FEATURE_DIRECTORY` and `.specify/feature.json`, do
not expand the deletion scope. A directory without a `.specify` project marker
is a no-op, even if it contains `specs/`.

Modified hash-tracked generated files outside `.specify` stop cleanup before
deletion unless `--force` is explicit. Contribution cleanup uses the existing
integration lifecycle's registry, provenance-marker, and hash checks. A flat
skill name alone does not establish ownership of same-named skills in other
agents' directories. `--force` does **not** imply confirmation, establish
ownership, override filesystem policy, or authorize deleting shared settings.
For generic integration outputs, force permits removal of modified extension files
only after the recorded command names, output paths, and ownership hashes have
passed validation. Incomplete contribution cleanup retains the integration state
needed to retry.
For example:

```bash
specify destroy --project ./my-project --dry-run --json
specify destroy --project ./my-project --yes --force
```

Non-default integrations are uninstalled first and the default last, without
switching defaults merely to remove the next integration. Their ordinary teardown
removes Spec Kit's merged native event entries while preserving user entries and
settings. The last installed integration referencing an owned `.specify/events.py`
dispatcher releases and removes it under the existing ownership and force rules.
Preview checks the dispatcher against its ownership records and the lifecycle's
accepted generated content, using the last claimant in uninstall order. A modified managed dispatcher requires force before
any integration is uninstalled; missing, partial, or recovered ownership does not
become deletion authority through force.
Claimed built-in native settings are also parsed during planning, so malformed
settings stop destruction before another integration is removed.
If teardown preserves the dispatcher or leaves cleanup unresolved, destroy stops
and retains recovery metadata instead of purging the remaining `.specify` tree.

Missing/corrupt ownership metadata and unsafe paths block cleanup. External
manifest paths and ownership modes must be authorized by the user's existing
local ownership binding; neither confirmation nor force replaces that proof.
Confirmed uninstall uses the normal trusted-adapter loading, teardown, recovery,
and rollback machinery. Dry-run validates metadata without loading adapter code.
Integration-specific uninstall behavior also applies to home-scoped outputs,
such as Hermes skills; those declared directories and registered contribution
files are shown separately in preview (`global_scopes` and `global_files` in
JSON). Only an installed integration's declared home scope can supply these
paths. They are removed by its normal teardown, not by project-tree deletion.
The CLI installation and machine-level trust records are not removed.
Untracked settings not owned by native event cleanup remain in place.

Persisted symlink policy applies. Destroy never traverses symlinked directories
to identify agent artifacts; allowed leaf links are unlinked without deleting
their targets. An explicitly preserved constitution or `specs/` entry may be a link and is
left untouched. Otherwise the persisted symlink policy applies; targets are
never recursively traversed merely because a link is selected for deletion.
Metadata is always read without following links.

Preview, rejected confirmation, and validation failures leave files unchanged.
An I/O failure during deletion can leave a partial uninstall and is reported
explicitly. External integration lifecycle transactions retain their normal
rollback behavior, but destroy as a whole is not atomic: earlier integrations
may already have been uninstalled when a later cleanup fails. Remaining
metadata is retained for recovery. Repeating destroy with the same preservation
flags succeeds without further changes. A retained constitution by itself is
a no-op with `--preserve-constitution` or `--preserve-all`; without those flags,
its deletion still requires confirmation.
Extension and preset registries are retained until their package files and
directories have been removed, so a failed package purge can be retried.
If teardown raises after deleting its manifest, destroy restores the original
ownership manifest so the recorded integration can be retried after the error
is resolved. This preserves recovery evidence; it does not undo files that
were already removed outside a lifecycle transaction.
Specification files and directories are removed before remaining infrastructure:
a locked `specs/` directory leaves the project marker available for retry.
Human-readable failures list remaining paths and completed file/integration
removals alongside the error; JSON errors expose the same recovery details.

Legacy setups with only an `init-options.json` integration selection and no
`integration.json` inventory are rejected during preview. Re-run `specify init`
for the selected integration to migrate that inventory before using destroy.

For removing just one integration while retaining Spec Kit tooling, use
[`specify integration uninstall`](../integrations/cli.md#uninstall-an-integration).
`destroy` is currently CLI-only; its MCP inventory records it as unavailable.

## Naming Features with the Helper Scripts

When calling the bundled `create-new-feature` helper scripts directly, generated
names retain Unicode letters and decimal digits in UTF-8, so a description such as
`添加用户` produces `001-添加用户`. Descriptions made only of punctuation can still
produce an empty suffix such as `001-`; the scripts warn on stderr when this
happens, including during a dry run. JSON output remains parseable.

To choose a different name, keep the original description and supply a short name:

```bash
bash .specify/scripts/bash/create-new-feature.sh --json --short-name 用户管理 "添加用户"
```

The Python helper also accepts `--short-name`; the PowerShell helper uses
`-ShortName`. A supplied short name is cleaned by the same rules, so it must
contain at least one letter or digit. For non-ASCII names, the Bash helper needs
an installed UTF-8 locale and a Python 3 interpreter for Unicode classification.
ASCII input, including tabs and newlines, is sanitized without either requirement.
If `LC_ALL` is non-empty, Bash uses that locale rather than selecting another:
Unicode names fail with an error if the selected locale is not usable for UTF-8
names. With `LC_ALL` unset or empty, Bash selects an installed UTF-8 locale even
when `LANG` or `LC_CTYPE` names a non-UTF-8 locale.
ASCII capitals are lowercased; non-ASCII letter casing is preserved across the
script variants.

## Check Installed Tools

```bash
specify check
```

Checks that CLI-based AI coding agents are available on your system. IDE-based agents are skipped since they don't require a CLI tool.

Installed project integrations are included when available. Any present
filesystem policy at the selected project boundary must be valid; a projectless
cwd remains supported without configuration.

This command stays offline. If a command behaves like an older Spec Kit version or an expected CLI feature is missing, run `specify self check` to check whether your local CLI is behind the latest release.

## Version Information

```bash
specify version
```

Displays the Spec Kit CLI version, Python version, platform, and architecture.

To inspect local CLI capabilities without checking the network:

```bash
specify version --features
```

To print complete version, runtime, system, and feature information as JSON,
use:

```bash
specify version --json
```

Combining `--features` and `--json` emits the same complete JSON output;
`--features` does not filter the result in JSON mode. If OpenSSL information
is unavailable, `runtime.openssl` is `null`.
Successful JSON output is written only to stdout. Failures leave stdout empty
and write one sanitized JSON error object to stderr.

A quick version check is also available via:

```bash
specify --version
specify -V
```

## Experimental MCP Server

```bash
specify mcp
```

Starts the experimental stdio-only MCP server. The initial server exposes only
the stable `version` JSON command through generic list, describe, and run tools.
See the [MCP Server reference](mcp.md) for the tool names, result contract, and
current limitations.
