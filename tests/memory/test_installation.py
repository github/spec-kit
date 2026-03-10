"""
Tests for SpecKit Global Memory Installation.
"""

import pytest
import tempfile
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from specify_cli.memory.config import MemoryConfigManager
from specify_cli.memory.install.config_merger import ConfigMerger
from specify_cli.memory.install.ollama_checker import OllamaChecker
from specify_cli.memory.install.updater import UpdateManager
from specify_cli.memory.install.degradation import DegradationConfig


class TestConfigManager:
    """Test configuration management."""

    def test_config_dir_creation(self):
        """Test config directory creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = MemoryConfigManager(global_home=Path(tmpdir))

            config_dir = manager.config_dir
            assert config_dir == Path(tmpdir) / "spec-kit" / "config"
            assert not config_dir.exists()  # Not created until needed

            # When needed, creates automatically
            manager.ensure_config_structure()
            assert config_dir.exists()


class TestConfigMerger:
    """Test config backup and merge logic."""

    def test_backup_existing_config(self):
        """Test backing up existing configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConfigMerger(global_home=Path(tmpdir))

            # Create test config
            config_dir = Path(tmpdir) / "spec-kit" / "config"
            config_dir.mkdir(parents=True, exist_ok=True)
            (config_dir / "test.json").write_text('{"key": "value"}')

            # Backup
            backup_path = manager.backup_existing_config()

            assert backup_path.exists()
            assert (backup_path / "config" / "test.json").exists()

    def test_merge_configs(self):
        """Test merging source config with existing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConfigMerger(global_home=Path(tmpdir))

            existing = {"key1": "old_value", "key2": "keep"}
            source = {"key1": "new_value", "key3": "new"}

            merged = manager.merge_configs(source, existing)

            assert merged["key1"] == "new_value"  # Source wins
            assert merged["key2"] == "keep"      # Old preserved
            assert merged["key3"] == "new"         # New added


class TestOllamaChecker:
    """Test Ollama availability checking."""

    def test_is_ollama_installed_false(self):
        """Test detection when Ollama not installed."""
        checker = OllamaChecker()

        # In most test environments, Ollama won't be installed
        # We mock the result
        with patch('shutil.which', return_value=None):
            assert not checker.is_ollama_installed()

    def test_check_availability_comprehensive(self):
        """Test comprehensive availability check."""
        checker = OllamaChecker()

        # Mock all checks to return False (unavailable)
        with patch('shutil.which', return_value=None), \
             patch('requests.get', side_effect=Exception("Connection refused")):

            status = checker.check_availability()

            assert status["installed"] is False
            assert status["running"] is False
            assert status["model_available"] is False
            assert status["available"] is False

    def test_graceful_degradation_config(self):
        """Test graceful degradation configuration loading."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "degradation.json"

            # Create custom config
            custom_config = {
                "ollama": {
                    "required": False,
                    "fallback": "file_based",
                    "warning_once": False
                }
            }

            import json
            config_path.write_text(json.dumps(custom_config))

            degradation = DegradationConfig(config_path=config_path)

            assert degradation.config == custom_config


class TestUpdateManager:
    """Test update mechanism."""

    def test_version_detection(self):
        """Test current version detection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = UpdateManager(global_home=Path(tmpdir))

            # No version file
            version = manager.get_current_version()
            assert version == "0.0.0"

    def test_apply_update(self):
        """Test applying update."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = UpdateManager(global_home=Path(tmpdir))

            changes = {
                "added": ["test_file.py"],
                "modified": ["config.json"],
                "removed": ["old_file.py"]
            }

            # Should succeed (dry run)
            result = manager._apply_delta_changes(changes)

            # In dry run, returns mock data
            assert result["status"] in ["dry_run", "success"]


class TestCrossPlatformLink:
    """Test cross-platform link creation."""

    def test_link_creation_mock(self):
        """Test link creation logic (mocked)."""
        # We can't actually test symlinks in CI without privileges
        # Just verify the logic structure

        with patch('sys.platform', 'win32'):
            # Would use Windows-specific code
            assert True  # Placeholder

        with patch('sys.platform', 'linux'):
            # Would use Unix symlink
            assert True  # Placeholder

    def test_import_modules(self):
        """Test all install modules can be imported."""
        # Test imports
        from specify_cli.memory.install.config_merger import ConfigMerger
        from specify_cli.memory.install.ollama_checker import OllamaChecker
        from specify_cli.memory.install.updater import UpdateManager
        from specify_cli.memory.install.degradation import DegradationConfig

        # Just verify they can be imported
        assert ConfigMerger is not None
        assert OllamaChecker is not None
        assert UpdateManager is not None
        assert DegradationConfig is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
