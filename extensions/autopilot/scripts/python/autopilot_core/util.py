"""Small shared helpers: atomic JSON files, subprocesses, git, timestamps."""

from __future__ import annotations

import datetime as _dt
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

STATE_DIR = Path(".specify") / "autopilot"
# Paths the autopilot never commits into an epic branch.
EXCLUDED_FROM_COMMITS = (".specify/autopilot", ".specify/workflows/runs")


def now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()


def ensure_state_dir(project_root: Path) -> Path:
    """Create ``.specify/autopilot`` with a catch-all ``.gitignore``."""
    path = project_root / STATE_DIR
    path.mkdir(parents=True, exist_ok=True)
    ignore = path / ".gitignore"
    if not ignore.exists():
        ignore.write_text(
            "# Autopilot run state is local to this checkout.\n*\n"
            "!.gitignore\n!epics.json\n!epics.md\n!dag.md\n!report.md\n",
            encoding="utf-8",
        )
    return path


def read_json(path: Path, default: Any = None) -> Any:
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(data, handle, indent=2, sort_keys=False)
            handle.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps({"at": now_iso(), **record}, sort_keys=False) + "\n")


def run(
    args: list[str] | str,
    cwd: Path,
    *,
    shell: bool = False,
    timeout: float | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a process, decode as UTF-8, never raise on non-zero exit."""
    merged_env = None
    if env is not None:
        merged_env = {**os.environ, **env}
    try:
        return subprocess.run(
            args,
            cwd=str(cwd),
            shell=shell,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=merged_env,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode("utf-8", "replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return subprocess.CompletedProcess(args, -1, stdout, stderr + f"\n[autopilot] timed out after {timeout}s")
    except OSError as exc:
        return subprocess.CompletedProcess(args, 127, "", f"[autopilot] could not start: {exc}")


class GitError(RuntimeError):
    pass


def git(cwd: Path, *args: str, check: bool = True) -> str:
    result = run(["git", *args], cwd)
    if check and result.returncode != 0:
        raise GitError(f"git {' '.join(args)} failed in {cwd}: {result.stderr.strip() or result.stdout.strip()}")
    return result.stdout.strip()


def git_ok(cwd: Path, *args: str) -> bool:
    return run(["git", *args], cwd).returncode == 0


def repo_root(cwd: Path) -> Path:
    return Path(git(cwd, "rev-parse", "--show-toplevel"))


def _under(path: str, prefixes: tuple[str, ...] | list[str]) -> bool:
    return any(path == p.rstrip("/") or path.startswith(p.rstrip("/") + "/") for p in prefixes)


def dirty_paths(cwd: Path, allow_untracked: tuple[str, ...] | list[str] = ()) -> list[str]:
    """Changed paths, ignoring autopilot state and untracked files under ``allow_untracked``."""
    status = git(cwd, "status", "--porcelain", "--untracked-files=all")
    dirty = []
    for line in status.splitlines():
        code, path = line[:2], line[3:].strip().strip('"')
        if _under(path, EXCLUDED_FROM_COMMITS) or (code == "??" and _under(path, allow_untracked)):
            continue
        dirty.append(path)
    return dirty


def is_clean(cwd: Path, allow_untracked: tuple[str, ...] | list[str] = ()) -> bool:
    return not dirty_paths(cwd, allow_untracked)


def tree_fingerprint(cwd: Path) -> str:
    """Hash of the working tree's changes relative to HEAD (tracked + untracked)."""
    import hashlib

    digest = hashlib.sha256()
    digest.update(git(cwd, "status", "--porcelain", "--untracked-files=all").encode())
    digest.update(git(cwd, "diff", "HEAD", "--binary", check=False).encode())
    for line in git(cwd, "ls-files", "--others", "--exclude-standard").splitlines():
        target = cwd / line
        if target.is_file():
            digest.update(line.encode())
            digest.update(target.read_bytes())
    return digest.hexdigest()


def exclude_pathspecs() -> list[str]:
    return [f":(exclude){path}" for path in EXCLUDED_FROM_COMMITS]


def identity_args(cwd: Path) -> list[str]:
    """``-c user.*`` fallbacks so commits work in repos without an identity."""
    name = git(cwd, "config", "user.name", check=False) or "Spec Kit Autopilot"
    email = git(cwd, "config", "user.email", check=False) or "autopilot@localhost"
    return ["-c", f"user.name={name}", "-c", f"user.email={email}"]


def stage_changes(cwd: Path, sync_paths: tuple[str, ...] | list[str] = ()) -> None:
    """Stage the epic's work: tracked changes anywhere, new files outside ``sync_paths``.

    Untracked files under ``sync_paths`` are Spec Kit / agent files the scheduler
    copied into the worktree; committing them would collide with the same
    untracked copies in other checkouts at merge time.
    """
    git(cwd, "add", "-u", "--", ".", *exclude_pathspecs())
    new_files = [
        path for path in git(cwd, "ls-files", "--others", "--exclude-standard", "-z").split("\0")
        if path and not _under(path, EXCLUDED_FROM_COMMITS) and not _under(path, sync_paths)
    ]
    for start in range(0, len(new_files), 200):
        git(cwd, "add", "--", *new_files[start:start + 200])


def commit_all(cwd: Path, message: str, sync_paths: tuple[str, ...] | list[str] = ()) -> bool:
    """Stage the epic's work (see ``stage_changes``) and commit; False if nothing to commit."""
    stage_changes(cwd, sync_paths)
    if git_ok(cwd, "diff", "--cached", "--quiet"):
        return False
    # Commit hooks are part of the project's environment constraints: never bypass them.
    git(cwd, *identity_args(cwd), "commit", "-q", "-m", message)
    return True
