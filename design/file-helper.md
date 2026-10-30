# Scoped FileHelper and project policy

`specify_cli.file_helper.FileHelper` owns filesystem operations under one
explicitly established root. Project-command boundaries now validate persisted
policy, and init-options bootstrap I/O uses the helper. Other existing command
filesystem operations are **not yet migrated**: loading policy alone does not
enforce symlink behavior on those operations. Shared infrastructure, registration,
managed storage, catalogs, scripts and runtime operations retain their existing
behavior until their dependent migration stages.

Preset registry reads and writes use a project-root-scoped deny-mode helper.
For the documented `.specify/presets` registry location, the root is two
parents above that directory, never the preset
storage directory itself. Registry metadata and its parent hierarchy must
not be links, independently of the operational `allow_symlinks` setting. Saves
validate the destination before file-change observers or directory creation
and preserve the existing registry text I/O and metadata behavior. This
migration covers registry persistence only, not the remaining preset lifecycle
filesystem operations. Shared artifact list/info operations translate registry
`FileHelperError` failures into their existing resolution errors, preserving
the CLI JSON envelope and MCP `artifact_resolution_failed` code. Contribution
lookup likewise translates registry failures into an artifact resolution error.
Registry reads and writes translate `SymlinkDeniedError` at the persistence
boundary, preserving the registry path and directing users to replace linked
entries with regular files/directories, not enable operational symlinks.
The preset CLI renders that diagnostic without rewriting it, including for
manager/resolver construction failures; integration registration warnings and
bundle errors receive the same guidance. JSON list/info retain a single error
envelope with no stdout output.

Integration upgrade layout guards reuse the same deny-mode registry text
reader, while retaining their stricter ownership/JSON validation. Only genuine
absence means no installed presets. Symlinked files or parents, including
dangling links, and other read/parse failures become
`_PresetRegistryUnreadableError`, refusing command-root or command/skills
migrations before mutation while preset ownership is unknown.

Full preset resolution reads the registry through that boundary before any
override, preset, extension, or core content can be selected. Followed
`exists()`/`is_symlink()` probes must not decide whether registry validation
runs: a dangling parent symlink or Windows junction can appear absent through
those probes. Genuine registry absence still permits the normal fallback
stack. Explicit core-only resolution continues to skip the preset tier and
does not inspect its registry.

Only `specify init --allow-symlinks` exposes the setting; init defaults to deny
and persists the literal JSON boolean `allow_symlinks` in
`.specify/init-options.json`. Re-init without the flag records `false`.
Other project-scoped commands validate the selected project's current
configuration each invocation, including successive invocations in one process.
No global flag, per-command override, mutable global policy, or cache is used.
Projectless help/version/tool operations do not require configuration.
`check` is an optional project consumer: it validates any present policy at its
selected cwd/override boundary before loading installed integrations or checking
tools, but still permits a missing project marker or configuration in cwd.
Existing resolution rules, including `SPECIFY_INIT_DIR`, bundle ancestor search,
direct workflow-file roots and explicit init targets, determine which root is
checked; policy loading does not add ancestor discovery.
Event execution retains its cwd-only selection and does not acquire an
override or project-marker requirement; it preflights any present cwd policy
before invoking handlers. Bundle ancestor search continues only when a marker
is genuinely absent. A nearer forbidden/present invalid `.specify` entry fails
at that candidate rather than selecting an ancestor or initializing elsewhere.

Missing configuration or a missing key means deny. Only literal JSON
`true`/`false` values are valid. Invalid JSON, non-object documents, invalid
encoding, unreadable files and invalid values fail explicitly before mutations
at the project boundary. Dangling configuration links are present forbidden
entries, not missing defaults.

Configuration bootstrap reads **and writes** always use a deny-mode helper,
even when stored operational policy or the init flag allows symlinks.
`.specify` and `init-options.json` below the trusted project root must not be
links or unsupported reparse points. Root/OS aliases retain the foundation's
trusted-boundary treatment. For a new init root, `prepare_init_root` creates its
missing suffix using a deny-mode helper rooted at the nearest existing parent;
an existing explicitly supplied root alias is trusted. `preflight_init_root`
validates the original requested spelling without creating a root, including
missing-parent traversal and dangling-parent evidence before canonicalization.
Before presence probes, every prefix preceding `..` must be an existing
directory: Windows can otherwise fold `missing/../existing` into an apparently
existing target. Valid existing-directory/root-alias traversal remains trusted;
prefix permission and other I/O failures remain explicit errors.
Init's external-adapter lifecycle validates existing target policy before
reading integration records, loading adapters or preparing catalog packages.
When that lifecycle requires a
transaction, it creates the target under the existing lock using the original
requested spelling and `prepare_init_root`, before invoking the inner handler.
The recorded pre-transaction directory state retains that spelling, so a newly
created root does not become a spurious existing-directory conflict. Lock,
journal and handler operations retain their canonical project identity after
the original spelling has been validated.

## Policy handoff for dependent migrations

`specify_cli._file_policy.read_project_options(root)` is the strict bootstrap
reader; it is separate from the legacy tolerant `load_init_options` library
API. `project_files(root)` reads policy afresh and returns an immutable
`FileHelper(root, allow_symlinks=...)`. Pass that returned operation owner
explicitly to domain consumers; do not reconstruct a default helper and lose
the policy. `specify_cli._project.resolve_specify_project_files()` performs the
normal existing-project resolution and returns the same handoff for new CLI
adapters. Commands using another established root call `project_files` on
their actually selected root. Retain a helper only for the current operation;
a later invocation resolves a new helper, so manual edits take effect.

Existing Path-returning resolvers preflight policy without changing their return
type or domain constructors. They do not implicitly equip unmigrated domain
consumers with an operation helper. Failures are translated into existing
command diagnostics, with a single `{"error": "..."}` on stderr and empty
stdout for JSON policy failures; artifact/list surfaces preserve their error
envelope contracts. Artifact list/info validate their explicit project roots in
the shared application operations, so CLI and MCP peer adapters share the same
policy semantics while retaining their own error envelopes.

`save_project_options` and the compatibility `save_init_options` writer use
deny-mode bootstrap I/O. Init merges its owned settings into existing valid
options, preserving unrelated fields. Integration option update/clear/version
paths use the strict reader and retain `allow_symlinks`. Unmigrated tolerant
library readers keep their existing missing/malformed fallback contracts.
Configuration writers validate their deny-mode destination before the existing
file-change observer snapshots it, then retain the before/after observer hooks
around the write. Downstream init failures therefore remain covered by the
existing lifecycle rollback, including prior policy and unrelated options.

```python
from specify_cli.file_helper import FileHelper

files = FileHelper(project_root)  # deny symlinks by default
files.mkdir("generated", exist_ok=True)
files.create_text("generated/config.txt", "initial\n")
files.write_text("generated/config.txt", "updated\n")
content = files.read_text("generated/config.txt")
files.delete("generated", recursive=True)
```

## Boundary and policy

Each helper has a frozen root and `allow_symlinks` setting. Relative operation
paths are root-relative. Absolute paths must be beneath the supplied root or
its canonical equivalent. User operation paths containing `..` are rejected
in their root-relative suffix rather than normalized before inspection. A
caller-established root spelling may itself contain `..`; absolute operation
paths derived from that exact supplied root prefix are supported. Only that
trusted prefix is removed before checking operation components, without
lexically collapsing the root or ignoring traversal in the remaining suffix.
Link targets may contain `..`, but
are walked component by component and may not leave the root, even temporarily.
Windows rooted-but-not-absolute paths (`/outside/file`, `\outside\file`) and
drive-relative paths (`C:outside/file`, `C:`) are rejected for both operation
paths and link targets. They are not root-relative: joining them can reset the
root or drive. Fully absolute paths still require scoped root matching.
For Windows containment comparisons, extended-length drive and UNC spellings
(`\\?\D:\project\file`, `\\?\UNC\server\share\project\file`) are compared with
their ordinary equivalents on both the target and root sides. This does not
resolve links or collapse `..`: accessed hierarchy evidence is retained for
the component walk. The UNC namespace marker is matched case-insensitively,
while the remaining path's original spelling is preserved. External targets,
ambiguous rooted-relative paths, and
unsupported device namespaces are still rejected. POSIX filenames are not
reinterpreted as Windows path spellings.

The caller must establish a trusted, existing directory root. Its alias is
resolved once, including OS and worktree aliases; the root itself and OS
ancestors above it are not subjected to the traversal policy. Thus explicitly
establishing a linked directory as a root trusts that alias even in deny mode.
Links *below* that boundary are checked in both the original accessed path and
any followed target hierarchy. An unrelated project symlink does not prevent
an operation. A helper cannot cross to another root; callers establish separate
helpers for independent project/source/managed boundaries.

| Operation | Default deny | Explicit allow |
|---|---|---|
| Read file | Reject accessed parent or leaf links | Follow only existing contained regular-file targets |
| Create directory | Reject accessed links before creating parents | Follow contained directory links; reject dangling targets |
| Exclusively create file | Reject accessed links | Follow contained parents; reject an existing leaf without opening its target |
| Atomic write/upsert | Reject accessed links | Replace the resolved regular-file target and preserve every link |
| Delete leaf link | Reject without mutation | Unlink the link, including dangling, cyclic, or external-target links |
| Delete through linked parent | Reject without mutation | Delete the contained target entry, leaving the parent link intact |
| Recursive delete | Preflight all descendants and reject any link before mutation | Preflight all descendants; unlink links without traversing their targets |
| Create symlink | Reject | Require an existing contained file/directory target |

## API and failures

- `mkdir(path, parents=False, exist_ok=False)` creates directories.
- `read_bytes(path)` / `read_text(path, encoding="utf-8")` read regular files.
- `create_bytes(path, content, mode=0o644)` / `create_text(...)` exclusively
  create files with existing parents. A no-follow `lstat` preflight rejects
  existing leaves, including dangling links, before opening the destination.
  This avoids target creation on backends that follow dangling links despite
  exclusive-open flags. `O_EXCL` and `O_NOFOLLOW` (where available) remain in use;
  the static preflight does not eliminate concurrent path-change races.
- `write_bytes(path, content, mode=0o644)` / `write_text(...)` atomically
  create or update files with existing parents. Text variants also accept
  `encoding="utf-8"`. Replacement files use the supplied mode; metadata and
  hard-link identity are not preserved. Atomic means same-directory
  `os.replace`, not crash durability.
- `overwrite_text(path, content, encoding="utf-8")` is a **non-atomic** text
  upsert with existing parents, used for configuration compatibility. It uses
  the same accessed-path/link/containment checks as other operations, follows
  only allowed existing contained file targets, and preserves link chains and
  the target inode (including hard-link identity and permissions). New files
  use `0o666` filtered by the process umask; text encoding and native newline
  translation match the previous configuration writer. An encoding or I/O
  failure propagates, and a write failure can leave truncated/partial content.
  This is not hard-link confinement: a hard-linked alias can observe updates.
- `delete(path, recursive=False)` unlinks files/links or removes directories.
  Nonrecursive directory deletion requires an empty directory. The established
  root cannot be deleted.
- `symlink(target, path)` creates a link exclusively. Relative targets are
  interpreted relative to the link parent, not the helper root.

`SymlinkDeniedError`, `PathEscapeError`, and `UnsupportedPathError` derive from
`FileHelperError` and describe policy failures. Missing paths (including
dangling read/update targets), permissions, existing exclusive-create
destinations, non-directory parents, and OS I/O failures retain native Python
exceptions. Nothing prints, warns-and-skips, or exits the CLI. Callers own
translation into their normal command error envelopes.

Only regular files, directories, and explicitly allowed symlinks are supported.
Below the established root, Windows directory junctions and other non-symlink
reparse entries are unsupported and rejected with `UnsupportedPathError` in
**both** policy modes. This includes contained junctions, leaf deletion, and
recursive deletion: preflight rejects them without traversing or removing
them. `allow_symlinks=True` does not authorize junction traversal or deletion.
The trusted root alias boundary may itself resolve through a junction just as
it may through a symlink; this does not authorize junctions below that root.
Read/update cycles and excessive link chains fail explicitly. A recursive
delete includes the entire selected tree; there is no exclusion filter in this
foundation. Future operations with exclusions must inspect only included
entries, not reject a whole project for excluded/unrelated links.

## Safety limits and migration

Preflight detects static policy failures before recursive deletion or parent
creation. Atomic writes recheck the original path before replacement, and
deletion rechecks each accessed entry. Portable path checks are **not** a
race-free sandbox: another process can exchange parents or entries between
checks and syscalls, and an I/O failure during mutation can leave partial
results. Protect against concurrent untrusted mutation separately; descriptor-
relative traversal or platform-specific mechanisms are future work, not a
claim of this API. The helper does not constrain subprocesses or third-party
code. Exclusive creation uses `O_EXCL` and `O_NOFOLLOW` where available.

Existing safe-write mechanisms informed this helper, but existing shared
infrastructure warning/skip behavior and development-mode link creation are
unchanged. Migrate one owned operation boundary at a time, carrying original
paths and an explicit root/policy into the helper before any early resolution.
Linked command directories and development-mode registration remain dependent
stages. Non-atomic configuration writes preserve legacy metadata semantics;
portable preflight does not guarantee race-free protection against concurrent
path replacement.

Windows path classification and directory-mode reparse rejection have portable
regression tests. Native Windows path and junction tests also exist and are
skipped on other hosts; running the portable cases on macOS does not validate
Windows filesystem syscalls or junction behavior.
