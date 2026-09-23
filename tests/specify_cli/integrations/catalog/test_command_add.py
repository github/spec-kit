"""Tests for TestIntegrationCatalogAdd."""

from __future__ import annotations

import json  # noqa: F401
import os  # noqa: F401

import pytest  # noqa: F401

from tests.specify_cli.integrations._catalog_helpers import IntegrationCatalogCliTestBase

class TestIntegrationCatalogAdd(IntegrationCatalogCliTestBase):
    def test_catalog_add_then_remove_roundtrip(self, tmp_path, monkeypatch):
        project = self._make_project(tmp_path)
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("USERPROFILE", str(tmp_path))
        monkeypatch.delenv("SPECKIT_INTEGRATION_CATALOG_URL", raising=False)

        add_result = self._invoke(
            [
                "integration",
                "catalog",
                "add",
                "https://new.example.com/catalog.json",
                "--name",
                "mine",
            ],
            project,
        )
        assert add_result.exit_code == 0, add_result.output
        assert "Catalog source added" in add_result.output

        cfg_path = project / ".specify" / "integration-catalogs.yml"
        assert cfg_path.exists()

        list_result = self._invoke(["integration", "catalog", "list"], project)
        assert list_result.exit_code == 0, list_result.output
        assert "Project catalog sources" in list_result.output
        assert "[0]" in list_result.output
        assert "mine" in list_result.output
        assert "default" not in list_result.output
        assert "community" not in list_result.output

        remove_result = self._invoke(
            ["integration", "catalog", "remove", "0"], project
        )
        assert remove_result.exit_code == 0, remove_result.output
        assert "'mine' removed" in remove_result.output

    def test_catalog_add_strips_whitespace_in_success_output_and_storage(
        self, tmp_path, monkeypatch
    ):
        """Surrounding whitespace in the URL must not appear in the success
        message or be persisted to the YAML config."""
        project = self._make_project(tmp_path)
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("USERPROFILE", str(tmp_path))
        monkeypatch.delenv("SPECKIT_INTEGRATION_CATALOG_URL", raising=False)

        padded_url = "  https://padded.example.com/catalog.json  "
        clean_url = "https://padded.example.com/catalog.json"

        add_result = self._invoke(
            [
                "integration",
                "catalog",
                "add",
                padded_url,
                "--name",
                "padded",
            ],
            project,
        )
        assert add_result.exit_code == 0, add_result.output
        assert clean_url in add_result.output
        assert padded_url not in add_result.output

        cfg_path = project / ".specify" / "integration-catalogs.yml"
        import yaml as _yaml
        data = _yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
        urls = [c["url"] for c in data["catalogs"]]
        assert clean_url in urls
        assert padded_url not in urls

    def test_catalog_add_rejects_invalid_url(self, tmp_path, monkeypatch):
        project = self._make_project(tmp_path)
        result = self._invoke(
            [
                "integration",
                "catalog",
                "add",
                "http://insecure.example.com/catalog.json",
            ],
            project,
        )
        assert result.exit_code == 1
        assert "HTTPS" in result.output

    def test_catalog_add_rejects_duplicate(self, tmp_path, monkeypatch):
        project = self._make_project(tmp_path)
        url = "https://dup.example.com/catalog.json"
        first = self._invoke(
            ["integration", "catalog", "add", url], project
        )
        assert first.exit_code == 0, first.output
        second = self._invoke(
            ["integration", "catalog", "add", url], project
        )
        assert second.exit_code == 1
        assert "already configured" in second.output
