# Refactor Design: `__init__.py` Code Quality Improvement

**Date:** 2026-04-25  
**Goal:** Improve testability and maintainability of `src/specify_cli/__init__.py` (5329 lines) without breaking any public CLI interfaces.

---

## Problem

`__init__.py` contains 7 distinct responsibilities in a single 5329-line file:

- Terminal UI utilities (StepTracker, BannerGroup, select_with_arrows)
- File system utilities (merge_json_files, handle_vscode_settings)
- Bundled asset location (_locate_core_pack, _locate_bundled_*)
- Git operations (is_git_repo, init_git_repo, ensure_executable_scripts)
- Version management (_get_installed_version, _fetch_latest_release_tag)
- Integration helpers (_read_integration_json, _write_integration_json)
- All CLI command handlers (init, integration_*, preset_*, extension_*, workflow_*)

Business logic is deeply entangled with `console.print` calls, making it impossible to unit-test without capturing rich output or running a full CLI subprocess.

---

## Constraints

- **Strict backward compatibility**: all CLI commands and flags remain unchanged
- **No public API breakage**: external import paths preserved via `__init__.py` re-exports
- **Incremental**: each PR is independently reviewable and verifiable against the existing test suite

---

## Approach: Progressive Targeted Extraction (Option C)

Two phases: module decomposition first, then service extraction for the highest-value testability targets.

---

## Module Structure (Target State)

```
src/specify_cli/
│
├── __init__.py              # app definition, main(), global constants, re-exports
│
├── _ui.py                   # Terminal interaction (console.print allowed here)
│   ├── StepTracker
│   ├── BannerGroup
│   ├── show_banner()
│   └── select_with_arrows()
│
├── _fs.py                   # File system utilities (no console.print)
│   ├── merge_json_files()
│   ├── handle_vscode_settings()
│   ├── save_init_options()
│   └── load_init_options()
│
├── _assets.py               # Bundled asset location (no console.print)
│   ├── AssetService
│   │   ├── locate_core_pack() -> Path | None
│   │   ├── locate_bundled_extension(id) -> Path | None
│   │   ├── locate_bundled_workflow(id) -> Path | None
│   │   └── locate_bundled_preset(id) -> Path | None
│
├── _git.py                  # Git operations (no console.print)
│   ├── GitService
│   │   ├── is_repo(path) -> bool
│   │   └── init_repo(path) -> tuple[bool, str | None]
│   └── ensure_executable_scripts()
│
├── _version.py              # Version management (no console.print)
│   ├── VersionService
│   │   ├── get_installed_version() -> str
│   │   ├── fetch_latest_tag() -> tuple[str | None, str | None]
│   │   └── is_newer(latest, current) -> bool
│   └── _normalize_tag()
│
└── commands/                # CLI handlers (console.print allowed)
    ├── __init__.py          # registers all sub-commands onto app
    ├── init.py              # specify init
    ├── integration.py       # specify integration *
    ├── preset.py            # specify preset *
    ├── extension.py         # specify extension *
    └── workflow.py          # specify workflow *
```

---

## Service Interfaces

### GitService

```python
class GitService:
    def is_repo(self, path: Path) -> bool: ...
    def init_repo(self, path: Path) -> tuple[bool, str | None]:
        # Returns (success, error_message_or_None)
        # Never prints to console
```

### VersionService

```python
class VersionService:
    def get_installed_version(self) -> str: ...
    def fetch_latest_tag(self) -> tuple[str | None, str | None]:
        # Returns (tag, url) or (None, None) on failure
    def is_newer(self, latest: str, current: str) -> bool: ...
```

### AssetService

```python
class AssetService:
    def locate_core_pack(self) -> Path | None: ...
    def locate_bundled_extension(self, extension_id: str) -> Path | None: ...
    def locate_bundled_workflow(self, workflow_id: str) -> Path | None: ...
    def locate_bundled_preset(self, preset_id: str) -> Path | None: ...
```

---

## Invariants

- Files in `_git.py`, `_fs.py`, `_assets.py`, `_version.py` **must not** import from `rich` or call `console.print`
- Files in `commands/` and `_ui.py` **may** use `console.print`
- All existing symbol names remain importable from `specify_cli` (re-exported in `__init__.py`)

---

## Migration Sequence

### PR-1: Extract UI and File Utilities (Low Risk)

Move to new files with no logic changes:
- `StepTracker`, `BannerGroup`, `show_banner`, `select_with_arrows`, `get_key` → `_ui.py`
- `merge_json_files`, `handle_vscode_settings`, `save_init_options`, `load_init_options` → `_fs.py`
- `__init__.py` imports and re-exports all moved symbols

Verification: `pytest` full suite passes unchanged.

### PR-2: Extract Services (Medium Risk)

- `GitService` → `_git.py` (wraps existing `is_git_repo`, `init_git_repo`)
- `VersionService` → `_version.py` (wraps existing version functions)
- `AssetService` → `_assets.py` (wraps existing `_locate_*` functions)
- CLI handlers updated to call services; `console.print` stays in handlers only
- Add unit tests for each service using `unittest.mock`

Verification: existing tests pass; new service unit tests added.

### PR-3: Split Command Handlers (Medium Risk)

- Move each command group to `commands/<group>.py`
- `commands/__init__.py` registers all sub-commands
- `__init__.py` shrinks to ~50 lines

Verification: full test suite passes; manual smoke-test of all CLI commands.

---

## Testing Strategy

After PR-2, each service is independently testable:

```python
# Example: test GitService without subprocess
def test_init_repo_success(tmp_path):
    svc = GitService()
    ok, err = svc.init_repo(tmp_path)
    assert ok is True
    assert err is None

# Example: test VersionService with mock HTTP
def test_is_newer():
    svc = VersionService()
    assert svc.is_newer("v0.9.0", "v0.8.0") is True
    assert svc.is_newer("v0.8.0", "v0.9.0") is False
```

---

## Out of Scope

- `presets.py` (3084 lines) and `extensions.py` (2672 lines) — separate effort
- `integrations/base.py` (1486 lines) — separate effort
- Any changes to CLI command signatures or output format
