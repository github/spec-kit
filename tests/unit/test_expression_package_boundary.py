"""Boundary test: only ``engine.py`` and the package facade see an engine.

Runtime and validation must reach the evaluator through the ``engine`` contract,
never by importing ``engine_current`` (or a future ``engine_lark``) directly, or
a swapped engine would leave one of them on the old implementation. This pins
the import boundary the package layout is built around.
"""

import ast
from pathlib import Path

from specify_cli.workflows import expressions

# Modules allowed to name an engine implementation. ``engine.py`` is the
# selection point; ``__init__.py`` may expose test-only internals.
_ENGINE_IMPORT_ALLOWED = {"engine.py", "__init__.py"}


def _imports_engine_implementation(source: str, filename: str = "<test>") -> bool:
    """True when *source* imports a module whose final component is ``engine_*``."""
    tree = ast.parse(source, filename=filename)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = (node.module or "").split(".")[-1]
            names = [alias.name.split(".")[-1] for alias in node.names]
            if module.startswith("engine_") or any(
                name.startswith("engine_") for name in names
            ):
                return True
        elif isinstance(node, ast.Import):
            if any(
                alias.name.split(".")[-1].startswith("engine_")
                for alias in node.names
            ):
                return True
    return False


def test_only_the_engine_module_and_facade_import_an_engine_implementation():
    package_dir = Path(expressions.__file__).parent
    offenders = [
        path.name
        for path in sorted(package_dir.glob("*.py"))
        if path.name not in _ENGINE_IMPORT_ALLOWED
        and _imports_engine_implementation(
            path.read_text(encoding="utf-8"), filename=str(path)
        )
    ]
    assert offenders == []


def test_the_engine_module_really_is_the_selection_point():
    """Guard against a vacuous boundary: ``engine.py`` must import an engine."""
    package_dir = Path(expressions.__file__).parent
    engine_source = (package_dir / "engine.py").read_text(encoding="utf-8")
    assert _imports_engine_implementation(engine_source, filename="engine.py")


def test_the_boundary_check_detects_a_direct_engine_import():
    direct = "from .engine_current import _evaluate_template\n"
    assert _imports_engine_implementation(direct, filename="diagnostics.py")
