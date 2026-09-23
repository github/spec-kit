from __future__ import annotations

from pathlib import Path

import yaml

from specify_cli.bundles.sources import _local_manifest_source
from tests.specify_cli.bundles.helpers import catalog_entry_dict, write_catalog_file

MARKUP_BUNDLE_ID = "[red]markup-id[/red]"
MARKUP_SOURCE_ID = "[underline]markup-source[/underline]"


def configure_markup_catalog(project: Path, **overrides: object) -> dict:
    entry = catalog_entry_dict(
        MARKUP_BUNDLE_ID,
        name="[green]Markup Name[/green]",
        version="[blue]1.0.0[/blue]",
        role="[magenta]Markup Role[/magenta]",
        description="[yellow]Markup Description[/yellow]",
        author="[cyan]Markup Author[/cyan]",
        license="[bold]Markup License[/bold]",
        download_url="https://example.com/markup-bundle.zip",
        requires={"speckit_version": "[italic]>=0.1.0[/italic]"},
        **overrides,
    )
    catalog = project / "markup-catalog.json"
    write_catalog_file(catalog, {MARKUP_BUNDLE_ID: entry})
    config = {
        "schema_version": "1.0",
        "catalogs": [
            {
                "id": MARKUP_SOURCE_ID,
                "url": str(catalog),
                "priority": 1,
                "install_policy": "install-allowed",
            }
        ],
    }
    (project / ".specify" / "bundle-catalogs.yml").write_text(
        yaml.safe_dump(config), encoding="utf-8"
    )
    return entry


def mock_manifest_download(monkeypatch, source_path: Path) -> None:
    monkeypatch.setattr(
        "specify_cli.bundles.command_info._download_manifest",
        lambda resolved, *, offline: _local_manifest_source(str(source_path)),
    )
