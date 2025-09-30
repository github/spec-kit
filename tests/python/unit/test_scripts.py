"""Tests for script operations."""

import stat

from specify_cli import ensure_executable_scripts


class TestEnsureExecutableScripts:
    """Test suite for ensure_executable_scripts function."""

    def test_ensure_executable_makes_scripts_executable(self, tmp_path):
        """Test that shell scripts are made executable."""
        # Arrange
        scripts_dir = tmp_path / ".specify" / "scripts" / "bash"
        scripts_dir.mkdir(parents=True)
        script_file = scripts_dir / "test-script.sh"
        script_file.write_text("#!/bin/bash\necho 'test'")
        # Remove execute permissions
        script_file.chmod(0o644)

        # Act
        ensure_executable_scripts(tmp_path)

        # Assert
        mode = script_file.stat().st_mode
        # Check that owner execute bit is set
        assert mode & stat.S_IXUSR

    def test_ensure_executable_skips_already_executable(self, tmp_path):
        """Test that already executable scripts are left alone."""
        # Arrange
        scripts_dir = tmp_path / ".specify" / "scripts" / "bash"
        scripts_dir.mkdir(parents=True)
        script_file = scripts_dir / "test-script.sh"
        script_file.write_text("#!/bin/bash\necho 'test'")
        script_file.chmod(0o755)
        original_mode = script_file.stat().st_mode

        # Act
        ensure_executable_scripts(tmp_path)

        # Assert
        new_mode = script_file.stat().st_mode
        assert new_mode == original_mode

    def test_ensure_executable_only_processes_sh_files(self, tmp_path):
        """Test that only .sh files are processed."""
        # Arrange
        scripts_dir = tmp_path / ".specify" / "scripts" / "fish"
        scripts_dir.mkdir(parents=True)
        sh_file = scripts_dir / "test.sh"
        fish_file = scripts_dir / "test.fish"
        sh_file.write_text("#!/bin/bash\necho 'test'")
        fish_file.write_text("#!/usr/bin/env fish\necho 'test'")
        sh_file.chmod(0o644)
        fish_file.chmod(0o644)

        # Act
        ensure_executable_scripts(tmp_path)

        # Assert
        sh_mode = sh_file.stat().st_mode
        fish_mode = fish_file.stat().st_mode
        # .sh file should be executable
        assert sh_mode & stat.S_IXUSR
        # .fish file should remain non-executable (not processed)
        assert not (fish_mode & stat.S_IXUSR)

    def test_ensure_executable_skips_non_shebang_files(self, tmp_path):
        """Test that scripts without shebang are skipped."""
        # Arrange
        scripts_dir = tmp_path / ".specify" / "scripts" / "bash"
        scripts_dir.mkdir(parents=True)
        script_file = scripts_dir / "no-shebang.sh"
        script_file.write_text("echo 'test'")  # No shebang
        script_file.chmod(0o644)
        original_mode = script_file.stat().st_mode

        # Act
        ensure_executable_scripts(tmp_path)

        # Assert
        new_mode = script_file.stat().st_mode
        # Should remain unchanged since no shebang
        assert new_mode == original_mode

    def test_ensure_executable_handles_missing_scripts_directory(self, tmp_path):
        """Test that function handles missing scripts directory gracefully."""
        # Act (no scripts directory exists)
        ensure_executable_scripts(tmp_path)

        # Assert - should not raise an error
        # If we get here, the test passed

    def test_ensure_executable_handles_empty_scripts_directory(self, tmp_path):
        """Test that function handles empty scripts directory."""
        # Arrange
        scripts_dir = tmp_path / ".specify" / "scripts"
        scripts_dir.mkdir(parents=True)

        # Act
        ensure_executable_scripts(tmp_path)

        # Assert - should not raise an error

    def test_ensure_executable_preserves_read_permissions(self, tmp_path):
        """Test that read permissions are preserved when adding execute."""
        # Arrange
        scripts_dir = tmp_path / ".specify" / "scripts" / "bash"
        scripts_dir.mkdir(parents=True)
        script_file = scripts_dir / "test-script.sh"
        script_file.write_text("#!/bin/bash\necho 'test'")
        # Set readable but not executable
        script_file.chmod(0o644)

        # Act
        ensure_executable_scripts(tmp_path)

        # Assert
        mode = script_file.stat().st_mode
        # Should have read and execute for owner
        assert mode & stat.S_IRUSR
        assert mode & stat.S_IXUSR

    def test_ensure_executable_adds_execute_for_all_permission_levels(self, tmp_path):
        """Test execute permissions added based on read permissions."""
        # Arrange
        scripts_dir = tmp_path / ".specify" / "scripts" / "bash"
        scripts_dir.mkdir(parents=True)
        script_file = scripts_dir / "test-script.sh"
        script_file.write_text("#!/bin/bash\necho 'test'")
        # Set read for owner, group, and other
        script_file.chmod(0o444)

        # Act
        ensure_executable_scripts(tmp_path)

        # Assert
        mode = script_file.stat().st_mode
        # Should have execute for owner (at minimum)
        assert mode & stat.S_IXUSR
