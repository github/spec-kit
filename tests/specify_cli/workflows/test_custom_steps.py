"""Runtime freshness tests for project-local custom workflow steps."""

from __future__ import annotations

import shutil
from pathlib import Path

from specify_cli.workflows import STEP_REGISTRY, load_custom_steps


def _write_step(project_root: Path, marker: str) -> None:
    step_dir = project_root / ".specify" / "workflows" / "steps" / "custom"
    step_dir.mkdir(parents=True)
    (step_dir / "step.yml").write_text(
        "step:\n  type_key: custom\n", encoding="utf-8"
    )
    (step_dir / "__init__.py").write_text(
        "from specify_cli.workflows.base import StepBase, StepResult\n\n"
        "class Custom(StepBase):\n"
        "    type_key = 'custom'\n"
        "    def execute(self, config, context):\n"
        f"        return StepResult(output={{'marker': {marker!r}}})\n",
        encoding="utf-8",
    )


def test_custom_steps_refresh_for_active_project(tmp_path):
    project_a = tmp_path / "a"
    project_b = tmp_path / "b"
    _write_step(project_a, "a")
    _write_step(project_b, "b")

    assert load_custom_steps(project_a) == ["custom"]
    assert STEP_REGISTRY["custom"].execute({}, None).output == {"marker": "a"}

    assert load_custom_steps(project_b) == ["custom"]
    assert STEP_REGISTRY["custom"].execute({}, None).output == {"marker": "b"}


def test_removed_custom_step_is_not_retained(tmp_path):
    project = tmp_path / "project"
    _write_step(project, "old")
    assert load_custom_steps(project) == ["custom"]

    step_dir = project / ".specify" / "workflows" / "steps" / "custom"
    shutil.rmtree(step_dir)

    assert load_custom_steps(project) == []
    assert "custom" not in STEP_REGISTRY
