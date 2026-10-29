"""Shared extension CLI error reporting."""

import json

import pytest
from typer.testing import CliRunner

from specify_cli import app


@pytest.mark.parametrize("arguments", [
    ["add", "example"],
    ["list"],
    ["list", "--json"],
    ["info", "example"],
    ["info", "example", "--json"],
    ["enable", "example"],
    ["disable", "example"],
    ["remove", "example", "--force"],
    ["set-priority", "example", "10"],
    ["update", "example"],
    ["update"],
])
def test_linked_registry_reports_cli_error(project_dir, tmp_path, monkeypatch, arguments):
    registry = project_dir / ".specify" / "extensions" / ".registry"
    registry.parent.mkdir(parents=True, exist_ok=True)
    external = tmp_path / "external-registry"
    external.write_text('{"extensions": {}}', encoding="utf-8")
    try:
        registry.symlink_to(external)
    except OSError:
        pytest.skip("Symlink creation unavailable")
    monkeypatch.chdir(project_dir)

    result = CliRunner().invoke(app, ["extension", *arguments])

    assert result.exit_code == 1, result.output
    assert isinstance(result.exception, SystemExit), repr(result.exception)
    if "--json" in arguments:
        assert result.stdout == ""
        assert "symlink" in json.loads(result.stderr)["error"]
    else:
        assert "Error:" in result.output
        assert "symlink" in result.output
    assert "Traceback" not in result.output
    assert external.read_text(encoding="utf-8") == '{"extensions": {}}'
