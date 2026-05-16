"""Tests for the bandit and detect-secrets baseline growth gate scripts.

Both scripts share the same shape: read the baseline at a base ref and a
head ref, compare *identities* (not counts) so a swap doesn't slip
through, and require an acknowledgement label when the head set is a
strict superset.

Shared cases (introduction, identical, growth±label, swap, corrupt-JSON
fallback) are parametrized across both scripts via the ``gate`` fixture.
Bandit-only quirks (no-base-ref, whitespace normalization) live in
``TestBanditSpecific``.

We drive the scripts as subprocesses against a throwaway git repo so the
``git show <ref>:<path>`` calls inside them resolve real refs.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

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
    (repo / ".github").mkdir()
    (repo / ".github" / "scripts").mkdir()
    return repo


def _install_script(repo: Path, source: Path) -> Path:
    target = repo / ".github" / "scripts" / source.name
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return target


def _commit_file(repo: Path, rel_path: str, content: str, message: str) -> str:
    target = repo / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    _git(repo, "add", rel_path)
    _git(repo, "commit", "-q", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


def _commit_baseline(repo: Path, baseline_path: str, payload: dict, message: str) -> str:
    return _commit_file(repo, baseline_path, json.dumps(payload, indent=2), message)


def _run_script(repo: Path, script: Path, env_overrides: dict[str, str]):
    env = {
        "PATH": "/usr/bin:/bin",
        "HOME": str(repo),
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
# Parametrization machinery
# ---------------------------------------------------------------------------


def _bandit_baseline(entries: list[tuple[str, int]]) -> dict:
    """Build a bandit-style baseline from (filename, line) tuples."""
    return {
        "results": [
            {
                "filename": filename,
                "line_number": line,
                "test_id": "B602",
                "issue_severity": "HIGH",
                "issue_confidence": "HIGH",
                "code": f"shell=True at {filename}:{line}",
            }
            for filename, line in entries
        ]
    }


def _secrets_baseline(entries: list[tuple[str, int]]) -> dict:
    """Build a detect-secrets-style baseline from (filename, line) tuples."""
    results: dict[str, list[dict]] = {}
    for filename, line in entries:
        results.setdefault(filename, []).append(
            {
                "type": "Secret Keyword",
                "filename": filename,
                # The hash is part of the identity, so make it unique per (file, line).
                "hashed_secret": f"h_{filename}_{line}",
                "is_verified": False,
                "line_number": line,
            }
        )
    return {"version": "1.5.0", "results": results}


@dataclass
class GateConfig:
    name: str
    script: Path
    env_prefix: str
    baseline_path: str
    label: str
    make_baseline: Callable[[list[tuple[str, int]]], dict]


BANDIT_GATE = GateConfig(
    name="bandit",
    script=BANDIT_SCRIPT,
    env_prefix="BANDIT_BASELINE",
    baseline_path=".github/bandit-baseline.json",
    label="security-baseline-change",
    make_baseline=_bandit_baseline,
)


SECRETS_GATE = GateConfig(
    name="secrets",
    script=SECRETS_SCRIPT,
    env_prefix="SECRETS_BASELINE",
    baseline_path=".secrets.baseline",
    label="secrets-baseline-change",
    make_baseline=_secrets_baseline,
)


@dataclass
class GateHandle:
    """Live test harness: a repo with the script installed and helpers."""

    config: GateConfig
    repo: Path

    def commit(self, entries: list[tuple[str, int]], message: str) -> str:
        return _commit_baseline(
            self.repo,
            self.config.baseline_path,
            self.config.make_baseline(entries),
            message,
        )

    def commit_raw(self, raw_content: str, message: str) -> str:
        return _commit_file(self.repo, self.config.baseline_path, raw_content, message)

    def delete_baseline(self, message: str) -> str:
        """Remove the baseline file from the working tree and commit."""
        (self.repo / self.config.baseline_path).unlink()
        _git(self.repo, "add", "-A")
        _git(self.repo, "commit", "-q", "-m", message)
        return _git(self.repo, "rev-parse", "HEAD")

    def overwrite_worktree(self, raw_content: str) -> None:
        """Replace the working-tree baseline without committing.

        Used to simulate a corrupt head state read from disk.
        """
        (self.repo / self.config.baseline_path).write_text(raw_content, encoding="utf-8")

    def run(self, *, base: str, labels: str = ""):
        # Head side reads the working tree directly — no env var needed.
        return _run_script(
            self.repo,
            self.repo / ".github" / "scripts" / self.config.script.name,
            {
                f"{self.config.env_prefix}_BASE": base,
                f"{self.config.env_prefix}_LABELS": labels,
            },
        )


@pytest.fixture(params=[BANDIT_GATE, SECRETS_GATE], ids=lambda c: c.name)
def gate(request, tmp_path) -> GateHandle:
    config: GateConfig = request.param
    repo = _init_repo(tmp_path)
    _install_script(repo, config.script)
    return GateHandle(config=config, repo=repo)


# ---------------------------------------------------------------------------
# Shared scenarios (parametrized across both scripts)
# ---------------------------------------------------------------------------


class TestSharedBaselineGate:
    """Scenarios that must hold for both the bandit and secrets gates."""

    def test_introduction_pr_skips_check(self, gate: GateHandle):
        # Baseline file did not exist at base ref → no acknowledgement needed.
        _git(gate.repo, "commit", "--allow-empty", "-q", "-m", "before baseline")
        base_sha = _git(gate.repo, "rev-parse", "HEAD")
        gate.commit([("a.py", 10)], "introduce baseline")

        result = gate.run(base=base_sha)

        assert result.returncode == 0, result.stderr
        assert "introduction of the baseline" in result.stdout

    def test_identical_baselines_pass(self, gate: GateHandle):
        base_sha = gate.commit([("a.py", 10)], "base")
        result = gate.run(base=base_sha)
        assert result.returncode == 0
        assert "no new identities" in result.stdout

    def test_growth_without_label_fails(self, gate: GateHandle):
        base_sha = gate.commit([("a.py", 10)], "base")
        gate.commit([("a.py", 10), ("b.py", 20)], "grow")

        result = gate.run(base=base_sha)

        assert result.returncode == 1
        assert f"'{gate.config.label}'" in result.stderr

    def test_growth_with_label_passes(self, gate: GateHandle):
        base_sha = gate.commit([("a.py", 10)], "base")
        gate.commit([("a.py", 10), ("b.py", 20)], "grow")

        result = gate.run(base=base_sha, labels=gate.config.label)

        assert result.returncode == 0, result.stderr
        assert "acknowledged via label" in result.stdout

    def test_swap_attack_detected(self, gate: GateHandle):
        """Remove one entry and add a different one → constant count, but
        a *new* identity appears. Gate must still fire."""
        base_sha = gate.commit([("a.py", 10)], "base")
        gate.commit([("b.py", 20)], "swap")  # same count, different ID

        result = gate.run(base=base_sha)

        assert result.returncode == 1, "identity diff must catch swaps"
        assert "1 new identities" in result.stderr

    def test_corrupt_json_at_base_falls_back_to_empty(self, gate: GateHandle):
        """If the baseline at the base ref is unparseable JSON, treat its
        contents as empty so the script still completes (the head set
        becomes 'all new' and the label gate fires)."""
        base_sha = gate.commit_raw("{ invalid json", "corrupt base")
        gate.commit([("a.py", 10)], "valid head")

        result = gate.run(base=base_sha)

        assert result.returncode == 1, "corrupt base should not crash the script"
        assert f"'{gate.config.label}'" in result.stderr
        assert "Could not parse baseline" in result.stderr

    def test_head_missing_fails_closed(self, gate: GateHandle):
        """If the baseline existed at base but is missing in the working
        tree (head), the gate must fail-closed — silently passing would
        let a PR delete the whole baseline file and neutralize the gate."""
        base_sha = gate.commit([("a.py", 10)], "base")
        gate.delete_baseline("remove baseline at head")

        result = gate.run(base=base_sha)

        assert result.returncode == 1
        assert "Refusing to fail-open" in result.stderr

    def test_head_corrupt_in_worktree_fails_closed(self, gate: GateHandle):
        """A corrupt JSON in the working tree must raise (not be silently
        treated as empty, which would also drop the gate). Simulates a
        flaky tool writing junk to the file just before the script runs."""
        base_sha = gate.commit([("a.py", 10)], "base")
        gate.overwrite_worktree("{ not json")

        result = gate.run(base=base_sha)

        assert result.returncode == 1
        assert "is corrupt" in result.stderr
        assert "fail-open" in result.stderr


# ---------------------------------------------------------------------------
# Bandit-only scenarios
# ---------------------------------------------------------------------------


class TestBanditSpecific:
    """Cases that only exist for the bandit gate."""

    @pytest.fixture
    def gate(self, tmp_path) -> GateHandle:
        repo = _init_repo(tmp_path)
        _install_script(repo, BANDIT_SCRIPT)
        return GateHandle(config=BANDIT_GATE, repo=repo)

    def test_no_base_ref_is_skipped(self, gate: GateHandle):
        gate.commit([], "init")  # need at least one commit so HEAD resolves
        result = gate.run(base="")
        assert result.returncode == 0
        assert "baseline diff check skipped" in result.stdout

    def test_whitespace_only_change_does_not_trip(self, gate: GateHandle):
        """A bandit version bump that reformats the code snippet (different
        whitespace) should not flag the same finding as new — that's the
        purpose of the whitespace-normalized identity hash."""
        base_sha = _commit_baseline(
            gate.repo,
            gate.config.baseline_path,
            {
                "results": [
                    {
                        "filename": "a.py",
                        "line_number": 10,
                        "test_id": "B602",
                        "issue_severity": "HIGH",
                        "issue_confidence": "HIGH",
                        "code": "shell=True\n    capture_output=True",
                    }
                ]
            },
            "base",
        )
        _commit_baseline(
            gate.repo,
            gate.config.baseline_path,
            {
                "results": [
                    {
                        "filename": "a.py",
                        "line_number": 10,
                        "test_id": "B602",
                        "issue_severity": "HIGH",
                        "issue_confidence": "HIGH",
                        "code": "shell=True\ncapture_output=True",  # one less space
                    }
                ]
            },
            "reformatted snippet",
        )

        result = gate.run(base=base_sha)

        assert result.returncode == 0, result.stderr
