"""Static checks for the dependency-audit security workflow."""

from __future__ import annotations

import importlib.util
import re
import subprocess
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
SECURITY_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "security.yml"
CONTRIBUTING = REPO_ROOT / "CONTRIBUTING.md"
SECURITY_REQUIREMENTS = REPO_ROOT / ".github" / "security-audit-requirements.txt"
SECURITY_REQUIREMENTS_SYNC_SCRIPT = (
    REPO_ROOT / ".github" / "scripts" / "check_security_requirements.py"
)

WORKFLOW_LIVE_AUDIT_REQUIREMENTS = '"${{ runner.temp }}/spec-kit-audit-requirements.txt"'
COMMITTED_AUDIT_REQUIREMENTS = ".github/security-audit-requirements.txt"
WORKFLOW_COMPILE_SCHEDULED_TEST_EXTRA_DEPS = (
    "uv pip compile pyproject.toml --extra test "
    '--python-version "${{ matrix.python-version }}" --upgrade --generate-hashes --quiet '
    f"--output-file {WORKFLOW_LIVE_AUDIT_REQUIREMENTS}"
)
LOCAL_REFRESH_TEST_EXTRA_DEPS = (
    "uv pip compile pyproject.toml --extra test --universal --upgrade --generate-hashes "
    f"--quiet --no-header --output-file {COMMITTED_AUDIT_REQUIREMENTS}"
)
WORKFLOW_SYNC_COMPILE_TEST_EXTRA_DEPS = (
    "uv pip compile pyproject.toml --extra test --universal --upgrade --generate-hashes "
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


def _job_run_text(*job_names: str) -> str:
    workflow = _load_security_workflow()
    return "\n".join(
        step.get("run", "")
        for job_name in job_names
        for step in workflow["jobs"][job_name]["steps"]
    )


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


class TestDependencyAuditWorkflow:
    """Guard the dependency-audit security workflow."""

    def test_dependency_audit_uses_committed_requirements_for_prs_and_pushes(self):
        workflow = _load_security_workflow()
        job = workflow["jobs"]["dependency-audit"]
        committed_audit = _step("dependency-audit", "Run pip-audit (committed requirements)")
        sync_check = _step("dependency-audit", "Check committed audit requirements are current")
        setup_python = _step("dependency-audit", "Set up Python")

        assert job["if"] == "${{ github.event_name != 'schedule' }}"
        assert job["runs-on"] == "ubuntu-latest"
        assert "strategy" not in job
        assert setup_python["with"]["python-version"] == "3.14"
        assert sync_check["env"]["DEPENDENCY_DIFF_BASE"] == (
            "${{ github.event.pull_request.base.sha || github.event.before || '' }}"
        )
        assert sync_check["env"]["DEPENDENCY_DIFF_HEAD"] == "${{ github.sha }}"
        assert sync_check["run"] == WORKFLOW_SYNC_SCRIPT
        assert committed_audit["run"] == LOCAL_PIP_AUDIT

        dependency_job_text = _job_run_text(
            "dependency-audit",
            "dependency-audit-scheduled",
        )
        protection_text = (
            dependency_job_text
            + "\n"
            + SECURITY_REQUIREMENTS_SYNC_SCRIPT.read_text(encoding="utf-8")
        )
        assert "--generate-hashes" in protection_text
        assert "--no-header" in protection_text
        assert "--require-hashes" in protection_text
        assert "--disable-pip" in protection_text
        assert WORKFLOW_LIVE_AUDIT_REQUIREMENTS in dependency_job_text
        assert COMMITTED_AUDIT_REQUIREMENTS in protection_text
        assert "uv export" not in protection_text
        assert "--frozen" not in protection_text
        assert "--locked" not in protection_text
        assert "uv.lock" not in protection_text
        assert "/tmp/" not in protection_text

    def test_dependency_audit_checkout_fetches_full_history_for_diff_base(self):
        checkout = _step("dependency-audit", "Checkout")

        assert checkout["with"]["fetch-depth"] == 0

    def test_security_workflow_triggers(self):
        triggers = _workflow_triggers()

        assert triggers["push"]["branches"] == ["main"]
        # Asserted by inclusion so later PRs (e.g. baseline-growth gates) can add
        # labeled/unlabeled without rewriting this test.
        assert {"opened", "synchronize", "reopened"} <= set(
            triggers["pull_request"]["types"]
        )
        assert "workflow_dispatch" in triggers
        assert triggers["schedule"] == [{"cron": "17 4 * * 1"}]

    def test_scheduled_dependency_audit_runs_supported_python_os_matrix(self):
        workflow = _load_security_workflow()
        job = workflow["jobs"]["dependency-audit-scheduled"]
        matrix = job["strategy"]["matrix"]
        scheduled_compile = _step(
            "dependency-audit-scheduled",
            "Compile scheduled audit requirements",
        )
        scheduled_audit = _step(
            "dependency-audit-scheduled",
            "Run pip-audit (scheduled live resolution)",
        )

        assert job["if"] == "${{ github.event_name == 'schedule' }}"
        assert matrix["os"] == ["ubuntu-latest", "windows-latest"]
        assert matrix["python-version"] == ["3.11", "3.12", "3.13", "3.14"]
        assert job["runs-on"] == "${{ matrix.os }}"
        assert WORKFLOW_COMPILE_SCHEDULED_TEST_EXTRA_DEPS in scheduled_compile["run"]
        assert scheduled_audit["run"] == WORKFLOW_LIVE_PIP_AUDIT

    def test_pip_audit_is_pinned(self):
        workflow_text = SECURITY_WORKFLOW.read_text(encoding="utf-8")

        assert WORKFLOW_LIVE_PIP_AUDIT in workflow_text
        assert LOCAL_PIP_AUDIT in workflow_text
        assert re.search(r"\buvx\s+pip-audit\b", workflow_text) is None

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

    def test_setup_python_pin_matches_repo_standard(self):
        workflow = _load_security_workflow()
        security_refs = {
            step["uses"]
            for job in workflow["jobs"].values()
            for step in job["steps"]
            if step.get("uses", "").startswith("actions/setup-python@")
        }
        repo_standard_refs = set()
        for workflow_path in (
            REPO_ROOT / ".github" / "workflows" / "test.yml",
            REPO_ROOT / ".github" / "workflows" / "publish-pypi.yml",
        ):
            workflow_data = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
            repo_standard_refs.update(
                step["uses"]
                for job in workflow_data["jobs"].values()
                for step in job["steps"]
                if step.get("uses", "").startswith("actions/setup-python@")
            )

        assert len(repo_standard_refs) == 1
        assert security_refs == repo_standard_refs

    def test_setup_uv_pin_matches_repo_standard(self):
        workflow = _load_security_workflow()
        security_refs = {
            step["uses"]
            for job in workflow["jobs"].values()
            for step in job["steps"]
            if step.get("uses", "").startswith("astral-sh/setup-uv@")
        }
        test_workflow = yaml.safe_load(
            (REPO_ROOT / ".github" / "workflows" / "test.yml").read_text(
                encoding="utf-8"
            )
        )
        repo_standard_refs = {
            step["uses"]
            for job in test_workflow["jobs"].values()
            for step in job["steps"]
            if step.get("uses", "").startswith("astral-sh/setup-uv@")
        }

        assert len(repo_standard_refs) == 1
        assert security_refs == repo_standard_refs

    def test_committed_audit_requirements_are_hashed(self):
        requirements = SECURITY_REQUIREMENTS.read_text(encoding="utf-8")

        assert "--hash=sha256:" in requirements
        assert not requirements.startswith("#")
        assert "pytest==" in requirements
        assert "pytest-cov==" in requirements

    def test_sync_script_skips_when_dependency_inputs_are_unchanged(self, monkeypatch, capsys):
        sync_script = _load_sync_script()

        def fake_run(command, **kwargs):
            assert command == [
                "git", "diff", "--name-only", "HEAD^", "HEAD", "--",
                "pyproject.toml", ".github/security-audit-requirements.txt",
            ]
            assert kwargs["check"] is True
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        monkeypatch.setattr(sync_script.subprocess, "run", fake_run)

        assert sync_script.main() == 0
        assert "sync check skipped" in capsys.readouterr().out

    def test_sync_script_uses_github_diff_refs_when_available(self, monkeypatch):
        sync_script = _load_sync_script()
        monkeypatch.setenv("DEPENDENCY_DIFF_BASE", "abc123")
        monkeypatch.setenv("DEPENDENCY_DIFF_HEAD", "def456")

        def fake_run(command, **_kwargs):
            assert command == [
                "git", "diff", "--name-only", "abc123", "def456", "--",
                "pyproject.toml", ".github/security-audit-requirements.txt",
            ]
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        monkeypatch.setattr(sync_script.subprocess, "run", fake_run)

        assert sync_script._dependency_inputs_changed() is False

    def test_sync_script_compiles_and_compares_when_dependency_inputs_changed(
        self, monkeypatch, tmp_path
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
                return subprocess.CompletedProcess(command, 0, stdout="pyproject.toml\n", stderr="")
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

    def test_sync_script_reports_missing_generated_requirements_env(
        self, monkeypatch, capsys
    ):
        sync_script = _load_sync_script()
        monkeypatch.delenv("GENERATED_REQUIREMENTS", raising=False)

        def fake_run(command, **_kwargs):
            if command[0] == "git":
                return subprocess.CompletedProcess(command, 0, stdout="pyproject.toml\n", stderr="")
            raise AssertionError("compile should not run without GENERATED_REQUIREMENTS")

        monkeypatch.setattr(sync_script.subprocess, "run", fake_run)

        assert sync_script.main() == 1
        assert "GENERATED_REQUIREMENTS must be set" in capsys.readouterr().err

    def test_sync_script_fails_when_generated_requirements_differ(
        self, monkeypatch, tmp_path, capsys
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
                return subprocess.CompletedProcess(command, 0, stdout="pyproject.toml\n", stderr="")
            generated_requirements.write_text("pytest==2\n", encoding="utf-8")
            return subprocess.CompletedProcess(command, 0)

        monkeypatch.setattr(sync_script.subprocess, "run", fake_run)

        assert sync_script.main() == 1
        assert "Regenerate .github/security-audit-requirements.txt" in capsys.readouterr().err

    def test_contributing_documents_security_commands(self):
        contributing_text = CONTRIBUTING.read_text(encoding="utf-8")

        assert LOCAL_REFRESH_TEST_EXTRA_DEPS in contributing_text
        assert LOCAL_PIP_AUDIT in contributing_text
        assert "/tmp/" not in contributing_text
        assert "uv export" not in contributing_text
