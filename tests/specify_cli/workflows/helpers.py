"""Shared helpers for workflow command tests."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml


class _StubStdin:
    def __init__(self, tty: bool):
        self._tty = tty

    def isatty(self):
        return self._tty


class _FakeSys:
    def __init__(self, tty: bool):
        self.stdin = _StubStdin(tty)

    def __getattr__(self, name):
        return getattr(sys, name)


def force_gate_stdin(monkeypatch, *, tty: bool):
    from specify_cli.workflows.step import gate as gate_module

    monkeypatch.setattr(gate_module, "sys", _FakeSys(tty=tty))


def force_workflow_stdin(monkeypatch, *, tty: bool):
    from specify_cli.workflows import _commands

    monkeypatch.setattr(_commands, "sys", _FakeSys(tty=tty))


def write_step_import_probe(project_root: Path) -> Path:
    """Create an unregistered step whose import has an observable side effect."""
    step_dir = project_root / ".specify" / "workflows" / "steps" / "import-probe"
    step_dir.mkdir(parents=True)
    marker = project_root / "step-imported.txt"
    (step_dir / "step.yml").write_text(
        "step:\n  type_key: import-probe\n", encoding="utf-8",
    )
    (step_dir / "__init__.py").write_text(
        "from pathlib import Path\n"
        "from specify_cli.workflows.base import StepBase, StepResult\n"
        f"Path({str(marker)!r}).write_text('imported', encoding='utf-8')\n"
        "class ImportProbe(StepBase):\n"
        "    type_key = 'import-probe'\n"
        "    def execute(self, config, context):\n"
        "        return StepResult(output={'ok': True})\n",
        encoding="utf-8",
    )
    return marker


def write_workflow(project_root: Path, workflow_id: str, data: dict) -> Path:
    workflow_dir = project_root / ".specify" / "workflows" / workflow_id
    workflow_dir.mkdir(parents=True, exist_ok=True)
    workflow_path = workflow_dir / "workflow.yml"
    workflow_path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return workflow_path


def write_overlay(
    project_root: Path, workflow_id: str, overlay_id: str, data: dict
) -> Path:
    overlay_dir = project_root / ".specify" / "workflows" / "overlays" / workflow_id
    overlay_dir.mkdir(parents=True, exist_ok=True)
    overlay_path = overlay_dir / f"{overlay_id}.yml"
    overlay_path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return overlay_path
