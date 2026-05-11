import pytest
import yaml
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

    def test_unregister_hooks_full_workflow(self, project_dir, tmp_path):
        """Full Workflow: unregister_hooks should remove hooks and prune installed list."""
        # Create a manifest with hooks
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
        
        # Register hooks first
        executor.register_hooks(manifest)
        
        config = executor.get_project_config()
        assert "hook-ext" in config["installed"]
        assert "after_tasks" in config["hooks"]
        
        # Now unregister hooks
        executor.unregister_hooks("hook-ext")
        
        config = executor.get_project_config()
        assert "hook-ext" not in config["installed"]
        # Hook entry should be removed from hooks dict
        if "after_tasks" in config["hooks"]:
            assert len(config["hooks"]["after_tasks"]) == 0

    def test_unregister_hooks_no_hooks_key(self, project_dir):
        """Resilience: unregister_hooks should work even if config has no 'hooks' key."""
        executor = HookExecutor(project_dir)
        
        # Register extension without hooks
        executor.register_extension("ext-no-hooks")
        
        config = executor.get_project_config()
        assert "ext-no-hooks" in config["installed"]
        
        # Unregister should not crash even if no hooks key exists
        executor.unregister_hooks("ext-no-hooks")
        
        config = executor.get_project_config()
        assert "ext-no-hooks" not in config["installed"]

    def test_unregister_hooks_corrupted_config(self, project_dir):
        """Resilience: unregister_hooks should gracefully handle corrupted config."""
        # Create a corrupted config (root is a list)
        config_path = project_dir / ".specify" / "extensions.yml"
        config_path.write_text(yaml.dump(["corrupted", "list"]))
        
        executor = HookExecutor(project_dir)
        
        # Should not raise even with corrupted config
        executor.unregister_hooks("non-existent")
        
        # Config should remain as-is or be handled gracefully
        config = executor.get_project_config()
        # If it's corrupted, it's returned as-is or handled by defensive logic
        assert config is not None

    def test_unregister_hooks_with_multiple_extensions(self, project_dir, tmp_path):
        """Multiple Extensions: unregister_hooks should only remove target extension's hooks."""
        # Create two manifests
        manifest_data_1 = {
            "schema_version": "1.0",
            "extension": {
                "id": "ext-1",
                "name": "Ext 1",
                "version": "1.0.0",
                "description": "Test 1",
            },
            "requires": {
                "speckit_version": ">=0.1.0",
                "commands": []
            },
            "provides": {"commands": []},
            "hooks": {
                "after_tasks": {"command": "speckit.ext-1.run"}
            }
        }
        manifest_data_2 = {
            "schema_version": "1.0",
            "extension": {
                "id": "ext-2",
                "name": "Ext 2",
                "version": "1.0.0",
                "description": "Test 2",
            },
            "requires": {
                "speckit_version": ">=0.1.0",
                "commands": []
            },
            "provides": {"commands": []},
            "hooks": {
                "after_tasks": {"command": "speckit.ext-2.run"}
            }
        }
        
        manifest_path_1 = tmp_path / "extension1.yml"
        manifest_path_2 = tmp_path / "extension2.yml"
        with open(manifest_path_1, "w") as f:
            yaml.dump(manifest_data_1, f)
        with open(manifest_path_2, "w") as f:
            yaml.dump(manifest_data_2, f)
        
        manifest1 = ExtensionManifest(manifest_path_1)
        manifest2 = ExtensionManifest(manifest_path_2)
        executor = HookExecutor(project_dir)
        
        # Register both extensions
        executor.register_hooks(manifest1)
        executor.register_hooks(manifest2)
        
        config = executor.get_project_config()
        assert "ext-1" in config["installed"]
        assert "ext-2" in config["installed"]
        assert len(config["hooks"]["after_tasks"]) == 2
        
        # Unregister first extension
        executor.unregister_hooks("ext-1")
        
        config = executor.get_project_config()
        assert "ext-1" not in config["installed"]
        assert "ext-2" in config["installed"]
        # ext-2's hook should still be there
        assert len(config["hooks"]["after_tasks"]) == 1
        assert config["hooks"]["after_tasks"][0].get("extension") == "ext-2"

    def test_register_hooks_no_hooks_still_registers(self, project_dir, tmp_path):
        """Commands-only manifest: register_hooks() must still update installed even with no hooks."""
        manifest_data = {
            "schema_version": "1.0",
            "extension": {
                "id": "commands-only-ext",
                "name": "Commands Only",
                "version": "1.0.0",
                "description": "No hooks, only commands",
            },
            "requires": {
                "speckit_version": ">=0.1.0",
                "commands": []
            },
            "provides": {"commands": [{"name": "speckit.commands-only-ext.run", "file": "commands/run.md"}]},
        }
        manifest_path = tmp_path / "extension.yml"
        with open(manifest_path, "w") as f:
            yaml.dump(manifest_data, f)

        manifest = ExtensionManifest(manifest_path)
        executor = HookExecutor(project_dir)
        executor.register_hooks(manifest)

        config = executor.get_project_config()
        assert "commands-only-ext" in config["installed"]

    def test_register_extension_mixed_type_installed(self, project_dir):
        """Regression: installed list with non-string entries must not crash on sort."""
        executor = HookExecutor(project_dir)

        # Manually write a corrupted installed list with non-string entries
        config_path = project_dir / ".specify" / "extensions.yml"
        config_path.write_text(yaml.dump({"installed": [1, True, "existing-ext"]}))

        # Should not raise TypeError on sort
        executor.register_extension("new-ext")

        config = executor.get_project_config()
        # Non-string entries are dropped; valid strings are preserved
        assert "existing-ext" in config["installed"]
        assert "new-ext" in config["installed"]
        assert 1 not in config["installed"]
        assert True not in config["installed"]

    def test_unregister_hooks_null_hook_values(self, project_dir):
        """Regression: hooks: {after_tasks: null} must not crash in unregister_hooks()."""
        executor = HookExecutor(project_dir)

        # Manually write a config with null hook event value
        config_path = project_dir / ".specify" / "extensions.yml"
        config_path.write_text(yaml.dump({
            "installed": ["broken-ext"],
            "hooks": {"after_tasks": None}
        }))

        # Should not raise TypeError when iterating None
        executor.unregister_hooks("broken-ext")

        config = executor.get_project_config()
        assert "broken-ext" not in config["installed"]

    def test_register_hooks_corrupted_hook_values(self, project_dir, tmp_path):
        """Regression: register_hooks() must handle non-list hook event values in config."""
        executor = HookExecutor(project_dir)

        # Manually write a config with null hook event value
        config_path = project_dir / ".specify" / "extensions.yml"
        config_path.write_text(yaml.dump({
            "installed": ["some-ext"],
            "hooks": {"after_tasks": None}
        }))

        # Create a manifest with a hook for the same event
        manifest_data = {
            "schema_version": "1.0",
            "extension": {
                "id": "new-ext",
                "name": "New Ext",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {
                "speckit_version": ">=0.1.0",
                "commands": []
            },
            "provides": {"commands": []},
            "hooks": {"after_tasks": {"command": "speckit.new-ext.run"}}
        }
        manifest_path = tmp_path / "extension.yml"
        with open(manifest_path, "w") as f:
            yaml.dump(manifest_data, f)
        
        manifest = ExtensionManifest(manifest_path)
        
        # Should not raise TypeError when trying to append to None
        executor.register_hooks(manifest)

        config = executor.get_project_config()
        assert "new-ext" in config["installed"]
        assert isinstance(config["hooks"]["after_tasks"], list)
        assert any(h["extension"] == "new-ext" for h in config["hooks"]["after_tasks"])

    def test_register_extension_already_present_in_corrupted_list(self, project_dir):
        """Regression: if extension is already present but list has non-strings, it must still be sanitized."""
        executor = HookExecutor(project_dir)

        # Extension is present, but list has garbage
        config_path = project_dir / ".specify" / "extensions.yml"
        config_path.write_text(yaml.dump({"installed": [1, "test-ext", True]}))

        # This should trigger sanitization and save, even though "test-ext" is already there
        executor.register_extension("test-ext")

        config = executor.get_project_config()
        assert config["installed"] == ["test-ext"]
        # Verify it was actually saved to disk
        raw_config = yaml.safe_load(config_path.read_text())
        assert raw_config["installed"] == ["test-ext"]

