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


def _write_catalog(repo: Path, versions: dict[str, str | dict]) -> None:
    """Write catalog.json; a value is either a bundled entry's version string
    or a full entry dict (for e.g. hosted, non-bundled entries)."""
    (repo / "extensions").mkdir(exist_ok=True)
    payload = {
        "schema_version": "1.0",
        "extensions": {
            ext_id: (
                {"id": ext_id, **spec}
                if isinstance(spec, dict)
                else {"id": ext_id, "version": spec, "bundled": True}
            )
            for ext_id, spec in versions.items()
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
    # git's default; pinned so the non-ASCII regression below exercises the
    # C-quoting code path even on machines whose global config disables it.
    _git(repo, "config", "core.quotePath", "true")

    _write_extension(repo, "demo", "1.0.0", "echo base")
    _write_extension(repo, "scratch", "1.0.0", "echo base")  # not in catalog
    _write_catalog(repo, {"demo": "1.0.0"})
    base_sha = _commit_all(repo, "base")
    return repo, base_sha


def _run_guard(
    repo: Path, base: str, head: str | None = None
) -> subprocess.CompletedProcess:
    """Invoke the guard as the workflow does: base ref only, head defaulting
    to HEAD inside the script. Pass *head* explicitly only to test the
    optional second argument."""
    return subprocess.run(
        [sys.executable, str(SCRIPT), base, *([head] if head else [])],
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


def test_unbumped_non_ascii_filename_fails(guard_repo):
    """With core.quotePath (git's default) `git diff --name-only` C-quotes a
    path like extensions/demo/café.txt, quotes included, so a line-based
    parser no longer sees `extensions` as the first component and the
    change escapes the guard. The NUL-delimited diff must still catch it."""
    repo, base = guard_repo
    (repo / "extensions" / "demo" / "café.txt").write_text("new\n", encoding="utf-8")
    _commit_all(repo, "add non-ascii file without bump")

    result = _run_guard(repo, base)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "did not increase" in result.stdout
    assert "extensions/demo/extension.yml" in result.stdout


def test_merge_commit_first_parent_ignores_base_branch_drift(guard_repo):
    """The workflow diffs against HEAD^1 of GitHub's pull-request merge commit,
    not github.event.pull_request.base.sha. The payload SHA is the base tip
    from when the PR was opened and is never refreshed, while the merge ref
    is rebuilt against the current base tip; diffing the stale SHA against
    the fresh merge commit blames base-branch drift on the PR (seen on
    #4395). The merge commit's first parent is the base it was built on."""
    repo, stale_base = guard_repo
    _git(repo, "checkout", "-q", "-b", "pr")
    (repo / "README.md").write_text("pr change\n", encoding="utf-8")
    _commit_all(repo, "unrelated PR change")

    # Base branch moves on after the PR branched off: an unbumped extension
    # change lands there. GitHub then rebuilds refs/pull/N/merge on top of it.
    _git(repo, "checkout", "-q", "-")
    _write_extension(repo, "demo", "1.0.0", "echo drifted on base")
    _commit_all(repo, "unbumped change on base after PR branched")
    _git(repo, "merge", "-q", "--no-ff", "--no-edit", "pr")

    stale = _run_guard(repo, stale_base)
    assert stale.returncode == 1, stale.stdout + stale.stderr
    assert "did not increase" in stale.stdout  # the trap: drift blamed on the PR

    fresh = _run_guard(repo, "HEAD^1")
    assert fresh.returncode == 0, fresh.stdout + fresh.stderr
    assert "all invariants hold" in fresh.stdout


def test_no_extension_changes_passes(guard_repo):
    """The workflow runs on every pull request (a path-filtered required check
    would block PRs that skip it), so a PR touching nothing under extensions/
    must pass rather than be reported as a violation."""
    repo, base = guard_repo
    (repo / "README.md").write_text("docs only\n", encoding="utf-8")
    _commit_all(repo, "unrelated change")

    result = _run_guard(repo, base)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "all invariants hold" in result.stdout


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


def test_explicit_head_argument_is_honored(guard_repo):
    """The optional HEAD_REF argument must select the head to check: pointing
    it at the base commit yields an empty diff even though HEAD has an
    unbumped change."""
    repo, base = guard_repo
    _write_extension(repo, "demo", "1.0.0", "echo changed")
    _commit_all(repo, "content change without bump")

    result = _run_guard(repo, base, head=base)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "all invariants hold" in result.stdout


def test_catalog_only_entry_with_unparseable_version_fails(guard_repo):
    """A hosted (non-bundled) entry has no in-repo directory, so nothing under
    extensions/ changes and Invariant 1 never sees it; its catalog version
    must still parse because `extension update` skips entries it cannot."""
    repo, base = guard_repo
    _write_catalog(
        repo,
        {
            "demo": "1.0.0",
            "hosted": {
                "version": "not-a-version",
                "bundled": False,
                "download_url": "https://example.com/hosted-1.0.0.zip",
            },
        },
    )
    _commit_all(repo, "add hosted entry with invalid version")

    result = _run_guard(repo, base)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "entry 'hosted'" in result.stdout
    assert "is not a valid PEP 440 version" in result.stdout


def test_catalog_only_promotion_with_unparseable_version_fails(guard_repo):
    """Promoting an existing uncataloged directory by adding only its catalog
    entry changes nothing under extensions/<id>/, so Invariant 1 skips it;
    matching invalid strings must still fail because the CLI cannot use them.
    The catalog-version parse rejects the entry first."""
    repo, _ = guard_repo
    _write_extension(repo, "draft", "not-a-version", "echo draft")
    base = _commit_all(repo, "uncataloged draft with invalid version on base")

    _write_catalog(repo, {"demo": "1.0.0", "draft": "not-a-version"})
    _commit_all(repo, "promote draft via catalog only")

    result = _run_guard(repo, base)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "entry 'draft'" in result.stdout
    assert "is not a valid PEP 440 version" in result.stdout


def test_catalog_only_promotion_with_invalid_manifest_version_fails(guard_repo):
    """Same promotion, but the catalog carries a valid version while the
    untouched in-repo manifest does not: Invariant 2 must parse the manifest
    itself (not only compare strings) and name the manifest in the error."""
    repo, _ = guard_repo
    _write_extension(repo, "draft", "not-a-version", "echo draft")
    base = _commit_all(repo, "uncataloged draft with invalid version on base")

    _write_catalog(repo, {"demo": "1.0.0", "draft": "1.0.0"})
    _commit_all(repo, "promote draft with a valid catalog version only")

    result = _run_guard(repo, base)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "extensions/draft/extension.yml" in result.stdout
    assert "is not a valid PEP 440 version" in result.stdout


def test_catalog_only_promotion_with_valid_version_passes(guard_repo):
    """The uncataloged `scratch` fixture carries a valid 1.0.0; cataloging it
    without touching its directory is a legitimate promotion."""
    repo, base = guard_repo
    _write_catalog(repo, {"demo": "1.0.0", "scratch": "1.0.0"})
    _commit_all(repo, "promote scratch via catalog only")

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
    assert "is not a valid PEP 440 version" in result.stdout
    assert "extensions/demo/extension.yml" in result.stdout


def test_new_extension_with_unparseable_version_fails(guard_repo):
    """A brand-new extension has no base manifest to compare against, but its
    version must still parse: ExtensionManifest rejects a version packaging
    cannot parse and `extension update` skips such catalog entries. Matching
    strings in manifest and catalog must not let it through."""
    repo, base = guard_repo
    _write_extension(repo, "fresh", "not-a-version", "echo new")
    _write_catalog(repo, {"demo": "1.0.0", "fresh": "not-a-version"})
    _commit_all(repo, "add new extension with invalid version")

    result = _run_guard(repo, base)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "is not a valid PEP 440 version" in result.stdout
    assert "extensions/fresh/extension.yml" in result.stdout
