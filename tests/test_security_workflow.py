"""Static checks for the GitHub Actions security workflow."""

from __future__ import annotations

import re
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
SECURITY_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "security.yml"
CONTRIBUTING = REPO_ROOT / "CONTRIBUTING.md"

AUDIT_REQUIREMENTS = "/tmp/spec-kit-audit-requirements.txt"
EXPORT_TEST_DEPS = (
    "uv export --quiet --extra test --frozen --format requirements.txt "
    f"--no-emit-project --output-file {AUDIT_REQUIREMENTS}"
)
PIP_AUDIT = (
    "uvx --from pip-audit==2.10.0 pip-audit "
    f"-r {AUDIT_REQUIREMENTS} --progress-spinner off"
)
BANDIT = "uvx --from bandit==1.9.4 bandit -r src -lll"


def _load_security_workflow() -> dict:
    return yaml.safe_load(SECURITY_WORKFLOW.read_text(encoding="utf-8"))


def _step_run(job_name: str, step_name: str) -> str:
    workflow = _load_security_workflow()
    for step in workflow["jobs"][job_name]["steps"]:
        if step.get("name") == step_name:
            return step["run"]
    raise AssertionError(f"Step {step_name!r} not found in job {job_name!r}.")


class TestSecurityWorkflow:
    """Guard the security workflow against review-feedback regressions."""

    def test_dependency_audit_uses_locked_test_extra_export(self):
        run = _step_run("dependency-audit", "Run pip-audit")

        assert EXPORT_TEST_DEPS in run
        assert PIP_AUDIT in run
        assert "uvx pip-audit ." not in run

    def test_security_tools_are_pinned(self):
        workflow_text = SECURITY_WORKFLOW.read_text(encoding="utf-8")

        assert PIP_AUDIT in workflow_text
        assert BANDIT in workflow_text
        assert re.search(r"\buvx\s+pip-audit\b", workflow_text) is None
        assert re.search(r"\buvx\s+bandit\b", workflow_text) is None

    def test_bandit_does_not_globally_skip_b602(self):
        run = _step_run("static-analysis", "Run Bandit")
        workflow_text = SECURITY_WORKFLOW.read_text(encoding="utf-8")

        assert run == BANDIT
        assert "--skip" not in run
        assert "--skip B602" not in workflow_text

    def test_contributing_documents_security_commands(self):
        contributing_text = CONTRIBUTING.read_text(encoding="utf-8")

        assert EXPORT_TEST_DEPS in contributing_text
        assert PIP_AUDIT in contributing_text
        assert BANDIT in contributing_text
