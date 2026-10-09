# Scoped FileHelper foundation

`specify_cli.file_helper.FileHelper` owns filesystem operations under one
explicitly established root. This is the first migration stage: existing CLI
commands retain their current behavior and do not yet use this helper. There is
no global CLI flag or process-global policy.

The user-directed persistence requirement belongs to the dependent
project-policy wiring stage: save the setting in `.specify/init-options.json`,
then load and validate it for future invocations and pass the resulting policy
explicitly to helper instances. Only `specify init` exposes and persists the
setting. Every other CLI command reads the current project configuration on
each invocation, so manual edits take effect without a cached policy. There
is no root/global flag and no per-command override flag. The low-level helper
does not read configuration. Strict persisted-policy loading and configuration-
read bootstrap semantics must be coordinated before migration.

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
| Exclusively create file | Reject accessed links | Follow contained parents; an existing leaf link is never overwritten |
| Atomic write/upsert | Reject accessed links | Replace the resolved regular-file target and preserve every link |
| Delete leaf link | Reject without mutation | Unlink the link, including dangling, cyclic, or external-target links |
| Delete through linked parent | Reject without mutation | Delete the contained target entry, leaving the parent link intact |
| Recursive delete | Preflight all descendants and reject any link before mutation | Preflight all descendants; unlink links without traversing their targets |
| Create symlink | Reject | Require an existing contained file/directory target |

## API and failures

- `mkdir(path, parents=False, exist_ok=False)` creates directories.
- `read_bytes(path)` / `read_text(path, encoding="utf-8")` read regular files.
- `create_bytes(path, content, mode=0o644)` / `create_text(...)` exclusively
  create files with existing parents.
- `write_bytes(path, content, mode=0o644)` / `write_text(...)` atomically
  create or update files with existing parents. Text variants also accept
  `encoding="utf-8"`. Replacement files use the supplied mode; metadata and
  hard-link identity are not preserved. Atomic means same-directory
  `os.replace`, not crash durability.
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
CLI option wiring, linked command directories, and development-mode
registration remain dependent stages.

Windows path classification and directory-mode reparse rejection have portable
regression tests. Native Windows path and junction tests also exist and are
skipped on other hosts; running the portable cases on macOS does not validate
Windows filesystem syscalls or junction behavior.
