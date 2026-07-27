"""Unit tests for the bundler YAML I/O helpers."""
from __future__ import annotations

from pathlib import Path

from specify_cli.bundler.lib.yamlio import dump_yaml, load_yaml


def test_dump_yaml_preserves_unicode(tmp_path: Path):
    # dump_yaml must write literal UTF-8, not \xNN / \uXXXX escapes, so bundle
    # config stays human-readable — matching _utils.dump_frontmatter and the
    # extensions/presets config writers (all allow_unicode=True).
    path = tmp_path / "f.yml"
    data = {"note": "café-münchen", "url": "https://例え.example"}
    dump_yaml(path, data)
    raw = path.read_text(encoding="utf-8")
    assert "café-münchen" in raw
    assert "例え" in raw
    assert "\\x" not in raw and "\\u" not in raw


def test_dump_yaml_round_trips_unicode(tmp_path: Path):
    path = tmp_path / "f.yml"
    data = {"note": "café", "city": "münchen"}
    dump_yaml(path, data)
    assert load_yaml(path) == data
