"""Tests for the bandit and detect-secrets baseline growth gate scripts.

Both scripts share the same shape: read the baseline at a base ref and a
head ref, compare *identities* (not counts) so a swap doesn't slip
through, and require an acknowledgement label when the head set is a
strict superset.

We drive the scripts as subprocesses against a throwaway git repo so the
``git show <ref>:<path>`` calls inside them resolve real refs.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
BANDIT_SCRIPT = REPO_ROOT / ".github" / "scripts" / "check_bandit_baseline.py"
SECRETS_SCRIPT = REPO_ROOT / ".github" / "scripts" / "check_secrets_baseline.py"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ).stdout.strip()


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    # Mirror the layout the scripts expect: REPO_ROOT/.github/...
    (repo / ".github").mkdir()
    (repo / ".github" / "scripts").mkdir()
    # Copy the script under test into the repo so REPO_ROOT inside the
    # script (resolve().parents[2]) points at our throwaway repo.
    return repo


def _install_script(repo: Path, source: Path) -> Path:
    target = repo / ".github" / "scripts" / source.name
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return target


def _commit_baseline(repo: Path, baseline_path: str, payload: dict, message: str) -> str:
    target = repo / baseline_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _git(repo, "add", baseline_path)
    _git(repo, "commit", "-q", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


def _run_script(repo: Path, script: Path, env_overrides: dict[str, str]):
    env = {
        "PATH": "/usr/bin:/bin",
        "HOME": str(repo),  # avoid leaking host gitconfig
        **env_overrides,
    }
    return subprocess.run(
        [sys.executable, str(script)],
        cwd=repo,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


# ---------------------------------------------------------------------------
# Bandit baseline gate
# ---------------------------------------------------------------------------


def _bandit_entry(filename: str, line: int, test_id: str = "B602", code: str = "shell=True") -> dict:
    return {
        "filename": filename,
        "line_number": line,
        "test_id": test_id,
        "issue_severity": "HIGH",
        "issue_confidence": "HIGH",
        "code": code,
    }


class TestBanditBaselineGate:
    @pytest.fixture
    def repo(self, tmp_path):
        repo = _init_repo(tmp_path)
        _install_script(repo, BANDIT_SCRIPT)
        return repo

    def _run(self, repo, base, head, labels=""):
        return _run_script(
            repo,
            repo / ".github" / "scripts" / BANDIT_SCRIPT.name,
            {
                "BANDIT_BASELINE_BASE": base,
                "BANDIT_BASELINE_HEAD": head,
                "BANDIT_BASELINE_LABELS": labels,
            },
        )

    def test_no_base_ref_is_skipped(self, repo):
        # Need at least one commit so HEAD resolves.
        _commit_baseline(repo, ".github/bandit-baseline.json", {"results": []}, "init")
        result = self._run(repo, base="", head="HEAD")
        assert result.returncode == 0
        assert "baseline diff check skipped" in result.stdout

    def test_introduction_pr_skips_check(self, repo):
        _git(repo, "commit", "--allow-empty", "-q", "-m", "before baseline")
        base_sha = _git(repo, "rev-parse", "HEAD")
        head_sha = _commit_baseline(
            repo,
            ".github/bandit-baseline.json",
            {"results": [_bandit_entry("a.py", 10)]},
            "introduce baseline",
        )
        result = self._run(repo, base=base_sha, head=head_sha)
        assert result.returncode == 0, result.stderr
        assert "introduction of the baseline" in result.stdout

    def test_identical_baselines_pass(self, repo):
        entries = [_bandit_entry("a.py", 10)]
        base_sha = _commit_baseline(repo, ".github/bandit-baseline.json", {"results": entries}, "base")
        # No changes; head == base.
        result = self._run(repo, base=base_sha, head=base_sha)
        assert result.returncode == 0
        assert "no new identities" in result.stdout

    def test_growth_without_label_fails(self, repo):
        base_sha = _commit_baseline(
            repo,
            ".github/bandit-baseline.json",
            {"results": [_bandit_entry("a.py", 10)]},
            "base",
        )
        head_sha = _commit_baseline(
            repo,
            ".github/bandit-baseline.json",
            {"results": [_bandit_entry("a.py", 10), _bandit_entry("b.py", 20)]},
            "grow",
        )
        result = self._run(repo, base=base_sha, head=head_sha)
        assert result.returncode == 1
        assert "'security-baseline-change'" in result.stderr

    def test_growth_with_label_passes(self, repo):
        base_sha = _commit_baseline(
            repo,
            ".github/bandit-baseline.json",
            {"results": [_bandit_entry("a.py", 10)]},
            "base",
        )
        head_sha = _commit_baseline(
            repo,
            ".github/bandit-baseline.json",
            {"results": [_bandit_entry("a.py", 10), _bandit_entry("b.py", 20)]},
            "grow",
        )
        result = self._run(repo, base=base_sha, head=head_sha, labels="security-baseline-change")
        assert result.returncode == 0
        assert "acknowledged via label" in result.stdout

    def test_swap_attack_detected(self, repo):
        """Removing one entry and adding a different one keeps the count
        constant but introduces a new identity; gate must still fire."""
        base_sha = _commit_baseline(
            repo,
            ".github/bandit-baseline.json",
            {"results": [_bandit_entry("a.py", 10)]},
            "base",
        )
        head_sha = _commit_baseline(
            repo,
            ".github/bandit-baseline.json",
            {"results": [_bandit_entry("b.py", 20)]},  # swapped, same count
            "swap",
        )
        result = self._run(repo, base=base_sha, head=head_sha)
        assert result.returncode == 1, "swap should be detected via identity diff"
        assert "1 new identities" in result.stderr

    def test_whitespace_only_change_does_not_trip(self, repo):
        """A bandit version bump that reformats the code snippet (different
        whitespace) shouldn't make every entry look new."""
        base_sha = _commit_baseline(
            repo,
            ".github/bandit-baseline.json",
            {"results": [_bandit_entry("a.py", 10, code="shell=True\n    capture_output=True")]},
            "base",
        )
        head_sha = _commit_baseline(
            repo,
            ".github/bandit-baseline.json",
            {
                "results": [
                    _bandit_entry("a.py", 10, code="shell=True\ncapture_output=True")
                ]
            },
            "reformatted snippet",
        )
        result = self._run(repo, base=base_sha, head=head_sha)
        assert result.returncode == 0, result.stderr


# ---------------------------------------------------------------------------
# Secrets baseline gate
# ---------------------------------------------------------------------------


def _secrets_baseline(*entries: tuple[str, int, str, str]) -> dict:
    """Build a detect-secrets-style baseline from (file, line, type, hash) tuples."""
    results: dict[str, list[dict]] = {}
    for filename, line, secret_type, hashed in entries:
        results.setdefault(filename, []).append(
            {
                "type": secret_type,
                "filename": filename,
                "hashed_secret": hashed,
                "is_verified": False,
                "line_number": line,
            }
        )
    return {"version": "1.5.0", "results": results}


class TestSecretsBaselineGate:
    @pytest.fixture
    def repo(self, tmp_path):
        repo = _init_repo(tmp_path)
        _install_script(repo, SECRETS_SCRIPT)
        return repo

    def _run(self, repo, base, head, labels=""):
        return _run_script(
            repo,
            repo / ".github" / "scripts" / SECRETS_SCRIPT.name,
            {
                "SECRETS_BASELINE_BASE": base,
                "SECRETS_BASELINE_HEAD": head,
                "SECRETS_BASELINE_LABELS": labels,
            },
        )

    def test_introduction_pr_skips_check(self, repo):
        _git(repo, "commit", "--allow-empty", "-q", "-m", "before baseline")
        base_sha = _git(repo, "rev-parse", "HEAD")
        head_sha = _commit_baseline(
            repo,
            ".secrets.baseline",
            _secrets_baseline(("a.py", 1, "Secret Keyword", "abc123")),
            "introduce",
        )
        result = self._run(repo, base=base_sha, head=head_sha)
        assert result.returncode == 0, result.stderr
        assert "introduction of the baseline" in result.stdout

    def test_growth_without_label_fails(self, repo):
        base_sha = _commit_baseline(
            repo,
            ".secrets.baseline",
            _secrets_baseline(("a.py", 1, "Secret Keyword", "abc")),
            "base",
        )
        head_sha = _commit_baseline(
            repo,
            ".secrets.baseline",
            _secrets_baseline(
                ("a.py", 1, "Secret Keyword", "abc"),
                ("b.py", 2, "Secret Keyword", "def"),
            ),
            "grow",
        )
        result = self._run(repo, base=base_sha, head=head_sha)
        assert result.returncode == 1
        assert "'secrets-baseline-change'" in result.stderr

    def test_growth_with_label_passes(self, repo):
        base_sha = _commit_baseline(
            repo,
            ".secrets.baseline",
            _secrets_baseline(("a.py", 1, "Secret Keyword", "abc")),
            "base",
        )
        head_sha = _commit_baseline(
            repo,
            ".secrets.baseline",
            _secrets_baseline(
                ("a.py", 1, "Secret Keyword", "abc"),
                ("b.py", 2, "Secret Keyword", "def"),
            ),
            "grow",
        )
        result = self._run(
            repo, base=base_sha, head=head_sha, labels="secrets-baseline-change"
        )
        assert result.returncode == 0, result.stderr
        assert "acknowledged via label" in result.stdout

    def test_swap_attack_detected(self, repo):
        base_sha = _commit_baseline(
            repo,
            ".secrets.baseline",
            _secrets_baseline(("a.py", 1, "Secret Keyword", "abc")),
            "base",
        )
        head_sha = _commit_baseline(
            repo,
            ".secrets.baseline",
            _secrets_baseline(("b.py", 2, "Secret Keyword", "def")),
            "swap",
        )
        result = self._run(repo, base=base_sha, head=head_sha)
        assert result.returncode == 1
        assert "1 new identities" in result.stderr

    def test_identical_baselines_pass(self, repo):
        entries = (("a.py", 1, "Secret Keyword", "abc"),)
        base_sha = _commit_baseline(
            repo, ".secrets.baseline", _secrets_baseline(*entries), "base"
        )
        result = self._run(repo, base=base_sha, head=base_sha)
        assert result.returncode == 0
        assert "no new identities" in result.stdout
