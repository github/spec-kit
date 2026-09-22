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
from tests.specify_cli.bundles.helpers import (
    valid_manifest_dict,
)

runner = CliRunner()


def test_validate_reports_invalid_manifest(project: Path):
    data = valid_manifest_dict()
    del data["bundle"]["license"]
    (project / "bundle.yml").write_text(yaml.safe_dump(data), encoding="utf-8")
    result = runner.invoke(app, ["bundle", "validate"])
    assert result.exit_code == 1
    assert "license" in result.output


def test_validate_accepts_valid_manifest(project: Path):
    (project / "bundle.yml").write_text(
        yaml.safe_dump(valid_manifest_dict()), encoding="utf-8"
    )
    # Offline mode does not fail on references it cannot verify (synthetic ids
    # here); they surface as warnings while structure is confirmed valid.
    result = runner.invoke(app, ["bundle", "validate", "--offline"])
    assert result.exit_code == 0, result.output
    assert "valid" in result.output


def test_validate_escapes_manifest_markup_in_errors(project: Path):
    data = valid_manifest_dict()
    # An invalid constraint is echoed back inside the validation error.
    data["requires"] = {"speckit_version": ">=1.0[/bold]"}
    (project / "bundle.yml").write_text(yaml.safe_dump(data), encoding="utf-8")

    result = runner.invoke(app, ["bundle", "validate", "--offline"])

    assert result.exit_code == 1
    assert isinstance(result.exception, SystemExit)
    assert ">=1.0[/bold]" in strip_ansi(result.output)


def test_validate_escapes_manifest_markup_in_warnings(project: Path):
    data = valid_manifest_dict()
    # Step ids are not charset-validated, and the unresolved-reference warning
    # echoes them -- so an otherwise *valid* manifest crashed just as readily as
    # an invalid one, on the success path.
    data["provides"]["steps"] = [{"id": "step[/bold]a"}]
    (project / "bundle.yml").write_text(yaml.safe_dump(data), encoding="utf-8")

    result = runner.invoke(app, ["bundle", "validate", "--offline"])

    assert result.exit_code == 0, repr(result.exception)
    assert "step[/bold]a" in strip_ansi(result.output)


def test_validate_rejects_broken_reference(project: Path):
    # Synthetic component ids resolve to nothing in any catalog → hard failure.
    (project / "bundle.yml").write_text(
        yaml.safe_dump(valid_manifest_dict()), encoding="utf-8"
    )
    result = runner.invoke(app, ["bundle", "validate"])
    assert result.exit_code == 1
    assert "preset-a" in result.output or "ext-a" in result.output


def test_validate_accepts_bundled_reference(project: Path):
    data = valid_manifest_dict()
    data["provides"] = {"extensions": [{"id": "agent-context", "version": "1.0.0"}]}
    (project / "bundle.yml").write_text(yaml.safe_dump(data), encoding="utf-8")
    result = runner.invoke(app, ["bundle", "validate"])
    assert result.exit_code == 0, result.output
    assert "valid" in result.output
