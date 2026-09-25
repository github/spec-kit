"""Tests for TestIntegrationCatalogRemove."""

from __future__ import annotations

import json  # noqa: F401
import os  # noqa: F401

import pytest  # noqa: F401

from tests.specify_cli.integrations._catalog_helpers import IntegrationCatalogCliTestBase

class TestIntegrationCatalogRemove(IntegrationCatalogCliTestBase):
    def test_catalog_remove_out_of_range(self, tmp_path, monkeypatch):
        project = self._make_project(tmp_path)
        # Need a config file for remove to attempt an index lookup
        self._invoke(
            [
                "integration",
                "catalog",
                "add",
                "https://only.example.com/catalog.json",
            ],
            project,
        )
        result = self._invoke(
            ["integration", "catalog", "remove", "9"], project
        )
        assert result.exit_code == 1
        assert "out of range" in result.output

    def test_catalog_remove_without_config(self, tmp_path, monkeypatch):
        project = self._make_project(tmp_path)
        result = self._invoke(
            ["integration", "catalog", "remove", "0"], project
        )
        assert result.exit_code == 1
        assert "No catalog config" in result.output

    def test_catalog_remove_final_entry_restores_defaults(
        self, tmp_path, monkeypatch
    ):
        """End-to-end: add → remove-last-entry → list should not error.

        Regression for the flow where a user adds a catalog, removes it, then
        runs any follow-up integration command. Without the fix the config
        file would be left as `catalogs: []` and every subsequent
        `integration` call would fail with "contains no 'catalogs' entries".
        """
        project = self._make_project(tmp_path)
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("USERPROFILE", str(tmp_path))
        monkeypatch.delenv("SPECKIT_INTEGRATION_CATALOG_URL", raising=False)

        add = self._invoke(
            [
                "integration",
                "catalog",
                "add",
                "https://only.example.com/catalog.json",
                "--name",
                "only",
            ],
            project,
        )
        assert add.exit_code == 0, add.output

        remove = self._invoke(
            ["integration", "catalog", "remove", "0"], project
        )
        assert remove.exit_code == 0, remove.output
        assert "'only' removed" in remove.output

        cfg_path = project / ".specify" / "integration-catalogs.yml"
        assert not cfg_path.exists(), (
            "config file should be deleted when the final catalog is removed"
        )

        # Follow-up command must succeed and show the built-in defaults,
        # not error out on "contains no 'catalogs' entries".
        listing = self._invoke(["integration", "catalog", "list"], project)
        assert listing.exit_code == 0, listing.output
        assert "default" in listing.output
        assert "community" in listing.output
