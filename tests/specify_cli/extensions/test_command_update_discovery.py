"""Tests for ``_command_update_discovery``."""
from __future__ import annotations

from pathlib import Path

import pytest
from packaging import version as pkg_version

from specify_cli.extensions import _commands
from specify_cli.extensions._command_update_discovery import discover_updates


class _Registry:
    def __init__(self, metadata):
        self.metadata = metadata

    def get(self, extension_id):
        return self.metadata.get(extension_id)


class _Manager:
    def __init__(self, installed, metadata):
        self._installed = installed
        self.registry = _Registry(metadata)

    def list_installed(self):
        return self._installed


class _Catalog:
    def __init__(self, entries):
        self.entries = entries

    def get_extension_info(self, extension_id):
        return self.entries.get(extension_id)


def test_discovery_reports_empty_installation():
    updates, blocked, has_installed = discover_updates(
        _Manager([], {}),
        _Catalog({}),
        None,
    )

    assert updates == []
    assert blocked == []
    assert has_installed is False


def test_discovery_returns_typed_candidate():
    manager = _Manager(
        [{"id": "test-ext"}],
        {"test-ext": {"version": "1.0.0"}},
    )
    catalog = _Catalog(
        {
            "test-ext": {
                "id": "test-ext",
                "name": "Test Extension",
                "version": "2.0.0",
                "download_url": "https://example.com/test-ext.zip",
                "_catalog_name": "test",
            }
        }
    )

    updates, blocked, has_installed = discover_updates(manager, catalog, None)

    assert blocked == []
    assert has_installed is True
    assert len(updates) == 1
    assert updates[0].extension_id == "test-ext"
    assert updates[0].installed == "1.0.0"
    assert updates[0].available == "2.0.0"
    assert updates[0].catalog_name == "test"


@pytest.mark.parametrize(
    "version_field", [{}, {"version": None}, {"version": []}, {"version": 2}]
)
def test_discovery_skips_catalog_entry_without_valid_version(capsys, version_field):
    manager = _Manager(
        [{"id": "broken-ext"}, {"id": "test-ext"}],
        {"broken-ext": {"version": "1.0.0"}, "test-ext": {"version": "1.0.0"}},
    )
    catalog = _Catalog(
        {
            "broken-ext": {"id": "broken-ext", "name": "Broken", **version_field},
            "test-ext": {"id": "test-ext", "name": "Test Extension", "version": "2.0.0"},
        }
    )

    updates, blocked, has_installed = discover_updates(manager, catalog, None)

    output = " ".join(capsys.readouterr().out.split())
    assert "broken-ext: Invalid catalog version" in output
    assert "(skipping)" in output
    assert [update.extension_id for update in updates] == ["test-ext"]
    assert blocked == []
    assert has_installed is True


def test_discovery_blocks_stale_bundled_source(monkeypatch, tmp_path: Path):
    manager = _Manager(
        [{"id": "test-ext"}],
        {"test-ext": {"version": "1.0.0"}},
    )
    catalog = _Catalog(
        {
            "test-ext": {
                "id": "test-ext",
                "name": "Test Extension",
                "version": "3.0.0",
                "bundled": True,
            }
        }
    )
    monkeypatch.setattr(
        _commands,
        "_bundled_update_source",
        lambda extension_id: (tmp_path, pkg_version.Version("2.0.0")),
    )

    updates, blocked, has_installed = discover_updates(manager, catalog, None)

    assert updates == []
    assert blocked == ["test-ext"]
    assert has_installed is True
