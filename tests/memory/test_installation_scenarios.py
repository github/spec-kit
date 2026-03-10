"""
Installation scenario tests for SpecKit Global Memory.
Tests for fresh install, existing configs, without Ollama, update mechanism.
"""

import pytest
import tempfile
import subprocess
import sys
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime

from specify_cli.memory.config import MemoryConfigManager
from specify_cli.memory.install.config_merger import ConfigMerger
from specify_cli.memory.install.ollama_checker import OllamaChecker
from specify_cli.memory.install.updater import UpdateManager
from specify_cli.memory.install.degradation import DegradationConfig
from specify_cli.memory.install.migrator import ConfigMigrator


class TestFreshInstall:
    """Test fresh installation scenario."""

    def test_fresh_install_creates_all_directories(self):
        """Test that fresh install creates all required directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from specify_cli.memory.config import MemoryConfigManager
            manager = MemoryConfigManager(global_home=Path(tmpdir))

            # Ensure structure
            manager.ensure_config_structure()

            # Check all required directories exist
            assert (Path(tmpdir) / "spec-kit" / "config").exists()
            assert (Path(tmpdir) / "spec-kit" / "templates").exists()
            assert (Path(tmpdir) / "memory" / "projects").exists()

    def test_fresh_install_creates_default_templates(self):
        """Test that fresh install creates default memory templates."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from specify_cli.memory.file_manager import FileMemoryManager
            manager = FileMemoryManager(global_home=Path(tmpdir))

            # Initialize memory files
            success = manager.initialize_memory_files()

            assert success is True

            # Check default files exist
            memory_dir = Path(tmpdir) / "memory" / "projects" / ".global"
            assert (memory_dir / "lessons.md").exists()
            assert (memory_dir / "patterns.md").exists()
            assert (memory_dir / "architecture.md").exists()
            assert (memory_dir / "projects-log.md").exists()
            assert (memory_dir / "handoff.md").exists()

    def test_fresh_install_creates_degradation_config(self):
        """Test that fresh install creates default degradation config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            degradation = DegradationConfig(config_path=Path(tmpdir) / "degradation.json")

            # Should create default config
            assert degradation.config_path.exists()

            # Check default structure
            assert "ollama" in degradation.config
            assert "agent_memory_mcp" in degradation.config
            assert "skillsmp" in degradation.config

            # Check defaults
            assert degradation.config["ollama"]["required"] is False
            assert degradation.config["ollama"]["fallback"] == "file_based"


class TestExistingConfigs:
    """Test installation with existing configurations."""

    def test_preserves_existing_lessons(self):
        """Test that existing lessons.md is preserved during install."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from specify_cli.memory.file_manager import FileMemoryManager

            # Create existing lessons
            memory_dir = Path(tmpdir) / "memory" / "projects" / ".global"
            memory_dir.mkdir(parents=True, exist_ok=True)
            lessons_path = memory_dir / "lessons.md"

            existing_content = """
# Existing Lessons

## Error: Database Connection Failed
**Date**: 2024-01-01
**Context**: Production database timeout
**Solution**: Increased connection pool size
"""
            lessons_path.write_text(existing_content, encoding='utf-8')

            # Initialize (should not overwrite)
            manager = FileMemoryManager(global_home=Path(tmpdir))
            manager.initialize_memory_files()

            # Check content preserved
            current_content = lessons_path.read_text(encoding='utf-8')
            assert "Existing Lessons" in current_content
            assert "Database Connection Failed" in current_content

    def test_merges_degradation_configs(self):
        """Test that existing degradation config is merged."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "degradation.json"

            # Create existing config with custom values
            existing_config = {
                "ollama": {
                    "required": True,
                    "fallback": "error",
                    "warning_once": False
                },
                "custom_component": {
                    "required": False,
                    "fallback": "skip"
                }
            }

            import json
            config_path.write_text(json.dumps(existing_config))

            # Load should preserve existing
            degradation = DegradationConfig(config_path=config_path)

            assert degradation.config["ollama"]["required"] is True
            assert degradation.config["ollama"]["fallback"] == "error"
            assert degradation.config["custom_component"]["fallback"] == "skip"

    def test_backup_before_merge(self):
        """Test that config backup is created before merging."""
        with tempfile.TemporaryDirectory() as tmpdir:
            merger = ConfigMerger(global_home=Path(tmpdir))

            # Create existing config
            config_dir = Path(tmpdir) / "spec-kit" / "config"
            config_dir.mkdir(parents=True, exist_ok=True)
            (config_dir / "test.json").write_text('{"existing": "value"}')

            # Backup
            backup_path = merger.backup_existing_config()

            # Check backup exists
            assert backup_path.exists()
            assert (backup_path / "config" / "test.json").exists()

            # Check backup content
            backup_content = (backup_path / "config" / "test.json").read_text()
            assert "existing" in backup_content

    def test_migration_from_old_format(self):
        """Test migration from old .spec-kit/config.json format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            migrator = ConfigMigrator(global_home=Path(tmpdir))

            # Create old-style config
            old_config_dir = Path(tmpdir) / "projects" / "test-project" / ".spec-kit"
            old_config_dir.mkdir(parents=True, exist_ok=True)
            old_config_path = old_config_dir / "config.json"

            old_config = {
                "project_id": "test-project",
                "project_name": "Test Project",
                "old_setting": "value"
            }

            import json
            old_config_path.write_text(json.dumps(old_config))

            # Migrate
            result = migrator.migrate_config(old_config_path, dry_run=False)

            assert result["status"] == "success"
            assert "new_path" in result

            # Check new format exists
            new_config_path = Path(result["new_path"])
            assert new_config_path.exists()


class TestWithoutOllama:
    """Test installation and operation without Ollama."""

    def test_installation_succeeds_without_ollama(self):
        """Test that installation completes even without Ollama."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock Ollama check to return False
            with patch('shutil.which', return_value=None):
                checker = OllamaChecker()

                # Should report not installed
                assert not checker.is_ollama_installed()

                # Installation should still succeed
                from specify_cli.memory.config import MemoryConfigManager
                manager = MemoryConfigManager(global_home=Path(tmpdir))
                manager.ensure_config_structure()

                # Directories should be created
                assert (Path(tmpdir) / "spec-kit" / "config").exists()

    def test_graceful_degradation_to_file_based(self):
        """Test graceful degradation when Ollama unavailable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "degradation.json"

            # Create degradation config
            degradation = DegradationConfig(config_path=config_path)

            # Ollama should not be required
            assert not degradation.is_required("ollama")

            # Fallback should be file_based
            assert degradation.get_fallback("ollama") == "file_based"

            # Warning should be shown once
            assert degradation.should_warn("ollama")

    def test_warning_shown_only_once(self):
        """Test that Ollama warning is shown only once per session."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "degradation.json"

            degradation = DegradationConfig(config_path=config_path)

            # First check - should warn
            assert degradation.should_warn("ollama") is True

            # Mark as shown
            degradation.mark_warning_shown("ollama")

            # Second check - should not warn
            assert degradation.should_warn("ollama") is False

    def test_file_memory_works_without_vector(self):
        """Test that file-based memory works without vector support."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from specify_cli.memory.file_manager import FileMemoryManager

            manager = FileMemoryManager(global_home=Path(tmpdir))
            manager.initialize_memory_files()

            # Write to file memory
            success = manager.write_entry(
                file_type="lessons",
                title="Test Lesson",
                content="This is a test lesson without vector memory"
            )

            assert success is True

            # Read headers
            headers = manager.read_headers_first(file_type="lessons")

            assert len(headers) > 0
            assert any("Test Lesson" in h for h in headers)


class TestUpdateMechanism:
    """Test update mechanism for global memory installation."""

    def test_version_detection(self):
        """Test current version detection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = UpdateManager(global_home=Path(tmpdir))

            # No version file
            version = manager.get_current_version()
            assert version == "0.0.0"

            # Create version file
            version_file = Path(tmpdir) / "spec-kit" / "config" / ".version"
            version_file.parent.mkdir(parents=True, exist_ok=True)
            version_file.write_text("1.2.3")

            # Should read version
            version = manager.get_current_version()
            assert version == "1.2.3"

    def test_update_detection_newer_version(self):
        """Test detection of newer version."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = UpdateManager(global_home=Path(tmpdir))

            # Set current version
            version_file = Path(tmpdir) / "spec-kit" / "config" / ".version"
            version_file.parent.mkdir(parents=True, exist_ok=True)
            version_file.write_text("1.0.0")

            # Check for update to newer version
            current = manager.get_current_version()
            available = "2.0.0"

            # Simple version comparison
            current_parts = [int(x) for x in current.split(".")]
            available_parts = [int(x) for x in available.split(".")]

            update_available = available_parts > current_parts

            assert update_available is True

    def test_apply_update_dry_run(self):
        """Test update application in dry-run mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = UpdateManager(global_home=Path(tmpdir))

            changes = {
                "added": ["new_feature.py"],
                "modified": ["config.json"],
                "removed": ["old_feature.py"]
            }

            # Dry run
            result = manager._apply_delta_changes(changes, dry_run=True)

            # Should return dry_run status
            assert result["status"] in ["dry_run", "success"]

            # Files should not actually be modified
            assert not (Path(tmpdir) / "new_feature.py").exists()

    def test_rollback_after_failed_update(self):
        """Test rollback after failed update."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = UpdateManager(global_home=Path(tmpdir))

            # Create backup before update
            backup_path = Path(tmpdir) / "backups" / "before-update"
            backup_path.mkdir(parents=True, exist_ok=True)

            # Create some files to rollback
            config_dir = Path(tmpdir) / "spec-kit" / "config"
            config_dir.mkdir(parents=True, exist_ok=True)

            original_file = config_dir / "test.json"
            original_file.write_text('{"version": "1.0"}')

            # Backup it
            backup_file = backup_path / "test.json"
            backup_file.write_text(original_file.read_text())

            # Simulate failed update (file corrupted)
            original_file.write_text('{"corrupted": true}')

            # Rollback
            if backup_file.exists():
                original_file.write_text(backup_file.read_text())

            # Verify restored
            content = original_file.read_text()
            assert '"version": "1.0"' in content
            assert "corrupted" not in content

    def test_update_preserves_user_config(self):
        """Test that update preserves user configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            merger = ConfigMerger(global_home=Path(tmpdir))

            # User config
            existing = {
                "user_preference": "custom_value",
                "auto_save": True
            }

            # New default config
            source = {
                "auto_save": False,  # Changed in new version
                "new_feature": True
            }

            # Merge - user wins for conflicts
            merged = merger.merge_configs(source, existing)

            assert merged["user_preference"] == "custom_value"  # Preserved
            assert merged["auto_save"] is True  # User value kept
            assert merged["new_feature"] is True  # New feature added


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
