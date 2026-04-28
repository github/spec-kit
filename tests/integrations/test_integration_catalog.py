"""Tests for the integration catalog system (catalog.py)."""

import json
import os

import pytest
import yaml

from specify_cli.integrations.catalog import (
    IntegrationCatalog,
    IntegrationCatalogEntry,
    IntegrationCatalogError,
    IntegrationDescriptor,
    IntegrationDescriptorError,
)


# ---------------------------------------------------------------------------
# IntegrationCatalogEntry
# ---------------------------------------------------------------------------


class TestIntegrationCatalogEntry:
    def test_create_entry(self):
        entry = IntegrationCatalogEntry(
            url="https://example.com/catalog.json",
            name="test",
            priority=1,
            install_allowed=True,
            description="Test catalog",
        )
        assert entry.url == "https://example.com/catalog.json"
        assert entry.name == "test"
        assert entry.priority == 1
        assert entry.install_allowed is True
        assert entry.description == "Test catalog"

    def test_default_description(self):
        entry = IntegrationCatalogEntry(
            url="https://example.com/catalog.json",
            name="test",
            priority=1,
            install_allowed=False,
        )
        assert entry.description == ""


# ---------------------------------------------------------------------------
# IntegrationCatalog — URL validation
# ---------------------------------------------------------------------------


class TestCatalogURLValidation:
    def test_https_allowed(self):
        IntegrationCatalog._validate_catalog_url("https://example.com/catalog.json")

    def test_http_rejected(self):
        with pytest.raises(IntegrationCatalogError, match="HTTPS"):
            IntegrationCatalog._validate_catalog_url("http://example.com/catalog.json")

    def test_http_localhost_allowed(self):
        IntegrationCatalog._validate_catalog_url("http://localhost:8080/catalog.json")
        IntegrationCatalog._validate_catalog_url("http://127.0.0.1/catalog.json")

    def test_missing_host_rejected(self):
        with pytest.raises(IntegrationCatalogError, match="valid URL"):
            IntegrationCatalog._validate_catalog_url("https:///no-host")


# ---------------------------------------------------------------------------
# IntegrationCatalog — active catalogs
# ---------------------------------------------------------------------------


class TestActiveCatalogs:
    def test_defaults_when_no_config(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("USERPROFILE", str(tmp_path))
        monkeypatch.delenv("SPECKIT_INTEGRATION_CATALOG_URL", raising=False)
        (tmp_path / ".specify").mkdir()
        cat = IntegrationCatalog(tmp_path)
        active = cat.get_active_catalogs()
        assert len(active) == 2
        assert active[0].name == "default"
        assert active[1].name == "community"

    def test_env_var_override(self, tmp_path, monkeypatch):
        (tmp_path / ".specify").mkdir()
        monkeypatch.setenv(
            "SPECKIT_INTEGRATION_CATALOG_URL",
            "https://custom.example.com/catalog.json",
        )
        cat = IntegrationCatalog(tmp_path)
        active = cat.get_active_catalogs()
        assert len(active) == 1
        assert active[0].name == "custom"

    def test_project_config_overrides_defaults(self, tmp_path):
        specify = tmp_path / ".specify"
        specify.mkdir()
        cfg = specify / "integration-catalogs.yml"
        cfg.write_text(yaml.dump({
            "catalogs": [
                {"url": "https://my.example.com/cat.json", "name": "mine", "priority": 1, "install_allowed": True},
            ]
        }))
        cat = IntegrationCatalog(tmp_path)
        active = cat.get_active_catalogs()
        assert len(active) == 1
        assert active[0].name == "mine"

    def test_empty_config_raises(self, tmp_path):
        specify = tmp_path / ".specify"
        specify.mkdir()
        cfg = specify / "integration-catalogs.yml"
        cfg.write_text(yaml.dump({"catalogs": []}))
        cat = IntegrationCatalog(tmp_path)
        with pytest.raises(IntegrationCatalogError, match="no 'catalogs' entries"):
            cat.get_active_catalogs()


# ---------------------------------------------------------------------------
# IntegrationCatalog — fetch & search (using monkeypatched urlopen responses)
# ---------------------------------------------------------------------------


class TestCatalogFetch:
    """Tests that use a local HTTP server stub via monkeypatch."""

    def _patch_urlopen(self, monkeypatch, catalog_data):
        """Patch authentication.http.urllib.request.urlopen to return *catalog_data*."""

        class FakeResponse:
            def __init__(self, data, url=""):
                self._data = json.dumps(data).encode()
                self._url = url if isinstance(url, str) else url.full_url

            def read(self):
                return self._data

            def geturl(self):
                return self._url

            def __enter__(self):
                return self

            def __exit__(self, *a):
                pass

        def fake_urlopen(req, timeout=10):
            url = req if isinstance(req, str) else req.full_url
            return FakeResponse(catalog_data, url)

        import specify_cli.authentication.http as _auth_http
        monkeypatch.setattr(_auth_http.urllib.request, "urlopen", fake_urlopen)

    def test_fetch_and_search_all(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("USERPROFILE", str(tmp_path))
        monkeypatch.delenv("SPECKIT_INTEGRATION_CATALOG_URL", raising=False)
        (tmp_path / ".specify").mkdir()
        cat = IntegrationCatalog(tmp_path)

        catalog = {
            "schema_version": "1.0",
            "updated_at": "2026-01-01T00:00:00Z",
            "integrations": {
                "acme-coder": {
                    "id": "acme-coder",
                    "name": "Acme Coder",
                    "version": "2.0.0",
                    "description": "Community integration for Acme Coder",
                    "author": "acme-org",
                    "tags": ["cli"],
                },
            },
        }
        self._patch_urlopen(monkeypatch, catalog)

        results = cat.search()
        assert len(results) >= 1
        ids = [r["id"] for r in results]
        assert "acme-coder" in ids

    def test_search_by_tag(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("USERPROFILE", str(tmp_path))
        monkeypatch.delenv("SPECKIT_INTEGRATION_CATALOG_URL", raising=False)
        (tmp_path / ".specify").mkdir()
        cat = IntegrationCatalog(tmp_path)

        catalog = {
            "schema_version": "1.0",
            "updated_at": "2026-01-01T00:00:00Z",
            "integrations": {
                "a": {"id": "a", "name": "A", "version": "1.0.0", "tags": ["cli"]},
                "b": {"id": "b", "name": "B", "version": "1.0.0", "tags": ["ide"]},
            },
        }
        self._patch_urlopen(monkeypatch, catalog)

        results = cat.search(tag="cli")
        assert all("cli" in r.get("tags", []) for r in results)

    def test_search_by_query(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("USERPROFILE", str(tmp_path))
        monkeypatch.delenv("SPECKIT_INTEGRATION_CATALOG_URL", raising=False)
        (tmp_path / ".specify").mkdir()
        cat = IntegrationCatalog(tmp_path)

        catalog = {
            "schema_version": "1.0",
            "updated_at": "2026-01-01T00:00:00Z",
            "integrations": {
                "claude": {"id": "claude", "name": "Claude Code", "version": "1.0.0", "description": "Anthropic", "tags": []},
                "gemini": {"id": "gemini", "name": "Gemini CLI", "version": "1.0.0", "description": "Google", "tags": []},
            },
        }
        self._patch_urlopen(monkeypatch, catalog)

        results = cat.search(query="claude")
        assert len(results) == 1
        assert results[0]["id"] == "claude"

    def test_get_integration_info(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("USERPROFILE", str(tmp_path))
        monkeypatch.delenv("SPECKIT_INTEGRATION_CATALOG_URL", raising=False)
        (tmp_path / ".specify").mkdir()
        cat = IntegrationCatalog(tmp_path)

        catalog = {
            "schema_version": "1.0",
            "updated_at": "2026-01-01T00:00:00Z",
            "integrations": {
                "claude": {"id": "claude", "name": "Claude Code", "version": "1.0.0"},
            },
        }
        self._patch_urlopen(monkeypatch, catalog)

        info = cat.get_integration_info("claude")
        assert info is not None
        assert info["name"] == "Claude Code"

        assert cat.get_integration_info("nonexistent") is None

    def test_invalid_catalog_format(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("USERPROFILE", str(tmp_path))
        monkeypatch.delenv("SPECKIT_INTEGRATION_CATALOG_URL", raising=False)
        (tmp_path / ".specify").mkdir()
        cat = IntegrationCatalog(tmp_path)

        self._patch_urlopen(monkeypatch, {"schema_version": "1.0"})  # missing "integrations"

        with pytest.raises(IntegrationCatalogError, match="Failed to fetch any integration catalog"):
            cat.search()

    def test_clear_cache(self, tmp_path):
        (tmp_path / ".specify").mkdir()
        cat = IntegrationCatalog(tmp_path)
        cat.cache_dir.mkdir(parents=True, exist_ok=True)
        (cat.cache_dir / "catalog-abc123.json").write_text("{}")
        cat.clear_cache()
        assert not list(cat.cache_dir.glob("catalog-*.json"))


# ---------------------------------------------------------------------------
# IntegrationDescriptor (integration.yml)
# ---------------------------------------------------------------------------

VALID_DESCRIPTOR = {
    "schema_version": "1.0",
    "integration": {
        "id": "my-agent",
        "name": "My Agent",
        "version": "1.0.0",
        "description": "Integration for My Agent",
        "author": "my-org",
    },
    "requires": {
        "speckit_version": ">=0.6.0",
    },
    "provides": {
        "commands": [
            {"name": "speckit.specify", "file": "templates/speckit.specify.md"},
        ],
        "scripts": [],
    },
}


class TestIntegrationDescriptor:
    def _write(self, tmp_path, data):
        p = tmp_path / "integration.yml"
        p.write_text(yaml.dump(data))
        return p

    def test_valid_descriptor(self, tmp_path):
        p = self._write(tmp_path, VALID_DESCRIPTOR)
        desc = IntegrationDescriptor(p)
        assert desc.id == "my-agent"
        assert desc.name == "My Agent"
        assert desc.version == "1.0.0"
        assert desc.description == "Integration for My Agent"
        assert desc.requires_speckit_version == ">=0.6.0"
        assert len(desc.commands) == 1
        assert desc.scripts == []

    def test_missing_schema_version(self, tmp_path):
        data = {**VALID_DESCRIPTOR}
        del data["schema_version"]
        p = self._write(tmp_path, data)
        with pytest.raises(IntegrationDescriptorError, match="Missing required field: schema_version"):
            IntegrationDescriptor(p)

    def test_unsupported_schema_version(self, tmp_path):
        data = {**VALID_DESCRIPTOR, "schema_version": "99.0"}
        p = self._write(tmp_path, data)
        with pytest.raises(IntegrationDescriptorError, match="Unsupported schema version"):
            IntegrationDescriptor(p)

    def test_missing_integration_id(self, tmp_path):
        data = {**VALID_DESCRIPTOR, "integration": {"name": "X", "version": "1.0.0", "description": "Y"}}
        p = self._write(tmp_path, data)
        with pytest.raises(IntegrationDescriptorError, match="Missing integration.id"):
            IntegrationDescriptor(p)

    def test_invalid_id_format(self, tmp_path):
        integ = {**VALID_DESCRIPTOR["integration"], "id": "BAD_ID"}
        data = {**VALID_DESCRIPTOR, "integration": integ}
        p = self._write(tmp_path, data)
        with pytest.raises(IntegrationDescriptorError, match="Invalid integration ID"):
            IntegrationDescriptor(p)

    def test_invalid_version(self, tmp_path):
        integ = {**VALID_DESCRIPTOR["integration"], "version": "not-semver"}
        data = {**VALID_DESCRIPTOR, "integration": integ}
        p = self._write(tmp_path, data)
        with pytest.raises(IntegrationDescriptorError, match="Invalid version"):
            IntegrationDescriptor(p)

    def test_missing_speckit_version(self, tmp_path):
        data = {**VALID_DESCRIPTOR, "requires": {}}
        p = self._write(tmp_path, data)
        with pytest.raises(IntegrationDescriptorError, match="requires.speckit_version"):
            IntegrationDescriptor(p)

    def test_no_commands_or_scripts(self, tmp_path):
        data = {**VALID_DESCRIPTOR, "provides": {}}
        p = self._write(tmp_path, data)
        with pytest.raises(IntegrationDescriptorError, match="at least one command or script"):
            IntegrationDescriptor(p)

    def test_command_missing_name(self, tmp_path):
        data = {**VALID_DESCRIPTOR, "provides": {"commands": [{"file": "x.md"}]}}
        p = self._write(tmp_path, data)
        with pytest.raises(IntegrationDescriptorError, match="missing 'name' or 'file'"):
            IntegrationDescriptor(p)

    def test_commands_not_a_list(self, tmp_path):
        data = {**VALID_DESCRIPTOR, "provides": {"commands": "not-a-list", "scripts": ["a.sh"]}}
        p = self._write(tmp_path, data)
        with pytest.raises(IntegrationDescriptorError, match="expected a list"):
            IntegrationDescriptor(p)

    def test_scripts_not_a_list(self, tmp_path):
        data = {**VALID_DESCRIPTOR, "provides": {"commands": [{"name": "a", "file": "b"}], "scripts": "not-a-list"}}
        p = self._write(tmp_path, data)
        with pytest.raises(IntegrationDescriptorError, match="expected a list"):
            IntegrationDescriptor(p)

    def test_file_not_found(self, tmp_path):
        with pytest.raises(IntegrationDescriptorError, match="Descriptor not found"):
            IntegrationDescriptor(tmp_path / "nonexistent.yml")

    def test_invalid_yaml(self, tmp_path):
        p = tmp_path / "integration.yml"
        p.write_text(": : :")
        with pytest.raises(IntegrationDescriptorError, match="Invalid YAML"):
            IntegrationDescriptor(p)

    def test_get_hash(self, tmp_path):
        p = self._write(tmp_path, VALID_DESCRIPTOR)
        desc = IntegrationDescriptor(p)
        h = desc.get_hash()
        assert h.startswith("sha256:")

    def test_tools_accessor(self, tmp_path):
        data = {**VALID_DESCRIPTOR, "requires": {
            "speckit_version": ">=0.6.0",
            "tools": [{"name": "my-agent", "version": ">=1.0.0", "required": True}],
        }}
        p = self._write(tmp_path, data)
        desc = IntegrationDescriptor(p)
        assert len(desc.tools) == 1
        assert desc.tools[0]["name"] == "my-agent"


# ---------------------------------------------------------------------------
# CLI: integration list --catalog
# ---------------------------------------------------------------------------


class TestIntegrationListCatalog:
    """Test ``specify integration list --catalog``."""

    def _init_project(self, tmp_path):
        """Create a minimal spec-kit project."""
        from typer.testing import CliRunner
        from specify_cli import app
        runner = CliRunner()
        project = tmp_path / "proj"
        project.mkdir()
        old = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "init", "--here",
                "--integration", "copilot",
                "--script", "sh",
                "--no-git",
                "--ignore-agent-tools",
            ], catch_exceptions=False)
        finally:
            os.chdir(old)
        assert result.exit_code == 0, result.output
        return project

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
            def read(self):
                return self._data
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


# ---------------------------------------------------------------------------
# CLI: integration upgrade
# ---------------------------------------------------------------------------


class TestIntegrationUpgrade:
    """Test ``specify integration upgrade``."""

    def _init_project(self, tmp_path, integration="copilot"):
        from typer.testing import CliRunner
        from specify_cli import app
        runner = CliRunner()
        project = tmp_path / "proj"
        project.mkdir()
        old = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "init", "--here",
                "--integration", integration,
                "--script", "sh",
                "--no-git",
                "--ignore-agent-tools",
            ], catch_exceptions=False)
        finally:
            os.chdir(old)
        assert result.exit_code == 0, result.output
        return project

    def test_upgrade_requires_speckit_project(self, tmp_path):
        from typer.testing import CliRunner
        from specify_cli import app
        runner = CliRunner()
        old = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, ["integration", "upgrade"])
        finally:
            os.chdir(old)
        assert result.exit_code != 0
        assert "Not a spec-kit project" in result.output

    def test_upgrade_no_integration_installed(self, tmp_path):
        from typer.testing import CliRunner
        from specify_cli import app
        runner = CliRunner()
        project = tmp_path / "proj"
        project.mkdir()
        (project / ".specify").mkdir()
        old = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "upgrade"])
        finally:
            os.chdir(old)
        assert result.exit_code == 0
        assert "No integration is currently installed" in result.output

    def test_upgrade_succeeds(self, tmp_path):
        from typer.testing import CliRunner
        from specify_cli import app
        runner = CliRunner()
        project = self._init_project(tmp_path, "copilot")

        old = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "upgrade"], catch_exceptions=False)
        finally:
            os.chdir(old)
        assert result.exit_code == 0
        assert "upgraded successfully" in result.output

    def test_upgrade_blocks_on_modified_files(self, tmp_path):
        from typer.testing import CliRunner
        from specify_cli import app
        runner = CliRunner()
        project = self._init_project(tmp_path, "copilot")

        # Modify a tracked file so the manifest hash won't match
        manifest_path = project / ".specify" / "integrations" / "copilot.manifest.json"
        assert manifest_path.exists(), "Manifest should exist after init"
        manifest_data = json.loads(manifest_path.read_text())
        tracked_files = manifest_data.get("files", {})
        assert tracked_files, "Manifest should track at least one file"
        first_rel = next(iter(tracked_files))
        target_file = project / first_rel
        assert target_file.exists(), f"Tracked file {first_rel} should exist"
        target_file.write_text("MODIFIED CONTENT\n")

        old = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "upgrade"])
        finally:
            os.chdir(old)
        assert result.exit_code != 0
        assert "modified" in result.output.lower()

    def test_upgrade_force_overwrites_modified(self, tmp_path):
        from typer.testing import CliRunner
        from specify_cli import app
        runner = CliRunner()
        project = self._init_project(tmp_path, "copilot")

        # Modify a tracked file
        manifest_path = project / ".specify" / "integrations" / "copilot.manifest.json"
        manifest_data = json.loads(manifest_path.read_text())
        tracked_files = manifest_data.get("files", {})
        assert tracked_files, "Manifest should track at least one file"
        first_rel = next(iter(tracked_files))
        target_file = project / first_rel
        assert target_file.exists(), f"Tracked file {first_rel} should exist"
        target_file.write_text("MODIFIED CONTENT\n")

        old = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "upgrade", "--force"], catch_exceptions=False)
        finally:
            os.chdir(old)
        assert result.exit_code == 0
        assert "upgraded successfully" in result.output

    def test_upgrade_wrong_integration_key(self, tmp_path):
        from typer.testing import CliRunner
        from specify_cli import app
        runner = CliRunner()
        project = self._init_project(tmp_path, "copilot")

        old = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "upgrade", "claude"])
        finally:
            os.chdir(old)
        assert result.exit_code != 0
        assert "not the currently installed integration" in result.output

    def test_upgrade_no_manifest(self, tmp_path):
        """Upgrade with missing manifest suggests fresh install."""
        from typer.testing import CliRunner
        from specify_cli import app
        runner = CliRunner()
        project = self._init_project(tmp_path, "copilot")

        # Remove manifest
        manifest_path = project / ".specify" / "integrations" / "copilot.manifest.json"
        if manifest_path.exists():
            manifest_path.unlink()

        old = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "upgrade"])
        finally:
            os.chdir(old)
        assert result.exit_code == 0
        assert "Nothing to upgrade" in result.output
