"""Tests for mirrored integration CLI behavior in test_command_list.py."""

from __future__ import annotations

import json  # noqa: F401
import os  # noqa: F401
import shutil  # noqa: F401
from pathlib import Path  # noqa: F401

import pytest  # noqa: F401

from specify_cli import app  # noqa: F401
from tests.conftest import strip_ansi  # noqa: F401
from tests.http_helpers import route_opener_open_through_urlopen  # noqa: F401
from tests.specify_cli.integrations._catalog_helpers import IntegrationListCatalogTestBase
from tests.specify_cli.integrations._helpers import (
    _copy_project_template,  # noqa: F401
    _init_project,  # noqa: F401
    _integration_list_row_cells,  # noqa: F401
    _move_kilocode_install_to_legacy_layout,  # noqa: F401
    _run_in_project,  # noqa: F401
    _write_invalid_manifest,  # noqa: F401
    runner,  # noqa: F401
)

class TestIntegrationList:
    def test_list_requires_speckit_project(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, ["integration", "list"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0
        assert "Not a Spec Kit project" in result.output

    def test_list_shows_installed(self, tmp_path):
        project = _init_project(tmp_path, "copilot")
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "list"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0
        assert "copilot" in result.output
        assert "installed" in result.output

    def test_list_shows_available_integrations(self, tmp_path):
        project = _init_project(tmp_path, "copilot")
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "list"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0
        # Should show multiple integrations
        assert "claude" in result.output
        assert "gemini" in result.output
        assert "zed" in result.output

    def test_list_shows_multi_install_safe_status(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "list"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0
        assert "Multi-install" in result.output
        assert "Safe" in result.output
        assert _integration_list_row_cells(result.output, "claude")[-1] == "yes"
        assert _integration_list_row_cells(result.output, "copilot")[-1] == "no"

    def test_list_rejects_newer_integration_state_schema(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        int_json = project / ".specify" / "integration.json"
        data = json.loads(int_json.read_text(encoding="utf-8"))
        data["integration_state_schema"] = 99
        int_json.write_text(json.dumps(data), encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "list"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code != 0
        normalized = " ".join(result.output.split())
        assert "schema 99" in normalized
        assert "only supports schema 1" in normalized


class TestIntegrationListCatalog(IntegrationListCatalogTestBase):
    def test_list_catalog_flag(self, tmp_path, monkeypatch):
        """--catalog should show catalog entries."""
        from typer.testing import CliRunner
        from specify_cli import app
        runner = CliRunner()
        project = self._init_project(tmp_path)

        catalog = {
            "schema_version": "1.0",
            "updated_at": "2026-01-01T00:00:00Z",
            "integrations": {
                "test-agent": {
                    "id": "test-agent",
                    "name": "Test Agent",
                    "version": "1.0.0",
                    "description": "A test agent",
                    "tags": ["cli"],
                },
            },
        }

        import specify_cli.authentication.http as _auth_http

        class FakeResponse:
            def __init__(self, data, url=""):
                self._data = json.dumps(data).encode()
                self._url = url if isinstance(url, str) else url.full_url
                self._offset = 0

            def read(self, size=-1):
                if size == -1:
                    chunk = self._data[self._offset:]
                    self._offset = len(self._data)
                else:
                    chunk = self._data[self._offset:self._offset + size]
                    self._offset += len(chunk)
                return chunk

            def geturl(self):
                return self._url

            def __enter__(self):
                return self

            def __exit__(self, *a):
                pass

        monkeypatch.setattr(_auth_http.urllib.request, "urlopen",
                            lambda req, timeout=10: FakeResponse(catalog, req if isinstance(req, str) else req.full_url))

        old = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "list", "--catalog"])
        finally:
            os.chdir(old)

        assert result.exit_code == 0
        assert "test-agent" in result.output
        assert "Test Agent" in result.output

    def test_list_without_catalog_still_works(self, tmp_path):
        """Default list (no --catalog) works as before."""
        from typer.testing import CliRunner
        from specify_cli import app
        runner = CliRunner()
        project = self._init_project(tmp_path)

        old = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "list"])
        finally:
            os.chdir(old)

        assert result.exit_code == 0
        assert "copilot" in result.output
        assert "installed" in result.output
