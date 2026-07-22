"""Contract tests for the script variants bundled into the wheel's core_pack.

``specify init --script <type>`` installs from ``specify_cli/core_pack/scripts/``
when the CLI runs from a wheel. Any script variant that lives in the repository
must therefore be force-included at build time, otherwise the generated
commands reference scripts the released package never ships (#3665).
"""

from __future__ import annotations

import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]


def _force_include() -> dict[str, str]:
    with (REPO_ROOT / "pyproject.toml").open("rb") as pyproject_file:
        pyproject = tomllib.load(pyproject_file)
    return pyproject["tool"]["hatch"]["build"]["targets"]["wheel"]["force-include"]


def test_every_script_variant_is_bundled_into_core_pack():
    force_include = _force_include()
    variants = sorted(
        path.name for path in (REPO_ROOT / "scripts").iterdir() if path.is_dir()
    )

    assert variants, "expected at least one script variant under scripts/"
    for variant in variants:
        assert force_include.get(f"scripts/{variant}") == (
            f"specify_cli/core_pack/scripts/{variant}"
        ), f"scripts/{variant} is missing from the wheel force-include list"


def test_python_script_variant_is_bundled():
    # Explicit regression guard for #3665: `--script py` shipped skills that
    # invoked python3 .specify/scripts/python/*.py while the wheel bundled
    # only the bash and PowerShell variants.
    assert _force_include()["scripts/python"] == "specify_cli/core_pack/scripts/python"
