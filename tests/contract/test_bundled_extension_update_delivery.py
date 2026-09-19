"""Contract tests: previously stale bundled installs are now offered an update.

Every bundled extension shipped at 1.0.0 from its creation while its content
kept changing, so installed copies were reported "Up to date" forever
(#4345). The version bumps in extensions/*/extension.yml and the synced
extensions/catalog.json are what finally make `specify extension update`
offer those installs a newer version, and the local-package route installs
it from the copy bundled with the running spec-kit.

Unit tests cover that route with synthetic extensions and versions, and the
version contract only checks catalog/manifest equality. These tests close
the gap with the real data: install each bundled extension's real source
at the pre-bump 1.0.0, run `extension update` against the real catalog
entry and the real bundled copy, and assert it reaches the catalog version.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from packaging.version import Version
from typer.testing import CliRunner

REPO_ROOT = Path(__file__).parents[2]
EXTENSIONS_ROOT = REPO_ROOT / "extensions"
PRE_BUMP_VERSION = "1.0.0"
# Bundled extensions whose content had drifted while still declaring 1.0.0
# when #4345 was filed. Their catalog version must stay above PRE_BUMP_VERSION
# so a copy installed before the fix is actually offered an update; a version
# that is not bumped past it here is a regression, not a skip.
DRIFTED_BEFORE_BUMP = frozenset({"agent-context", "assess", "git"})


def _catalog_entries() -> dict[str, dict]:
    catalog = json.loads((EXTENSIONS_ROOT / "catalog.json").read_text(encoding="utf-8"))
    return catalog["extensions"]


def _bundled_ids() -> list[str]:
    return sorted(
        ext_id
        for ext_id, entry in _catalog_entries().items()
        if entry.get("bundled")
        and not entry.get("download_url")
        and (EXTENSIONS_ROOT / ext_id / "extension.yml").is_file()
    )


def _make_project(tmp_path: Path) -> Path:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / ".specify").mkdir()
    (project_dir / ".claude" / "skills").mkdir(parents=True)
    return project_dir


def _stale_copy(tmp_path: Path, ext_id: str, version: str) -> Path:
    """The real bundled source with only its manifest version rewritten."""
    source = tmp_path / "stale" / ext_id
    shutil.copytree(EXTENSIONS_ROOT / ext_id, source)
    manifest_path = source / "extension.yml"
    data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    data["extension"]["version"] = version
    manifest_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return source


def _run_update(project_dir: Path, ext_id: str):
    from specify_cli import app
    from specify_cli.extensions import ExtensionCatalog

    catalog_info = dict(_catalog_entries()[ext_id])
    catalog_info.setdefault("_install_allowed", True)
    # Real catalog entry and real bundled copy; only the network fetch of the
    # catalog is replaced, and downloading must never be attempted for a
    # bundled extension.
    with patch.object(Path, "cwd", return_value=project_dir), \
         patch.object(ExtensionCatalog, "get_extension_info", return_value=catalog_info), \
         patch.object(
             ExtensionCatalog,
             "download_extension",
             side_effect=AssertionError("bundled update must not download"),
         ):
        return CliRunner().invoke(
            app, ["extension", "update", ext_id], input="y\n", catch_exceptions=True
        )


def test_bundled_ids_present():
    assert _bundled_ids(), "expected bundled extensions with in-repo sources"


@pytest.mark.parametrize("ext_id", _bundled_ids())
def test_stale_bundled_install_is_updated_to_catalog_version(tmp_path: Path, ext_id: str):
    from specify_cli._assets import get_speckit_version
    from specify_cli.extensions import ExtensionManager

    catalog_version = Version(_catalog_entries()[ext_id]["version"])
    if catalog_version <= Version(PRE_BUMP_VERSION):
        assert ext_id not in DRIFTED_BEFORE_BUMP, (
            f"'{ext_id}' drifted at {PRE_BUMP_VERSION} before #4345 but the catalog still "
            f"advertises {catalog_version}; installs made before the fix would never be "
            f"offered the shipped changes"
        )
        pytest.skip(f"'{ext_id}' has not been bumped past {PRE_BUMP_VERSION}; nothing to deliver")

    project_dir = _make_project(tmp_path)
    stale_source = _stale_copy(tmp_path, ext_id, PRE_BUMP_VERSION)
    manager = ExtensionManager(project_dir)
    manager.install_from_directory(stale_source, get_speckit_version())
    assert manager.registry.get(ext_id)["version"] == PRE_BUMP_VERSION

    result = _run_update(project_dir, ext_id)

    flat = " ".join(result.output.split())
    assert result.exit_code == 0, result.output
    assert f"Updated to v{catalog_version}" in flat, flat
    assert "Up to date" not in flat, flat
    assert ExtensionManager(project_dir).registry.get(ext_id)["version"] == str(catalog_version)


@pytest.mark.parametrize("ext_id", _bundled_ids())
def test_current_bundled_install_is_up_to_date(tmp_path: Path, ext_id: str):
    """The bumped catalog must not re-offer an update to an install that
    already carries the bundled version, or every fresh install would loop."""
    from specify_cli._assets import get_speckit_version
    from specify_cli.extensions import ExtensionManager

    catalog_version = _catalog_entries()[ext_id]["version"]
    project_dir = _make_project(tmp_path)
    ExtensionManager(project_dir).install_from_directory(
        EXTENSIONS_ROOT / ext_id, get_speckit_version()
    )

    result = _run_update(project_dir, ext_id)

    flat = " ".join(result.output.split())
    assert result.exit_code == 0, result.output
    assert f"Up to date (v{catalog_version})" in flat, flat
    assert ExtensionManager(project_dir).registry.get(ext_id)["version"] == catalog_version
