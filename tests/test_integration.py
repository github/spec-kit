"""Integration tests for --spec-dir functionality."""

import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
import typer

# Import module directly to avoid dependency issues
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from specify_cli import app


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
    def test_init_with_invalid_spec_dir_absolute_path(self, mock_check_tool):
        """Test init with invalid absolute path spec directory."""
        mock_check_tool.return_value = True
        
        result = self.runner.invoke(app, [
            'init', 
            'test-project',
            '--ai', 'claude',
            '--script', 'sh',
            '--spec-dir', '/etc/specs',  # Invalid: absolute path
            '--no-git'
        ])
        
        assert result.exit_code == 1
        assert "must be relative to project root" in result.stdout

    @patch('specify_cli.check_tool')
    def test_init_with_invalid_spec_dir_parent_traversal(self, mock_check_tool):
        """Test init with invalid parent traversal spec directory."""
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

    @patch('specify_cli.check_tool')
    def test_init_with_invalid_spec_dir_trailing_slash(self, mock_check_tool):
        """Test init with invalid trailing slash spec directory."""
        mock_check_tool.return_value = True
        
        result = self.runner.invoke(app, [
            'init', 
            'test-project',
            '--ai', 'claude',
            '--script', 'sh',
            '--spec-dir', 'specs/',  # Invalid: trailing slash
            '--no-git'
        ])
        
        assert result.exit_code == 1
        assert "cannot end with a slash or backslash" in result.stdout

    @patch('specify_cli.check_tool')
    def test_init_with_invalid_spec_dir_empty(self, mock_check_tool):
        """Test init with empty spec directory."""
        mock_check_tool.return_value = True
        
        result = self.runner.invoke(app, [
            'init', 
            'test-project',
            '--ai', 'claude',
            '--script', 'sh',
            '--spec-dir', '',  # Invalid: empty
            '--no-git'
        ])
        
        assert result.exit_code == 1
        assert "cannot be empty" in result.stdout

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
            'project_docs',
            '123specs',  # Numeric start
            'specs_v2',  # With underscore
            'my-specs-dir'  # With dashes
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
            
            assert result.exit_code == 0, f"Failed for valid spec_dir: {spec_dir}"
            call_args = mock_download.call_args
            assert call_args.kwargs['spec_dir'] == spec_dir

    @patch('specify_cli.download_and_extract_template')
    @patch('specify_cli.check_tool')
    def test_init_with_nested_spec_dir(self, mock_check_tool, mock_download):
        """Test init with nested spec directory."""
        mock_check_tool.return_value = True
        mock_download.return_value = self.temp_dir
        
        result = self.runner.invoke(app, [
            'init', 
            'test-project',
            '--ai', 'claude',
            '--script', 'sh',
            '--spec-dir', 'documentation/feature-specs',
            '--no-git'
        ])
        
        assert result.exit_code == 0
        call_args = mock_download.call_args
        assert call_args.kwargs['spec_dir'] == 'documentation/feature-specs'

    @patch('specify_cli.download_and_extract_template')
    @patch('specify_cli.check_tool')
    def test_init_here_with_custom_spec_dir(self, mock_check_tool, mock_download):
        """Test init --here with custom spec directory."""
        mock_check_tool.return_value = True
        mock_download.return_value = self.temp_dir
        
        result = self.runner.invoke(app, [
            'init', 
            '--here',
            '--ai', 'claude',
            '--script', 'sh',
            '--spec-dir', 'requirements',
            '--no-git'
        ])
        
        assert result.exit_code == 0
        call_args = mock_download.call_args
        assert call_args.kwargs['spec_dir'] == 'requirements'

    @patch('specify_cli.download_and_extract_template')
    @patch('specify_cli.check_tool')
    def test_init_with_special_characters(self, mock_check_tool, mock_download):
        """Test init with special characters in spec directory."""
        mock_check_tool.return_value = True
        mock_download.return_value = self.temp_dir
        
        # Test valid special characters (should pass)
        valid_special_chars = [
            'spécs',  # Accented character
            'αspecs',  # Greek character
            'specs_测试',  # Chinese character
            'specs-тест',  # Cyrillic character
        ]
        
        for spec_dir in valid_special_chars:
            result = self.runner.invoke(app, [
                'init', 
                f'test-{spec_dir}',
                '--ai', 'claude',
                '--script', 'sh',
                '--spec-dir', spec_dir,
                '--no-git'
            ])
            
            assert result.exit_code == 0, f"Failed for valid unicode spec_dir: {spec_dir}"
            call_args = mock_download.call_args
            assert call_args.kwargs['spec_dir'] == spec_dir

    @patch('specify_cli.download_and_extract_template')
    @patch('specify_cli.check_tool')
    def test_init_with_edge_cases(self, mock_check_tool, mock_download):
        """Test init with edge cases."""
        mock_check_tool.return_value = True
        mock_download.return_value = self.temp_dir
        
        # Test edge cases
        edge_cases = [
            ('s', 'Single character'),
            ('1', 'Single numeric'),
            ('specs123', 'Mixed alphanumeric'),
            ('a' * 255, 'Maximum length'),
        ]
        
        for spec_dir, description in edge_cases:
            result = self.runner.invoke(app, [
                'init', 
                f'test-{description.replace(" ", "-")}',
                '--ai', 'claude',
                '--script', 'sh',
                '--spec-dir', spec_dir,
                '--no-git'
            ])
            
            assert result.exit_code == 0, f"Failed for edge case: {description}"
            call_args = mock_download.call_args
            assert call_args.kwargs['spec_dir'] == spec_dir

    @patch('specify_cli.check_tool')
    def test_init_help_includes_spec_dir(self, mock_check_tool):
        """Test that help includes --spec-dir option."""
        mock_check_tool.return_value = True
        
        result = self.runner.invoke(app, ['init', '--help'])
        
        assert result.exit_code == 0
        assert '--spec-dir' in result.stdout
        assert 'Custom directory path for specifications' in result.stdout
        assert 'default: specs' in result.stdout