"""Unit tests for the bundler YAML I/O helpers."""
from __future__ import annotations

from pathlib import Path

import pytest

from specify_cli.bundler import BundlerError
from specify_cli.bundles.yamlio import dump_yaml, load_json, load_yaml, loads_json


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


def test_load_yaml_non_utf8_raises_bundler_error(tmp_path: Path):
    """A non-UTF-8 file must degrade into BundlerError, per this module's
    documented contract. UnicodeDecodeError is a ValueError, not an OSError, so
    it previously escaped as a raw traceback. UTF-16 is the realistic case:
    PowerShell 5.1's `Out-File`/`>` default to it."""
    path = tmp_path / "bundle-catalogs.yml"
    path.write_bytes('catalogs: []\n'.encode("utf-16"))
    with pytest.raises(BundlerError, match="Could not read"):
        load_yaml(path)


def test_load_json_non_utf8_raises_bundler_error(tmp_path: Path):
    """Same for the JSON reader: json.JSONDecodeError is a *sibling* of
    UnicodeDecodeError, so it does not cover a decode failure."""
    path = tmp_path / "records.json"
    path.write_bytes('{"bundles": []}'.encode("utf-16"))
    with pytest.raises(BundlerError, match="Could not read"):
        load_json(path)


def test_load_json_malformed_still_reports_invalid_json(tmp_path: Path):
    """Clause order regression guard: decodable-but-malformed JSON must keep the
    more specific 'Invalid JSON' message rather than the read-error one."""
    path = tmp_path / "records.json"
    path.write_text('{"bundles": [', encoding="utf-8")
    with pytest.raises(BundlerError, match="Invalid JSON"):
        load_json(path)


def test_load_json_accepts_single_utf8_bom(tmp_path: Path):
    path = tmp_path / "records.json"
    path.write_bytes(b"\xef\xbb\xbf" + '{"name": "café", "note": "\ufeff"}'.encode())
    assert load_json(path) == {"name": "café", "note": "\ufeff"}


def test_load_json_reads_symlinked_file_outside_parent(tmp_path: Path):
    target = tmp_path / "records.json"
    target.write_text('{"name": "café"}', encoding="utf-8")
    link_dir = tmp_path / "links"
    link_dir.mkdir()
    link = link_dir / "records.json"
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"cannot create symlink: {exc}")
    assert load_json(link) == {"name": "café"}


@pytest.mark.parametrize(
    "text",
    [
        '\ufeff\ufeff{"name": 1}',
        ' \ufeff{"name": 1}',
        '\ufeff{"name": ',
    ],
)
def test_load_json_bom_does_not_hide_invalid_json(tmp_path: Path, text: str):
    path = tmp_path / "records.json"
    path.write_bytes(text.encode("utf-8"))
    with pytest.raises(BundlerError, match="Invalid JSON"):
        load_json(path)


def test_loads_json_accepts_single_leading_bom():
    assert loads_json('\ufeff{"name": "café", "note": "\ufeff"}') == {
        "name": "café",
        "note": "\ufeff",
    }


@pytest.mark.parametrize(
    "text",
    [
        '\ufeff\ufeff{"name": 1}',
        ' \ufeff{"name": 1}',
        '\ufeff{"name": ',
        '\ufeff{"name": 1, "name": 2}',
    ],
)
def test_loads_json_bom_does_not_hide_invalid_json(text: str):
    with pytest.raises(BundlerError, match="Invalid JSON"):
        loads_json(text)
