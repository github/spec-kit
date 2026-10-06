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
from tests.specify_cli.bundles._command_helpers import (
    MARKUP_SOURCE_ID,
    configure_markup_catalog as _configure_markup_catalog,
)
from tests.specify_cli.bundles.helpers import (
    catalog_entry_dict,
    write_catalog_file,
)

runner = CliRunner()


def test_search_works_without_a_project(tmp_path: Path, monkeypatch):
    # Discovery commands fall back to the built-in/user catalog stack and must
    # not require a Spec Kit project (matches README/quickstart examples).
    monkeypatch.chdir(tmp_path)  # no .specify/
    result = runner.invoke(app, ["bundle", "search", "--offline", "--json"])
    assert result.exit_code == 0, result.output
    assert result.output.strip().startswith("[")


def test_search_escapes_catalog_markup(project: Path):
    entry = _configure_markup_catalog(project)

    result = runner.invoke(app, ["bundle", "search", "--offline"])

    assert result.exit_code == 0, result.output
    output = " ".join(strip_ansi(result.output).split())
    for value in (
        entry["id"],
        entry["name"],
        entry["version"],
        entry["role"],
        entry["description"],
        MARKUP_SOURCE_ID,
    ):
        assert value in output


def test_search_json_offline(project: Path):
    catalog = project / "c.json"
    write_catalog_file(catalog, {"demo": catalog_entry_dict("demo")})
    config = {
        "schema_version": "1.0",
        "catalogs": [
            {
                "id": "c",
                "url": str(catalog),
                "priority": 0,
                "install_policy": "install-allowed",
            }
        ],
    }
    (project / ".specify" / "bundle-catalogs.yml").write_text(
        yaml.safe_dump(config), encoding="utf-8"
    )
    result = runner.invoke(app, ["bundle", "search", "--offline", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    by_id = {entry["id"]: entry for entry in payload}
    assert "demo" in by_id
    # Trust indicator is exposed on the discovery surface (FR-010 / FR-027).
    assert by_id["demo"]["verified"] is True
    assert by_id["demo"]["trust"] == "verified"


def test_search_text_shows_trust(project: Path):
    catalog = project / "c.json"
    write_catalog_file(
        catalog,
        {
            "verified-one": catalog_entry_dict("verified-one", verified=True),
            "community-one": catalog_entry_dict("community-one", verified=False),
        },
    )
    config = {
        "schema_version": "1.0",
        "catalogs": [
            {
                "id": "c",
                "url": str(catalog),
                "priority": 1,
                "install_policy": "install-allowed",
            }
        ],
    }
    (project / ".specify" / "bundle-catalogs.yml").write_text(
        yaml.safe_dump(config), encoding="utf-8"
    )
    result = runner.invoke(app, ["bundle", "search", "--offline"])
    assert result.exit_code == 0, result.output
    assert "verified" in result.output
    assert "community" in result.output
