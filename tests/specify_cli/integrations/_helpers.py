"""Shared helpers for mirrored integration command tests."""

import json
import os
import shutil

from typer.testing import CliRunner

from specify_cli import app
from tests.conftest import strip_ansi


runner = CliRunner()

def _init_project(tmp_path, integration="copilot", integration_options=None):
    """Helper: init a spec-kit project with the given integration."""
    project = tmp_path / "proj"
    project.mkdir()
    args = [
        "init", "--here",
        "--integration", integration,
        "--script", "sh",
        "--ignore-agent-tools",
    ]
    if integration_options:
        args += ["--integration-options", integration_options]
    old_cwd = os.getcwd()
    try:
        os.chdir(project)
        result = runner.invoke(app, args, catch_exceptions=False)
    finally:
        os.chdir(old_cwd)
    assert result.exit_code == 0, f"init failed: {result.output}"
    return project

def _run_in_project(project, args):
    """Run a CLI command from inside a generated project."""
    old_cwd = os.getcwd()
    try:
        os.chdir(project)
        return runner.invoke(app, args, catch_exceptions=False)
    finally:
        os.chdir(old_cwd)

def _write_invalid_manifest(project, key):
    manifest = project / ".specify" / "integrations" / f"{key}.manifest.json"
    manifest.write_bytes(b"\xff\xfe\x00")
    return manifest

def _move_kilocode_install_to_legacy_layout(project):
    """Simulate a pre-.kilo Kilo install tracked under .kilocode/workflows."""
    canonical = project / ".kilo" / "commands"
    legacy = project / ".kilocode" / "workflows"
    assert canonical.is_dir(), "init should have created .kilo/commands/"
    legacy.parent.mkdir(parents=True, exist_ok=True)
    canonical.rename(legacy)
    assert legacy.is_dir()
    assert not canonical.exists()

    manifest_path = project / ".specify" / "integrations" / "kilocode.manifest.json"
    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_data["files"] = {
        path.replace(".kilo/commands/", ".kilocode/workflows/"): info
        for path, info in manifest_data.get("files", {}).items()
    }
    manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")
    return canonical, legacy

def _copy_project_template(tmp_path, template):
    project = tmp_path / "proj"
    shutil.copytree(template, project)
    return project

def _integration_list_row_cells(output: str, key: str) -> list[str]:
    plain = strip_ansi(output)
    row = next(line for line in plain.splitlines() if line.startswith(f"│ {key}"))
    return [cell.strip() for cell in row.split("│")[1:-1]]
