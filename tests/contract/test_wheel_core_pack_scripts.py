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


def _script_variants() -> list[str]:
    """Return source script variants, excluding interpreter caches."""

    return sorted(
        path.name
        for path in (REPO_ROOT / "scripts").iterdir()
        if path.is_dir()
        and path.name != "__pycache__"
        and any(
            candidate.is_file()
            for pattern in ("*.sh", "*.ps1", "*.py")
            for candidate in path.glob(pattern)
        )
    )


def _force_include() -> dict[str, str]:
    with (REPO_ROOT / "pyproject.toml").open("rb") as pyproject_file:
        pyproject = tomllib.load(pyproject_file)
    return pyproject["tool"]["hatch"]["build"]["targets"]["wheel"]["force-include"]


def test_every_script_variant_is_bundled_into_core_pack():
    force_include = _force_include()
    variants = _script_variants()

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


def test_script_variants_require_source_files(tmp_path, monkeypatch):
    scripts = tmp_path / "scripts"
    for name in ("bash", "powershell", "python", "empty", "docs", "__pycache__"):
        (scripts / name).mkdir(parents=True)
    for variant, filename in (
        ("bash", "run.sh"),
        ("powershell", "run.ps1"),
        ("python", "run.py"),
        ("docs", "README.md"),
        ("__pycache__", "cached.py"),
    ):
        (scripts / variant / filename).write_text("", encoding="utf-8")
    monkeypatch.setitem(_script_variants.__globals__, "REPO_ROOT", tmp_path)

    assert _script_variants() == ["bash", "powershell", "python"]
