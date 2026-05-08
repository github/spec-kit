import pytest
import yaml
from pathlib import Path
from specify_cli.extensions import HookExecutor, ExtensionManifest

@pytest.fixture
def project_dir(tmp_path):
    """Create a mock spec-kit project directory."""
    proj_dir = tmp_path / "project"
    proj_dir.mkdir()
    (proj_dir / ".specify").mkdir()
    return proj_dir

class TestExtensionRegistration:
    """Tests for the 'installed' list management in HookExecutor."""

    def test_register_extension_new(self, project_dir):
        """Standard registration: Adding an extension should add it to the list."""
        executor = HookExecutor(project_dir)
        executor.register_extension("test-ext")
        
        config = executor.get_project_config()
        assert "installed" in config
        assert config["installed"] == ["test-ext"]

    def test_register_extension_sorting(self, project_dir):
        """Order Stability: Extensions should be stored in alphabetical order."""
        executor = HookExecutor(project_dir)
        executor.register_extension("zebra-ext")
        executor.register_extension("apple-ext")
        executor.register_extension("middle-ext")
        
        config = executor.get_project_config()
        assert config["installed"] == ["apple-ext", "middle-ext", "zebra-ext"]

    def test_register_extension_idempotency(self, project_dir):
        """Idempotency: Adding the same extension twice should not result in duplicates."""
        executor = HookExecutor(project_dir)
        executor.register_extension("test-ext")
        executor.register_extension("test-ext")
        
        config = executor.get_project_config()
        assert config["installed"] == ["test-ext"]
        assert len(config["installed"]) == 1

    def test_unregister_extension(self, project_dir):
        """Standard unregistration: Removing an extension should prune it from the list."""
        executor = HookExecutor(project_dir)
        executor.register_extension("ext-1")
        executor.register_extension("ext-2")
        
        executor.unregister_extension("ext-1")
        
        config = executor.get_project_config()
        assert config["installed"] == ["ext-2"]

    def test_unregister_extension_not_present(self, project_dir):
        """Safe Removal: Unregistering a non-existent extension should do nothing."""
        executor = HookExecutor(project_dir)
        executor.register_extension("ext-1")
        
        # Should not raise or change the list
        executor.unregister_extension("ext-nonexistent")
        
        config = executor.get_project_config()
        assert config["installed"] == ["ext-1"]

    def test_register_hooks_triggers_registration(self, project_dir, tmp_path):
        """Full Workflow: register_hooks should automatically register the extension."""
        # Create a mock manifest
        manifest_data = {
            "schema_version": "1.0",
            "extension": {
                "id": "hook-ext",
                "name": "Hook Ext",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {
                "speckit_version": ">=0.1.0",
                "commands": []
            },
            "provides": {"commands": []},
            "hooks": {
                "after_tasks": {"command": "speckit.hook-ext.run"}
            }
        }
        manifest_path = tmp_path / "extension.yml"
        with open(manifest_path, "w") as f:
            yaml.dump(manifest_data, f)
        
        manifest = ExtensionManifest(manifest_path)
        executor = HookExecutor(project_dir)
        
        # This should call register_extension internally
        executor.register_hooks(manifest)
        
        config = executor.get_project_config()
        assert "hook-ext" in config["installed"]

    def test_missing_installed_key_initialization(self, project_dir):
        """Graceful Initialization: If 'installed' key is missing, it should be created."""
        executor = HookExecutor(project_dir)
        
        # Manually create a config without 'installed'
        config_path = project_dir / ".specify" / "extensions.yml"
        config_path.write_text(yaml.dump({"settings": {"auto_execute_hooks": True}}))
        
        # This should detect the missing key and initialize it
        executor.register_extension("new-ext")
        
        config = executor.get_project_config()
        assert "installed" in config
        assert config["installed"] == ["new-ext"]
