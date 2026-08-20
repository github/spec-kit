"""Wheel/source count-parity contract test.

Guarantees the shipped baseline surfaces the same count of commands, templates
and scripts regardless of whether ``build_core_inventory`` finds the wheel's
``core_pack/`` directory or falls back to the source checkout. Deep equality
is intentionally not asserted here: source and wheel builds may embed slightly
different absolute paths but the count invariant is what protects consumers.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from specify_cli import core as core_pkg
from specify_cli.core import build_core_inventory


def _mirror_source_into_pack(src_root: Path, pack_root: Path) -> None:
    """Copy shipped source assets into a fake wheel-style ``core_pack/`` tree."""
    import shutil

    (pack_root / "commands").mkdir(parents=True, exist_ok=True)
    (pack_root / "templates").mkdir(parents=True, exist_ok=True)
    (pack_root / "scripts").mkdir(parents=True, exist_ok=True)

    for md in (src_root / "templates" / "commands").glob("*.md"):
        shutil.copy2(md, pack_root / "commands" / md.name)
    for tmpl in (src_root / "templates").glob("*.md"):
        shutil.copy2(tmpl, pack_root / "templates" / tmpl.name)
    for runtime in ("bash", "powershell", "python"):
        runtime_dir = src_root / "scripts" / runtime
        if not runtime_dir.exists():
            continue
        dest = pack_root / "scripts" / runtime
        dest.mkdir(exist_ok=True)
        for script in runtime_dir.iterdir():
            if script.is_file():
                shutil.copy2(script, dest / script.name)


def test_wheel_and_source_layouts_agree_on_counts(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # 1) Source-layout snapshot: force the wheel pack lookup to miss.
    monkeypatch.setattr(core_pkg, "_locate_core_pack", lambda: None)
    source_inv = build_core_inventory()

    # 2) Wheel-layout snapshot: mirror the shipped source into a fake pack tree
    #    and force ``_locate_core_pack`` to return it.
    src_root = core_pkg._repo_root()
    pack_root = tmp_path / "core_pack"
    _mirror_source_into_pack(src_root, pack_root)
    monkeypatch.setattr(core_pkg, "_locate_core_pack", lambda: pack_root)
    wheel_inv = build_core_inventory()

    for section in ("commands", "templates", "scripts"):
        assert len(source_inv[section]) == len(wheel_inv[section]), section
        assert [e["name"] for e in source_inv[section]] == [
            e["name"] for e in wheel_inv[section]
        ], section
