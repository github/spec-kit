"""Test spec directory validation functionality."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch
from typer.testing import CliRunner

from specify_cli import validate_spec_dir, app


class TestSpecDirValidation:
    """Test spec directory validation function."""

    def test_valid_spec_dir(self):
        """Test valid spec directory names."""
        valid_dirs = [
            "specs",
            "docs", 
            "requirements",
            "feature-specs",
            "documentation",
            "specifications",
            "s",
            "spec_docs",
            "my-specs-123"
        ]
        
        for spec_dir in valid_dirs:
            result = validate_spec_dir(spec_dir)
            assert result == spec_dir

    def test_empty_spec_dir(self):
        """Test empty spec directory raises error."""
        with patch('specify_cli.console') as mock_console:
            with pytest.raises(SystemExit) as exc_info:
                validate_spec_dir("")
            assert exc_info.value.code == 1
            mock_console.print.assert_called_with("[red]Error:[/red] Spec directory cannot be empty")

    def test_whitespace_only_spec_dir(self):
        """Test whitespace-only spec directory raises error."""
        with patch('specify_cli.console') as mock_console:
            with pytest.raises(SystemExit) as exc_info:
                validate_spec_dir("   ")
            assert exc_info.value.code == 1
            mock_console.print.assert_called_with("[red]Error:[/red] Spec directory cannot be empty")

    def test_absolute_path_spec_dir(self):
        """Test absolute path raises error."""
        absolute_paths = [
            "/etc/specs",
            "C:\\specs",
            "/home/user/specs",
            "C:/Users/user/specs"
        ]
        
        for path in absolute_paths:
            with patch('specify_cli.console') as mock_console:
                with pytest.raises(SystemExit) as exc_info:
                    validate_spec_dir(path)
                assert exc_info.value.code == 1
                mock_console.print.assert_called_with("[red]Error:[/red] Spec directory must be relative to project root, not an absolute path")

    def test_parent_traversal_spec_dir(self):
        """Test parent directory traversal raises error."""
        traversal_paths = [
            "../specs",
            "specs/../..",
            "../../specs",
            "docs/../../specs"
        ]
        
        for path in traversal_paths:
            with patch('specify_cli.console') as mock_console:
                with pytest.raises(SystemExit) as exc_info:
                    validate_spec_dir(path)
                assert exc_info.value.code == 1
                mock_console.print.assert_called_with("[red]Error:[/red] Spec directory cannot contain parent directory traversal (..)")

    def test_invalid_characters_spec_dir(self):
        """Test invalid characters raise error."""
        # Test each invalid character individually
        invalid_chars = ['<', '>', '"', '|', '?', '*', '\0']
        
        for char in invalid_chars:
            with patch('specify_cli.console') as mock_console:
                with pytest.raises(SystemExit) as exc_info:
                    validate_spec_dir(f"specs{char}test")
                assert exc_info.value.code == 1
                mock_console.print.assert_called_with(f"[red]Error:[/red] Spec directory contains invalid characters: {', '.join(invalid_chars)}")
        
        # Test colon separately since it's handled differently
        with patch('specify_cli.console') as mock_console:
            with pytest.raises(SystemExit) as exc_info:
                validate_spec_dir("specs:test")
            assert exc_info.value.code == 1
            mock_console.print.assert_called_with("[red]Error:[/red] Spec directory contains invalid characters: :")

    def test_trailing_slash_spec_dir(self):
        """Test trailing slash raises error."""
        trailing_slash_paths = [
            "specs/",
            "docs\\",
            "requirements/",
            "feature\\"
        ]
        
        for path in trailing_slash_paths:
            with patch('specify_cli.console') as mock_console:
                with pytest.raises(SystemExit) as exc_info:
                    validate_spec_dir(path)
                assert exc_info.value.code == 1
                mock_console.print.assert_called_with("[red]Error:[/red] Spec directory cannot end with a slash or backslash")

    def test_too_long_spec_dir(self):
        """Test too long path raises error."""
        long_path = "a" * 256  # 256 characters, over the 255 limit
        
        with patch('specify_cli.console') as mock_console:
            with pytest.raises(SystemExit) as exc_info:
                validate_spec_dir(long_path)
            assert exc_info.value.code == 1
            mock_console.print.assert_called_with("[red]Error:[/red] Spec directory path is too long (max 255 characters)")

    def test_non_alphanumeric_start_spec_dir(self):
        """Test non-alphanumeric start raises error."""
        invalid_starts = [
            "-specs",
            "_specs",
            ".specs"
        ]
        
        for path in invalid_starts:
            with patch('specify_cli.console') as mock_console:
                with pytest.raises(SystemExit) as exc_info:
                    validate_spec_dir(path)
                assert exc_info.value.code == 1
                mock_console.print.assert_called_with("[red]Error:[/red] Spec directory must start with an alphanumeric character")
        
        # Test leading space separately
        with patch('specify_cli.console') as mock_console:
            with pytest.raises(SystemExit) as exc_info:
                validate_spec_dir(" specs")
            assert exc_info.value.code == 1
            mock_console.print.assert_called_with("[red]Error:[/red] Spec directory cannot start or end with whitespace")

    def test_numeric_start_spec_dir(self):
        """Test numeric start is valid."""
        with patch('specify_cli.console') as mock_console:
            result = validate_spec_dir("123specs")
            assert result == "123specs"
            mock_console.print.assert_not_called()


class TestSpecDirIntegration:
    """Integration tests for spec directory functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()
        self.temp_dir = Path(tempfile.mkdtemp())
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def teardown_method(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('specify_cli.download_and_extract_template')
    @patch('specify_cli.check_tool')
    def test_init_with_default_spec_dir(self, mock_check_tool, mock_download):
        """Test init with default spec directory."""
        mock_check_tool.return_value = True
        mock_download.return_value = self.temp_dir
        
        result = self.runner.invoke(app, [
            'init', 
            'test-project',
            '--ai', 'claude',
            '--script', 'sh',
            '--no-git'
        ])
        
        assert result.exit_code == 0
        mock_download.assert_called_once()
        # Check that specs/ is used by default
        call_args = mock_download.call_args
        assert call_args.kwargs['spec_dir'] == 'specs'

    @patch('specify_cli.download_and_extract_template')
    @patch('specify_cli.check_tool')
    def test_init_with_custom_spec_dir(self, mock_check_tool, mock_download):
        """Test init with custom spec directory."""
        mock_check_tool.return_value = True
        mock_download.return_value = self.temp_dir
        
        result = self.runner.invoke(app, [
            'init', 
            'test-project',
            '--ai', 'claude',
            '--script', 'sh',
            '--spec-dir', 'documentation',
            '--no-git'
        ])
        
        assert result.exit_code == 0
        mock_download.assert_called_once()
        # Check that custom spec directory is passed
        call_args = mock_download.call_args
        assert call_args.kwargs['spec_dir'] == 'documentation'

    @patch('specify_cli.check_tool')
    def test_init_with_invalid_spec_dir(self, mock_check_tool):
        """Test init with invalid spec directory fails."""
        mock_check_tool.return_value = True
        
        result = self.runner.invoke(app, [
            'init', 
            'test-project',
            '--ai', 'claude',
            '--script', 'sh',
            '--spec-dir', '../specs',  # Invalid: parent traversal
            '--no-git'
        ])
        
        assert result.exit_code == 1
        assert "cannot contain parent directory traversal" in result.stdout

    @patch('specify_cli.download_and_extract_template')
    @patch('specify_cli.check_tool')
    def test_init_with_various_valid_spec_dirs(self, mock_check_tool, mock_download):
        """Test init with various valid spec directories."""
        mock_check_tool.return_value = True
        mock_download.return_value = self.temp_dir
        
        valid_spec_dirs = [
            'docs',
            'requirements',
            'feature-specs',
            'specifications',
            'project_docs'
        ]
        
        for spec_dir in valid_spec_dirs:
            result = self.runner.invoke(app, [
                'init', 
                f'test-{spec_dir}',
                '--ai', 'claude',
                '--script', 'sh',
                '--spec-dir', spec_dir,
                '--no-git'
            ])
            
            assert result.exit_code == 0
            call_args = mock_download.call_args
            assert call_args.kwargs['spec_dir'] == spec_dir