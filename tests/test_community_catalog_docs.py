from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from specify_cli.community_catalog_docs import (
    COMMUNITY_INDEX_PATH,
    iter_community_extensions,
    load_community_catalog,
    render_community_extensions_index,
)


ROOT_DIR = Path(__file__).resolve().parents[1]


def test_community_extensions_index_matches_generator() -> None:
    """The committed community index should stay in sync with the generator."""
    assert COMMUNITY_INDEX_PATH.read_text(encoding="utf-8") == render_community_extensions_index()


def test_community_extensions_are_sorted_by_name() -> None:
    """The generated index should keep entries in a stable alphabetical order."""
    catalog = load_community_catalog()
    rows = iter_community_extensions(catalog)
    names = [row["name"] for row in rows]

    assert names == sorted(names, key=str.casefold)


def test_community_extensions_generator_check_mode() -> None:
    """The CLI check mode should fail when the committed index drifts."""
    result = subprocess.run(
        [
            sys.executable,
            "scripts/generate_community_extensions_index.py",
            "--check",
        ],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout
