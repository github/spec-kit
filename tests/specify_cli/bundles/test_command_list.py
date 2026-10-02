from __future__ import annotations

import io  # noqa: F401
import json  # noqa: F401
from pathlib import Path
from unittest.mock import patch  # noqa: F401

import yaml  # noqa: F401
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.bundles.packager import build_bundle  # noqa: F401
from tests.conftest import strip_ansi  # noqa: F401

runner = CliRunner()


def _make_project(tmp_path: Path, name: str) -> Path:
    project = tmp_path / name
    (project / ".specify").mkdir(parents=True)
    return project


def test_list_empty_project(project: Path):
    result = runner.invoke(app, ["bundle", "list"])
    assert result.exit_code == 0
    assert "No bundles installed" in result.output


def test_commands_outside_project_fail_with_guidance(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # no .specify/
    result = runner.invoke(app, ["bundle", "list"])
    assert result.exit_code == 1
    assert "Spec Kit project" in result.output


def test_list_escapes_markup_in_records(project: Path):
    """``bundle list`` renders record fields that are never charset-validated.

    ``InstalledBundleRecord.from_dict`` accepts any non-empty string for
    ``bundle_id``/``version`` and any string for ``installed_at``, so a records
    file that *loads cleanly* could still crash the command that displays it.
    """
    (project / ".specify" / "bundle-records.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "bundles": [
                    {
                        "bundle_id": "demo[/red]id",
                        "version": "1.0.0[/bold]",
                        "installed_at": "2026-01-01T00:00:00Z[/dim]",
                        "contributed_components": [],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["bundle", "list"])

    assert result.exit_code == 0, repr(result.exception)
    output = strip_ansi(result.output)
    assert "demo[/red]id" in output
    assert "1.0.0[/bold]" in output
    assert "2026-01-01T00:00:00Z[/dim]" in output


def test_override_redirects_bundle_commands(tmp_path, monkeypatch):
    web = _make_project(tmp_path, "web")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    monkeypatch.setenv("SPECIFY_INIT_DIR", str(web))

    result = runner.invoke(app, ["bundle", "list"])
    assert result.exit_code == 0, result.output
    assert "No bundles installed" in result.output


def test_override_nonexistent_errors_bundle_commands_no_fallback(tmp_path, monkeypatch):
    """Bundle commands also honor the strict override contract."""
    cwd_proj = _make_project(tmp_path, "cwd")
    monkeypatch.chdir(cwd_proj)
    monkeypatch.setenv("SPECIFY_INIT_DIR", str(tmp_path / "does_not_exist"))

    result = runner.invoke(app, ["bundle", "list"])
    assert result.exit_code != 0
    assert "does not point to an existing directory" in result.output
    assert "No bundles installed" not in result.output


def test_override_nonexistent_bundle_json_error_stays_off_stdout(tmp_path, monkeypatch):
    """Invalid override errors must not contaminate JSON stdout."""
    cwd_proj = _make_project(tmp_path, "cwd")
    monkeypatch.chdir(cwd_proj)
    monkeypatch.setenv("SPECIFY_INIT_DIR", str(tmp_path / "does_not_exist"))

    result = runner.invoke(app, ["bundle", "list", "--json"])
    assert result.exit_code != 0
    assert result.stdout == ""
    assert "does not point to an existing directory" in result.stderr
