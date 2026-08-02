"""Contract tests: every bundled preset must ship inside the wheel's core_pack.

``specify preset add <id>`` resolves a bundled preset via
``specify_cli._assets._locate_bundled_preset``, which checks the wheel's
``specify_cli/core_pack/presets/<id>/`` directory first. Any preset marked
``bundled: true`` in ``presets/catalog.json`` must therefore be force-included
at build time; otherwise the released wheel advertises a bundled preset it does
not actually ship, and ``specify preset add <id>`` falls through and reports the
preset as missing.
"""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]


def _force_include() -> dict[str, str]:
    with (REPO_ROOT / "pyproject.toml").open("rb") as pyproject_file:
        pyproject = tomllib.load(pyproject_file)
    return pyproject["tool"]["hatch"]["build"]["targets"]["wheel"]["force-include"]


def _bundled_preset_ids() -> list[str]:
    catalog = json.loads((REPO_ROOT / "presets" / "catalog.json").read_text())
    return sorted(
        preset_id
        for preset_id, entry in catalog["presets"].items()
        if entry.get("bundled")
    )


def test_every_bundled_preset_is_force_included():
    force_include = _force_include()
    bundled = _bundled_preset_ids()

    assert bundled, "expected at least one bundled preset in presets/catalog.json"
    for preset_id in bundled:
        assert force_include.get(f"presets/{preset_id}") == (
            f"specify_cli/core_pack/presets/{preset_id}"
        ), f"bundled preset '{preset_id}' is missing from the wheel force-include list"


def test_constitution_sync_is_bundled_and_shipped():
    # Explicit regression guard: constitution-sync was advertised as bundled
    # before it was added to the wheel force-include list.
    assert "constitution-sync" in _bundled_preset_ids()
    assert _force_include()["presets/constitution-sync"] == (
        "specify_cli/core_pack/presets/constitution-sync"
    )
