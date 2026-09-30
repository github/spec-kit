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
    catalog_entry_dict,
    write_catalog_file,
)

runner = CliRunner()


def test_catalog_add_and_remove(project: Path):
    catalog = project / "local-catalog.json"
    write_catalog_file(catalog, {"demo": catalog_entry_dict("demo")})

    added = runner.invoke(
        app, ["bundle", "catalog", "add", str(catalog), "--id", "local"]
    )
    assert added.exit_code == 0, added.output
    assert "Added catalog" in added.output

    unchanged = runner.invoke(
        app, ["bundle", "catalog", "add", str(catalog), "--id", "local"]
    )
    assert unchanged.exit_code == 0, unchanged.output
    assert "already configured" in unchanged.output

    listed = runner.invoke(app, ["bundle", "catalog", "list"])
    assert "local" in listed.output

    removed = runner.invoke(app, ["bundle", "catalog", "remove", "local"])
    assert removed.exit_code == 0
