"""Tests for the extension version-bump CI guard script (#4345).

The guard (`.github/scripts/check_extension_version_bump.py`) is the
primary regression prevention for bundled-extension version staleness, so
its failure behavior must be pinned by tests: each scenario builds a real
throwaway git repository and invokes the script against base/head SHAs,
exactly as the `extension-version-guard.yml` workflow does. Without this,
a change to the script's diff or parsing logic could silently disable the
guard while CI stays green.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[2]
SCRIPT = REPO_ROOT / ".github" / "scripts" / "check_extension_version_bump.py"


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _write_extension(repo: Path, ext_id: str, version: str, script_line: str) -> None:
    ext_dir = repo / "extensions" / ext_id
    ext_dir.mkdir(parents=True, exist_ok=True)
    (ext_dir / "extension.yml").write_text(
        'schema_version: "1.0"\n'
        "\n"
        "extension:\n"
        f"  id: {ext_id}\n"
        f'  version: "{version}"\n',
        encoding="utf-8",
    )
    (ext_dir / "script.sh").write_text(f"{script_line}\n", encoding="utf-8")


def _write_catalog(repo: Path, versions: dict[str, str]) -> None:
    (repo / "extensions").mkdir(exist_ok=True)
    payload = {
        "schema_version": "1.0",
        "extensions": {
            ext_id: {"id": ext_id, "version": version, "bundled": True}
            for ext_id, version in versions.items()
        },
    }
    (repo / "extensions" / "catalog.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )


def _commit_all(repo: Path, message: str) -> str:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


@pytest.fixture
def guard_repo(tmp_path: Path) -> tuple[Path, str]:
    """A git repo with one cataloged and one uncataloged extension at base."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "guard-tests@example.com")
    _git(repo, "config", "user.name", "Guard Tests")
    _git(repo, "config", "commit.gpgsign", "false")

    _write_extension(repo, "demo", "1.0.0", "echo base")
    _write_extension(repo, "scratch", "1.0.0", "echo base")  # not in catalog
    _write_catalog(repo, {"demo": "1.0.0"})
    base_sha = _commit_all(repo, "base")
    return repo, base_sha


def _run_guard(repo: Path, base: str, head: str = "HEAD") -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), base, head],
        cwd=repo,
        capture_output=True,
        text=True,
    )


def test_valid_bump_passes(guard_repo):
    repo, base = guard_repo
    _write_extension(repo, "demo", "1.1.0", "echo changed")
    _write_catalog(repo, {"demo": "1.1.0"})
    _commit_all(repo, "content change with bump")

    result = _run_guard(repo, base)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "all invariants hold" in result.stdout


def test_unbumped_content_change_fails(guard_repo):
    repo, base = guard_repo
    _write_extension(repo, "demo", "1.0.0", "echo changed")
    _commit_all(repo, "content change without bump")

    result = _run_guard(repo, base)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "did not increase" in result.stdout
    assert "extensions/demo/extension.yml" in result.stdout


def test_downgrade_fails(guard_repo):
    repo, base = guard_repo
    _write_extension(repo, "demo", "0.9.0", "echo changed")
    _write_catalog(repo, {"demo": "0.9.0"})
    _commit_all(repo, "downgrade")

    result = _run_guard(repo, base)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "did not increase" in result.stdout


def test_prerelease_downgrade_fails(guard_repo):
    """PEP 440 semantics: 1.0.0rc1 is lower than 1.0.0, and it must not slip
    through as a plain string inequality."""
    repo, base = guard_repo
    _write_extension(repo, "demo", "1.0.0rc1", "echo changed")
    _write_catalog(repo, {"demo": "1.0.0rc1"})
    _commit_all(repo, "prerelease downgrade")

    result = _run_guard(repo, base)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "did not increase" in result.stdout


def test_manifest_bump_without_catalog_sync_fails(guard_repo):
    repo, base = guard_repo
    _write_extension(repo, "demo", "1.1.0", "echo changed")
    _commit_all(repo, "bump without catalog sync")

    result = _run_guard(repo, base)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "must move together" in result.stdout
    assert "catalog.json" in result.stdout


def test_uncataloged_extension_change_is_exempt(guard_repo):
    repo, base = guard_repo
    _write_extension(repo, "scratch", "1.0.0", "echo changed")
    _commit_all(repo, "uncataloged change without bump")

    result = _run_guard(repo, base)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "all invariants hold" in result.stdout


def test_new_cataloged_extension_passes_without_base_version(guard_repo):
    repo, base = guard_repo
    _write_extension(repo, "fresh", "0.1.0", "echo new")
    _write_catalog(repo, {"demo": "1.0.0", "fresh": "0.1.0"})
    _commit_all(repo, "add new extension")

    result = _run_guard(repo, base)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "all invariants hold" in result.stdout


def test_unparseable_version_fails_closed(guard_repo):
    repo, base = guard_repo
    _write_extension(repo, "demo", "not-a-version", "echo changed")
    _write_catalog(repo, {"demo": "not-a-version"})
    _commit_all(repo, "unparseable version")

    result = _run_guard(repo, base)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "could not compare versions" in result.stdout
