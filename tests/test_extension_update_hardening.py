import pytest
import yaml
from typer.testing import CliRunner
from specify_cli import app

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
    # chdir into project_dir so _require_specify_project() succeeds
    monkeypatch.chdir(project_dir)
    
    # Corrupt extensions.yml
    config_path = project_dir / ".specify" / "extensions.yml"
    config_path.write_text(yaml.dump(123))
    
    # Mock ExtensionManager to return an installed extension for resolution
    from specify_cli.extensions import ExtensionManager, ExtensionCatalog, ExtensionRegistry
    
    monkeypatch.setattr(ExtensionManager, "list_installed", lambda self: [{"id": "test-ext", "name": "Test Ext", "version": "1.0.0"}])
    monkeypatch.setattr(ExtensionRegistry, "get", lambda self, ext_id: {"version": "1.0.0", "enabled": True})
    monkeypatch.setattr(ExtensionCatalog, "get_extension_info", lambda self, ext_id: {"id": "test-ext", "name": "Test Ext", "version": "1.1.0", "download_url": "https://example.com/ext.zip"})
    
    # Mock download_extension to avoid network calls; use tmp_path so the test is hermetic
    # and returns a Path so zip_path.exists() / zip_path.unlink() work without AttributeError
    mock_zip = project_dir / "mock.zip"
    monkeypatch.setattr(ExtensionCatalog, "download_extension", lambda self, ext_id: mock_zip)
    
    # Mock confirmation to true
    monkeypatch.setattr("typer.confirm", lambda _: True)
    
    # Run update
    result = runner.invoke(app, ["extension", "update", "test-ext"], obj={"project_root": project_dir})
    
    # It might fail because of the mock zip, but must NOT raise AttributeError from config handling
    assert not isinstance(result.exception, AttributeError)

def test_extension_update_corrupted_hooks_value(project_dir, monkeypatch):
    """Regression: extension update must handle non-dict 'hooks' in extensions.yml."""
    monkeypatch.chdir(project_dir)
    
    config_path = project_dir / ".specify" / "extensions.yml"
    config_path.write_text(yaml.dump({
        "installed": ["test-ext"],
        "hooks": ["not", "a", "dict"]
    }))
    
    from specify_cli.extensions import ExtensionManager, ExtensionCatalog, ExtensionRegistry
    
    monkeypatch.setattr(ExtensionManager, "list_installed", lambda self: [{"id": "test-ext", "name": "Test Ext", "version": "1.0.0"}])
    monkeypatch.setattr(ExtensionRegistry, "get", lambda self, ext_id: {"version": "1.0.0", "enabled": True})
    monkeypatch.setattr(ExtensionCatalog, "get_extension_info", lambda self, ext_id: {"id": "test-ext", "name": "Test Ext", "version": "1.1.0", "download_url": "https://example.com/ext.zip"})
    # Use tmp_path-scoped zip so the test is hermetic and returns a Path for zip_path.exists()
    mock_zip = project_dir / "mock.zip"
    monkeypatch.setattr(ExtensionCatalog, "download_extension", lambda self, ext_id: mock_zip)
    monkeypatch.setattr("typer.confirm", lambda _: True)
    
    result = runner.invoke(app, ["extension", "update", "test-ext"], obj={"project_root": project_dir})
    
    assert not isinstance(result.exception, AttributeError)

def test_extension_update_rollback_corrupted_config(project_dir, monkeypatch):
    """Regression: extension update rollback must handle corrupted extensions.yml."""
    monkeypatch.chdir(project_dir)
    
    config_path = project_dir / ".specify" / "extensions.yml"
    # hooks: null should be preserved even after a failed update attempt
    config_path.write_text(yaml.dump({"installed": ["test-ext"], "hooks": None}))
    
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
    assert not isinstance(result.exception, AttributeError)
    
    # Verify hooks key was preserved (normalized to {} if it was null/corrupted)
    restored_config = yaml.safe_load(config_path.read_text())
    assert isinstance(restored_config, dict)
    assert "hooks" in restored_config
    assert restored_config["hooks"] == {}
