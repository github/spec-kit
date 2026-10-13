"""Contract tests: every bundled workflow must ship inside the wheel's core_pack.

``specify workflow add <id>`` (and the bundler's workflow primitive) resolve a
bundled workflow via ``specify_cli._assets._locate_bundled_workflow``, which
checks the wheel's ``specify_cli/core_pack/workflows/<id>/`` directory first.
Any workflow marked ``bundled: true`` in ``workflows/catalog.json`` must
therefore be force-included at build time; otherwise the released wheel
advertises a bundled workflow it does not actually ship.
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


def _bundled_workflow_ids() -> list[str]:
    catalog = json.loads((REPO_ROOT / "workflows" / "catalog.json").read_text())
    return sorted(
        workflow_id
        for workflow_id, entry in catalog["workflows"].items()
        if entry.get("bundled")
    )


def test_every_bundled_workflow_is_force_included():
    force_include = _force_include()
    bundled = _bundled_workflow_ids()

    assert bundled, "expected at least one bundled workflow in workflows/catalog.json"
    for workflow_id in bundled:
        assert force_include.get(f"workflows/{workflow_id}") == (
            f"specify_cli/core_pack/workflows/{workflow_id}"
        ), f"bundled workflow '{workflow_id}' is missing from the wheel force-include list"


def test_stock_bundled_workflows_are_force_included():
    # Explicit regression guard for the first-party workflows shipped in #4495.
    force_include = _force_include()
    for workflow_id in ("speckit", "bugfix", "assess"):
        assert force_include[f"workflows/{workflow_id}"] == (
            f"specify_cli/core_pack/workflows/{workflow_id}"
        )
