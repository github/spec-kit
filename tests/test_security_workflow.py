"""Static checks for the GitHub Actions security workflow."""

from __future__ import annotations

import inspect
import importlib.util
import json
import re
import subprocess
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
SECURITY_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "security.yml"
CONTRIBUTING = REPO_ROOT / "CONTRIBUTING.md"
BANDIT_BASELINE = REPO_ROOT / ".github" / "bandit-baseline.json"
SECURITY_REQUIREMENTS = REPO_ROOT / ".github" / "security-audit-requirements.txt"
SECURITY_REQUIREMENTS_SYNC_SCRIPT = (
    REPO_ROOT / ".github" / "scripts" / "check_security_requirements.py"
)

WORKFLOW_LIVE_AUDIT_REQUIREMENTS = '"${{ runner.temp }}/spec-kit-audit-requirements.txt"'
COMMITTED_AUDIT_REQUIREMENTS = ".github/security-audit-requirements.txt"
WORKFLOW_COMPILE_SCHEDULED_TEST_EXTRA_DEPS = (
    "uv pip compile pyproject.toml --extra test "
    '--python-version "${{ matrix.python-version }}" --generate-hashes --quiet '
    f"--output-file {WORKFLOW_LIVE_AUDIT_REQUIREMENTS}"
)
LOCAL_REFRESH_TEST_EXTRA_DEPS = (
    "uv pip compile pyproject.toml --extra test --universal --generate-hashes "
    f"--quiet --no-header --output-file {COMMITTED_AUDIT_REQUIREMENTS}"
)
WORKFLOW_SYNC_COMPILE_TEST_EXTRA_DEPS = (
    "uv pip compile pyproject.toml --extra test --universal --generate-hashes "
    "--quiet --no-header --output-file"
)
WORKFLOW_SYNC_SCRIPT = "python .github/scripts/check_security_requirements.py"
WORKFLOW_LIVE_PIP_AUDIT = (
    "uvx --from pip-audit==2.10.0 pip-audit --disable-pip --require-hashes "
    f"-r {WORKFLOW_LIVE_AUDIT_REQUIREMENTS} --progress-spinner off"
)
LOCAL_PIP_AUDIT = (
    "uvx --from pip-audit==2.10.0 pip-audit --disable-pip --require-hashes "
    f"-r {COMMITTED_AUDIT_REQUIREMENTS} --progress-spinner off"
)
BANDIT = (
    "uvx --from bandit==1.9.4 bandit -r src -lll "
    "--baseline .github/bandit-baseline.json"
)


def _load_security_workflow() -> dict:
    return yaml.safe_load(SECURITY_WORKFLOW.read_text(encoding="utf-8"))


def _workflow_triggers() -> dict:
    workflow = _load_security_workflow()
    return workflow.get("on") or workflow[True]


def _step(job_name: str, step_name: str) -> dict:
    workflow = _load_security_workflow()
    for step in workflow["jobs"][job_name]["steps"]:
        if step.get("name") == step_name:
            return step
    raise AssertionError(f"Step {step_name!r} not found in job {job_name!r}.")


def _step_run(job_name: str, step_name: str) -> str:
    return _step(job_name, step_name)["run"]


def _find_step_by_run_signature(job_name: str, marker: str) -> dict:
    """Locate a step in *job_name* whose ``run`` command contains *marker*.

    Step naming is incidental to behavior; tests that assert on what a
    step *does* should look it up by what it runs, not by its label, so
    renames don't silently make the assertion skip.
    """
    workflow = _load_security_workflow()
    matches = [
        step
        for step in workflow["jobs"][job_name]["steps"]
        if marker in (step.get("run") or "")
    ]
    if not matches:
        raise AssertionError(
            f"No step in job {job_name!r} runs a command containing {marker!r}."
        )
    if len(matches) > 1:
        raise AssertionError(
            f"Marker {marker!r} matched {len(matches)} steps in job "
            f"{job_name!r}; expected exactly one."
        )
    return matches[0]


def _load_sync_script():
    spec = importlib.util.spec_from_file_location(
        "check_security_requirements",
        SECURITY_REQUIREMENTS_SYNC_SCRIPT,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestSecurityWorkflow:
    """Guard the security workflow against review-feedback regressions."""

    def test_dependency_audit_uses_committed_requirements_for_prs_and_pushes(self):
        scheduled_compile = _step(
            "dependency-audit",
            "Compile scheduled audit requirements",
        )
        scheduled_audit = _step(
            "dependency-audit",
            "Run pip-audit (scheduled live resolution)",
        )
        committed_audit = _step(
            "dependency-audit",
            "Run pip-audit (committed requirements)",
        )
        sync_check = _step(
            "dependency-audit",
            "Check committed audit requirements are current",
        )

        assert scheduled_compile["if"] == "${{ github.event_name == 'schedule' }}"
        assert WORKFLOW_COMPILE_SCHEDULED_TEST_EXTRA_DEPS in scheduled_compile["run"]
        assert scheduled_audit["if"] == "${{ github.event_name == 'schedule' }}"
        assert scheduled_audit["run"] == WORKFLOW_LIVE_PIP_AUDIT
        assert sync_check["if"] == "${{ github.event_name != 'schedule' }}"
        assert sync_check["env"]["DEPENDENCY_DIFF_BASE"] == (
            "${{ github.event.pull_request.base.sha || github.event.before || '' }}"
        )
        assert sync_check["env"]["DEPENDENCY_DIFF_HEAD"] == "${{ github.sha }}"
        assert sync_check["run"] == WORKFLOW_SYNC_SCRIPT
        assert committed_audit["if"] == "${{ github.event_name != 'schedule' }}"
        assert committed_audit["run"] == LOCAL_PIP_AUDIT

        dependency_job_text = "\n".join(
            step.get("run", "")
            for step in _load_security_workflow()["jobs"]["dependency-audit"]["steps"]
        )
        dependency_protection_text = (
            dependency_job_text
            + "\n"
            + SECURITY_REQUIREMENTS_SYNC_SCRIPT.read_text(encoding="utf-8")
        )
        assert "--generate-hashes" in dependency_protection_text
        assert "--no-header" in dependency_protection_text
        assert "--require-hashes" in dependency_protection_text
        assert "--disable-pip" in dependency_protection_text
        assert WORKFLOW_LIVE_AUDIT_REQUIREMENTS in dependency_job_text
        assert COMMITTED_AUDIT_REQUIREMENTS in dependency_protection_text
        assert "uv export" not in dependency_protection_text
        assert "--frozen" not in dependency_protection_text
        assert "--locked" not in dependency_protection_text
        assert "uv.lock" not in dependency_protection_text
        assert "/tmp/" not in dependency_protection_text
        assert "uvx pip-audit ." not in dependency_protection_text

    def test_dependency_audit_checkout_fetches_previous_commit(self):
        checkout = _step("dependency-audit", "Checkout")

        assert checkout["with"]["fetch-depth"] == 2

    def test_security_workflow_triggers_are_preserved(self):
        triggers = _workflow_triggers()

        assert triggers["push"]["branches"] == ["main"]
        assert triggers["pull_request"] is None
        assert triggers["workflow_dispatch"] is None
        assert triggers["schedule"] == [{"cron": "17 4 * * 1"}]

    def test_dependency_audit_runs_supported_python_os_matrix(self):
        workflow = _load_security_workflow()
        matrix = workflow["jobs"]["dependency-audit"]["strategy"]["matrix"]

        assert matrix["os"] == ["ubuntu-latest", "windows-latest"]
        assert matrix["python-version"] == ["3.11", "3.12", "3.13"]
        assert workflow["jobs"]["dependency-audit"]["runs-on"] == "${{ matrix.os }}"

    def test_security_tools_are_pinned(self):
        workflow_text = SECURITY_WORKFLOW.read_text(encoding="utf-8")

        assert WORKFLOW_LIVE_PIP_AUDIT in workflow_text
        assert LOCAL_PIP_AUDIT in workflow_text
        assert BANDIT in workflow_text
        assert re.search(r"\buvx\s+pip-audit\b", workflow_text) is None
        assert re.search(r"\buvx\s+bandit\b", workflow_text) is None

    def test_actions_are_pinned_to_full_commit_shas(self):
        workflow = _load_security_workflow()
        uses_refs = [
            step["uses"]
            for job in workflow["jobs"].values()
            for step in job["steps"]
            if "uses" in step
        ]

        assert uses_refs
        for uses_ref in uses_refs:
            assert re.search(r"@[0-9a-f]{40}$", uses_ref), uses_ref
            assert re.search(r"@v\d+", uses_ref) is None

    def test_bandit_does_not_globally_skip_b602(self):
        # Identify the blocking bandit step by its baseline-arg rather than
        # by exact step name — name is incidental, behavior is what matters.
        bandit_step = _find_step_by_run_signature(
            "static-analysis", "--baseline .github/bandit-baseline.json"
        )
        run = bandit_step["run"]
        workflow_text = SECURITY_WORKFLOW.read_text(encoding="utf-8")

        assert run == BANDIT
        assert "--skip" not in run
        assert "--skip B602" not in workflow_text

    def test_bandit_baseline_only_ignores_shell_step_b602(self):
        baseline = json.loads(BANDIT_BASELINE.read_text(encoding="utf-8"))
        results = baseline["results"]

        assert len(results) == 1
        assert results[0]["test_id"] == "B602"
        assert (
            results[0]["filename"]
            == "src/specify_cli/workflows/steps/shell/__init__.py"
        )

    def test_bandit_nosec_is_not_suppressed_in_source(self):
        nosec_lines = []
        for path in (REPO_ROOT / "src").rglob("*.py"):
            for line_number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(),
                start=1,
            ):
                if re.search(r"#\s*nosec\b", line, flags=re.IGNORECASE):
                    nosec_lines.append(f"{path.relative_to(REPO_ROOT)}:{line_number}")

        assert nosec_lines == []

    def test_run_command_does_not_accept_shell_argument(self):
        from specify_cli import run_command

        assert "shell" not in inspect.signature(run_command).parameters

    def test_committed_audit_requirements_are_hashed(self):
        requirements = SECURITY_REQUIREMENTS.read_text(encoding="utf-8")

        assert "--hash=sha256:" in requirements
        assert not requirements.startswith("#")
        assert "pytest==" in requirements
        assert "pytest-cov==" in requirements

    def test_sync_script_skips_when_dependency_inputs_are_unchanged(
        self,
        monkeypatch,
        capsys,
    ):
        sync_script = _load_sync_script()

        def fake_run(command, **kwargs):
            assert command == [
                "git",
                "diff",
                "--name-only",
                "HEAD^",
                "HEAD",
                "--",
                "pyproject.toml",
                ".github/security-audit-requirements.txt",
            ]
            assert kwargs["check"] is True
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        monkeypatch.setattr(sync_script.subprocess, "run", fake_run)

        assert sync_script.main() == 0
        assert "sync check skipped" in capsys.readouterr().out

    def test_sync_script_uses_github_diff_refs_when_available(
        self,
        monkeypatch,
    ):
        sync_script = _load_sync_script()
        monkeypatch.setenv("DEPENDENCY_DIFF_BASE", "abc123")
        monkeypatch.setenv("DEPENDENCY_DIFF_HEAD", "def456")

        def fake_run(command, **_kwargs):
            assert command == [
                "git",
                "diff",
                "--name-only",
                "abc123",
                "def456",
                "--",
                "pyproject.toml",
                ".github/security-audit-requirements.txt",
            ]
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        monkeypatch.setattr(sync_script.subprocess, "run", fake_run)

        assert sync_script._dependency_inputs_changed() is False

    def test_sync_script_compiles_and_compares_when_dependency_inputs_changed(
        self,
        monkeypatch,
        tmp_path,
    ):
        sync_script = _load_sync_script()
        committed_requirements = tmp_path / ".github" / "security-audit-requirements.txt"
        generated_requirements = tmp_path / "generated-requirements.txt"
        committed_requirements.parent.mkdir()
        committed_requirements.write_text("pytest==1\n", encoding="utf-8")
        compile_commands = []

        monkeypatch.setattr(sync_script, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(sync_script, "COMMITTED_REQUIREMENTS", committed_requirements)
        monkeypatch.setenv("GENERATED_REQUIREMENTS", str(generated_requirements))

        def fake_run(command, **kwargs):
            if command[0] == "git":
                return subprocess.CompletedProcess(
                    command,
                    0,
                    stdout="pyproject.toml\n",
                    stderr="",
                )

            compile_commands.append(command)
            assert kwargs["check"] is True
            generated_requirements.write_text("pytest==1\n", encoding="utf-8")
            return subprocess.CompletedProcess(command, 0)

        monkeypatch.setattr(sync_script.subprocess, "run", fake_run)

        assert sync_script.main() == 0
        assert len(compile_commands) == 1
        compile_command = " ".join(compile_commands[0])
        assert WORKFLOW_SYNC_COMPILE_TEST_EXTRA_DEPS in compile_command
        assert "--output-file" in compile_commands[0]
        assert str(generated_requirements) in compile_commands[0]

    def test_sync_script_fails_when_generated_requirements_differ(
        self,
        monkeypatch,
        tmp_path,
        capsys,
    ):
        sync_script = _load_sync_script()
        committed_requirements = tmp_path / ".github" / "security-audit-requirements.txt"
        generated_requirements = tmp_path / "generated-requirements.txt"
        committed_requirements.parent.mkdir()
        committed_requirements.write_text("pytest==1\n", encoding="utf-8")

        monkeypatch.setattr(sync_script, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(sync_script, "COMMITTED_REQUIREMENTS", committed_requirements)
        monkeypatch.setenv("GENERATED_REQUIREMENTS", str(generated_requirements))

        def fake_run(command, **_kwargs):
            if command[0] == "git":
                return subprocess.CompletedProcess(
                    command,
                    0,
                    stdout="pyproject.toml\n",
                    stderr="",
                )

            generated_requirements.write_text("pytest==2\n", encoding="utf-8")
            return subprocess.CompletedProcess(command, 0)

        monkeypatch.setattr(sync_script.subprocess, "run", fake_run)

        assert sync_script.main() == 1
        assert (
            "Regenerate .github/security-audit-requirements.txt"
            in capsys.readouterr().err
        )

    def test_contributing_documents_security_commands(self):
        contributing_text = CONTRIBUTING.read_text(encoding="utf-8")

        assert LOCAL_REFRESH_TEST_EXTRA_DEPS in contributing_text
        assert LOCAL_PIP_AUDIT in contributing_text
        assert BANDIT in contributing_text
        assert "/tmp/" not in contributing_text
        assert "uv export" not in contributing_text
        assert "--frozen" not in contributing_text
        assert "--locked" not in contributing_text
        assert (
            re.search(
                r"--output-file\s+spec-kit-audit-requirements\.txt\b",
                contributing_text,
            )
            is None
        )
        assert (
            re.search(r"-r\s+spec-kit-audit-requirements\.txt\b", contributing_text)
            is None
        )
