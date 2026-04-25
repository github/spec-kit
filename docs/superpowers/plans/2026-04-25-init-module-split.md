# `__init__.py` Module Split Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split `src/specify_cli/__init__.py` (5329 lines) into focused modules and extract three service classes to improve testability, with zero change to public CLI behavior.

**Architecture:** Three sequential PRs — PR-1 extracts UI/FS utilities into `_ui.py` and `_fs.py` with a shared `_console.py` singleton; PR-2 extracts `AssetService`, `GitService`, `VersionService` as pure classes; PR-3 moves CLI handlers into a `commands/` subpackage. All symbols remain importable from `specify_cli` via re-exports.

**Tech Stack:** Python 3.11+, pytest, typer, rich

---

## PR-1: Extract UI and File System Utilities

### Task 1: Create `_console.py` — shared Rich console singleton

**Files:**
- Create: `src/specify_cli/_console.py`
- Modify: `src/specify_cli/__init__.py` (line 329 — replace inline definition with import)

- [ ] **Step 1: Write the test**

```python
# tests/test_console_singleton.py
from specify_cli._console import console
from rich.console import Console

def test_console_is_rich_console():
    assert isinstance(console, Console)

def test_console_imported_in_init():
    import specify_cli
    assert hasattr(specify_cli, 'console')
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/darion.yaphet/source/spec-kit
python -m pytest tests/test_console_singleton.py -v
```

Expected: `ModuleNotFoundError: No module named 'specify_cli._console'`

- [ ] **Step 3: Create `_console.py`**

```python
# src/specify_cli/_console.py
from rich.console import Console

console = Console(highlight=False)
```

- [ ] **Step 4: Update `__init__.py` line 329**

Replace:
```python
console = Console(highlight=False)
```
With:
```python
from ._console import console
```

Also remove `from rich.console import Console` from `__init__.py` imports **only if** it is not used elsewhere in the file. Check first:

```bash
grep -n "Console(" src/specify_cli/__init__.py | grep -v "from ._console"
```

If Console is still used directly (e.g. in BannerGroup), keep the import. Otherwise remove it.

- [ ] **Step 5: Run tests**

```bash
python -m pytest tests/test_console_singleton.py tests/test_merge.py tests/test_extensions.py -v
```

Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add src/specify_cli/_console.py src/specify_cli/__init__.py tests/test_console_singleton.py
git commit -m "refactor: extract shared console singleton to _console.py"
```

---

### Task 2: Create `_ui.py` — terminal interaction utilities

**Files:**
- Create: `src/specify_cli/_ui.py`
- Modify: `src/specify_cli/__init__.py` (remove moved code, add imports)
- Test: `tests/test_ui.py`

Symbols to move (from `__init__.py`):
- `StepTracker` (lines 149–232)
- `get_key` (lines 234–252)
- `select_with_arrows` (lines 254–329)
- `BannerGroup` (lines 331–346)
- `show_banner` (lines 348–360)

- [ ] **Step 1: Write the test**

```python
# tests/test_ui.py
from specify_cli._ui import StepTracker, BannerGroup, show_banner, select_with_arrows

def test_step_tracker_add_and_complete():
    t = StepTracker("test")
    t.add("step1", "Step One")
    t.complete("step1", "done")
    assert t.steps[0]["status"] == "done"

def test_step_tracker_render_returns_tree():
    from rich.tree import Tree
    t = StepTracker("test")
    t.add("s", "S")
    result = t.render()
    assert isinstance(result, Tree)

def test_step_tracker_error():
    t = StepTracker("test")
    t.add("s", "S")
    t.error("s", "failed")
    assert t.steps[0]["status"] == "error"

def test_banner_group_is_typer_group():
    from typer.core import TyperGroup
    assert issubclass(BannerGroup, TyperGroup)

def test_symbols_re_exported_from_package():
    import specify_cli
    assert hasattr(specify_cli, 'StepTracker')
    assert hasattr(specify_cli, 'BannerGroup')
    assert hasattr(specify_cli, 'show_banner')
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_ui.py -v
```

Expected: `ImportError: cannot import name 'StepTracker' from 'specify_cli._ui'`

- [ ] **Step 3: Create `_ui.py`**

Copy `StepTracker` (lines 149–232), `get_key` (lines 234–252), `select_with_arrows` (lines 254–329), `BannerGroup` (lines 331–346), `show_banner` (lines 348–360) verbatim into a new file:

```python
# src/specify_cli/_ui.py
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.tree import Tree
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.align import Align
from typer.core import TyperGroup
import readchar

from ._console import console

# Paste StepTracker class here (lines 149-232 from __init__.py)
# Paste get_key function here (lines 234-252)
# Paste select_with_arrows function here (lines 254-329)
# Paste BannerGroup class here (lines 331-346)
# Paste show_banner function here (lines 348-360)
```

> **Note:** `show_banner` references the `BANNER` and `TAGLINE` constants. Move those constants to `_ui.py` as well, or import them from `__init__.py`. Prefer moving them since they are display-only.

- [ ] **Step 4: Update `__init__.py`**

Replace the moved code blocks (lines 149–360) with:
```python
from ._ui import StepTracker, get_key, select_with_arrows, BannerGroup, show_banner, BANNER, TAGLINE
```

Remove from `__init__.py` the now-redundant rich imports that are only used in `_ui.py`:
- `from rich.tree import Tree`
- `from rich.panel import Panel`
- `from rich.text import Text`
- `from rich.live import Live`
- `from rich.align import Align`
- `import readchar`

Before removing each import, verify it is no longer used in `__init__.py`:
```bash
grep -n "Tree\|Panel\|Text\|Live\|Align\|readchar" src/specify_cli/__init__.py
```

Only remove imports confirmed as unused.

- [ ] **Step 5: Run full test suite**

```bash
python -m pytest tests/test_ui.py tests/test_merge.py tests/test_extensions.py tests/test_presets.py -v
```

Expected: all PASS

- [ ] **Step 6: Smoke test CLI**

```bash
python -m specify_cli --help
python -m specify_cli init --help
```

Expected: help text renders normally with banner

- [ ] **Step 7: Commit**

```bash
git add src/specify_cli/_ui.py src/specify_cli/__init__.py tests/test_ui.py
git commit -m "refactor: extract UI utilities to _ui.py"
```

---

### Task 3: Create `_fs.py` — file system utilities

**Files:**
- Create: `src/specify_cli/_fs.py`
- Modify: `src/specify_cli/__init__.py`
- Test: existing `tests/test_merge.py` covers `merge_json_files`

Symbols to move:
- `handle_vscode_settings` (lines 481–548)
- `merge_json_files` (lines 550–627)
- `save_init_options` (lines 910–920)
- `load_init_options` (lines 922–933)

- [ ] **Step 1: Verify existing merge tests pass before changes**

```bash
python -m pytest tests/test_merge.py -v
```

Expected: all PASS (baseline)

- [ ] **Step 2: Create `_fs.py`**

```python
# src/specify_cli/_fs.py
import json
import json5
import os
import shutil
import stat
import tempfile
from pathlib import Path
from typing import Any, Optional

from ._console import console


# Paste handle_vscode_settings (lines 481-548) verbatim
# Paste merge_json_files (lines 550-627) verbatim
# Paste save_init_options (lines 910-920) verbatim
# Paste load_init_options (lines 922-933) verbatim
```

> **Note:** `handle_vscode_settings` calls `merge_json_files` — both are in the same file so no import needed. `save_init_options` and `load_init_options` use `json` and `Path` — already imported above.

- [ ] **Step 3: Update `__init__.py`**

Replace the moved code blocks with:
```python
from ._fs import handle_vscode_settings, merge_json_files, save_init_options, load_init_options
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/test_merge.py tests/test_setup_plan_feature_json.py -v
```

Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add src/specify_cli/_fs.py src/specify_cli/__init__.py
git commit -m "refactor: extract file system utilities to _fs.py"
```

---

## PR-2: Extract Service Classes

### Task 4: Create `_assets.py` — AssetService

**Files:**
- Create: `src/specify_cli/_assets.py`
- Modify: `src/specify_cli/__init__.py`
- Test: `tests/test_asset_service.py`

- [ ] **Step 1: Write the test**

```python
# tests/test_asset_service.py
from pathlib import Path
from specify_cli._assets import AssetService

def test_locate_core_pack_returns_path_or_none():
    svc = AssetService()
    result = svc.locate_core_pack()
    assert result is None or isinstance(result, Path)

def test_locate_bundled_extension_invalid_id_returns_none():
    svc = AssetService()
    assert svc.locate_bundled_extension("../evil") is None
    assert svc.locate_bundled_extension("UPPER") is None

def test_locate_bundled_extension_valid_id():
    svc = AssetService()
    result = svc.locate_bundled_extension("git")
    # In source checkout, git extension should exist
    assert result is None or isinstance(result, Path)

def test_locate_bundled_workflow_invalid_id_returns_none():
    svc = AssetService()
    assert svc.locate_bundled_workflow("") is None
    assert svc.locate_bundled_workflow("BAD ID") is None

def test_locate_bundled_preset_invalid_id_returns_none():
    svc = AssetService()
    assert svc.locate_bundled_preset("../etc/passwd") is None

def test_backward_compat_module_functions():
    # The old underscore functions must still work via __init__.py
    from specify_cli import _locate_core_pack, _locate_bundled_extension
    result = _locate_core_pack()
    assert result is None or isinstance(result, Path)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_asset_service.py -v
```

Expected: `ImportError: cannot import name 'AssetService' from 'specify_cli._assets'`

- [ ] **Step 3: Create `_assets.py`**

```python
# src/specify_cli/_assets.py
import re
from pathlib import Path


class AssetService:
    """Locates bundled assets (core_pack, extensions, workflows, presets)."""

    def locate_core_pack(self) -> Path | None:
        candidate = Path(__file__).parent / "core_pack"
        if candidate.is_dir():
            return candidate
        return None

    def locate_bundled_extension(self, extension_id: str) -> Path | None:
        if not re.match(r'^[a-z0-9-]+$', extension_id):
            return None
        core = self.locate_core_pack()
        if core is not None:
            candidate = core / "extensions" / extension_id
            if (candidate / "extension.yml").is_file():
                return candidate
        repo_root = Path(__file__).parent.parent.parent
        candidate = repo_root / "extensions" / extension_id
        if (candidate / "extension.yml").is_file():
            return candidate
        return None

    def locate_bundled_workflow(self, workflow_id: str) -> Path | None:
        if not re.match(r'^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$', workflow_id):
            return None
        core = self.locate_core_pack()
        if core is not None:
            candidate = core / "workflows" / workflow_id
            if (candidate / "workflow.yml").is_file():
                return candidate
        repo_root = Path(__file__).parent.parent.parent
        candidate = repo_root / "workflows" / workflow_id
        if (candidate / "workflow.yml").is_file():
            return candidate
        return None

    def locate_bundled_preset(self, preset_id: str) -> Path | None:
        if not re.match(r'^[a-z0-9-]+$', preset_id):
            return None
        core = self.locate_core_pack()
        if core is not None:
            candidate = core / "presets" / preset_id
            if (candidate / "preset.yml").is_file():
                return candidate
        repo_root = Path(__file__).parent.parent.parent
        candidate = repo_root / "presets" / preset_id
        if (candidate / "preset.yml").is_file():
            return candidate
        return None


# Module-level singleton for backward compat
_asset_service = AssetService()
```

- [ ] **Step 4: Update `__init__.py` — replace `_locate_*` functions with wrappers**

Replace the four `_locate_*` function bodies (lines 629–718) with:

```python
from ._assets import AssetService as _AssetService, _asset_service as _svc

def _locate_core_pack() -> Path | None:
    return _svc.locate_core_pack()

def _locate_bundled_extension(extension_id: str) -> Path | None:
    return _svc.locate_bundled_extension(extension_id)

def _locate_bundled_workflow(workflow_id: str) -> Path | None:
    return _svc.locate_bundled_workflow(workflow_id)

def _locate_bundled_preset(preset_id: str) -> Path | None:
    return _svc.locate_bundled_preset(preset_id)
```

- [ ] **Step 5: Run tests**

```bash
python -m pytest tests/test_asset_service.py tests/test_extensions.py tests/test_presets.py -v
```

Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add src/specify_cli/_assets.py src/specify_cli/__init__.py tests/test_asset_service.py
git commit -m "refactor: extract AssetService to _assets.py"
```

---

### Task 5: Create `_git.py` — GitService

**Files:**
- Create: `src/specify_cli/_git.py`
- Modify: `src/specify_cli/__init__.py`
- Test: `tests/test_git_service.py`

- [ ] **Step 1: Write the test**

```python
# tests/test_git_service.py
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock
from specify_cli._git import GitService

def test_is_repo_true_in_real_git_repo(tmp_path):
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    svc = GitService()
    assert svc.is_repo(tmp_path) is True

def test_is_repo_false_in_plain_dir(tmp_path):
    svc = GitService()
    assert svc.is_repo(tmp_path) is False

def test_init_repo_success(tmp_path):
    svc = GitService()
    ok, err = svc.init_repo(tmp_path)
    assert ok is True
    assert err is None
    assert (tmp_path / ".git").is_dir()

def test_init_repo_returns_error_on_failure():
    svc = GitService()
    with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, ["git"])):
        ok, err = svc.init_repo(Path("/nonexistent"))
    assert ok is False
    assert err is not None

def test_init_repo_does_not_print(tmp_path, capsys):
    svc = GitService()
    svc.init_repo(tmp_path)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""

def test_backward_compat_is_git_repo(tmp_path):
    from specify_cli import is_git_repo
    assert is_git_repo(tmp_path) is False

def test_backward_compat_init_git_repo(tmp_path):
    from specify_cli import init_git_repo
    ok, err = init_git_repo(tmp_path, quiet=True)
    assert ok is True
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_git_service.py -v
```

Expected: `ImportError: cannot import name 'GitService' from 'specify_cli._git'`

- [ ] **Step 3: Create `_git.py`**

```python
# src/specify_cli/_git.py
import os
import subprocess
from pathlib import Path
from typing import Optional


class GitService:
    """Pure git operations — no console output."""

    def is_repo(self, path: Path = None) -> bool:
        if path is None:
            path = Path.cwd()
        if not path.is_dir():
            return False
        try:
            subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                check=True,
                capture_output=True,
                cwd=path,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def init_repo(self, project_path: Path) -> tuple[bool, Optional[str]]:
        """Initialize a git repo. Returns (success, error_message_or_None)."""
        try:
            original_cwd = Path.cwd()
            os.chdir(project_path)
            subprocess.run(["git", "init"], check=True, capture_output=True, text=True)
            subprocess.run(["git", "add", "."], check=True, capture_output=True, text=True)
            subprocess.run(
                ["git", "commit", "-m", "Initial commit from Specify template"],
                check=True, capture_output=True, text=True,
            )
            return True, None
        except subprocess.CalledProcessError as e:
            error_msg = f"Command: {' '.join(e.cmd)}\nExit code: {e.returncode}"
            if e.stderr:
                error_msg += f"\nError: {e.stderr.strip()}"
            elif e.stdout:
                error_msg += f"\nOutput: {e.stdout.strip()}"
            return False, error_msg
        finally:
            try:
                os.chdir(original_cwd)
            except Exception:
                pass


_git_service = GitService()
```

- [ ] **Step 4: Update `__init__.py` — replace `is_git_repo` and `init_git_repo` with wrappers**

Replace `is_git_repo` (lines 435–452) and `init_git_repo` (lines 455–477) bodies with:

```python
from ._git import GitService as _GitService, _git_service as _git_svc

def is_git_repo(path: Path = None) -> bool:
    return _git_svc.is_repo(path)

def init_git_repo(project_path: Path, quiet: bool = False) -> tuple[bool, Optional[str]]:
    ok, err = _git_svc.init_repo(project_path)
    if not quiet:
        if ok:
            console.print("[green]✓[/green] Git repository initialized")
        else:
            console.print(f"[red]Error initializing git repository:[/red] {err}")
    return ok, err
```

- [ ] **Step 5: Run tests**

```bash
python -m pytest tests/test_git_service.py tests/test_check_tool.py -v
```

Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add src/specify_cli/_git.py src/specify_cli/__init__.py tests/test_git_service.py
git commit -m "refactor: extract GitService to _git.py"
```

---

### Task 6: Create `_version.py` — VersionService

**Files:**
- Create: `src/specify_cli/_version.py`
- Modify: `src/specify_cli/__init__.py`
- Test: `tests/test_version_service.py`

- [ ] **Step 1: Write the test**

```python
# tests/test_version_service.py
from unittest.mock import patch, MagicMock
import json
from specify_cli._version import VersionService

def test_is_newer_true():
    svc = VersionService()
    assert svc.is_newer("0.9.0", "0.8.0") is True

def test_is_newer_false_when_equal():
    svc = VersionService()
    assert svc.is_newer("0.8.0", "0.8.0") is False

def test_is_newer_false_when_older():
    svc = VersionService()
    assert svc.is_newer("0.7.0", "0.8.0") is False

def test_is_newer_false_with_unknown():
    svc = VersionService()
    assert svc.is_newer("unknown", "0.8.0") is False
    assert svc.is_newer("0.9.0", "unknown") is False

def test_normalize_tag_strips_v():
    svc = VersionService()
    assert svc._normalize_tag("v0.9.0") == "0.9.0"
    assert svc._normalize_tag("0.9.0") == "0.9.0"
    assert svc._normalize_tag("vv0.9.0") == "v0.9.0"

def test_get_installed_version_returns_string():
    svc = VersionService()
    result = svc.get_installed_version()
    assert isinstance(result, str)

def test_fetch_latest_tag_returns_tuple_on_network_error():
    svc = VersionService()
    import urllib.error
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")):
        tag, failure = svc.fetch_latest_tag()
    assert tag is None
    assert failure == "offline or timeout"

def test_fetch_latest_tag_success():
    svc = VersionService()
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps({"tag_name": "v0.9.0"}).encode()
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    with patch("urllib.request.urlopen", return_value=mock_response):
        tag, failure = svc.fetch_latest_tag()
    assert tag == "v0.9.0"
    assert failure is None

def test_backward_compat_normalize_tag():
    from specify_cli import _normalize_tag
    assert _normalize_tag("v1.0.0") == "1.0.0"

def test_backward_compat_is_newer():
    from specify_cli import _is_newer
    assert _is_newer("1.0.0", "0.9.0") is True
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_version_service.py -v
```

Expected: `ImportError: cannot import name 'VersionService' from 'specify_cli._version'`

- [ ] **Step 3: Create `_version.py`**

```python
# src/specify_cli/_version.py
import json
import os
import urllib.error
import urllib.request
from typing import Optional

from packaging.version import InvalidVersion, Version

GITHUB_API_LATEST = "https://api.github.com/repos/github/spec-kit/releases/latest"


class VersionService:
    """Version checking and comparison — no console output."""

    def get_installed_version(self) -> str:
        import importlib.metadata
        metadata_errors = [importlib.metadata.PackageNotFoundError]
        invalid_err = getattr(importlib.metadata, "InvalidMetadataError", None)
        if invalid_err is not None:
            metadata_errors.append(invalid_err)
        try:
            return importlib.metadata.version("specify-cli")
        except tuple(metadata_errors):
            return "unknown"

    def _normalize_tag(self, tag: str) -> str:
        return tag[1:] if tag.startswith("v") else tag

    def is_newer(self, latest: str, current: str) -> bool:
        if latest == "unknown" or current == "unknown":
            return False
        try:
            return Version(latest) > Version(current)
        except InvalidVersion:
            return False

    def fetch_latest_tag(self) -> tuple[Optional[str], Optional[str]]:
        """Returns (tag, failure_category). One of the two is always None."""
        req = urllib.request.Request(
            GITHUB_API_LATEST,
            headers={"Accept": "application/vnd.github+json"},
        )
        token = None
        for env_var in ("GH_TOKEN", "GITHUB_TOKEN"):
            candidate = os.environ.get(env_var)
            if candidate is not None:
                candidate = candidate.strip()
                if candidate:
                    token = candidate
                    break
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
                tag = payload.get("tag_name")
                if not isinstance(tag, str) or not tag:
                    raise ValueError("GitHub API response missing valid tag_name")
                return tag, None
        except urllib.error.HTTPError as e:
            if e.code == 403:
                return None, "rate limited (try setting GH_TOKEN or GITHUB_TOKEN)"
            return None, f"HTTP {e.code}"
        except (urllib.error.URLError, OSError):
            return None, "offline or timeout"


_version_service = VersionService()
```

- [ ] **Step 4: Update `__init__.py` — replace version functions with wrappers**

Replace `_get_installed_version` (lines 1670–1690), `_normalize_tag` (lines 1692–1699), `_is_newer` (lines 1701–1713), `_fetch_latest_release_tag` (lines 1716–1751) with:

```python
from ._version import VersionService as _VersionService, _version_service as _ver_svc

def _get_installed_version() -> str:
    return _ver_svc.get_installed_version()

def _normalize_tag(tag: str) -> str:
    return _ver_svc._normalize_tag(tag)

def _is_newer(latest: str, current: str) -> bool:
    return _ver_svc.is_newer(latest, current)

def _fetch_latest_release_tag() -> tuple[str | None, str | None]:
    return _ver_svc.fetch_latest_tag()
```

- [ ] **Step 5: Run tests**

```bash
python -m pytest tests/test_version_service.py tests/test_cli_version.py tests/test_upgrade.py -v
```

Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add src/specify_cli/_version.py src/specify_cli/__init__.py tests/test_version_service.py
git commit -m "refactor: extract VersionService to _version.py"
```

---

## PR-3: Split CLI Command Handlers

> **Circular import rule:** `commands/*.py` modules MUST NOT import from `specify_cli.__init__`. They import only from sibling utility modules (`_ui`, `_fs`, `_git`, `_assets`, `_version`, `_console`, `_helpers`). Each commands module defines its own sub-typer; `__init__.py` imports the sub-typer and wires it with `app.add_typer()`.

### Task 7: Create `_helpers.py` — init-command utilities

**Files:**
- Create: `src/specify_cli/_helpers.py`
- Modify: `src/specify_cli/__init__.py` (replace bodies with wrapper imports)
- Test: `tests/test_helpers.py`

Functions to move: `run_command` (line 378), `check_tool` (line 396), `_install_shared_infra` (line 721), `ensure_executable_scripts` (line 819), `ensure_constitution_from_template` (line 871), `_get_skills_dir` (line 936).

- [ ] **Step 1: Write the test**

```python
# tests/test_helpers.py
import shutil
from pathlib import Path
from unittest.mock import patch
from specify_cli._helpers import check_tool, run_command

def test_check_tool_git_found():
    if shutil.which("git"):
        assert check_tool("git") is True

def test_check_tool_nonexistent_returns_false():
    assert check_tool("__nonexistent_tool_xyz__") is False

def test_run_command_capture():
    result = run_command(["echo", "hello"], capture=True)
    assert result == "hello"

def test_run_command_no_capture_returns_none():
    result = run_command(["true"])
    assert result is None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_helpers.py -v
```

Expected: `ImportError: cannot import name 'check_tool' from 'specify_cli._helpers'`

- [ ] **Step 3: Create `_helpers.py`**

```python
# src/specify_cli/_helpers.py
import os
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any, Optional

from ._console import console
from ._ui import StepTracker

CLAUDE_LOCAL_PATH = Path.home() / ".claude" / "local" / "claude"
CLAUDE_NPM_LOCAL_PATH = Path.home() / ".claude" / "local" / "node_modules" / ".bin" / "claude"

# Paste run_command (lines 378-394) verbatim
# Paste check_tool (lines 396-432) verbatim
# Paste _install_shared_infra (lines 721-817) verbatim
# Paste ensure_executable_scripts (lines 819-868) verbatim
# Paste ensure_constitution_from_template (lines 871-908) verbatim
# Paste _get_skills_dir (lines 936-962) verbatim
```

- [ ] **Step 4: Update `__init__.py`** — replace the moved function bodies with imports

```python
from ._helpers import (
    run_command, check_tool,
    _install_shared_infra, ensure_executable_scripts,
    ensure_constitution_from_template, _get_skills_dir,
    CLAUDE_LOCAL_PATH, CLAUDE_NPM_LOCAL_PATH,
)
```

Remove the now-redundant `CLAUDE_LOCAL_PATH` and `CLAUDE_NPM_LOCAL_PATH` constant definitions from `__init__.py` (lines 136–137).

- [ ] **Step 5: Run tests**

```bash
python -m pytest tests/test_helpers.py tests/test_check_tool.py -v
```

Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add src/specify_cli/_helpers.py src/specify_cli/__init__.py tests/test_helpers.py
git commit -m "refactor: extract init helper utilities to _helpers.py"
```

---

### Task 8: Create `commands/` package skeleton

**Files:**
- Create: `src/specify_cli/commands/__init__.py`
- Create: `src/specify_cli/commands/init.py` (empty stub)
- Create: `src/specify_cli/commands/integration.py` (empty stub)
- Create: `src/specify_cli/commands/preset.py` (empty stub)
- Create: `src/specify_cli/commands/extension.py` (empty stub)
- Create: `src/specify_cli/commands/workflow.py` (empty stub)

- [ ] **Step 1: Write the structure test**

```python
# tests/test_commands_package.py
def test_commands_package_importable():
    import specify_cli.commands
    assert specify_cli.commands is not None

def test_command_modules_importable():
    from specify_cli.commands import init, integration, preset, extension, workflow
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_commands_package.py -v
```

Expected: `ModuleNotFoundError: No module named 'specify_cli.commands'`

- [ ] **Step 3: Create the package**

```python
# src/specify_cli/commands/__init__.py
# CLI command groups — each module registers its commands onto the shared app.
```

```python
# src/specify_cli/commands/init.py
# specify init command — placeholder, content moved in Task 8
```

```python
# src/specify_cli/commands/integration.py
# specify integration * commands — placeholder, content moved in Task 9
```

```python
# src/specify_cli/commands/preset.py
# specify preset * commands — placeholder, content moved in Task 10
```

```python
# src/specify_cli/commands/extension.py
# specify extension * / catalog * commands — placeholder, content moved in Task 11
```

```python
# src/specify_cli/commands/workflow.py
# specify workflow * commands — placeholder, content moved in Task 12
```

- [ ] **Step 4: Run test**

```bash
python -m pytest tests/test_commands_package.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/specify_cli/commands/
git commit -m "refactor: create commands/ package skeleton"
```

---

### Task 9: Move `init` command handler

**Files:**
- Modify: `src/specify_cli/commands/init.py`
- Modify: `src/specify_cli/__init__.py`

The `init` command spans approximately lines 964–1596 in `__init__.py`.

> **No circular imports:** `commands/init.py` imports ONLY from `_console`, `_ui`, `_fs`, `_git`, `_assets`, `_helpers`, and third-party libraries. Never from `specify_cli.__init__`. The `app` object is defined in `__init__.py`; pass it in via a `register(app)` pattern or keep `app` import as a lazy import at call-time.

- [ ] **Step 1: Move handler to `commands/init.py`**

Pattern: define a `register(app)` function that attaches the command, call it from `__init__.py`.

```python
# src/specify_cli/commands/init.py
from pathlib import Path
from typing import Any, Optional
import shlex

import typer

from .._console import console
from .._ui import StepTracker, show_banner, select_with_arrows
from .._fs import handle_vscode_settings, merge_json_files, save_init_options, load_init_options
from .._git import _git_service
from .._assets import _asset_service
from .._helpers import (
    run_command, check_tool, _install_shared_infra,
    ensure_constitution_from_template, ensure_executable_scripts, _get_skills_dir,
    AGENT_CONFIG, AI_ASSISTANT_ALIASES, AI_ASSISTANT_HELP, SCRIPT_TYPE_CHOICES,
)

def _build_ai_deprecation_warning(integration_key: str, ai_commands_dir: str | None = None) -> str:
    replacement = f"--integration {integration_key}"
    if integration_key == "generic" and ai_commands_dir:
        replacement += f' --integration-options="--commands-dir {shlex.quote(ai_commands_dir)}"'
    return (
        "[bold]--ai[/bold] is deprecated and will no longer be available in version 0.10.0 or later.\n\n"
        f"Use [bold]{replacement}[/bold] instead."
    )

def register(app: typer.Typer) -> None:
    @app.command()
    def init(
        project_name: str = typer.Argument(None, ...),
        # ... all parameters exactly as in __init__.py lines 966-983
    ):
        # Paste full init() body verbatim from lines 1023-1596
        # Replace: is_git_repo(path) → _git_service.is_repo(path)
        # Replace: init_git_repo(path, quiet=q) →
        #   ok, err = _git_service.init_repo(path)
        #   if not quiet:
        #       console.print("[green]✓[/green] Git repository initialized" if ok else f"[red]Error:[/red] {err}")
        pass
```

- [ ] **Step 2: Update `__init__.py`**

Replace the `init` command block (lines 964–1596) with:

```python
from .commands import init as _init_cmd
_init_cmd.register(app)
```

Also move `_build_ai_deprecation_warning` and `_build_integration_equivalent` to `_helpers.py` since they are no longer needed in `__init__.py` after this task.

- [ ] **Step 3: Run full test suite**

```bash
python -m pytest -v
```

Expected: all PASS

- [ ] **Step 4: Smoke test**

```bash
python -m specify_cli init --help
```

Expected: init help renders correctly with all flags

- [ ] **Step 5: Commit**

```bash
git add src/specify_cli/commands/init.py src/specify_cli/__init__.py
git commit -m "refactor: move init command handler to commands/init.py"
```

---

### Task 10: Move `integration` command handlers

**Files:**
- Modify: `src/specify_cli/commands/integration.py`
- Modify: `src/specify_cli/__init__.py`

Functions to move: `integration_list`, `integration_install`, `integration_uninstall`, `integration_switch`, `integration_upgrade` and helpers `_parse_integration_options`, `_update_init_options_for_integration`, `_read_integration_json`, `_write_integration_json`, `_remove_integration_json`, `_normalize_script_type`, `_resolve_script_type`.

> **Sub-typer pattern:** define `integration_app` inside `commands/integration.py`. `__init__.py` imports it and calls `app.add_typer(integration_app, name="integration")`. This avoids circular imports.

- [ ] **Step 1: Move to `commands/integration.py`**

```python
# src/specify_cli/commands/integration.py
from pathlib import Path
from typing import Any, Optional

import typer

from .._console import console
from .._ui import StepTracker
from .._fs import save_init_options, load_init_options
from .._helpers import run_command, check_tool, AGENT_CONFIG, SCRIPT_TYPE_CHOICES

integration_app = typer.Typer(
    name="integration",
    help="Manage coding agent integrations",
    add_completion=False,
)

# Paste _read_integration_json, _write_integration_json, _remove_integration_json verbatim
# Paste _normalize_script_type, _resolve_script_type verbatim
# Paste _parse_integration_options, _update_init_options_for_integration verbatim
# Paste all @integration_app.command(...) decorated functions verbatim
```

- [ ] **Step 2: Update `__init__.py`**

Replace the sub-typer definition (lines 1882–1887) and all integration handler code with:
```python
from .commands.integration import (
    integration_app,
    _read_integration_json, _write_integration_json, _remove_integration_json,
    _normalize_script_type, _resolve_script_type,
)
app.add_typer(integration_app, name="integration")
```

- [ ] **Step 3: Run tests**

```bash
python -m pytest -v
python -m specify_cli integration --help
```

Expected: all PASS, help renders correctly

- [ ] **Step 4: Commit**

```bash
git add src/specify_cli/commands/integration.py src/specify_cli/__init__.py
git commit -m "refactor: move integration command handlers to commands/integration.py"
```

---

### Task 11: Move `preset` command handlers

**Files:**
- Modify: `src/specify_cli/commands/preset.py`
- Modify: `src/specify_cli/__init__.py`

Functions: `preset_list`, `preset_add`, `preset_remove`, `preset_search`, `preset_resolve`, `preset_info`, `preset_set_priority`, `preset_enable`, `preset_disable`, `preset_catalog_list`, `preset_catalog_add`, `preset_catalog_remove`.

- [ ] **Step 1: Move to `commands/preset.py`**

```python
# src/specify_cli/commands/preset.py
import typer
from .._console import console
from .._ui import StepTracker
from .._assets import _asset_service

preset_app = typer.Typer(name="preset", help="Manage spec-kit presets", add_completion=False)
preset_catalog_app = typer.Typer(name="catalog", help="Manage preset catalogs", add_completion=False)
preset_app.add_typer(preset_catalog_app, name="catalog")

# Paste all @preset_app.command(...) and @preset_catalog_app.command(...) decorated functions verbatim
```

- [ ] **Step 2: Update `__init__.py`**

Replace lines 1844–1856 and all preset handler code with:
```python
from .commands.preset import preset_app, preset_catalog_app
app.add_typer(preset_app, name="preset")
```

- [ ] **Step 3: Run tests**

```bash
python -m pytest tests/test_presets.py -v
python -m specify_cli preset --help
```

Expected: all PASS

- [ ] **Step 4: Commit**

```bash
git add src/specify_cli/commands/preset.py src/specify_cli/__init__.py
git commit -m "refactor: move preset command handlers to commands/preset.py"
```

---

### Task 12: Move `extension` and `catalog` command handlers

**Files:**
- Modify: `src/specify_cli/commands/extension.py`
- Modify: `src/specify_cli/__init__.py`

Functions: `extension_list`, `extension_add`, `extension_remove`, `extension_search`, `extension_info`, `extension_update`, `extension_enable`, `extension_disable`, `extension_set_priority`, `catalog_list`, `catalog_add`, `catalog_remove`, `_resolve_installed_extension`, `_resolve_catalog_extension`, `_print_extension_info`.

- [ ] **Step 1: Move to `commands/extension.py`**

```python
# src/specify_cli/commands/extension.py
import typer
from .._console import console
from .._ui import StepTracker
from .._assets import _asset_service

extension_app = typer.Typer(name="extension", help="Manage spec-kit extensions", add_completion=False)
catalog_app = typer.Typer(name="catalog", help="Manage extension catalogs", add_completion=False)
extension_app.add_typer(catalog_app, name="catalog")

# Paste _resolve_installed_extension, _resolve_catalog_extension, _print_extension_info verbatim
# Paste all @extension_app.command(...) and @catalog_app.command(...) decorated functions verbatim
```

- [ ] **Step 2: Update `__init__.py`**

Replace lines 1830–1842 and all extension/catalog handler code with:
```python
from .commands.extension import extension_app, catalog_app
app.add_typer(extension_app, name="extension")
```

- [ ] **Step 3: Run tests**

```bash
python -m pytest tests/test_extensions.py tests/integrations/ -v
python -m specify_cli extension --help
```

Expected: all PASS

- [ ] **Step 4: Commit**

```bash
git add src/specify_cli/commands/extension.py src/specify_cli/__init__.py
git commit -m "refactor: move extension command handlers to commands/extension.py"
```

---

### Task 13: Move `workflow` command handlers

**Files:**
- Modify: `src/specify_cli/commands/workflow.py`
- Modify: `src/specify_cli/__init__.py`

Functions: `workflow_run`, `workflow_resume`, `workflow_status`, `workflow_list`, `workflow_add`, `workflow_remove`, `workflow_search`, `workflow_info`, `workflow_catalog_list`, `workflow_catalog_add`, `workflow_catalog_remove`.

- [ ] **Step 1: Move to `commands/workflow.py`**

```python
# src/specify_cli/commands/workflow.py
import typer
from .._console import console
from .._ui import StepTracker
from .._assets import _asset_service

workflow_app = typer.Typer(name="workflow", help="Run spec-driven workflows", add_completion=False)
workflow_catalog_app = typer.Typer(name="catalog", help="Manage workflow catalogs", add_completion=False)
workflow_app.add_typer(workflow_catalog_app, name="catalog")

# Paste all @workflow_app.command(...) and @workflow_catalog_app.command(...) decorated functions verbatim
```

- [ ] **Step 2: Update `__init__.py`**

```python
from .commands.workflow import workflow_app
app.add_typer(workflow_app, name="workflow")
```

- [ ] **Step 3: Run full test suite + smoke test**

```bash
python -m pytest -v
python -m specify_cli --help
python -m specify_cli integration --help
python -m specify_cli preset --help
python -m specify_cli extension --help
python -m specify_cli workflow --help
python -m specify_cli self check
```

Expected: all PASS, all help renders correctly

- [ ] **Step 4: Commit**

```bash
git add src/specify_cli/commands/workflow.py src/specify_cli/__init__.py
git commit -m "refactor: move workflow command handlers to commands/workflow.py"
```

---

### Task 14: Final `__init__.py` cleanup

**Files:**
- Modify: `src/specify_cli/__init__.py`

After all moves, `__init__.py` should contain only:
- Module docstring
- `app = typer.Typer(cls=BannerGroup, ...)` definition
- `app.add_typer(...)` calls for each sub-typer (imported from commands modules)
- The `@app.callback()` function
- `main()` entry point
- Re-export imports for backward compatibility (all previously-public symbols)

The `GITHUB_API_LATEST` constant moves to `_version.py`. Sub-typer objects (`integration_app`, `extension_app`, etc.) are no longer defined here — they live in their respective commands modules.

- [ ] **Step 1: Count remaining lines**

```bash
wc -l src/specify_cli/__init__.py
```

Expected: under 200 lines

- [ ] **Step 2: Remove any unused imports from `__init__.py`**

```bash
python -m py_compile src/specify_cli/__init__.py && echo "syntax OK"
```

Then run:
```bash
python -m pytest -v
```

Expected: all PASS

- [ ] **Step 3: Final commit**

```bash
git add src/specify_cli/__init__.py
git commit -m "refactor: clean up __init__.py after full module extraction"
```

---

## Verification Checklist

After all tasks complete:

- [ ] `wc -l src/specify_cli/__init__.py` shows < 200 lines
- [ ] `python -m pytest -v` — all existing tests pass
- [ ] `python -m specify_cli --help` — renders correctly
- [ ] `python -m specify_cli init --help` — renders correctly
- [ ] New service unit tests exist: `test_asset_service.py`, `test_git_service.py`, `test_version_service.py`
- [ ] No `console.print` in `_assets.py`, `_git.py`, `_version.py`, `_fs.py`
- [ ] All old symbol names importable from `specify_cli` (checked by backward-compat tests)
