from __future__ import annotations

import io  # noqa: F401
import json  # noqa: F401
from pathlib import Path
from unittest.mock import patch  # noqa: F401

import pytest
import yaml
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.bundles.packager import build_bundle  # noqa: F401
from tests.conftest import strip_ansi
from tests.specify_cli.bundles.helpers import (
    bundled_extension_version,
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


@pytest.mark.parametrize("version", ["1.2.0", "1.20.30-12alpha.1+build.01", "V10.20.30"])
def test_validate_accepts_valid_manifest(project: Path, version: str):
    data = valid_manifest_dict()
    data["bundle"]["version"] = version
    (project / "bundle.yml").write_text(
        yaml.safe_dump(data), encoding="utf-8"
    )
    # Offline mode does not fail on references it cannot verify (synthetic ids
    # here); they surface as warnings while structure is confirmed valid.
    result = runner.invoke(app, ["bundle", "validate", "--offline"])
    assert result.exit_code == 0, result.output
    assert "valid" in result.output


@pytest.mark.parametrize("version", ["1٢.2.3", "1.2.3-1٢", "1.2.3-٢alpha"])
@pytest.mark.parametrize("field", ["bundle", "extension"])
def test_validate_rejects_non_ascii_version(project: Path, version: str, field: str):
    data = valid_manifest_dict()
    if field == "bundle":
        data["bundle"]["version"] = version
    else:
        data["provides"]["extensions"][0]["version"] = version
    (project / "bundle.yml").write_text(yaml.safe_dump(data), encoding="utf-8")

    result = runner.invoke(app, ["bundle", "validate", "--offline"])

    assert result.exit_code == 1, result.output
    assert "invalid" in result.output
    assert version in result.output


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


def test_validate_warns_instead_of_rejecting_reference_during_partial_outage(
    project: Path, monkeypatch,
):
    from urllib.error import URLError

    from specify_cli.workflows.catalog import (
        StepCatalog,
        StepCatalogEntry,
    )

    data = valid_manifest_dict(
        provides={"steps": [{"id": "requested", "version": "1.0.0"}]}
    )
    (project / "bundle.yml").write_text(yaml.safe_dump(data), encoding="utf-8")
    sources = [
        StepCatalogEntry("https://example.com/high.json", "high", 1, True),
        StepCatalogEntry("https://example.com/low.json", "low", 2, True),
    ]
    monkeypatch.setattr(StepCatalog, "get_active_catalogs", lambda self: sources)

    def fetch(self, entry, force_refresh=False):
        if entry.name == "low":
            raise URLError("catalog timed out")
        return {"steps": {"other-step": {"version": "1.0.0"}}}

    monkeypatch.setattr(StepCatalog, "_fetch_single_catalog", fetch)

    result = runner.invoke(app, ["bundle", "validate"])

    assert result.exit_code == 0, result.output
    assert "unreachable" in result.output
    assert "not available" not in result.output


def test_validate_accepts_bundled_reference(project: Path):
    data = valid_manifest_dict()
    data["provides"] = {"extensions": [{
        "id": "agent-context", "version": bundled_extension_version("agent-context")
    }]}
    (project / "bundle.yml").write_text(yaml.safe_dump(data), encoding="utf-8")
    result = runner.invoke(app, ["bundle", "validate"])
    assert result.exit_code == 0, result.output
    assert "valid" in result.output


@pytest.mark.parametrize("kind,id,version", [
    ("presets", "lean", "1.0.0"),
    ("extensions", "agent-context", bundled_extension_version("agent-context")),
])
@pytest.mark.parametrize("offline", [False, True])
def test_validate_rejects_mismatched_bundled_component(
    project: Path, monkeypatch, kind: str, id: str, version: str, offline: bool,
):
    from specify_cli.extensions import ExtensionCatalog
    from specify_cli.presets import PresetCatalog

    data = valid_manifest_dict(
        provides={kind: [{"id": id, "version": "9.9.9"}]}
    )
    (project / "bundle.yml").write_text(yaml.safe_dump(data), encoding="utf-8")
    monkeypatch.setattr(
        PresetCatalog, "get_pack_info",
        lambda self, _id, version=None: {
            "version": version or "9.9.9",
            "_catalog_name": "trusted",
            "_install_allowed": True,
        },
    )
    monkeypatch.setattr(
        ExtensionCatalog, "get_extension_info",
        lambda self, _id, version=None: {
            "version": version or "9.9.9",
            "_catalog_name": "trusted",
            "_install_allowed": True,
        },
    )

    command = ["bundle", "validate", *(["--offline"] if offline else [])]
    result = runner.invoke(app, command)

    assert result.exit_code == 1, result.output
    assert f"resolved version is {version}" in result.output
