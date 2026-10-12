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


def test_update_accepts_integration_override():
    # Update must expose --integration so integration-pinned bundles can be
    # updated in projects where the active integration can't be auto-detected.
    # Rich may insert ANSI escapes between the two leading dashes, so match the
    # un-split option word rather than the literal "--integration".
    result = runner.invoke(app, ["bundle", "update", "--help"])
    assert result.exit_code == 0
    assert "integration" in result.output


def test_update_refuses_discovery_only_source(project: Path):
    # An installed bundle whose only resolvable source is discovery-only must
    # not be updatable from there (FR-025), mirroring the install policy gate.
    from specify_cli.bundles.manifest import ComponentRef
    from specify_cli.bundles.records import (
        InstalledBundleRecord,
        save_records,
    )

    save_records(
        project,
        [
            InstalledBundleRecord.create(
                "demo",
                "1.0.0",
                [ComponentRef(kind="extensions", id="ext-a", version=None)],
            )
        ],
    )

    catalog = project / "disc.json"
    write_catalog_file(catalog, {"demo": catalog_entry_dict("demo")})
    config = {
        "schema_version": "1.0",
        "catalogs": [
            {
                "id": "disc",
                "url": str(catalog),
                "priority": 1,
                "install_policy": "discovery-only",
            }
        ],
    }
    (project / ".specify" / "bundle-catalogs.yml").write_text(
        yaml.safe_dump(config), encoding="utf-8"
    )

    result = runner.invoke(app, ["bundle", "update", "demo", "--offline"])
    assert result.exit_code == 1
    assert "discovery-only" in result.output
