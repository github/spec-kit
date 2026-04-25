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
    IntegrationValidationError,
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
        """Patch urllib.request.urlopen to return *catalog_data*."""

        class FakeResponse:
            def __init__(self, data, url=""):
                self._data = json.dumps(data).encode()
                self._url = url

            def read(self):
                return self._data

            def geturl(self):
                return self._url

            def __enter__(self):
                return self

            def __exit__(self, *a):
                pass

        def fake_urlopen(url, timeout=10):
            return FakeResponse(catalog_data, url)

        import urllib.request
        monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

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

        import urllib.request

        class FakeResponse:
            def __init__(self, data, url=""):
                self._data = json.dumps(data).encode()
                self._url = url
            def read(self):
                return self._data
            def geturl(self):
                return self._url
            def __enter__(self):
                return self
            def __exit__(self, *a):
                pass

        monkeypatch.setattr(urllib.request, "urlopen", lambda url, timeout=10: FakeResponse(catalog, url))

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


# ---------------------------------------------------------------------------
# IntegrationCatalog — catalog source management (get_catalog_configs / add / remove)
# ---------------------------------------------------------------------------


class TestCatalogSourceManagement:
    """Unit tests for add_catalog / remove_catalog / get_catalog_configs."""

    def _isolate(self, tmp_path, monkeypatch):
        """Point HOME at tmp_path and clear the env override so we read built-ins."""
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("USERPROFILE", str(tmp_path))
        monkeypatch.delenv("SPECKIT_INTEGRATION_CATALOG_URL", raising=False)
        (tmp_path / ".specify").mkdir()

    def test_get_catalog_configs_returns_builtin_stack(self, tmp_path, monkeypatch):
        self._isolate(tmp_path, monkeypatch)
        cat = IntegrationCatalog(tmp_path)
        configs = cat.get_catalog_configs()
        assert [c["name"] for c in configs] == ["default", "community"]
        assert all(isinstance(c["url"], str) and c["url"] for c in configs)
        assert configs[0]["install_allowed"] is True
        assert configs[1]["install_allowed"] is False

    def test_add_catalog_creates_config_file(self, tmp_path, monkeypatch):
        self._isolate(tmp_path, monkeypatch)
        cat = IntegrationCatalog(tmp_path)
        cat.add_catalog("https://new.example.com/catalog.json", name="mine")

        cfg_path = tmp_path / ".specify" / "integration-catalogs.yml"
        assert cfg_path.exists()
        data = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
        assert data["catalogs"] == [
            {
                "name": "mine",
                "url": "https://new.example.com/catalog.json",
                "priority": 1,
                "install_allowed": True,
                "description": "",
            }
        ]
        # Round-trip: active catalogs should now come from the config file.
        active = cat.get_active_catalogs()
        assert [e.name for e in active] == ["mine"]

    def test_add_catalog_auto_derives_name_and_priority(self, tmp_path, monkeypatch):
        self._isolate(tmp_path, monkeypatch)
        cat = IntegrationCatalog(tmp_path)
        cat.add_catalog("https://a.example.com/catalog.json")
        cat.add_catalog("https://b.example.com/catalog.json")

        data = yaml.safe_load(
            (tmp_path / ".specify" / "integration-catalogs.yml").read_text(encoding="utf-8")
        )
        entries = data["catalogs"]
        assert [e["name"] for e in entries] == ["catalog-1", "catalog-2"]
        assert [e["priority"] for e in entries] == [1, 2]

    def test_add_catalog_rejects_duplicate_url(self, tmp_path, monkeypatch):
        self._isolate(tmp_path, monkeypatch)
        cat = IntegrationCatalog(tmp_path)
        cat.add_catalog("https://dup.example.com/catalog.json")
        with pytest.raises(IntegrationValidationError, match="already configured"):
            cat.add_catalog("https://dup.example.com/catalog.json")

    def test_add_catalog_rejects_invalid_url(self, tmp_path, monkeypatch):
        self._isolate(tmp_path, monkeypatch)
        cat = IntegrationCatalog(tmp_path)
        with pytest.raises(IntegrationCatalogError, match="HTTPS"):
            cat.add_catalog("http://insecure.example.com/catalog.json")
        assert not (tmp_path / ".specify" / "integration-catalogs.yml").exists()

    def test_remove_catalog_without_config_errors(self, tmp_path, monkeypatch):
        self._isolate(tmp_path, monkeypatch)
        cat = IntegrationCatalog(tmp_path)
        with pytest.raises(IntegrationValidationError, match="No catalog config"):
            cat.remove_catalog(0)

    def test_remove_catalog_happy_path(self, tmp_path, monkeypatch):
        self._isolate(tmp_path, monkeypatch)
        cat = IntegrationCatalog(tmp_path)
        cat.add_catalog("https://a.example.com/catalog.json", name="a")
        cat.add_catalog("https://b.example.com/catalog.json", name="b")

        removed = cat.remove_catalog(0)
        assert removed == "a"

        data = yaml.safe_load(
            (tmp_path / ".specify" / "integration-catalogs.yml").read_text(encoding="utf-8")
        )
        assert [e["name"] for e in data["catalogs"]] == ["b"]

    def test_remove_catalog_index_out_of_range(self, tmp_path, monkeypatch):
        self._isolate(tmp_path, monkeypatch)
        cat = IntegrationCatalog(tmp_path)
        cat.add_catalog("https://a.example.com/catalog.json", name="a")
        with pytest.raises(IntegrationValidationError, match="out of range"):
            cat.remove_catalog(5)
        with pytest.raises(IntegrationValidationError, match="out of range"):
            cat.remove_catalog(-1)

    def test_corrupt_config_rejected_on_add(self, tmp_path, monkeypatch):
        self._isolate(tmp_path, monkeypatch)
        cfg_path = tmp_path / ".specify" / "integration-catalogs.yml"
        cfg_path.write_text("- just\n- a\n- list\n", encoding="utf-8")
        cat = IntegrationCatalog(tmp_path)
        with pytest.raises(IntegrationValidationError, match="corrupted"):
            cat.add_catalog("https://new.example.com/catalog.json")

    def test_add_catalog_rejects_corrupt_sibling_entry(self, tmp_path, monkeypatch):
        """add_catalog must fail fast if an existing entry is structurally invalid."""
        self._isolate(tmp_path, monkeypatch)
        cfg_path = tmp_path / ".specify" / "integration-catalogs.yml"
        cfg_path.write_text(
            yaml.dump({"catalogs": [{"url": "", "name": "broken"}]}),
            encoding="utf-8",
        )
        cat = IntegrationCatalog(tmp_path)
        with pytest.raises(IntegrationValidationError, match="non-empty string"):
            cat.add_catalog("https://new.example.com/catalog.json")

    def test_add_catalog_rejects_non_integer_priority(self, tmp_path, monkeypatch):
        self._isolate(tmp_path, monkeypatch)
        cfg_path = tmp_path / ".specify" / "integration-catalogs.yml"
        cfg_path.write_text(
            yaml.dump(
                {
                    "catalogs": [
                        {
                            "url": "https://a.example.com/catalog.json",
                            "name": "a",
                            "priority": "first",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        cat = IntegrationCatalog(tmp_path)
        with pytest.raises(IntegrationValidationError, match="'priority' must be an integer"):
            cat.add_catalog("https://b.example.com/catalog.json")

    def test_add_catalog_rejects_existing_entry_with_bad_url(self, tmp_path, monkeypatch):
        """A sibling entry with an http:// URL should block a new add."""
        self._isolate(tmp_path, monkeypatch)
        cfg_path = tmp_path / ".specify" / "integration-catalogs.yml"
        cfg_path.write_text(
            yaml.dump(
                {
                    "catalogs": [
                        {
                            "url": "http://insecure.example.com/catalog.json",
                            "name": "bad",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        cat = IntegrationCatalog(tmp_path)
        with pytest.raises(IntegrationCatalogError, match="HTTPS"):
            cat.add_catalog("https://good.example.com/catalog.json")

    def test_add_catalog_wraps_yaml_parse_errors(self, tmp_path, monkeypatch):
        """Invalid YAML on disk surfaces as IntegrationValidationError, not a raw YAMLError."""
        self._isolate(tmp_path, monkeypatch)
        cfg_path = tmp_path / ".specify" / "integration-catalogs.yml"
        cfg_path.write_text(
            "catalogs:\n  - url: 'https://a.example.com/cat.json'\n  - [bad\n",
            encoding="utf-8",
        )
        cat = IntegrationCatalog(tmp_path)
        with pytest.raises(
            IntegrationValidationError, match="Failed to read catalog config"
        ):
            cat.add_catalog("https://b.example.com/catalog.json")

    def test_remove_catalog_wraps_yaml_parse_errors(self, tmp_path, monkeypatch):
        """Invalid YAML on disk surfaces as IntegrationValidationError from remove_catalog too."""
        self._isolate(tmp_path, monkeypatch)
        cfg_path = tmp_path / ".specify" / "integration-catalogs.yml"
        cfg_path.write_text(
            "catalogs:\n  - url: 'https://a.example.com/cat.json'\n  - [bad\n",
            encoding="utf-8",
        )
        cat = IntegrationCatalog(tmp_path)
        with pytest.raises(
            IntegrationValidationError, match="Failed to read catalog config"
        ):
            cat.remove_catalog(0)

    def test_add_catalog_defaults_missing_priority_to_index_plus_one(
        self, tmp_path, monkeypatch
    ):
        """Existing entries without `priority` should be treated as idx + 1.

        Matches the rule in `_load_catalog_config()`: a valid catalog entry
        without an explicit `priority` sorts at `idx + 1`, so the new entry
        should get `max(...) + 1` from those derived values.
        """
        self._isolate(tmp_path, monkeypatch)
        cfg_path = tmp_path / ".specify" / "integration-catalogs.yml"
        cfg_path.write_text(
            yaml.dump(
                {
                    "catalogs": [
                        # No explicit priority → should be treated as 1
                        {"url": "https://a.example.com/cat.json", "name": "a"},
                        # No explicit priority → should be treated as 2
                        {"url": "https://b.example.com/cat.json", "name": "b"},
                    ]
                }
            ),
            encoding="utf-8",
        )
        cat = IntegrationCatalog(tmp_path)
        cat.add_catalog("https://c.example.com/cat.json", name="c")

        data = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
        new_entry = data["catalogs"][-1]
        assert new_entry["name"] == "c"
        # max(implicit [1, 2]) + 1 == 3
        assert new_entry["priority"] == 3

    def test_add_catalog_strips_whitespace_in_url(self, tmp_path, monkeypatch):
        """Whitespace around the incoming URL should be normalized before write."""
        self._isolate(tmp_path, monkeypatch)
        cat = IntegrationCatalog(tmp_path)
        cat.add_catalog("  https://a.example.com/catalog.json\n", name="a")

        cfg_path = tmp_path / ".specify" / "integration-catalogs.yml"
        data = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
        assert data["catalogs"][0]["url"] == "https://a.example.com/catalog.json"

    def test_add_catalog_rejects_whitespace_only_duplicate(self, tmp_path, monkeypatch):
        """A second add with only whitespace differences must be rejected as a duplicate."""
        self._isolate(tmp_path, monkeypatch)
        cat = IntegrationCatalog(tmp_path)
        cat.add_catalog("https://a.example.com/catalog.json", name="a")
        with pytest.raises(IntegrationValidationError, match="already configured"):
            cat.add_catalog("  https://a.example.com/catalog.json  ")

    def test_remove_catalog_wraps_unlink_oserror(self, tmp_path, monkeypatch):
        """An OSError from `Path.unlink` surfaces as IntegrationValidationError."""
        self._isolate(tmp_path, monkeypatch)
        cat = IntegrationCatalog(tmp_path)
        cat.add_catalog("https://only.example.com/catalog.json", name="only")

        from pathlib import Path as _Path

        def boom(self, *args, **kwargs):
            raise OSError("simulated unlink failure")

        monkeypatch.setattr(_Path, "unlink", boom)

        with pytest.raises(
            IntegrationValidationError, match="Failed to delete catalog config"
        ):
            cat.remove_catalog(0)

    def test_remove_catalog_empty_list_gives_clear_error(self, tmp_path, monkeypatch):
        """Hand-edited empty `catalogs:` produces a clear error, not '0--1'."""
        self._isolate(tmp_path, monkeypatch)
        cfg_path = tmp_path / ".specify" / "integration-catalogs.yml"
        cfg_path.write_text(yaml.dump({"catalogs": []}), encoding="utf-8")
        cat = IntegrationCatalog(tmp_path)
        with pytest.raises(
            IntegrationValidationError, match="contains no catalog entries"
        ):
            cat.remove_catalog(0)

    def test_remove_last_catalog_deletes_file_and_restores_defaults(
        self, tmp_path, monkeypatch
    ):
        """Removing the final catalog must not leave behind `catalogs: []`.

        `_load_catalog_config` treats an empty `catalogs` list as an error,
        so writing that file would break every subsequent `integration`
        command. Removing the last entry should delete the config file so the
        project falls back to built-in defaults.
        """
        self._isolate(tmp_path, monkeypatch)
        cat = IntegrationCatalog(tmp_path)
        cfg_path = tmp_path / ".specify" / "integration-catalogs.yml"

        cat.add_catalog("https://only.example.com/catalog.json", name="only")
        assert cfg_path.exists()
        assert [e.name for e in cat.get_active_catalogs()] == ["only"]

        removed = cat.remove_catalog(0)
        assert removed == "only"

        assert not cfg_path.exists(), (
            "remove_catalog should delete the config file when emptying it"
        )
        # Follow-up loads fall back to built-in defaults, not an error.
        active = cat.get_active_catalogs()
        assert [e.name for e in active] == ["default", "community"]

    def test_load_catalog_config_raises_validation_error_for_invalid_yaml(
        self, tmp_path, monkeypatch
    ):
        """Local-config problems must surface as IntegrationValidationError so
        CLI handlers can route them to local-config (not network) guidance."""
        self._isolate(tmp_path, monkeypatch)
        cfg_path = tmp_path / ".specify" / "integration-catalogs.yml"
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        cfg_path.write_text("catalogs:\n  - [bad\n", encoding="utf-8")

        cat = IntegrationCatalog(tmp_path)
        # Subclass match: IntegrationValidationError (specifically), not the
        # bare IntegrationCatalogError parent that callers used previously.
        with pytest.raises(IntegrationValidationError, match="Failed to read catalog config"):
            cat.get_active_catalogs()

    def test_load_catalog_config_rejects_boolean_priority(self, tmp_path, monkeypatch):
        self._isolate(tmp_path, monkeypatch)
        cfg_path = tmp_path / ".specify" / "integration-catalogs.yml"
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        cfg_path.write_text(
            yaml.dump(
                {
                    "catalogs": [
                        {
                            "url": "https://a.example.com/catalog.json",
                            "name": "a",
                            "priority": True,
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

        cat = IntegrationCatalog(tmp_path)
        with pytest.raises(IntegrationValidationError, match="Invalid priority|expected integer"):
            cat.get_active_catalogs()

    def test_remove_catalog_uses_display_order_with_explicit_priorities(
        self, tmp_path, monkeypatch
    ):
        """`remove_catalog(index)` must remove the entry shown at that index by
        `catalog list`, not the entry at that raw YAML position."""
        self._isolate(tmp_path, monkeypatch)
        # YAML order: alpha (priority=20), beta (priority=10), gamma (priority=15).
        # Display (sorted by priority asc): beta (10), gamma (15), alpha (20).
        cfg_path = tmp_path / ".specify" / "integration-catalogs.yml"
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        cfg_path.write_text(
            yaml.dump(
                {
                    "catalogs": [
                        {"url": "https://alpha.example.com/c.json", "name": "alpha", "priority": 20},
                        {"url": "https://beta.example.com/c.json", "name": "beta", "priority": 10},
                        {"url": "https://gamma.example.com/c.json", "name": "gamma", "priority": 15},
                    ]
                }
            ),
            encoding="utf-8",
        )
        cat = IntegrationCatalog(tmp_path)

        # Display index 0 = beta (lowest priority), not alpha (raw YAML idx 0).
        removed = cat.remove_catalog(0)
        assert removed == "beta"

        data = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
        remaining_names = [c["name"] for c in data["catalogs"]]
        # YAML order is preserved for the survivors; only beta is gone.
        assert remaining_names == ["alpha", "gamma"]

    def test_remove_catalog_display_order_with_missing_priorities(
        self, tmp_path, monkeypatch
    ):
        """Entries without `priority` default to `idx + 1` (matching
        `_load_catalog_config`), so display order tracks YAML order and the
        first display entry is the first YAML entry."""
        self._isolate(tmp_path, monkeypatch)
        cfg_path = tmp_path / ".specify" / "integration-catalogs.yml"
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        cfg_path.write_text(
            yaml.dump(
                {
                    "catalogs": [
                        {"url": "https://one.example.com/c.json", "name": "one"},
                        {"url": "https://two.example.com/c.json", "name": "two"},
                        {"url": "https://three.example.com/c.json", "name": "three"},
                    ]
                }
            ),
            encoding="utf-8",
        )
        cat = IntegrationCatalog(tmp_path)

        # Implicit priorities: one=1, two=2, three=3 → display order matches YAML.
        removed = cat.remove_catalog(0)
        assert removed == "one"

        data = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
        assert [c["name"] for c in data["catalogs"]] == ["two", "three"]

    def test_remove_catalog_display_order_mixes_explicit_and_default(
        self, tmp_path, monkeypatch
    ):
        """An explicit low priority should sort ahead of default-priority
        siblings, even if it appears later in the YAML."""
        self._isolate(tmp_path, monkeypatch)
        cfg_path = tmp_path / ".specify" / "integration-catalogs.yml"
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        # Defaults: a=1, b=2 (implicit). Explicit c=0 → display: c, a, b.
        cfg_path.write_text(
            yaml.dump(
                {
                    "catalogs": [
                        {"url": "https://a.example.com/c.json", "name": "a"},
                        {"url": "https://b.example.com/c.json", "name": "b"},
                        {"url": "https://c.example.com/c.json", "name": "c", "priority": 0},
                    ]
                }
            ),
            encoding="utf-8",
        )
        cat = IntegrationCatalog(tmp_path)

        removed = cat.remove_catalog(0)
        assert removed == "c"

        data = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
        assert [c["name"] for c in data["catalogs"]] == ["a", "b"]
