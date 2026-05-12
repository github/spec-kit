import pytest
import yaml
from pathlib import Path
from typer.testing import CliRunner
from specify_cli import app
from specify_cli.extensions import HookExecutor

runner = CliRunner()

@pytest.fixture
def project_dir(tmp_path):
    """Create a mock spec-kit project directory."""
    proj_dir = tmp_path / "project"
    proj_dir.mkdir()
    (proj_dir / ".specify").mkdir()
    # Create required files for a project
    (proj_dir / ".specify" / "config.toml").write_text("ai = 'claude'")
    return proj_dir

def test_extension_update_corrupted_config_root(project_dir, monkeypatch):
    """Regression: extension update must handle corrupted extensions.yml (root is scalar)."""
    # Corrupt extensions.yml
    config_path = project_dir / ".specify" / "extensions.yml"
    config_path.write_text(yaml.dump(123))
    
    # Mock ExtensionManager to return an installed extension for resolution
    from specify_cli.extensions import ExtensionManager, ExtensionCatalog, ExtensionRegistry
    
    def mock_list_installed(self):
        return [{"id": "test-ext", "name": "Test Ext", "version": "1.0.0"}]
    
    def mock_get(self, ext_id):
        return {"version": "1.0.0", "enabled": True}
        
    def mock_get_extension_info(self, ext_id):
        return {"id": "test-ext", "name": "Test Ext", "version": "1.1.0", "download_url": "https://example.com/ext.zip"}

    monkeypatch.setattr(ExtensionManager, "list_installed", mock_list_installed)
    monkeypatch.setattr(ExtensionRegistry, "get", mock_get)
    monkeypatch.setattr(ExtensionCatalog, "get_extension_info", mock_get_extension_info)
    
    # Mock confirmation to true
    monkeypatch.setattr("typer.confirm", lambda _: True)
    
    # Run update
    result = runner.invoke(app, ["extension", "update", "test-ext"], obj={"project_root": project_dir})
    
    # It might fail because of the mock zip, but it should NOT be an AttributeError from config.get()
    assert "AttributeError" not in result.output

def test_extension_update_corrupted_hooks_value(project_dir, monkeypatch):
    """Regression: extension update must handle non-dict 'hooks' in extensions.yml."""
    config_path = project_dir / ".specify" / "extensions.yml"
    config_path.write_text(yaml.dump({
        "installed": ["test-ext"],
        "hooks": ["not", "a", "dict"]
    }))
    
    from specify_cli.extensions import ExtensionManager, ExtensionCatalog, ExtensionRegistry
    
    monkeypatch.setattr(ExtensionManager, "list_installed", lambda self: [{"id": "test-ext", "name": "Test Ext", "version": "1.0.0"}])
    monkeypatch.setattr(ExtensionRegistry, "get", lambda self, ext_id: {"version": "1.0.0", "enabled": True})
    monkeypatch.setattr(ExtensionCatalog, "get_extension_info", lambda self, ext_id: {"id": "test-ext", "name": "Test Ext", "version": "1.1.0", "download_url": "https://example.com/ext.zip"})
    monkeypatch.setattr("typer.confirm", lambda _: True)
    
    result = runner.invoke(app, ["extension", "update", "test-ext"], obj={"project_root": project_dir})
    
    assert "AttributeError" not in result.output

def test_extension_update_rollback_corrupted_config(project_dir, monkeypatch):
    """Regression: extension update rollback must handle corrupted extensions.yml."""
    config_path = project_dir / ".specify" / "extensions.yml"
    config_path.write_text(yaml.dump({"installed": ["test-ext"]}))
    
    from specify_cli.extensions import ExtensionManager, ExtensionCatalog, ExtensionRegistry
    
    # Mock update process to fail after backup
    monkeypatch.setattr(ExtensionManager, "list_installed", lambda self: [{"id": "test-ext", "name": "Test Ext", "version": "1.0.0"}])
    monkeypatch.setattr(ExtensionRegistry, "get", lambda self, ext_id: {"version": "1.0.0", "enabled": True})
    
    # Force failure in download_extension to trigger rollback
    def mock_download_fail(*args, **kwargs):
        # Corrupt the config BEFORE rollback is triggered
        config_path.write_text(yaml.dump("CORRUPTED"))
        raise Exception("Download failed")
        
    monkeypatch.setattr(ExtensionCatalog, "get_extension_info", lambda self, ext_id: {"id": "test-ext", "name": "Test Ext", "version": "1.1.0", "download_url": "https://example.com/ext.zip"})
    monkeypatch.setattr(ExtensionCatalog, "download_extension", mock_download_fail)
    monkeypatch.setattr("typer.confirm", lambda _: True)
    
    result = runner.invoke(app, ["extension", "update", "test-ext"], obj={"project_root": project_dir})
    
    # Should handle Exception and NOT crash with AttributeError during rollback
    assert "Download failed" in result.output
    assert "AttributeError" not in result.output
